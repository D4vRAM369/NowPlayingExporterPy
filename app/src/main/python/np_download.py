
import csv
import os
import yt_dlp

def download_songs(csv_path, download_folder, callback=None):
    """
    Downloads songs from a CSV file using yt-dlp.

    Args:
        csv_path (str): The absolute path to the CSV file.
        download_folder (str): The absolute path to the folder where songs will be saved.
        callback (object): A callback object with an onProgressUpdate method.
    """
    
    def progress_hook(d):
        if callback:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0.0%')
                speed = d.get('_speed_str', '0.0B/s')
                eta = d.get('_eta_str', '00:00')
                callback.onProgressUpdate(f"    -> Descargando: {percent} a {speed}, ETA: {eta}")
            elif d['status'] == 'finished':
                callback.onProgressUpdate(f"  -> Descarga completa: {d['filename']}")

    results = {"success": [], "errors": []}

    # Ensure the download folder exists
    os.makedirs(download_folder, exist_ok=True)

    # yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        # Save files to the specified folder with a clean name
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'default_search': 'ytsearch',
        'noplaylist': True,
        'nocheckcertificate': True, # Can help avoid some SSL/TLS verification errors
        'progress_hooks': [progress_hook],
    }

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if not row:
                    continue
                
                song_title = row.get('title', '')
                artist_name = row.get('artist', '')
                search_query = f"{artist_name} - {song_title}"

                if not artist_name or not song_title:
                    continue

                try:
                    if callback:
                        callback.onProgressUpdate(f"Buscando: {search_query}")
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([search_query])
                    results["success"].append(search_query)
                except Exception as e:
                    if callback:
                        callback.onProgressUpdate(f"Error descargando {search_query}: {e}")
                    results["errors"].append({"query": search_query, "error": str(e)})

    except FileNotFoundError:
        error_message = f"CSV file not found at: {csv_path}"
        print(error_message)
        results["errors"].append({"query": "File Operation", "error": error_message})
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        results["errors"].append({"query": "General", "error": error_message})

    return results

