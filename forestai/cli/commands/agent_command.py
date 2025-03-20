"""
Commande pour exécuter un agent ForestAI spécifique.

Ce module permet d'exécuter un agent spécifique avec des actions et paramètres personnalisés.
"""

import os
import sys
import json
import logging
import argparse
from typing import Optional, List, Dict, Any, Union

# Configuration du logger
logger = logging.getLogger("forestai.cli.agent")

def run_agent(args: Optional[List[str]] = None) -> int:
    """
    Exécute un agent ForestAI spécifique.
    
    Args:
        args (Optional[List[str]]): Arguments de ligne de commande.
            Si None, utilise sys.argv[1:].
    
    Returns:
        int: Code de sortie (0 pour succès, non-zéro pour erreur)
    """
    # Créer le parseur d'arguments
    parser = argparse.ArgumentParser(description="Exécuter un agent ForestAI spécifique")
    
    # Options de configuration
    parser.add_argument("agent_name", help="Nom de l'agent à exécuter")
    parser.add_argument("--action", help="Action spécifique à exécuter")
    parser.add_argument("--params", help="Paramètres de l'action (format JSON)")
    parser.add_argument("--log-level", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      default="INFO", 
                      help="Niveau de journalisation (défaut: INFO)")
    parser.add_argument("--output-format", 
                      choices=["text", "json", "pretty"], 
                      default="pretty",
                      help="Format de sortie (défaut: pretty)")
    
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
    try:
        from forestai.core.patches import apply_all_patches
        apply_all_patches(verbose=False)
    except ImportError:
        logger.warning("Module de correctifs non trouvé. Continuez sans correctifs.")
    
    # Charger l'agent demandé
    try:
        # Analyser les paramètres JSON si fournis
        params = {}
        if parsed_args.params:
            try:
                params = json.loads(parsed_args.params)
            except json.JSONDecodeError as e:
                logger.error(f"Erreur dans le format JSON des paramètres: {e}")
                return 1
        
        # Trouver l'agent
        agent_name = parsed_args.agent_name.lower()
        logger.info(f"Chargement de l'agent '{agent_name}'...")
        
        # Utiliser le nouveau système d'agents
        try:
            from forestai.agents import get_agent
            agent = get_agent(agent_name)
        except (ImportError, AttributeError):
            # Fallback vers l'ancien système
            logger.warning("Utilisation de l'ancien système d'agents...")
            agent_module_name = f"forestai.agents.{agent_name}.{agent_name}_agent"
            agent_class_name = f"{agent_name.capitalize()}Agent"
            
            try:
                agent_module = __import__(agent_module_name, fromlist=[agent_class_name])
                agent_class = getattr(agent_module, agent_class_name)
                agent = agent_class()
            except (ImportError, AttributeError) as e:
                logger.error(f"Agent '{agent_name}' non trouvé: {e}")
                return 1
        
        # Exécuter l'action demandée
        if parsed_args.action:
            action = parsed_args.action
            logger.info(f"Exécution de l'action '{action}' avec les paramètres: {params}")
            
            if not hasattr(agent, action):
                logger.error(f"Action '{action}' non disponible pour l'agent '{agent_name}'")
                return 1
            
            try:
                result = getattr(agent, action)(**params)
                
                # Formater la sortie selon le format demandé
                if parsed_args.output_format == "json":
                    print(json.dumps(result))
                elif parsed_args.output_format == "pretty":
                    import pprint
                    pprint.pprint(result)
                else:
                    print(result)
                
                return 0
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution de l'action '{action}': {e}")
                return 1
        else:
            # Aucune action spécifiée, afficher les actions disponibles
            actions = [name for name in dir(agent) if not name.startswith("_") and callable(getattr(agent, name))]
            logger.info(f"Actions disponibles pour l'agent '{agent_name}':")
            for action in actions:
                print(f"  - {action}")
            return 0
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de l'agent: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_agent())
