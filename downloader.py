import yt_dlp
from tkinter import Tk
from tkinter.filedialog import askdirectory
import os
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def sanitize_filename(filename):
    return ''.join(c for c in filename if c.isalnum() or c in (' ', '_', '-')).rstrip()

def my_hook(d):
    global pbar
    if d['status'] == 'downloading':
        if 'total_bytes' in d:
            total_size = d['total_bytes']
        else:
            total_size = None

        if 'downloaded_bytes' in d and total_size:
            downloaded_size = d['downloaded_bytes']
            percent_complete = downloaded_size / total_size * 100
            pbar.n = percent_complete
            pbar.refresh()

    if d['status'] == 'finished':
        pbar.n = 100
        pbar.refresh()
        pbar.close()
        print(f"\nDone downloading {current_video}")

def download_video(video_url, ydl_opts):
    retries = 3
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            break
        except Exception as e:
            print(f"Error downloading {video_url}: {e}")
            if attempt < retries - 1:
                print(f"Retrying... ({attempt + 1}/{retries})")
                time.sleep(5)
            else:
                print(f"Failed to download {video_url} after {retries} attempts.")

def download_and_update(video_url, ydl_opts, overall_pbar):
    global pbar
    global current_video
    current_video = sanitize_filename(video_url)
    pbar = tqdm(total=100, desc=f"Downloading: {current_video}", bar_format='{l_bar}{bar}| {n:.1f}%')
    download_video(video_url, ydl_opts)
    overall_pbar.update(1)

def download_youtube_playlist():
    playlist_url = input("Enter the YouTube playlist URL: ")
    root = Tk()
    root.withdraw()
    download_path = askdirectory(title="Select Download Folder")

    if not download_path:
        print("No folder selected. Exiting...")
        return

    global pbar
    global current_video

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'progress_hooks': [my_hook],
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'retries': 5,
        'fragment_retries': 5,
        'concurrent_fragment_downloads': 5,
        'http_chunk_size': 10 * 1024 * 1024,  # 10 MB
        'ffmpeg_location': 'C:/ffmpeg/bin'  # Ensure this path points to your ffmpeg bin directory
    }

    start_time = time.time()

    # Fetch metadata once
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
        video_urls = [video['webpage_url'] for video in playlist_info['entries']]

    print(f"Metadata fetched in {time.time() - start_time:.2f} seconds")

    overall_pbar = tqdm(total=len(video_urls), desc='Overall Progress', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')

    with ThreadPoolExecutor(max_workers=20) as executor:  # Increased thread pool size
        futures = [executor.submit(download_and_update, url, ydl_opts, overall_pbar) for url in video_urls]
        for future in as_completed(futures):
            future.result()

    overall_pbar.close()

if __name__ == "__main__":
    download_youtube_playlist()
