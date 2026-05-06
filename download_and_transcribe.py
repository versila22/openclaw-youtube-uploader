import os
import yt_dlp
import subprocess
import json

VIDEO_URL = "https://www.youtube.com/watch?v=PqVbypvxDto"
OUTPUT_DIR = "temp_processing"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_media(url):
    print(f"Téléchargement de la vidéo et de l'audio depuis : {url}")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{OUTPUT_DIR}/%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt',
        'keepvideo': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info['id']
        video_path = f"{OUTPUT_DIR}/{video_id}.mp4"
        audio_path = f"{OUTPUT_DIR}/{video_id}.mp3"
        return video_path, audio_path

def transcribe_audio(audio_path):
    print(f"\nLancement de Whisper (CLI) pour {audio_path}...")
    
    # Appel du CLI Whisper via subprocess, génération des formats json et txt
    command = [
        "whisper",
        audio_path,
        "--model", "base",
        "--output_dir", OUTPUT_DIR,
        "--output_format", "all" # Génère srt, vtt, txt, tsv, json
    ]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la transcription avec Whisper CLI: {e}")
        return None

    json_path = os.path.join(OUTPUT_DIR, f"{os.path.basename(audio_path).split('.')[0]}.json")
    txt_path = os.path.join(OUTPUT_DIR, f"{os.path.basename(audio_path).split('.')[0]}.txt")

    print(f"\n✅ Transcription terminée !")
    print(f"-> Fichiers générés dans le dossier : {OUTPUT_DIR}")
    
    # On renvoie les chemins pour utilisation ultérieure
    return json_path, txt_path

if __name__ == "__main__":
    print("🚀 Début de la Phase 1 : Ingestion & Transcription")
    try:
        video_file, audio_file = download_media(VIDEO_URL)
        print(f"Vidéo enregistrée : {video_file}")
        transcribe_audio(audio_file)
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")
