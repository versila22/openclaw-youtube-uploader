import os
import sys
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# -- Configuration des chemins --
# Le script est dans /data/.openclaw/workspace/openclaw-youtube-uploader
# Mais on a placé client_secret.json dans /data/.openclaw/workspace/config/ pour la sécurité
CLIENT_SECRETS_FILE = "/data/.openclaw/workspace/openclaw-youtube-uploader/config/client_secret.json"
TOKEN_FILE = "/data/.openclaw/workspace/openclaw-youtube-uploader/config/token.json"

VIDEO_FILE = "output_video.mp4"

# Ce scope autorise l'upload de vidéos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    print("🔐 Initialisation de l'authentification YouTube...")
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ ERREUR CRITIQUE (Guardrail) : Le fichier secret client est introuvable à l'emplacement : {CLIENT_SECRETS_FILE}")
        print("Assure-toi de l'avoir bien téléchargé depuis Google Cloud et placé dans le dossier config/ de ton workspace principal.")
        sys.exit(1)

    credentials = None
    # 1. Tenter de charger un token existant
    if os.path.exists(TOKEN_FILE):
        print("🔄 Chargement du token d'authentification existant...")
        try:
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except ValueError as e:
            print(f"⚠️ Avertissement : Le fichier token.json est corrompu ou invalide. Il va être ignoré. Erreur : {e}")
            # On ignore l'erreur, le flux ci-dessous va regénérer un token.
            pass

    # 2. Si pas de token valide, lancer le flux d'autorisation OAuth2
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("🔄 Rafraîchissement du token expiré...")
            credentials.refresh(google.auth.Request())
        else:
            print("🌐 Démarrage du flux d'autorisation initial OAuth2 (Une action manuelle sera requise)...")
            
            # ATTENTION ARCHITECTURE :
            # Sur un VPS sans interface graphique (Headless), on DOIT utiliser run_console() 
            # et non run_local_server() qui essaierait d'ouvrir un navigateur sur le serveur distant.
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            
            # Utilisation de run_console() pour les environnements serveur
            try:
                credentials = flow.run_console()
            except AttributeError:
                 print("⚠️ La méthode run_console n'est plus supportée dans les versions récentes de google-auth-oauthlib.")
                 print("Nous allons utiliser un contournement en générant une URL manuelle.")
                 
                 # Mode manuel "out of band" (OOB) qui est la solution de repli standard
                 flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                 auth_url, _ = flow.authorization_url(prompt='consent')
                 
                 print("\n" + "="*60)
                 print("🚨 ACTION MANUELLE REQUISE POUR L'AUTHENTIFICATION YOUTUBE 🚨")
                 print("="*60)
                 print("1. Copie cette URL et ouvre-la dans le navigateur de TON ordinateur personnel :")
                 print(f"\n{auth_url}\n")
                 print("2. Connecte-toi avec le compte Google de ta chaîne YouTube.")
                 print("3. Autorise l'application à uploader des vidéos.")
                 print("4. Google va t'afficher un 'Code d'autorisation' (Authorization Code).")
                 print("5. Copie ce code.")
                 print("="*60 + "\n")
                 
                 code = input("👉 Colle le code d'autorisation ici et appuie sur Entrée : ")
                 
                 try:
                    flow.fetch_token(code=code)
                    credentials = flow.credentials
                 except Exception as e:
                     print(f"❌ Erreur lors de la récupération du token avec le code fourni : {e}")
                     sys.exit(1)

        # 3. Sauvegarder le nouveau token pour les prochaines fois
        print(f"💾 Sauvegarde du nouveau token dans : {TOKEN_FILE}")
        # S'assurer que le dossier config/ existe (il devrait, vu que client_secret y est)
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())

    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

def upload_video(youtube, file_path, title, description, privacy_status="private"):
    print(f"\n📤 Préparation de l'upload de : {file_path}")
    print(f"📝 Titre : '{title}'")
    print(f"🔒 Confidentialité : {privacy_status}")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["OpenClaw", "AI", "Test"],
            "categoryId": "22" # People & Blogs
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    # chunksize=-1 signifie qu'on laisse la librairie gérer la taille des morceaux (chunks)
    # resumable=True est crucial pour les gros fichiers et la stabilité réseau
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    print("🚀 Démarrage de l'envoi vers YouTube...")
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = request.execute()
        print("\n✅ UPLOAD RÉUSSI !")
        print(f"🔗 ID de la vidéo YouTube : {response['id']}")
        print(f"Tu peux la voir (en privé) ici : https://youtu.be/{response['id']}")
    except googleapiclient.errors.HttpError as e:
        print(f"\n❌ Erreur API YouTube lors de l'upload :")
        print(f"Status code : {e.resp.status}")
        print(f"Détails : {e.content.decode('utf-8')}")
        sys.exit(1)

if __name__ == "__main__":
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ ERREUR (Guardrail) : La vidéo à uploader '{VIDEO_FILE}' est introuvable.")
        print("As-tu bien exécuté le script compose_video.py juste avant ?")
        sys.exit(1)

    # 1. S'authentifier
    youtube_service = get_authenticated_service()

    # Lecture des métadonnées générées par le Cerveau
    video_title = "Test d'Industrialisation OpenClaw"
    video_desc = "Vidéo générée automatiquement par le pipeline AI de Jay (TTS ElevenLabs + Moviepy)."
    
    if os.path.exists("metadata.json"):
        try:
            with open("metadata.json", "r", encoding="utf-8") as f:
                meta = json.load(f)
                video_title = meta.get("title", video_title)
                video_desc = meta.get("description", video_desc)
        except Exception as e:
            print(f"⚠️ Erreur de lecture des métadonnées, utilisation des valeurs par défaut : {e}")

    # 2. Lancer l'upload
    upload_video(
        youtube=youtube_service,
        file_path=VIDEO_FILE,
        title=video_title,
        description=video_desc,
        privacy_status="private" # Toujours tester en privé
    )