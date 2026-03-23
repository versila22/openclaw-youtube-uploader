import os
import sys
import subprocess

# -- Configuration des scripts du Pipeline --
SCRIPT_BRAIN = "generate_script.py"
SCRIPT_TTS = "test_tts.py"
SCRIPT_COMPOSE = "compose_video.py"
SCRIPT_UPLOAD = "upload_youtube.py"

# Chemin vers l'exécutable Python de l'environnement virtuel (CRITIQUE pour l'industrialisation)
PYTHON_EXECUTABLE = sys.executable

def run_step(step_name, script_file, args=None):
    """
    Exécute un script Python du pipeline et gère les erreurs.
    """
    print(f"\n{'='*50}")
    print(f"🔄 ÉTAPE : {step_name}")
    print(f"{'='*50}")
    
    if not os.path.exists(script_file):
        print(f"❌ ERREUR FATALE : Le script '{script_file}' est introuvable.")
        sys.exit(1)
        
    cmd = [PYTHON_EXECUTABLE, script_file]
    if args:
        cmd.extend(args)
        
    try:
        # On lance le sous-processus de manière synchrone
        result = subprocess.run(cmd, check=True, text=True)
        print(f"✅ {step_name} terminé avec succès.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERREUR D'EXÉCUTION lors de l'étape '{step_name}' (Script: {script_file})")
        print(f"Code de sortie de l'erreur : {e.returncode}")
        print("🛑 Arrêt immédiat de l'Orchestrateur pour éviter des effets de bord.")
        sys.exit(1)

def main():
    print("🚀 DÉMARRAGE DE L'ORCHESTRATEUR OPENCLAW YOUTUBE (V2 - IA INJECTÉE)")
    print("Vérification de l'environnement :", PYTHON_EXECUTABLE)
    
    # 0. Récupération du sujet depuis les arguments de la ligne de commande
    if len(sys.argv) < 2:
        print("❌ ERREUR : L'Orchestrateur nécessite un sujet pour la vidéo.")
        print('Usage: python run_pipeline.py "Ton sujet de vidéo entre guillemets"')
        sys.exit(1)
        
    sujet = sys.argv[1]
    print(f"🎯 Lancement de l'Usine Logicielle sur le sujet : '{sujet}'")
    
    # Étape 1 : Le Cerveau (Génération du script par Gemini)
    run_step("Génération du Script et des Métadonnées", SCRIPT_BRAIN, args=[sujet])
    
    # Étape 2 : La Voix (Text-to-Speech ElevenLabs)
    run_step("Génération Audio (Text-to-Speech)", SCRIPT_TTS)
    
    # Étape 3 : Le Corps (Assemblage visuel dynamique et sonore)
    run_step("Composition Vidéo", SCRIPT_COMPOSE)
    
    # Étape 4 : La Livraison (Téléversement final autonome)
    run_step("Upload YouTube", SCRIPT_UPLOAD)
    
    print(f"\n{'='*50}")
    print("🎉 PIPELINE COMPLET EXÉCUTÉ AVEC SUCCÈS ! 🎉")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
