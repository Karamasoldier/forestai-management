#!/usr/bin/env python
"""
Point d'entrée principal de l'interface en ligne de commande ForestAI.

Ce script fournit une interface unifiée pour toutes les fonctionnalités
de ForestAI via une interface en ligne de commande.
"""

import sys
import argparse
import logging
from importlib import import_module
from typing import Optional, List, Dict, Any, Union

# Configuration du logger
logger = logging.getLogger("forestai.cli")

def main(args: Optional[List[str]] = None) -> int:
    """
    Point d'entrée principal pour l'interface en ligne de commande.
    
    Args:
        args (Optional[List[str]]): Arguments de ligne de commande.
            Si None, utilise sys.argv[1:].
    
    Returns:
        int: Code de sortie (0 pour succès, non-zéro pour erreur)
    """
    # Créer le parseur principal
    parser = argparse.ArgumentParser(
        description="ForestAI - Gestion Forestière Intelligente",
        epilog="Pour plus d'informations, consultez la documentation."
    )
    
    # Options globales
    parser.add_argument("--version", action="store_true", help="Afficher la version")
    parser.add_argument("--log-level", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default="INFO", 
                        help="Niveau de journalisation (défaut: INFO)")
    
    # Créer des sous-commandes
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Sous-commande "api" - Démarrer le serveur API
    api_parser = subparsers.add_parser("api", help="Démarrer le serveur API")
    api_parser.add_argument("--host", default="127.0.0.1", help="Adresse d'hôte (défaut: 127.0.0.1)")
    api_parser.add_argument("--port", type=int, default=8000, help="Port d'écoute (défaut: 8000)")
    api_parser.add_argument("--debug", action="store_true", help="Activer le mode debug")
    api_parser.add_argument("--no-patches", action="store_true", 
                          help="Ne pas appliquer les correctifs pour les erreurs de récursion")
    
    # Sous-commande "web" - Démarrer l'interface web
    web_parser = subparsers.add_parser("web", help="Démarrer l'interface web")
    web_parser.add_argument("--port", type=int, default=3000, help="Port de l'interface web (défaut: 3000)")
    web_parser.add_argument("--api-host", default="127.0.0.1", help="Hôte de l'API (défaut: 127.0.0.1)")
    web_parser.add_argument("--api-port", type=int, default=8000, help="Port de l'API (défaut: 8000)")
    web_parser.add_argument("--web-dir", help="Répertoire de l'interface web (défaut: détection automatique)")
    web_parser.add_argument("--dev", action="store_true", help="Démarrer en mode développement")
    web_parser.add_argument("--api-only", action="store_true", help="Démarrer uniquement l'API")
    web_parser.add_argument("--web-only", action="store_true", help="Démarrer uniquement l'interface web")
    web_parser.add_argument("--interface", choices=["vite", "vue"], default="vite",
                         help="Interface à utiliser (vite ou vue) (défaut: vite)")
    
    # Sous-commande "run" - Démarrer le système complet (API + interface web)
    run_parser = subparsers.add_parser("run", help="Démarrer le système complet")
    run_parser.add_argument("--web-port", type=int, default=3000, help="Port de l'interface web (défaut: 3000)")
    run_parser.add_argument("--api-port", type=int, default=8000, help="Port de l'API (défaut: 8000)")
    run_parser.add_argument("--debug", action="store_true", help="Activer le mode debug")
    run_parser.add_argument("--interface", choices=["vite", "vue"], default="vite",
                         help="Interface à utiliser (vite ou vue) (défaut: vite)")
    
    # Sous-commande "agent" - Exécuter un agent spécifique
    agent_parser = subparsers.add_parser("agent", help="Exécuter un agent spécifique")
    agent_parser.add_argument("agent_name", help="Nom de l'agent à exécuter")
    agent_parser.add_argument("--action", help="Action spécifique à exécuter")
    agent_parser.add_argument("--params", help="Paramètres de l'action (format JSON)")
    
    # Sous-commande "diagnostics" - Exécuter des diagnostics du système
    diagnostics_parser = subparsers.add_parser("diagnostics", help="Exécuter des diagnostics du système")
    diagnostics_parser.add_argument("--check-dependencies", action="store_true", 
                                 help="Vérifier les dépendances du système")
    diagnostics_parser.add_argument("--check-models", action="store_true", 
                                 help="Vérifier les modèles Pydantic")
    diagnostics_parser.add_argument("--fix", action="store_true", 
                                 help="Tenter de corriger les problèmes détectés")
    
    # Analyser les arguments
    if args is None:
        args = sys.argv[1:]
    parsed_args = parser.parse_args(args)
    
    # Configurer la journalisation
    logging.basicConfig(
        level=getattr(logging, parsed_args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Traiter les commandes
    if parsed_args.version:
        from forestai import __version__
        print(f"ForestAI version {__version__}")
        return 0
    
    # Exécuter la commande demandée
    if parsed_args.command == "api":
        from forestai.cli.commands.api_command import run_api
        return run_api([
            "--host", parsed_args.host,
            "--port", str(parsed_args.port),
            "--log-level", parsed_args.log_level
        ] + (["--debug"] if parsed_args.debug else [])
          + (["--no-patches"] if parsed_args.no_patches else []))
    
    elif parsed_args.command == "web":
        from forestai.cli.commands.web_command import run_web
        cmd_args = [
            "--port", str(parsed_args.port),
            "--api-host", parsed_args.api_host,
            "--api-port", str(parsed_args.api_port),
            "--log-level", parsed_args.log_level,
            "--interface", parsed_args.interface
        ]
        
        if parsed_args.web_dir:
            cmd_args.extend(["--web-dir", parsed_args.web_dir])
        if parsed_args.dev:
            cmd_args.append("--dev")
        if parsed_args.api_only:
            cmd_args.append("--api-only")
        if parsed_args.web_only:
            cmd_args.append("--web-only")
        
        return run_web(cmd_args)
    
    elif parsed_args.command == "run":
        from forestai.cli.commands.complete_command import run_complete
        cmd_args = [
            "--web-port", str(parsed_args.web_port),
            "--api-port", str(parsed_args.api_port),
            "--log-level", parsed_args.log_level,
            "--interface", parsed_args.interface
        ]
        
        if parsed_args.debug:
            cmd_args.append("--debug")
        
        return run_complete(cmd_args)
    
    elif parsed_args.command == "agent":
        from forestai.cli.commands.agent_command import run_agent
        cmd_args = [
            parsed_args.agent_name,
            "--log-level", parsed_args.log_level
        ]
        
        if parsed_args.action:
            cmd_args.extend(["--action", parsed_args.action])
        if parsed_args.params:
            cmd_args.extend(["--params", parsed_args.params])
        
        return run_agent(cmd_args)
    
    elif parsed_args.command == "diagnostics":
        from forestai.cli.commands.diagnostics_command import run_diagnostics
        cmd_args = ["--log-level", parsed_args.log_level]
        
        if parsed_args.check_dependencies:
            cmd_args.append("--check-dependencies")
        if parsed_args.check_models:
            cmd_args.append("--check-models")
        if parsed_args.fix:
            cmd_args.append("--fix")
        
        return run_diagnostics(cmd_args)
    
    else:
        # Aucune commande spécifiée, afficher l'aide
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
