import os
import sys
import json
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.errors

# -- Configuration des chemins --
TOKEN_FILE = "/data/.openclaw/workspace/openclaw-youtube-uploader/config/token.json"
ANALYTICS_FILE = "/data/.openclaw/workspace/openclaw-youtube-uploader/analytics.json"

# Les mêmes scopes que l'upload pour réutiliser le même token OAuth
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_authenticated_service():
    """Charge le service YouTube Analytics avec le token existant."""
    print("🔐 Vérification de l'authentification YouTube Analytics...")
    if not os.path.exists(TOKEN_FILE):
        print(f"⚠️ Aucun token d'authentification trouvé à {TOKEN_FILE}.")
        print("Démarrage du flux d'autorisation initial OAuth2 (Une action manuelle sera requise)...")
        
        CLIENT_SECRETS_FILE = "/data/.openclaw/workspace/openclaw-youtube-uploader/config/client_secret.json"
        
        if not os.path.exists(CLIENT_SECRETS_FILE):
            print(f"❌ ERREUR CRITIQUE : Le fichier secret client est introuvable à l'emplacement : {CLIENT_SECRETS_FILE}")
            sys.exit(1)
            
        import google_auth_oauthlib.flow
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
            
        try:
             # Mode manuel "out of band" (OOB)
             flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
             auth_url, _ = flow.authorization_url(prompt='consent')
             
             print("\n" + "="*60)
             print("🚨 ACTION MANUELLE REQUISE POUR L'AUTHENTIFICATION ANALYTICS 🚨")
             print("="*60)
             print("1. Copie cette URL et ouvre-la dans le navigateur de TON ordinateur personnel :")
             print(f"\n{auth_url}\n")
             print("2. Connecte-toi avec le compte Google de ta chaîne YouTube.")
             print("3. Autorise l'application à lire et gérer tes vidéos.")
             print("4. Google va t'afficher un 'Code d'autorisation' (Authorization Code).")
             print("5. Copie ce code.")
             print("="*60 + "\n")
             
             code = input("👉 Colle le code d'autorisation ici et appuie sur Entrée : ")
             
             flow.fetch_token(code=code)
             credentials = flow.credentials
             
             print(f"💾 Sauvegarde du nouveau token dans : {TOKEN_FILE}")
             os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
             with open(TOKEN_FILE, 'w') as token:
                 token.write(credentials.to_json())
                 
             return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
        except Exception as e:
             print(f"❌ Erreur lors de la récupération du token avec le code fourni : {e}")
             sys.exit(1)

    try:
        # On a besoin d'un scope supplémentaire pour lire les statistiques (read-only)
        # Mais comme on utilise un token généré avec le scope 'upload', Google permet souvent 
        # l'accès basique en lecture aux propres vidéos de l'utilisateur.
        # Pour des analytics profonds, il faudrait demander 'https://www.googleapis.com/auth/yt-analytics.readonly'
        # On va tester avec l'API Data classique (v3) qui donne déjà les vues, likes, commentaires.
        # On utilise notre liste de scopes globale.
        credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if credentials.expired and credentials.refresh_token:
            print("🔄 Rafraîchissement du token expiré...")
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            # Sauvegarde du nouveau token
            with open(TOKEN_FILE, 'w') as token:
                token.write(credentials.to_json())
                
        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    except Exception as e:
        print(f"❌ Erreur d'authentification : {e}")
        sys.exit(1)

def fetch_latest_videos_stats(youtube, max_results=10):
    """Récupère les statistiques (vues, likes, commentaires) des dernières vidéos."""
    print(f"📊 Récupération des statistiques des {max_results} dernières vidéos...")
    
    try:
        # 1. Récupérer l'ID de la chaîne de l'utilisateur (Uploads playlist)
        channels_response = youtube.channels().list(
            mine=True,
            part="contentDetails"
        ).execute()
        
        if not channels_response.get("items"):
            print("❌ Aucune chaîne YouTube trouvée pour ce compte.")
            return []
            
        uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # 2. Récupérer les dernières vidéos de cette playlist
        playlistitems_list_request = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet",
            maxResults=max_results
        )
        playlistitems_list_response = playlistitems_list_request.execute()
        
        video_ids = []
        for item in playlistitems_list_response.get("items", []):
            video_ids.append(item["snippet"]["resourceId"]["videoId"])
            
        if not video_ids:
            print("ℹ️ Aucune vidéo trouvée sur la chaîne.")
            return []
            
        # 3. Récupérer les statistiques précises pour ces vidéos
        videos_list_request = youtube.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics"
        )
        videos_list_response = videos_list_request.execute()
        
        stats_data = []
        for video in videos_list_response.get("items", []):
            title = video["snippet"]["title"]
            stats = video["statistics"]
            
            video_data = {
                "id": video["id"],
                "title": title,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "engagement_score": 0
            }
            
            # Calcul d'un "Score d'Engagement" basique (Likes + Commentaires / Vues)
            if video_data["views"] > 0:
                engagement = ((video_data["likes"] + video_data["comments"]) / video_data["views"]) * 100
                video_data["engagement_score"] = round(engagement, 2)
                
            stats_data.append(video_data)
            
        return stats_data
        
    except googleapiclient.errors.HttpError as e:
        print(f"❌ Erreur API YouTube Analytics : {e}")
        return []

if __name__ == "__main__":
    youtube_service = get_authenticated_service()
    stats = fetch_latest_videos_stats(youtube_service, max_results=5)
    
    if stats:
        # Tri par vues décroissantes
        stats.sort(key=lambda x: x["views"], reverse=True)
        
        print("\n🏆 TOP 5 DES VIDÉOS (Par vues) :")
        for i, s in enumerate(stats):
            print(f"{i+1}. {s['title']}")
            print(f"   👁️ Vues: {s['views']} | 👍 Likes: {s['likes']} | 💬 Coms: {s['comments']} | 📈 Engagement: {s['engagement_score']}%")
            
        # Sauvegarde pour le Cerveau (Gemini)
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Statistiques sauvegardées dans {ANALYTICS_FILE} pour guider les prochains scripts de l'IA.")
    else:
        print("\nℹ️ Pas de statistiques à sauvegarder.")
