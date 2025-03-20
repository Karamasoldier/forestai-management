#!/usr/bin/env python
"""
Script de démarrage unifié pour ForestAI avec correction des erreurs de récursion.

Ce script applique les correctifs nécessaires puis démarre l'API et/ou l'interface web.

Usage:
    python run_forestai.py [options]

Options:
    --api-only         Démarrer uniquement l'API
    --web-only         Démarrer uniquement l'interface web
    --web-type TYPE    Type d'interface web (vue, vite)
    --api-host HOST    Hôte pour l'API (défaut: 0.0.0.0)
    --api-port PORT    Port pour l'API (défaut: 8000)
    --reload           Activer le rechargement automatique

Exemples:
    # Démarrer l'API et l'interface web (défaut)
    python run_forestai.py

    # Démarrer uniquement l'API sur le port 8080
    python run_forestai.py --api-only --api-port 8080

    # Démarrer uniquement l'interface web Vite.js
    python run_forestai.py --web-only --web-type vite
"""

import os
import sys
import argparse
import logging
import importlib
import subprocess
import time
import threading

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run_forestai")

def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Les arguments parsés
    """
    parser = argparse.ArgumentParser(description='ForestAI - Script de démarrage unifié')
    parser.add_argument('--api-only', action='store_true', help='Démarrer uniquement l\'API')
    parser.add_argument('--web-only', action='store_true', help='Démarrer uniquement l\'interface web')
    parser.add_argument('--web-type', type=str, choices=['vue', 'vite'], default='vue', help='Type d\'interface web (vue, vite)')
    parser.add_argument('--api-host', type=str, default="0.0.0.0", help='Hôte pour l\'API (défaut: 0.0.0.0)')
    parser.add_argument('--api-port', type=int, default=8000, help='Port pour l\'API (défaut: 8000)')
    parser.add_argument('--reload', action='store_true', help='Activer le rechargement automatique')
    
    return parser.parse_args()

def apply_pydantic_fix():
    """
    Applique le correctif pour Pydantic v1.
    
    Returns:
        bool: True si le correctif a été appliqué avec succès, False sinon
    """
    logger.info("Application du correctif pour Pydantic v1...")
    
    try:
        import fix_pydantic_v1_recursion
        fix_pydantic_v1_recursion.main()
        logger.info("✅ Correctif pour Pydantic v1 appliqué avec succès")
        return True
    except ImportError:
        logger.error("❌ Impossible d'importer le module fix_pydantic_v1_recursion")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'application du correctif: {e}")
        return False

def run_api(host, port, reload):
    """
    Lance l'API ForestAI.
    
    Args:
        host: Hôte d'écoute
        port: Port d'écoute
        reload: Activer le rechargement automatique
    """
    logger.info(f"Démarrage de l'API sur {host}:{port}...")
    
    # Import de l'API server
    try:
        from forestai.api.server import app
        import uvicorn
        
        if reload:
            uvicorn.run("forestai.api.server:app", host=host, port=port, reload=reload)
        else:
            uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'API: {e}", exc_info=True)
        sys.exit(1)

def run_web_interface(web_type, api_port):
    """
    Lance l'interface web.
    
    Args:
        web_type: Type d'interface (vue, vite)
        api_port: Port de l'API
    """
    logger.info(f"Démarrage de l'interface web {web_type}...")
    
    # Répertoire de l'interface web
    web_dir = "web" if web_type == "vite" else "webui"
    
    # Vérifier si le répertoire existe
    if not os.path.isdir(web_dir):
        logger.error(f"❌ Répertoire {web_dir} introuvable")
        return False
    
    # Configurer l'URL de l'API
    os.environ["VUE_APP_API_URL"] = f"http://localhost:{api_port}"
    
    # Lancer l'interface web
    try:
        # Vérifier si npm est installé
        try:
            subprocess.run(["npm", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ npm n'est pas installé ou n'est pas disponible dans le PATH")
            return False
        
        # Lancer l'interface web
        logger.info(f"Lancement de l'interface web dans {web_dir}...")
        web_process = subprocess.Popen(
            ["npm", "run", "serve" if web_type == "vue" else "dev"],
            cwd=web_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Afficher la sortie en temps réel
        def log_output(stream, log_level):
            for line in iter(stream.readline, ""):
                if log_level == logging.INFO:
                    logger.info(f"[WEB] {line.strip()}")
                else:
                    logger.error(f"[WEB] {line.strip()}")
        
        threading.Thread(target=log_output, args=(web_process.stdout, logging.INFO), daemon=True).start()
        threading.Thread(target=log_output, args=(web_process.stderr, logging.ERROR), daemon=True).start()
        
        return web_process
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'interface web: {e}", exc_info=True)
        return False

def main():
    """
    Fonction principale.
    """
    # Parser les arguments
    args = parse_arguments()
    
    logger.info("=== ForestAI - Démarrage du système ===")
    
    # Appliquer le correctif Pydantic
    if not apply_pydantic_fix():
        logger.warning("⚠️ Le correctif Pydantic n'a pas pu être appliqué, des erreurs de récursion peuvent survenir")
    
    # Démarrer l'API si demandé
    api_process = None
    if not args.web_only:
        if os.environ.get("API_STARTED") != "1":
            # Éviter de démarrer l'API plusieurs fois en cas de rechargement
            os.environ["API_STARTED"] = "1"
            
            # Démarrer l'API dans un thread séparé
            api_thread = threading.Thread(
                target=run_api,
                args=(args.api_host, args.api_port, args.reload),
                daemon=True
            )
            api_thread.start()
            
            # Si API uniquement, rejoindre le thread pour bloquer
            if args.api_only:
                try:
                    api_thread.join()
                except KeyboardInterrupt:
                    logger.info("Arrêt de l'API")
                    sys.exit(0)
            else:
                # Attendre que l'API démarre
                logger.info("Attente du démarrage de l'API...")
                time.sleep(2)
    
    # Démarrer l'interface web si demandé
    if not args.api_only:
        web_process = run_web_interface(args.web_type, args.api_port)
        
        if web_process:
            try:
                # Attendre la fin du processus
                web_process.wait()
            except KeyboardInterrupt:
                logger.info("Arrêt de l'interface web")
                web_process.terminate()
                sys.exit(0)
        else:
            logger.error("❌ Échec du démarrage de l'interface web")
            sys.exit(1)

if __name__ == "__main__":
    main()
