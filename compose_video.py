import os
import sys
import json
import urllib.request
import requests
import numpy as np
import random
import glob
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, CompositeAudioClip
import moviepy.audio.fx.all as afx
import moviepy.video.fx.all as vfx
import openai # L'intégration officielle OpenAI

AUDIO_FILE = "test_audio.mp3"
TIMESTAMPS_FILE = "timestamps.json"
SCENES_FILE = "scenes.json"
OUTPUT_VIDEO = "output_video.mp4"
FONT_FILE = "Roboto-Black.ttf"
FONT_URL = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Black.ttf"
MUSIC_DIR = "assets/music/"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not os.path.exists(AUDIO_FILE) or not os.path.exists(TIMESTAMPS_FILE) or not os.path.exists(SCENES_FILE):
    print("❌ ERREUR : Les fichiers d'Audio, Timestamps ou Scenes sont introuvables.")
    sys.exit(1)

if not OPENAI_API_KEY:
    print("❌ ERREUR (Guardrail) : OPENAI_API_KEY non définie.")
    print("Exécute : export OPENAI_API_KEY='sk-...'")
    sys.exit(1)

if not os.path.exists(FONT_FILE):
    urllib.request.urlretrieve(FONT_URL, FONT_FILE)

print("🚀 Lancement de la Composition (NIVEAU 7 : DALL-E 3 + Ken Burns + BGM)...")

try:
    # 0. Initialisation du client OpenAI
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    voice_clip = AudioFileClip(AUDIO_FILE)
    audio_duration = voice_clip.duration
    
    # === PHASE 1 : LE SOUND DESIGN (Musique de fond) ===
    final_audio = voice_clip
    if os.path.exists(MUSIC_DIR):
        music_files = glob.glob(os.path.join(MUSIC_DIR, "*.mp3"))
        if music_files:
            chosen_music = random.choice(music_files)
            print(f"🔊 Musique : {os.path.basename(chosen_music)}")
            bgm_clip = AudioFileClip(chosen_music)
            bgm_clip = afx.audio_loop(bgm_clip, duration=audio_duration)
            bgm_clip = bgm_clip.volumex(0.1)
            final_audio = CompositeAudioClip([bgm_clip, voice_clip])
    
    # === PHASE 2 : RERANKING VISUEL (Génération DALL-E 3 + Ken Burns) ===
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        scenes = json.load(f)
        
    num_scenes = len(scenes)
    duration_per_scene = audio_duration / num_scenes
    background_clips = []
    
    for i, scene in enumerate(scenes):
        # On utilise le prompt complexe et hyper-détaillé généré par Gemini
        image_prompt = scene.get("image_prompt", "cyberpunk futuristic neon lights 8k resolution")
        print(f"🎨 Génération de la scène {i+1}/{num_scenes} (DALL-E 3)...")
        print(f"   Prompt: '{image_prompt}'")
        
        bg_img_file = f"dalle_scene_{i}.jpg"
        
        try:
            # L'API d'OpenAI a parfois des sautes d'humeur. On gère les retrys et les Timeouts.
            response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt + " -- Vertical cinematic shot, dramatic lighting, high contrast, 8k.",
                size="1024x1792", 
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            
            # Téléchargement de l'image fraîchement générée
            img_res = requests.get(image_url, stream=True, timeout=30)
            if img_res.status_code == 200:
                with open(bg_img_file, 'wb') as f:
                    for chunk in img_res.iter_content(1024):
                        f.write(chunk)
                print("   ✅ Image DALL-E 3 téléchargée avec succès.")
            else:
                raise Exception(f"HTTP {img_res.status_code} au téléchargement de l'URL DALL-E")
                
        except Exception as api_err:
            print(f"   ⚠️ Erreur API OpenAI / Réseau : {api_err}. Fallback sémantique sur Picsum.")
            # Fallback en cas d'erreur DALL-E (ex: quota dépassé, erreur réseau)
            seed = abs(hash(scene.get("pexels_keyword", "tech"))) % 10000 
            url_secours = f"https://picsum.photos/seed/{seed}/1080/1920?blur=4"
            headers_img = {'User-Agent': 'Mozilla/5.0'}
            res_secours = requests.get(url_secours, stream=True, timeout=15, headers=headers_img)
            with open(bg_img_file, 'wb') as f:
                for chunk in res_secours.iter_content(1024):
                    f.write(chunk)
            
        # --- L'EFFET KEN BURNS (Zoom Lent) ---
        # On crée le clip à partir de l'image générée
        clip = ImageClip(bg_img_file)
        
        # Patch Pillow 10+ pour le redimensionnement MoviePy
        if not hasattr(Image, 'ANTIALIAS'):
            Image.ANTIALIAS = Image.LANCZOS
            
        # 1. On redimensionne au format exact du Short (au cas où DALL-E sort du 1024x1792)
        clip = clip.resize((1080, 1920))
        
        # 2. On applique un zoom mathématique lent de 1.0 (taille normale) à 1.15 (+15%) sur la durée de la scène
        # C'est LA magie du dynamisme visuel sans utiliser de vidéo
        def zoom_effect(t):
            # Calcule un facteur de zoom progressif en fonction du temps 't' de la scène
            # La formule : 1 + (0.15 * (temps_actuel / durée_totale_scene))
            zoom_factor = 1 + 0.15 * (t / duration_per_scene)
            return zoom_factor
            
        # On applique le redimensionnement dynamique (resize) avec notre fonction de zoom
        # Et on le "crop" (rogne) immédiatement au centre en 1080x1920 pour qu'il ne déborde pas de l'écran en zoomant
        clip = clip.resize(zoom_effect).crop(x_center=540, y_center=960, width=1080, height=1920)
        
        # 3. Positionnement temporel et assombrissement
        clip = clip.set_start(i * duration_per_scene).set_duration(duration_per_scene)
        clip = clip.fl_image(lambda image: (image * 0.6).astype(np.uint8)) # Assombrir de 40% pour les sous-titres
        
        background_clips.append(clip)
        
    # === SOUS-TITRES DYNAMIQUES ===
    print("📝 Incrustation des sous-titres Shorts (Police jaune, contour noir)...")
    with open(TIMESTAMPS_FILE, "r", encoding="utf-8") as f:
        words_data = json.load(f)
        
    subtitle_clips = []
    for item in words_data:
        word = item["word"].upper()
        start_time = item["start"]
        end_time = item["end"]
        duration = (end_time - start_time) + 0.1 
        
        img = Image.new('RGBA', (1080, 1920), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(FONT_FILE, 110)
        
        bbox = draw.textbbox((0, 0), word, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (1080 - w) / 2
        y = (1920 - h) / 2
        
        draw.text((x, y), word, font=font, fill=(255, 255, 0, 255), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        txt_clip = ImageClip(np.array(img)).set_start(start_time).set_duration(duration)
        subtitle_clips.append(txt_clip)

    print(f"🎬 Fusion finale (DALL-E 3 + Ken Burns + Sous-Titres + Audio)...")
    final_video = CompositeVideoClip(background_clips + subtitle_clips)
    final_video = final_video.set_audio(final_audio)

    print(f"⚙️ Exportation (Render) vers : {OUTPUT_VIDEO} (Traitement des zooms en cours...)...")
    final_video.write_videofile(
        OUTPUT_VIDEO, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        audio_bitrate="192k",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        logger=None
    )
    print("✅ Vidéo NIVEAU 7 (DALL-E 3 Qualité Agence) générée avec succès !")

except Exception as e:
    print(f"❌ Erreur de composition vidéo : {e}")
    sys.exit(1)
