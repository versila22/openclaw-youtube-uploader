import os
import sys
import json
from google import genai

# 1. Vérification des arguments
if len(sys.argv) < 2:
    print("❌ ERREUR : Tu dois fournir un sujet.")
    sys.exit(1)

sujet = sys.argv[1]

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERREUR : GEMINI_API_KEY non définie.")
    sys.exit(1)

print(f"🧠 [NIVEAU 1] Prompt Engineering avancé pour le sujet : '{sujet}'...")

# Configuration du nouveau client
client = genai.Client(api_key=api_key)

# --- LECTURE DE L'ANALYTICS (LE FEEDBACK LOOP) ---
analytics_file = "/data/.openclaw/workspace/openclaw-youtube-uploader/analytics.json"
historique_prompt = ""
if os.path.exists(analytics_file):
    try:
        with open(analytics_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
            
        if stats and len(stats) > 0:
            # On trie pour trouver la meilleure vidéo et la pire (en vues)
            stats.sort(key=lambda x: x["views"], reverse=True)
            top_video = stats[0]
            pire_video = stats[-1]
            
            historique_prompt = f"""
[CONTEXTE D'AUDIENCE ET FEEDBACK LOOP]
Voici les statistiques réelles de tes dernières vidéos sur la chaîne. Sers-t'en pour optimiser ton nouveau script.
- La vidéo qui a le MIEUX marché s'appelle "{top_video['title']}" avec {top_video['views']} vues et un engagement de {top_video['engagement_score']}%. Analyse pourquoi ce titre et ce sujet ont marché (ton ? mystère ?).
- La vidéo qui a le MOINS marché s'appelle "{pire_video['title']}" avec {pire_video['views']} vues. Évite ce style ou ce type d'accroche.
Ton objectif est de battre le record de {top_video['views']} vues.
"""
    except Exception as e:
        print(f"⚠️ Erreur lecture Analytics (Ignoré) : {e}")

# CHANGEMENT ARCHITECTURAL NIVEAU 9 : Le Prompt Auto-Apprenant (Feedback Loop)
prompt = f"""Tu es le meilleur copywriter de YouTube Shorts et TikTok au monde, spécialisé dans la Tech et l'Informatique.
Ton objectif est de retenir l'attention du spectateur à 100% sur une durée d'environ 50 à 60 secondes.

{historique_prompt}

Écris un script ultra-fascinant, au rythme effréné, sur le nouveau sujet : {sujet}.

Structure obligatoire en 5 à 6 scènes dynamiques :
1. HOOK (0-3s) : Une question impossible ou une affirmation choc qui brise les croyances.
2. BUILD-UP (3-15s) : L'introduction du mystère ou du problème complexe de manière très imagée.
3. CLIMAX (15-35s) : La révélation technique fascinante expliquée avec des analogies simples mais puissantes.
4. TWIST (35-50s) : Une implication inattendue ou effrayante pour le futur.
5. CTA (50-60s) : Un appel à l'action hyper organique (Abonne-toi pour comprendre le futur).

RÈGLE ABSOLUE POUR LA VOIX OFF : 
- Écris des phrases courtes et percutantes.
- N'écris AUCUN MOT entièrement en majuscules dans la clé "texte" (pour éviter qu'ElevenLabs ne l'épelle).
- Le texte total doit faire environ 120 à 150 mots.

RÈGLE POUR LES IMAGES (DALL-E 3) : 
Pour chaque scène, écris un "image_prompt" hyper détaillé en ANGLAIS. 
Décris le sujet, l'action, l'éclairage dramatique (cinematic lighting, neon, glowing), et le style (photorealistic, 8k, unreal engine 5, macro photography). 
Chaque image doit être un chef-d'œuvre visuel qui illustre parfaitement le texte de la scène.

Tu dois ABSOLUMENT répondre avec un format JSON strict et valide.
Format exact attendu :
{{
  "titre": "Titre YouTube Shorts ultra viral (max 60 caractères)",
  "scenes": [
    {{"texte": "Texte de la scène 1 avec casse normale...", "image_prompt": "english detailed prompt for DALL-E..."}},
    {{"texte": "Texte de la scène 2...", "image_prompt": "english detailed prompt..."}},
    {{"texte": "Texte de la scène 3...", "image_prompt": "english detailed prompt..."}}
  ]
}}
"""

try:
    # Nouveau format d'appel
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    text = response.text.strip()
    
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()

    data = json.loads(text)
    
    # 1. Concaténer le texte pour l'audio (ElevenLabs a juste besoin du texte complet)
    full_script = " ".join([scene["texte"] for scene in data["scenes"]])
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(full_script)
        
    # 2. Sauvegarder la structure des scènes pour le montage vidéo (Le Niveau 2)
    with open("scenes.json", "w", encoding="utf-8") as f:
        json.dump(data["scenes"], f, indent=4, ensure_ascii=False)
        
    # 3. Métadonnées YouTube
    with open("metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": data["titre"], 
            "description": f"Généré par l'Usine IA d'OpenClaw.\nSujet : {sujet}\n\n#Shorts #Tech #IA"
        }, f, indent=4, ensure_ascii=False)
        
    print("✅ Cerveau V2 exécuté ! Script structuré en scènes généré.")
    print(f"📝 Titre généré : {data['titre']}")
    
except Exception as e:
    print(f"❌ Erreur lors de la génération du Cerveau : {e}")
    sys.exit(1)
