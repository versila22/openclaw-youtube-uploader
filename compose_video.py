import os
import sys
import requests
from moviepy.editor import AudioFileClip, ImageClip

# Chemins des fichiers
AUDIO_FILE = "test_audio.mp3"
BG_IMAGE_FILE = "background.jpg"
OUTPUT_VIDEO = "output_video.mp4"

# 1. Vérification de l'Audio
if not os.path.exists(AUDIO_FILE):
    print(f"❌ ERREUR : Le fichier audio '{AUDIO_FILE}' est introuvable.")
    sys.exit(1)

print("🚀 Lancement du module de Composition Vidéo (V2 - Visuels Dynamiques)...")

try:
    # 2. Téléchargement d'une image de fond dynamique (1920x1080)
    # On utilise picsum.photos pour avoir une belle image aléatoire libre de droits
    print("🌍 Téléchargement d'une image de fond HD...")
    image_url = "https://picsum.photos/1920/1080?blur=2" # blur=2 ajoute un léger flou élégant
    response = requests.get(image_url)
    
    if response.status_code == 200:
        with open(BG_IMAGE_FILE, 'wb') as f:
            f.write(response.content)
        print(f"📸 Image sauvegardée sous : {BG_IMAGE_FILE}")
    else:
        print(f"❌ Erreur lors du téléchargement de l'image (HTTP {response.status_code})")
        sys.exit(1)

    # 3. Charger l'audio
    print(f"🎵 Chargement de l'audio : {AUDIO_FILE}...")
    audio_clip = AudioFileClip(AUDIO_FILE)
    audio_duration = audio_clip.duration
    
    # 4. Charger l'image de fond et l'ajuster à l'audio
    print(f"🖼️ Création du visuel (durée calée sur l'audio : {audio_duration}s)...")
    # On utilise ImageClip au lieu de ColorClip
    background_clip = ImageClip(BG_IMAGE_FILE)
    
    # On force la durée de l'image pour qu'elle corresponde exactement à l'audio
    background_clip = background_clip.set_duration(audio_duration)

    # 5. Assemblage (Audio + Visuel)
    print("🎬 Fusion de l'audio et de l'image...")
    final_video = background_clip.set_audio(audio_clip)

    # 6. Exportation
    print(f"⚙️ Exportation de la vidéo vers : {OUTPUT_VIDEO}...")
    final_video.write_videofile(
        OUTPUT_VIDEO, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        audio_bitrate="192k",
        logger=None # Désactive les logs verbeux
    )

    print("✅ Succès de l'opération ! La vidéo V2 est prête pour l'upload.")

except Exception as e:
    print(f"❌ Erreur lors de la composition vidéo : {e}")
    sys.exit(1)
finally:
    # Nettoyage de la mémoire
    try:
        if 'audio_clip' in locals(): audio_clip.close()
        if 'background_clip' in locals(): background_clip.close()
        if 'final_video' in locals(): final_video.close()
    except:
        pass
