#!/usr/bin/env python
"""
Script de démarrage direct de l'API REST ForestAI avec correctifs.
Ce script ne dépend pas de l'import des modules externes du projet.

Usage:
    python api_server_run_directly.py
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Configuration basique du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("forestai.direct_server")

def run_api_server():
    """
    Exécute directement le serveur API en utilisant uvicorn.
    """
    try:
        logger.info("Démarrage du serveur API REST ForestAI en mode direct...")
        logger.info("Serveur en cours de démarrage sur http://localhost:8000")
        
        # Démarrer le serveur avec uvicorn en pointant vers le module app
        uvicorn.run(
            "forestai.api.server:app",
            host="localhost",
            port=8000,
            reload=False
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_api_server()
