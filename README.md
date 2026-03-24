# 🚀 openclaw-youtube-uploader

Ce projet est une solution d'automatisation conçue pour simplifier et accélérer le processus de publication de contenu sur YouTube. Intégré à l'écosystème OpenClaw, il permet de gérer et de téléverser des vidéos sur votre chaîne YouTube de manière programmatique.

## ✨ Fonctionnalités (hypothétiques, à confirmer avec le code !)

-   **Upload Automatisé :** Téléversement de vidéos sur YouTube à des intervalles ou selon des déclencheurs définis.
-   **Gestion des Métadonnées :** Possibilité de définir titres, descriptions, tags, catégories et paramètres de confidentialité pour chaque vidéo.
-   **Intégration OpenClaw :** Conçu pour fonctionner au sein de l'environnement OpenClaw pour une gestion facilitée des workflows d'automatisation.

## 🛠️ Configuration

Pour utiliser cet uploader, vous aurez besoin de :

-   Accès à l'API YouTube Data v3 (via Google Cloud Console).
-   Un fichier de configuration (`client_secrets.json` ou des variables d'environnement) pour l'authentification OAuth2 avec YouTube.
-   Vos identifiants Google Gemini API (si le projet intègre des fonctionnalités GenAI pour la génération de métadonnées).

## 🚀 Utilisation (Exemple)

```bash
# Exemple de commande pour lancer l'uploader (à adapter)
python main.py --video_path "./path/to/your/video.mp4" --title "Mon Titre de Vidéo AI" --description "Description générée par IA"
```
