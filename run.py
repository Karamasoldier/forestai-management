#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import json
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("forestai.log")
    ]
)

logger = logging.getLogger("forestai")

def main():
    # Définir les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="ForestAI - Système de gestion forestière")
    parser.add_argument(
        "--agent", 
        type=str,
        choices=["geoagent", "subsidy", "diagnostic", "document", "operator"],
        help="Agent spécifique à exécuter"
    )
    parser.add_argument(
        "--config", 
        type=str,
        default="config.json",
        help="Chemin vers le fichier de configuration"
    )
    parser.add_argument(
        "--action", 
        type=str,
        help="Action spécifique à effectuer par l'agent"
    )
    parser.add_argument(
        "--params", 
        type=str,
        help="Paramètres JSON pour l'action"
    )
    
    args = parser.parse_args()
    
    # Charger la configuration
    config_path = args.config
    if not os.path.exists(config_path):
        # Utiliser la configuration par défaut
        config = {
            "data_path": os.getenv("DATA_PATH", "./data"),
            "output_path": os.getenv("OUTPUT_PATH", "./data/outputs"),
            "db": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 5432)),
                "name": os.getenv("DB_NAME", "forestai"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "")
            },
            "api": {
                "port": int(os.getenv("UI_PORT", 8000)),
                "debug": os.getenv("DEBUG", "False").lower() == "true"
            }
        }
    else:
        with open(config_path, "r") as f:
            config = json.load(f)
    
    # Vérifier et créer les répertoires nécessaires
    os.makedirs(config["data_path"], exist_ok=True)
    os.makedirs(config["output_path"], exist_ok=True)
    os.makedirs(os.path.join(config["data_path"], "raw"), exist_ok=True)
    os.makedirs(os.path.join(config["data_path"], "processed"), exist_ok=True)
    os.makedirs(os.path.join(config["data_path"], "cache"), exist_ok=True)
    
    # Exécuter l'agent spécifié ou le système complet
    if args.agent:
        run_specific_agent(args.agent, config, args.action, args.params)
    else:
        run_full_system(config)

def run_specific_agent(agent_name, config, action=None, params=None):
    """Exécute un agent spécifique avec les paramètres fournis."""
    logger.info(f"Démarrage de l'agent {agent_name}")
    
    try:
        # Importer dynamiquement l'agent
        if agent_name == "geoagent":
            # Note: à implémenter quand la structure sera créée
            from forestai.agents.geo_agent.geo_agent import GeoAgent
            agent = GeoAgent(config)
        elif agent_name == "subsidy":
            from forestai.agents.subsidy_agent.subsidy_agent import SubsidyAgent
            agent = SubsidyAgent(config)
        elif agent_name == "diagnostic":
            from forestai.agents.diagnostic_agent.diagnostic_agent import DiagnosticAgent
            agent = DiagnosticAgent(config)
        elif agent_name == "document":
            from forestai.agents.document_agent.document_agent import DocumentAgent
            agent = DocumentAgent(config)
        elif agent_name == "operator":
            from forestai.agents.operator_agent.operator_agent import OperatorAgent
            agent = OperatorAgent(config)
        else:
            logger.error(f"Agent inconnu: {agent_name}")
            return
        
        # Exécuter l'action spécifiée
        if action:
            if hasattr(agent, action) and callable(getattr(agent, action)):
                if params:
                    # Convertir les paramètres JSON en dict
                    params_dict = json.loads(params)
                    result = getattr(agent, action)(**params_dict)
                else:
                    result = getattr(agent, action)()
                
                logger.info(f"Résultat de {action}: {result}")
            else:
                logger.error(f"Action inconnue pour l'agent {agent_name}: {action}")
        else:
            # Action par défaut: exécuter l'agent
            agent.run()
            
    except ImportError as e:
        logger.error(f"Erreur d'importation de l'agent {agent_name}: {e}")
        logger.info("L'agent n'est probablement pas encore implémenté.")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de l'agent {agent_name}: {e}", exc_info=True)

def run_full_system(config):
    """Exécute le système complet avec tous les agents."""
    logger.info("Démarrage du système ForestAI complet")
    
    try:
        # Démarrer l'API REST pour l'interface utilisateur
        from forestai.core.api.app import start_api
        start_api(config)
    except ImportError:
        logger.warning("API REST non implémentée. Exécution des agents en mode CLI uniquement.")
        # Exécuter les agents disponibles en séquence
        for agent in ["geoagent", "subsidy", "diagnostic", "document", "operator"]:
            run_specific_agent(agent, config)

if __name__ == "__main__":
    main()