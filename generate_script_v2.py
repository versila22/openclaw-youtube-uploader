import sys
import json
import os
from google import genai

def main():
    json_path = "temp_processing/video.json"
    if not os.path.exists(json_path):
        print(f"{json_path} not found. Ensure transcription is complete.")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    text = data.get("text", "")
    if not text:
        print("No text found in JSON.")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)

    system_instruction = (
        "Tu es Jayvis, l'expert IA et coach de Jerome. Ton objectif est de transformer une transcription brute "
        "en un script vidéo français de 15-20 minutes à forte valeur ajoutée pour son Personal Branding IA.\n\n"
        "CONSIGNES DE RÉDACTION :\n"
        "1. Style : Percutant, expert, pédagogue, avec une pointe d'humour.\n"
        "2. Structure : Format 'Script de tournage' avec deux colonnes :\n"
        "   - Colonne AUDIO : Le texte que Jerome doit lire (ou faire lire par son clone ElevenLabs).\n"
        "   - Colonne VISUEL : Indications sur les extraits de la vidéo d'origine à utiliser (basé sur le contenu) "
        "ou idées de B-roll/graphismes.\n"
        "3. Contenu : Supprime le superflu, garde l'essence stratégique et technique.\n"
    )

    prompt = f"Transcription brute de la vidéo source :\n\n{text}"

    print("Génération du script stratégique avec Gemini 3.1 Pro Preview...")
    response = client.models.generate_content(
        model='gemini-3.1-pro-preview',
        config={'system_instruction': system_instruction},
        contents=prompt,
    )

    script_text = response.text

    with open("script_strategique.md", "w", encoding="utf-8") as f:
        f.write(script_text)

    print(f"✅ Script généré avec succès dans script_strategique.md ({len(script_text)} caractères)")

if __name__ == "__main__":
    main()