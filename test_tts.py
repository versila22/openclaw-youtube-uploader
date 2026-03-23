import os
import requests
import sys

# Récupération de la clé depuis l'environnement
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    print("❌ ERREUR (Guardrail) : La variable d'environnement ELEVENLABS_API_KEY n'est pas définie.")
    print("Assure-toi de l'avoir exportée dans ton terminal : export ELEVENLABS_API_KEY='ta_cle'")
    sys.exit(1)

# Voice ID (Adam - voix masculine standard pour l'exemple)
VOICE_ID = "21m00Tcm4TlvDq8ikWAM" # ID de Rachel pour le test 
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY
}

# --- Injection du Cerveau (Lecture du script) ---
script_text = "Texte par défaut en cas d'erreur du pipeline."
if os.path.exists("script.txt"):
    with open("script.txt", "r", encoding="utf-8") as f:
        script_text = f.read().strip()

data = {
    "text": script_text,
    "model_id": "eleven_multilingual_v2", # Recommandé pour le français et autres langues
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
    }
}

print(f"🚀 Lancement du test Text-to-Speech (Voix ID: {VOICE_ID})...")
print("Appel à l'API ElevenLabs en cours (monitoring latence)...")

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    output_filename = "test_audio.mp3"
    with open(output_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print(f"✅ Succès de l'opération ! Le fichier audio a été sauvegardé sous : {output_filename}")
else:
    print(f"❌ Erreur HTTP {response.status_code}")
    print(f"Détails de l'erreur : {response.text}")
