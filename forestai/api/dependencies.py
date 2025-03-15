"""
Dépendances pour l'API REST ForestAI.
Fournit les mécanismes d'injection de dépendances pour les routes FastAPI.
"""

import logging
from typing import Dict, Any, Optional
from functools import lru_cache

from forestai.core.utils.config import Config
from forestai.agents.geo_agent import GeoAgent
from forestai.agents.subsidy_agent import SubsidyAgent
from forestai.agents.diagnostic_agent import DiagnosticAgent

# Configuration du logger
logger = logging.getLogger("forestai.api.dependencies")

# Singleton pour les agents partagés
_geo_agent_instance = None
_subsidy_agent_instance = None
_diagnostic_agent_instance = None

@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    """
    Récupérer la configuration du système.
    
    Returns:
        Dictionnaire de configuration
    """
    config = Config.get_instance()
    config.load_config(env_file=".env")
    return config.as_dict()

def get_geo_agent() -> GeoAgent:
    """
    Récupérer l'instance de GeoAgent.
    
    Returns:
        Instance de GeoAgent
    """
    global _geo_agent_instance
    
    if _geo_agent_instance is None:
        logger.info("Initialisation du GeoAgent")
        config = get_config()
        _geo_agent_instance = GeoAgent(config)
    
    return _geo_agent_instance

def get_subsidy_agent() -> SubsidyAgent:
    """
    Récupérer l'instance de SubsidyAgent.
    
    Returns:
        Instance de SubsidyAgent
    """
    global _subsidy_agent_instance
    
    if _subsidy_agent_instance is None:
        logger.info("Initialisation du SubsidyAgent")
        config = get_config()
        _subsidy_agent_instance = SubsidyAgent(config)
    
    return _subsidy_agent_instance

def get_diagnostic_agent() -> DiagnosticAgent:
    """
    Récupérer l'instance de DiagnosticAgent.
    
    Returns:
        Instance de DiagnosticAgent
    """
    global _diagnostic_agent_instance
    
    if _diagnostic_agent_instance is None:
        logger.info("Initialisation du DiagnosticAgent")
        config = get_config()
        _diagnostic_agent_instance = DiagnosticAgent(config)
    
    return _diagnostic_agent_instance

def shutdown_agents():
    """
    Arrêter proprement les agents lors de l'arrêt de l'application.
    """
    global _geo_agent_instance, _subsidy_agent_instance, _diagnostic_agent_instance
    
    if _geo_agent_instance:
        logger.info("Arrêt du GeoAgent")
        _geo_agent_instance.unsubscribe_all()
        _geo_agent_instance = None
    
    if _subsidy_agent_instance:
        logger.info("Arrêt du SubsidyAgent")
        _subsidy_agent_instance.unsubscribe_all()
        _subsidy_agent_instance = None
    
    if _diagnostic_agent_instance:
        logger.info("Arrêt du DiagnosticAgent")
        _diagnostic_agent_instance.unsubscribe_all()
        _diagnostic_agent_instance = None
