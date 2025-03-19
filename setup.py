#!/usr/bin/env python
"""
Script d'installation et de configuration du projet ForestAI.
Crée les répertoires nécessaires et prépare l'environnement.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_directory_if_not_exists(path):
    """Crée un répertoire s'il n'existe pas déjà."""
    path = Path(path)
    if not path.exists():
        print(f"Création du répertoire: {path}")
        path.mkdir(parents=True)
    else:
        print(f"Le répertoire existe déjà: {path}")

def setup_data_directories():
    """Crée les répertoires de données."""
    # Répertoires principaux
    data_dir = Path("data")
    create_directory_if_not_exists(data_dir)

    # Sous-répertoires pour les données brutes
    raw_data_directories = [
        "data/raw",
        "data/raw/cadastre",
        "data/raw/bdtopo",
        "data/raw/mnt",
        "data/raw/occupation_sol",
        "data/raw/orthophotos"
    ]
    
    for directory in raw_data_directories:
        create_directory_if_not_exists(directory)
    
    # Répertoires pour les sorties et résultats
    output_directories = [
        "data/outputs",
        "data/processed"
    ]
    
    for directory in output_directories:
        create_directory_if_not_exists(directory)
    
    # Répertoire pour les logs
    create_directory_if_not_exists("logs")

def check_env_files():
    """Vérifie et crée les fichiers .env s'ils n'existent pas."""
    # Fichier .env à la racine
    if not os.path.exists(".env"):
        print("Création du fichier .env à partir de .env.example...")
        shutil.copy(".env.example", ".env")
        print("N'oubliez pas de mettre à jour les valeurs dans le fichier .env")
    else:
        print("Le fichier .env existe déjà")
    
    # Fichier .env pour web
    web_env_path = Path("web/.env")
    if not web_env_path.exists():
        print("Création du fichier .env pour l'interface web...")
        with open(web_env_path, "w") as f:
            f.write("VITE_API_URL=http://localhost:8000")
        print("Fichier web/.env créé")
    else:
        print("Le fichier web/.env existe déjà")
    
    # Fichier .env pour webui
    webui_env_path = Path("webui/.env")
    if not webui_env_path.exists():
        print("Création du fichier .env pour l'interface webui...")
        with open(webui_env_path, "w") as f:
            f.write("VUE_APP_API_URL=http://localhost:8000")
        print("Fichier webui/.env créé")
    else:
        print("Le fichier webui/.env existe déjà")

def install_dependencies():
    """Installe les dépendances Python."""
    print("Installation des dépendances Python...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("Dépendances Python installées avec succès")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation des dépendances Python: {e}")
        return False

    return True

def install_web_dependencies():
    """Installe les dépendances pour l'interface web."""
    print("Installation des dépendances pour l'interface web...")
    if os.path.exists("web/package.json"):
        try:
            os.chdir("web")
            subprocess.run(["npm", "install"], check=True)
            os.chdir("..")
            print("Dépendances web installées avec succès")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation des dépendances web: {e}")
            return False
    else:
        print("Le fichier web/package.json n'existe pas, dépendances web ignorées")
    
    return True

def install_webui_dependencies():
    """Installe les dépendances pour l'interface webui."""
    print("Installation des dépendances pour l'interface webui...")
    if os.path.exists("webui/package.json"):
        try:
            os.chdir("webui")
            subprocess.run(["npm", "install"], check=True)
            os.chdir("..")
            print("Dépendances webui installées avec succès")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation des dépendances webui: {e}")
            return False
    else:
        print("Le fichier webui/package.json n'existe pas, dépendances webui ignorées")
    
    return True

def main():
    """Fonction principale du script de setup."""
    print("=== Installation et configuration de ForestAI ===")
    
    # Création des répertoires
    print("\n--- Création des répertoires de données ---")
    setup_data_directories()
    
    # Vérification et création des fichiers .env
    print("\n--- Configuration des fichiers d'environnement ---")
    check_env_files()
    
    # Installation des dépendances
    print("\n--- Installation des dépendances ---")
    python_deps_success = install_dependencies()
    web_deps_success = install_web_dependencies()
    webui_deps_success = install_webui_dependencies()
    
    # Bilan
    print("\n=== Bilan de l'installation ===")
    print(f"Dépendances Python: {'✓' if python_deps_success else '✗'}")
    print(f"Dépendances web: {'✓' if web_deps_success else '✗'}")
    print(f"Dépendances webui: {'✓' if webui_deps_success else '✗'}")
    
    print("\n=== Instructions pour démarrer ForestAI ===")
    print("1. Démarrer le serveur API:")
    print("   python api_server.py")
    print("2. Démarrer l'interface web (dans un autre terminal):")
    print("   cd web && npm run dev")
    print("   ou")
    print("   cd webui && npm run serve")
    print("\nL'API sera accessible à: http://localhost:8000")
    print("L'interface web sera accessible à l'adresse indiquée dans le terminal (généralement http://localhost:3000 ou http://localhost:8080)")

if __name__ == "__main__":
    main()
