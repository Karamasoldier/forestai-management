"""
Commande pour démarrer le système complet ForestAI (API + interface web).

Ce module contient le code pour démarrer à la fois l'API et l'interface web dans un seul processus.
"""

import os
import sys
import logging
import argparse
import threading
from typing import Optional, List, Dict, Any, Union

# Configuration du logger
logger = logging.getLogger("forestai.cli.complete")

def run_complete(args: Optional[List[str]] = None) -> int:
    """
    Démarre le système complet ForestAI (API + interface web).
    
    Args:
        args (Optional[List[str]]): Arguments de ligne de commande.
            Si None, utilise sys.argv[1:].
    
    Returns:
        int: Code de sortie (0 pour succès, non-zéro pour erreur)
    """
    # Créer le parseur d'arguments
    parser = argparse.ArgumentParser(
        description="Démarrer le système complet ForestAI (API + interface web)"
    )
    
    # Options de configuration
    parser.add_argument("--web-port", type=int, default=3000, 
                      help="Port de l'interface web (défaut: 3000)")
    parser.add_argument("--api-port", type=int, default=8000, 
                      help="Port de l'API (défaut: 8000)")
    parser.add_argument("--api-host", default="127.0.0.1", 
                      help="Hôte de l'API (défaut: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", 
                      help="Activer le mode debug")
    parser.add_argument("--log-level", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      default="INFO", 
                      help="Niveau de journalisation (défaut: INFO)")
    parser.add_argument("--interface", choices=["vite", "vue"], default="vite",
                     help="Interface à utiliser (vite ou vue) (défaut: vite)")
    
    # Analyser les arguments
    if args is None:
        args = sys.argv[1:]
    parsed_args = parser.parse_args(args)
    
    # Configurer la journalisation
    logging.basicConfig(
        level=getattr(logging, parsed_args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Importer les modules d'API et web
    try:
        from forestai.cli.commands.web_command import run_web
        
        # Préparer les arguments pour la commande web
        web_args = [
            "--port", str(parsed_args.web_port),
            "--api-host", parsed_args.api_host,
            "--api-port", str(parsed_args.api_port),
            "--log-level", parsed_args.log_level,
            "--interface", parsed_args.interface
        ]
        
        if parsed_args.debug:
            web_args.append("--dev")  # Mode développement pour l'interface web si debug activé
        
        # Lancer la commande web (qui lancera aussi l'API)
        logger.info("Démarrage du système complet ForestAI...")
        return run_web(web_args)
        
    except ImportError as e:
        logger.error(f"Erreur lors de l'importation des modules: {e}")
        return 1
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du système complet: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_complete())
