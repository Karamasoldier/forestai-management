#!/usr/bin/env python
"""
Script de démarrage du serveur API REST ForestAI avec correctifs pour les erreurs de récursion.

Usage:
    python api_server_fix.py [--host HOST] [--port PORT] [--reload]

Exemples:
    # Démarrer le serveur corrigé sur localhost:8000 avec rechargement automatique
    python api_server_fix.py --reload

    # Démarrer le serveur corrigé sur une adresse et port spécifiques
    python api_server_fix.py --host 0.0.0.0 --port 8080
"""

import os
import sys
import argparse
import logging
from pathlib import Path

from forestai.core.utils.config import Config
from forestai.core.utils.logging_config import LoggingConfig
from forestai.api.server_fix import patched_run_server

def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Les arguments parsés
    """
    parser = argparse.ArgumentParser(description='ForestAI API REST Server (avec correctifs)')
    parser.add_argument('--host', type=str, default="0.0.0.0", help='Hôte d\'écoute (défaut: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port d\'écoute (défaut: 8000)')
    parser.add_argument('--reload', action='store_true', help='Activer le rechargement automatique')
    
    return parser.parse_args()

def main():
    """
    Fonction principale.
    """
    # Parser les arguments
    args = parse_arguments()
    
    # Configuration du logging
    LoggingConfig.get_instance().init({
        "level": "INFO",
        "log_dir": "logs",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    logger = logging.getLogger("forestai.api_server_fix")
    logger.info("Démarrage du serveur API REST ForestAI avec correctifs pour les erreurs de récursion")
    
    # Charger la configuration
    config = Config.get_instance()
    config.load_config(env_file=".env")
    
    # Afficher les informations de démarrage
    logger.info(f"Démarrage du serveur corrigé sur {args.host}:{args.port}")
    if args.reload:
        logger.info("Mode rechargement automatique activé")
    
    # Démarrer le serveur avec les correctifs
    try:
        patched_run_server(host=args.host, port=args.port, reload=args.reload)
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
