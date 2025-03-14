#!/usr/bin/env python
"""
Script principal pour exécuter les agents ForestAI.

Usage:
    python run.py [--agent AGENT_NAME] [--action ACTION_NAME] [--params JSON_PARAMS]

Exemples:
    # Lancer le système complet
    python run.py

    # Utiliser un agent spécifique
    python run.py --agent geoagent

    # Rechercher des parcelles dans une commune spécifique
    python run.py --agent geoagent --action search_parcels --params '{"commune": "Saint-Martin-de-Crau", "section": "B"}'

    # Vérifier la conformité réglementaire d'une parcelle
    python run.py --agent reglementation --action check_compliance --params '{"parcels": ["123456789"], "project_type": "boisement"}'

    # Rechercher des subventions pour un type de projet
    python run.py --agent subsidy --action search_subsidies --params '{"project_type": "reboisement", "region": "Occitanie"}'
"""

import os
import sys
import argparse
import json
import logging
import signal
import time
from typing import Dict, Any, Optional

from forestai.core.utils.config import Config
from forestai.core.utils.logging_config import LoggingConfig
from forestai.agents.geo_agent import GeoAgent
from forestai.agents.subsidy_agent import SubsidyAgent

# Configuration du logging
LoggingConfig.get_instance().init({
    "level": "INFO",
    "log_dir": "logs",
    "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
})

logger = logging.getLogger("forestai")

# Agents disponibles
AVAILABLE_AGENTS = {
    "geoagent": GeoAgent,
    "subsidy": SubsidyAgent,
    # "reglementation": ReglementationAgent,  # À décommenter une fois implémenté
}

def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Les arguments parsés
    """
    parser = argparse.ArgumentParser(description='ForestAI - Gestion Forestière Intelligente')
    parser.add_argument('--agent', type=str, help='Agent à utiliser (geoagent, subsidy, reglementation, etc.)')
    parser.add_argument('--action', type=str, help='Action à exécuter')
    parser.add_argument('--params', type=str, help='Paramètres de l\'action au format JSON')
    
    return parser.parse_args()

def handle_exit(signum, frame):
    """
    Gestionnaire de signal pour une sortie propre.
    """
    logger.info("Exiting ForestAI...")
    sys.exit(0)

def run_agent(agent_name: str, action: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
    """
    Exécute un agent spécifique.
    
    Args:
        agent_name: Nom de l'agent
        action: Action à exécuter (optionnel)
        params: Paramètres de l'action (optionnel)
    """
    # Vérifier si l'agent existe
    if agent_name not in AVAILABLE_AGENTS:
        logger.error(f"Agent '{agent_name}' not found. Available agents: {', '.join(AVAILABLE_AGENTS.keys())}")
        return
    
    # Charger la configuration
    config = Config.get_instance()
    config.load_config(".env")
    
    # Initialiser l'agent
    agent_class = AVAILABLE_AGENTS[agent_name]
    agent = agent_class(config.as_dict())
    logger.info(f"Agent '{agent_name}' initialized")
    
    try:
        if action:
            # Exécuter une action spécifique
            logger.info(f"Executing action '{action}' with params: {params}")
            result = agent.execute_action(action, params or {})
            
            # Afficher le résultat
            if result["status"] == "success":
                print(json.dumps(result["result"], indent=2, ensure_ascii=False))
            else:
                logger.error(f"Error executing action: {result.get('error_message', 'Unknown error')}")
        else:
            # Mode interactif - l'agent écoute les messages
            logger.info(f"Running agent '{agent_name}' in interactive mode (Ctrl+C to exit)")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info(f"Agent '{agent_name}' stopped")
    finally:
        # Nettoyer les ressources de l'agent
        agent.unsubscribe_all()

def run_system():
    """
    Exécute le système complet avec tous les agents.
    """
    # Charger la configuration
    config = Config.get_instance()
    config.load_config(".env")
    
    # Initialiser tous les agents
    agents = {}
    for agent_name, agent_class in AVAILABLE_AGENTS.items():
        agents[agent_name] = agent_class(config.as_dict())
        logger.info(f"Agent '{agent_name}' initialized")
    
    logger.info("ForestAI system running (Ctrl+C to exit)")
    
    try:
        # Boucle principale
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("ForestAI system stopped")
    finally:
        # Nettoyer les ressources de tous les agents
        for agent in agents.values():
            agent.unsubscribe_all()

def main():
    """
    Fonction principale.
    """
    # Configurer le gestionnaire de signal pour une sortie propre
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Parser les arguments
    args = parse_arguments()
    
    # Interpréter les paramètres JSON si fournis
    params = None
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON params: {e}")
            return
    
    # Exécuter le système ou un agent spécifique
    if args.agent:
        run_agent(args.agent, args.action, params)
    else:
        run_system()

if __name__ == "__main__":
    main()
