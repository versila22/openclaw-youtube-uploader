import os
import sys
import json
import google.generativeai as genai

# 1. Vérification des arguments
if len(sys.argv) < 2:
    print("❌ ERREUR : Tu dois fournir un sujet. Ex: python generate_script.py 'L histoire de Rome'")
    sys.exit(1)

sujet = sys.argv[1]

# 2. Récupération de la clé API Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERREUR (Guardrail) : La variable d'environnement GEMINI_API_KEY n'est pas définie.")
    print("Exécute : export GEMINI_API_KEY='ta_cle_gemini'")
    sys.exit(1)

print(f"🧠 Appel à Gemini pour le sujet : '{sujet}'...")

# 3. Configuration de l'IA (On utilise le modèle Flash pour la rapidité et le coût)
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 4. Le Prompt d'Ingénierie
prompt = f"""Tu es un créateur de contenu YouTube Short viral.
Écris un script très court (30 secondes max à l'oral, environ 60 mots) sur le sujet suivant : {sujet}.
Ne mets pas de didascalies ni de description visuelle, juste le texte pur à prononcer par la voix off.
Donne aussi un titre accrocheur pour la vidéo.
Tu dois ABSOLUMENT répondre avec un format JSON strict et valide, sans bloc Markdown autour.
Format exact attendu :
{{
  "titre": "Titre accrocheur ici",
  "script": "Texte à lire par la voix off ici..."
}}
"""

try:
    # 5. Appel à l'API
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # Nettoyage du Markdown si Gemini en ajoute quand même
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()

    # 6. Parsing et Sauvegarde
    data = json.loads(text)
    
    # Sauvegarde du script pour ElevenLabs
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(data["script"])
        
    # Sauvegarde des métadonnées pour YouTube
    with open("metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": data["titre"], 
            "description": f"Vidéo générée de A à Z par l'IA d'OpenClaw sur le sujet : {sujet}\n\n#IA #OpenClaw #Shorts"
        }, f, indent=4, ensure_ascii=False)
        
    print("✅ Script et métadonnées générés avec succès !")
    print(f"📝 Titre généré : {data['titre']}")
    
except Exception as e:
    print(f"❌ Erreur lors de la génération ou du parsing JSON : {e}")
    if 'response' in locals():
        print(f"Texte brut reçu : {response.text}")
    sys.exit(1)
