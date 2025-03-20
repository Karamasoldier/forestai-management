"""
Commande pour démarrer le serveur API ForestAI.

Ce module contient le code pour démarrer le serveur API avec les correctifs appropriés.
"""

import os
import sys
import logging
import argparse
from typing import Optional, List, Dict, Any, Union

# Configuration du logger
logger = logging.getLogger("forestai.cli.api")

def run_api(args: Optional[List[str]] = None) -> int:
    """
    Démarre le serveur API ForestAI.
    
    Args:
        args (Optional[List[str]]): Arguments de ligne de commande.
            Si None, utilise sys.argv[1:].
    
    Returns:
        int: Code de sortie (0 pour succès, non-zéro pour erreur)
    """
    # Créer le parseur d'arguments
    parser = argparse.ArgumentParser(description="Démarrer le serveur API ForestAI")
    
    # Options de configuration du serveur
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'hôte (défaut: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port d'écoute (défaut: 8000)")
    parser.add_argument("--debug", action="store_true", help="Activer le mode debug")
    parser.add_argument("--no-patches", action="store_true", 
                        help="Ne pas appliquer les correctifs pour les erreurs de récursion")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default="INFO", help="Niveau de journalisation (défaut: INFO)")
    
    # Analyser les arguments
    if args is None:
        args = sys.argv[1:]
    parsed_args = parser.parse_args(args)
    
    # Configurer la journalisation
    logging.basicConfig(
        level=getattr(logging, parsed_args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Appliquer les correctifs si nécessaire
    if not parsed_args.no_patches:
        logger.info("Application des correctifs pour éviter les erreurs de récursion...")
        try:
            from forestai.core.patches import apply_all_patches
            success = apply_all_patches()
            if not success:
                logger.warning("Certains correctifs n'ont pas pu être appliqués")
        except ImportError:
            logger.warning("Module de correctifs non trouvé. Continuez sans correctifs.")
    
    # Importer et démarrer le serveur API
    try:
        logger.info(f"Démarrage du serveur API sur {parsed_args.host}:{parsed_args.port}...")
        
        try:
            # Importer le serveur avec de meilleurs messages d'erreur
            try:
                from forestai.api.server import start_server
            except ImportError as e:
                logger.error(f"Erreur d'importation du serveur API: {e}")
                logger.info("Tentative d'import du serveur alternatif...")
                from forestai.api.server_fix import start_server
            
            # Démarrer le serveur
            start_server(
                host=parsed_args.host,
                port=parsed_args.port,
                debug=parsed_args.debug
            )
            
            logger.info("Serveur API démarré avec succès")
            return 0
            
        except ImportError as e:
            logger.error(f"Erreur lors du démarrage du serveur API: {e}")
            
            # Tenter une approche alternative si l'importation échoue
            logger.info("Tentative de démarrage direct de l'API...")
            
            # Importer directement uvicorn et FastAPI
            try:
                import uvicorn
                from fastapi import FastAPI
                from fastapi.middleware.cors import CORSMiddleware
                
                app = FastAPI(title="ForestAI API")
                
                # Configurer CORS
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                
                @app.get("/")
                async def root():
                    return {"message": "ForestAI API en fonctionnement (mode de secours)"}
                
                # Démarrer le serveur directement
                logger.info(f"Démarrage du serveur API de secours sur {parsed_args.host}:{parsed_args.port}...")
                uvicorn.run(app, host=parsed_args.host, port=parsed_args.port)
                return 0
                
            except ImportError as e2:
                logger.error(f"Échec du démarrage du serveur de secours: {e2}")
                return 1
            
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur API par l'utilisateur")
        return 0
    except Exception as e:
        logger.error(f"Erreur inattendue lors du démarrage du serveur API: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_api())
