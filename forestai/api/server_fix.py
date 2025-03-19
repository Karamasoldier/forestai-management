"""
Module correctif pour le serveur API FastAPI qui résout les problèmes de récursion.

Ce module contient une version modifiée de la fonction run_server qui applique
les correctifs nécessaires avant de démarrer le serveur.
"""

import logging
import uvicorn
from fastapi import FastAPI

from forestai.api.server import app
from forestai.api.models_fix import apply_model_fixes

# Configuration du logger
logger = logging.getLogger("forestai.api.server_fix")

def patched_run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Version corrigée de la fonction run_server qui applique les correctifs
    pour les références circulaires avant de démarrer le serveur.
    
    Args:
        host: Hôte d'écoute
        port: Port d'écoute
        reload: Activer le rechargement automatique
    """
    try:
        # Appliquer les correctifs pour les modèles Pydantic
        logger.info("Application des correctifs pour les modèles Pydantic...")
        apply_model_fixes()
        
        # Démarrer le serveur
        logger.info(f"Démarrage du serveur API corrigé sur {host}:{port}...")
        if reload:
            # En mode rechargement, il faut utiliser le module et non l'application
            uvicorn.run("forestai.api.server:app", host=host, port=port, reload=reload)
        else:
            # En mode normal, on peut utiliser directement l'instance app
            uvicorn.run(app, host=host, port=port)
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur corrigé: {e}", exc_info=True)
        raise
