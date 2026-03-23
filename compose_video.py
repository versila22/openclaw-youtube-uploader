import os
import sys
import json
import urllib.request
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip

AUDIO_FILE = "test_audio.mp3"
TIMESTAMPS_FILE = "timestamps.json"
BG_IMAGE_FILE = "background.jpg"
OUTPUT_VIDEO = "output_video.mp4"
FONT_FILE = "Roboto-Black.ttf"
# Téléchargement d'une police libre et ultra lisible (Google Fonts)
FONT_URL = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Black.ttf"

if not os.path.exists(AUDIO_FILE) or not os.path.exists(TIMESTAMPS_FILE):
    print("❌ ERREUR : Les fichiers d'Audio ou de Timestamps sont introuvables.")
    sys.exit(1)

# Guardrail "Architecte" : On ne fait pas confiance au système hôte (Docker/Linux) pour avoir
# ImageMagick et les bonnes polices d'installées. On télécharge notre propre police.
if not os.path.exists(FONT_FILE):
    print("🔤 Téléchargement de la police de caractères (Roboto Black)...")
    urllib.request.urlretrieve(FONT_URL, FONT_FILE)

print("🚀 Lancement de la Composition Vidéo (NIVEAU 3 - Sous-titres dynamiques)...")

try:
    print("🌍 Téléchargement d'une image de fond floutée...")
    # On ajoute un flou encore plus prononcé (blur=4) pour faire ressortir le texte
    response = requests.get("https://picsum.photos/1920/1080?blur=4")
    if response.status_code == 200:
        with open(BG_IMAGE_FILE, 'wb') as f:
            f.write(response.content)
            
    # Chargement de la base
    audio_clip = AudioFileClip(AUDIO_FILE)
    background_clip = ImageClip(BG_IMAGE_FILE).set_duration(audio_clip.duration)
    
    print("📝 Génération des calques de sous-titres via Pillow (100% Python)...")
    with open(TIMESTAMPS_FILE, "r", encoding="utf-8") as f:
        words_data = json.load(f)
        
    subtitle_clips = []
    
    # Création d'une image transparente individuelle pour chaque mot lu !
    for item in words_data:
        word = item["word"].upper() # En majuscules, c'est le standard des Shorts
        start_time = item["start"]
        end_time = item["end"]
        
        # Astuce : on prolonge très légèrement l'affichage du mot (0.1s) pour éviter l'effet "stroboscope"
        duration = (end_time - start_time) + 0.1 
        
        # Image transparente (1920x1080)
        img = Image.new('RGBA', (1920, 1080), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        # Taille massive (130px) pour l'impact visuel
        font = ImageFont.truetype(FONT_FILE, 130)
        
        # Calcul de la position (centrage horizontal, légèrement plus bas que le centre)
        bbox = draw.textbbox((0, 0), word, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (1920 - w) / 2
        y = (1080 - h) / 2
        
        # Dessin du texte : Jaune pétant avec un gros contour noir de 8px pour la lisibilité
        draw.text((x, y), word, font=font, fill=(255, 255, 0, 255), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        
        # Conversion "magique" de l'image Pillow (NumPy) en Clip MoviePy
        txt_clip = ImageClip(np.array(img)).set_start(start_time).set_duration(duration)
        subtitle_clips.append(txt_clip)

    print(f"🎬 Fusion de {len(subtitle_clips)} mots-clips sur la timeline principale...")
    
    # La magie de CompositeVideoClip : on lui donne le fond puis la liste de tous nos mots !
    final_video = CompositeVideoClip([background_clip] + subtitle_clips)
    final_video = final_video.set_audio(audio_clip)

    print(f"⚙️ Exportation du Build vers : {OUTPUT_VIDEO} (Cela peut prendre un peu plus de temps)...")
    final_video.write_videofile(
        OUTPUT_VIDEO, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        audio_bitrate="192k",
        ffmpeg_params=["-pix_fmt", "yuv420p"], # CRITIQUE : Force le format de pixel standard web
        logger=None # Désactive la console spammy
    )
    print("✅ Vidéo NIVEAU 3 (Sous-titrée) générée avec succès !")

except Exception as e:
    print(f"❌ Erreur de composition vidéo : {e}")
    sys.exit(1)
