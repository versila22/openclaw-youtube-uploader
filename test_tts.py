import os
import sys
import json
import requests
import base64

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    print("❌ ERREUR : La variable d'environnement ELEVENLABS_API_KEY n'est pas définie.")
    sys.exit(1)

VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
# CHANGEMENT ARCHITECTURAL : Nouvel endpoint pour récupérer le timing des mots
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps"

headers = {
    "Content-Type": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY
}

script_text = "Texte par défaut en cas d'erreur du pipeline."
if os.path.exists("script.txt"):
    with open("script.txt", "r", encoding="utf-8") as f:
        script_text = f.read().strip()

data = {
    "text": script_text,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
}

print(f"🚀 Génération Audio ET Timestamps (Voix ID: {VOICE_ID})...")
response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    res_json = response.json()
    
    # 1. Sauvegarde de l'audio (qui est renvoyé encodé en Base64)
    audio_bytes = base64.b64decode(res_json["audio_base64"])
    with open("test_audio.mp3", 'wb') as f:
        f.write(audio_bytes)
        
    # 2. Traitement des timestamps (L'API renvoie des lettres, on doit reconstituer les mots)
    alignment = res_json.get("alignment", {})
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])
    
    words = []
    current_word = ""
    current_start = None
    
    for i, char in enumerate(chars):
        if char.strip() == "": # Un espace signifie la fin du mot précédent
            if current_word:
                words.append({"word": current_word, "start": current_start, "end": ends[i-1]})
                current_word = ""
                current_start = None
        else:
            if current_word == "":
                current_start = starts[i]
            current_word += char
            
    if current_word: # Ne pas oublier le tout dernier mot !
        words.append({"word": current_word, "start": current_start, "end": ends[-1]})
        
    # 3. Sauvegarde du dictionnaire de timing pour le module vidéo
    with open("timestamps.json", "w", encoding="utf-8") as f:
        json.dump(words, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Audio et Timestamps générés avec succès ! ({len(words)} mots synchronisés à la milliseconde)")
else:
    print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    sys.exit(1)
