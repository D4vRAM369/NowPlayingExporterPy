import csv
import os
import yt_dlp
import time

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
LONG_SLEEP_INTERVAL = 15 # Descargas antes de un sleep largo
LONG_SLEEP_SECONDS = 4 # Duración del sleep largo
VERY_LONG_SLEEP_INTERVAL = 70 # Descargas antes de un sleep muy largo
VERY_LONG_SLEEP_SECONDS = 30 # Duración del sleep muy largo

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
            download_count = 0
            for row in reader:
                if not row:
                    continue
                
                song_title = row.get('title', '')
                artist_name = row.get('artist', '')
                search_query = f"{artist_name} - {song_title}"

                if not artist_name or not song_title:
                    continue

                for attempt in range(MAX_RETRIES):
                    try:
                        if callback:
                            callback.onProgressUpdate(f"Buscando: {search_query} (Intento {attempt + 1}/{MAX_RETRIES})")
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([search_query])
                        results["success"].append(search_query)
                        download_count += 1
                        if download_count % VERY_LONG_SLEEP_INTERVAL == 0:
                            if callback:
                                callback.onProgressUpdate(f"Pausa MUY larga de {VERY_LONG_SLEEP_SECONDS} segundos para evitar detección de bot...")
                            time.sleep(VERY_LONG_SLEEP_SECONDS)
                        elif download_count % LONG_SLEEP_INTERVAL == 0:
                            if callback:
                                callback.onProgressUpdate(f"Pausa larga de {LONG_SLEEP_SECONDS} segundos para evitar detección de bot...")
                            time.sleep(LONG_SLEEP_SECONDS)
                        break # Salir del bucle de reintentos si tiene éxito
                    except Exception as e:
                        error_msg = str(e)
                        if callback:
                            callback.onProgressUpdate(f"Error descargando {search_query}: {error_msg}")
                        if attempt < MAX_RETRIES - 1:
                            if callback:
                                callback.onProgressUpdate(f"Reintentando en {RETRY_DELAY_SECONDS} segundos...")
                            time.sleep(RETRY_DELAY_SECONDS)
                        else:
                            results["errors"].append({"query": search_query, "error": error_msg})

    except FileNotFoundError:
        error_message = f"CSV file not found at: {csv_path}"
        if callback:
            callback.onProgressUpdate(error_message)
        results["errors"].append({"query": "File Operation", "error": error_message})
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        if callback:
            callback.onProgressUpdate(error_message)
        results["errors"].append({"query": "General", "error": error_message})

    return results