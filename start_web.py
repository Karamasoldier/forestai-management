#!/usr/bin/env python
"""
Script pour démarrer l'API ForestAI et l'interface web.
Lance le serveur API et l'application web dans des processus séparés.
"""

import os
import sys
import subprocess
import argparse
import time
import signal
import platform
from pathlib import Path

# Variables globales pour les processus
api_process = None
web_process = None

def parse_arguments():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description='Démarrer ForestAI API et interface web')
    parser.add_argument('--api-only', action='store_true', help='Démarrer uniquement l\'API')
    parser.add_argument('--web-only', action='store_true', help='Démarrer uniquement l\'interface web')
    parser.add_argument('--web-type', choices=['vite', 'vue'], default='vue', 
                        help='Type d\'interface web à lancer (vite pour web/ ou vue pour webui/)')
    parser.add_argument('--api-port', type=int, default=8000, help='Port pour l\'API (défaut: 8000)')
    parser.add_argument('--api-host', type=str, default='0.0.0.0', help='Hôte pour l\'API (défaut: 0.0.0.0)')
    parser.add_argument('--reload', action='store_true', help='Activer le rechargement automatique pour l\'API')
    
    return parser.parse_args()

def start_api_server(host, port, reload):
    """Démarre le serveur API ForestAI."""
    print(f"Démarrage de l'API ForestAI sur {host}:{port}...")
    cmd = [sys.executable, "api_server.py", "--host", host, "--port", str(port)]
    
    if reload:
        cmd.append("--reload")
    
    return subprocess.Popen(cmd)

def start_web_interface(web_type):
    """Démarre l'interface web."""
    if web_type == 'vite':
        # Interface web avec Vite (web/)
        print("Démarrage de l'interface web Vite...")
        cwd = Path('web')
        if not cwd.exists() or not (cwd / 'package.json').exists():
            print("Erreur: Le répertoire 'web' ou son fichier package.json n'existe pas.")
            return None
        
        cmd = ["npm", "run", "dev"]
    else:
        # Interface web avec Vue CLI (webui/)
        print("Démarrage de l'interface web Vue...")
        cwd = Path('webui')
        if not cwd.exists() or not (cwd / 'package.json').exists():
            print("Erreur: Le répertoire 'webui' ou son fichier package.json n'existe pas.")
            return None
        
        cmd = ["npm", "run", "serve"]
    
    # Déterminer les options de redirection adaptées à la plateforme
    if platform.system() == 'Windows':
        # Sur Windows, rediriger vers PIPE pour éviter les problèmes d'encodage
        return subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        # Sur Unix/Linux, on peut directement rediriger vers les flux
        return subprocess.Popen(cmd, cwd=str(cwd))

def check_node_npm():
    """Vérifie si Node.js et npm sont installés."""
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["npm", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Erreur: Node.js et npm sont requis pour exécuter l'interface web.")
        print("Veuillez les installer depuis https://nodejs.org/")
        return False

def signal_handler(sig, frame):
    """Gestionnaire de signaux pour arrêter proprement les processus."""
    print("\nArrêt des services...")
    
    if api_process:
        print("Arrêt de l'API ForestAI...")
        api_process.terminate()
    
    if web_process:
        print("Arrêt de l'interface web...")
        web_process.terminate()
    
    # Attendre max 5 secondes pour les processus
    time.sleep(1)
    
    # Forcer la fermeture si nécessaire
    if api_process and api_process.poll() is None:
        print("Forçage de l'arrêt de l'API...")
        if platform.system() == 'Windows':
            api_process.kill()
        else:
            os.killpg(os.getpgid(api_process.pid), signal.SIGKILL)
    
    if web_process and web_process.poll() is None:
        print("Forçage de l'arrêt de l'interface web...")
        if platform.system() == 'Windows':
            web_process.kill()
        else:
            os.killpg(os.getpgid(web_process.pid), signal.SIGKILL)
    
    print("Tous les services ont été arrêtés.")
    sys.exit(0)

def check_env_file(path):
    """Vérifie si le fichier .env existe."""
    env_path = Path(path)
    if not env_path.exists():
        print(f"Attention: Le fichier {env_path} n'existe pas.")
        return False
    return True

def main():
    """Fonction principale."""
    global api_process, web_process
    
    # Capturer les signaux d'interruption
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parser les arguments
    args = parse_arguments()
    
    # Vérifier les fichiers .env
    env_ok = check_env_file('.env')
    if args.web_only or not args.api_only:
        if args.web_type == 'vite':
            web_env_ok = check_env_file('web/.env')
        else:
            web_env_ok = check_env_file('webui/.env')
    
    # Démarrer l'API si demandé
    if not args.web_only:
        api_process = start_api_server(args.api_host, args.api_port, args.reload)
        if not api_process:
            print("Erreur lors du démarrage de l'API. Arrêt du script.")
            sys.exit(1)
        
        # Attendre un peu pour que l'API démarre
        print("Attente du démarrage de l'API...")
        time.sleep(3)
    
    # Démarrer l'interface web si demandé
    if not args.api_only:
        # Vérifier Node.js et npm
        if not check_node_npm():
            if api_process:
                api_process.terminate()
            sys.exit(1)
        
        web_process = start_web_interface(args.web_type)
        if not web_process:
            print("Erreur lors du démarrage de l'interface web. Arrêt du script.")
            if api_process:
                api_process.terminate()
            sys.exit(1)
    
    # Afficher les informations d'accès
    print("\n--- ForestAI est prêt! ---")
    if not args.web_only:
        print(f"API accessible à: http://{args.api_host}:{args.api_port}")
        print(f"Documentation API: http://{args.api_host}:{args.api_port}/docs")
    
    if not args.api_only:
        if args.web_type == 'vite':
            print("Interface web: l'adresse sera affichée dans le terminal de l'interface web")
            print("(généralement http://localhost:3000)")
        else:
            print("Interface web: l'adresse sera affichée dans le terminal de l'interface web")
            print("(généralement http://localhost:8080)")
    
    print("\nAppuyez sur Ctrl+C pour arrêter tous les services.")
    
    # Garder le script en cours d'exécution
    try:
        while True:
            # Vérifier que les processus sont toujours en cours d'exécution
            if api_process and api_process.poll() is not None:
                print("L'API s'est arrêtée de manière inattendue. Code de sortie:", api_process.returncode)
                if web_process:
                    web_process.terminate()
                break
            
            if web_process and web_process.poll() is not None:
                print("L'interface web s'est arrêtée de manière inattendue. Code de sortie:", web_process.returncode)
                if api_process:
                    api_process.terminate()
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
