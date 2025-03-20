#!/usr/bin/env python
"""
Script de démarrage de l'API ForestAI avec correctif pour les erreurs de récursion Pydantic v1.

Ce script applique d'abord le correctif pour Pydantic v1 puis lance l'API.
Il est conçu pour fonctionner même avec une version plus ancienne de Pydantic.

Usage:
    python run_api_with_fix.py [--host HOST] [--port PORT] [--reload]

Exemples:
    # Démarrer l'API avec correctif sur localhost:8000
    python run_api_with_fix.py

    # Démarrer l'API avec correctif sur une adresse et port spécifiques
    python run_api_with_fix.py --host 0.0.0.0 --port 8080
"""

import os
import sys
import argparse
import logging
import importlib
import subprocess

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run_api_with_fix")

def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Les arguments parsés
    """
    parser = argparse.ArgumentParser(description='ForestAI API avec correctif pour Pydantic v1')
    parser.add_argument('--host', type=str, default="0.0.0.0", help='Hôte d\'écoute (défaut: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port d\'écoute (défaut: 8000)')
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
        # Importer directement le module de correctif
        import fix_pydantic_v1_recursion
        fix_pydantic_v1_recursion.main()
        logger.info("✅ Correctif pour Pydantic v1 appliqué avec succès")
        return True
    except ImportError:
        logger.error("❌ Impossible d'importer le module fix_pydantic_v1_recursion")
        logger.info("Tentative d'application du correctif via subprocess...")
        
        # Essayer d'exécuter le script en tant que process séparé
        try:
            result = subprocess.run([sys.executable, "fix_pydantic_v1_recursion.py"], 
                                   check=True, capture_output=True, text=True)
            logger.info(f"Sortie du correctif: {result.stdout}")
            logger.info("✅ Correctif pour Pydantic v1 appliqué avec succès via subprocess")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Échec de l'exécution du correctif: {e}")
            logger.error(f"Erreur: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("❌ Script fix_pydantic_v1_recursion.py non trouvé")
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
    
    # Essayer d'importer et d'utiliser l'API corrigée
    try:
        from forestai.api.server_fix import patched_run_server
        logger.info("Utilisation du serveur avec correctifs intégrés")
        patched_run_server(host=host, port=port, reload=reload)
    except ImportError:
        logger.info("Serveur corrigé non disponible, utilisation du serveur standard")
        # Fallback sur uvicorn directement
        import uvicorn
        from forestai.api.server import app
        
        if reload:
            uvicorn.run("forestai.api.server:app", host=host, port=port, reload=reload)
        else:
            uvicorn.run(app, host=host, port=port)

def main():
    """
    Fonction principale.
    """
    # Parser les arguments
    args = parse_arguments()
    
    logger.info("=== Démarrage de l'API ForestAI avec correctif pour Pydantic v1 ===")
    
    # Appliquer le correctif
    if not apply_pydantic_fix():
        logger.warning("⚠️ Le correctif n'a pas pu être appliqué, l'API pourrait rencontrer des erreurs de récursion")
    
    # Démarrer l'API
    try:
        run_api(args.host, args.port, args.reload)
    except KeyboardInterrupt:
        logger.info("Arrêt de l'API")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'API: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
