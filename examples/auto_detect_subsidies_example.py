#!/usr/bin/env python
"""
Exemple de détection automatique des zones prioritaires pour subventions.

Cet exemple montre comment:
1. Rechercher une parcelle forestière
2. Détecter automatiquement les zones prioritaires
3. Calculer l'impact des zones prioritaires sur les subventions
4. Rechercher des subventions adaptées avec le SubsidyAgent

Usage:
    python examples/auto_detect_subsidies_example.py
"""

import os
import sys
import logging
import json
import time
from typing import Dict, Any, List, Optional
import uuid

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

logger = logging.getLogger("auto_detect_subsidies")

def main():
    """
    Fonction principale de l'exemple.
    """
    logger.info("Starting automatic subsidy detection example")
    
    # Charger la configuration
    config = Config.get_instance()
    config.load_config(".env")
    logger.info("Configuration loaded")
    
    # Initialiser les agents
    geo_agent = GeoAgent(config.as_dict())
    subsidy_agent = SubsidyAgent(config.as_dict())
    logger.info("Agents initialized")
    
    try:
        # 1. Rechercher une parcelle
        logger.info("Searching parcels in Saint-Martin-de-Crau")
        parcels_result = geo_agent.execute_action("search_parcels", {
            "commune": "Saint-Martin-de-Crau",
            "section": "B"
        })
        
        if parcels_result["status"] != "success":
            logger.error(f"Error searching parcels: {parcels_result.get('error_message', 'Unknown error')}")
            return
        
        parcels = parcels_result["result"]["parcels"]
        if not parcels:
            logger.error("No parcels found")
            return
        
        # Sélectionner la première parcelle
        parcel = parcels[0]
        parcel_id = parcel["id"]
        logger.info(f"Selected parcel: {parcel_id} ({parcel['area_ha']} ha)")
        
        # 2. Détecter automatiquement les zones prioritaires et calculer l'impact sur les subventions
        logger.info(f"Auto-detecting subsidy opportunities for parcel: {parcel_id}")
        
        auto_detect_result = geo_agent.execute_action("auto_detect_subsidies", {
            "parcel_id": parcel_id,
            "region": "Provence-Alpes-Côte d'Azur"
        })
        
        if auto_detect_result["status"] != "success":
            logger.error(f"Error auto-detecting subsidies: {auto_detect_result.get('error_message', 'Unknown error')}")
            return
        
        # Récupérer les résultats
        detection_results = auto_detect_result["result"]
        priority_zones = detection_results["priority_zones"]
        subsidy_impact = detection_results["subsidy_impact"]
        
        # Afficher les zones prioritaires détectées
        logger.info(f"Detected {len(priority_zones)} priority zones:")
        for zone in priority_zones:
            logger.info(f"- {zone['zone_type']} ({zone['name']}): {zone['coverage_percentage']}% coverage")
        
        # Afficher l'impact sur les subventions
        logger.info(f"Total subsidy bonus potential: {subsidy_impact['total_bonus_potential']}%")
        
        # Afficher les types de subventions recommandés
        recommended_subsidies = subsidy_impact["recommended_subsidies"]
        if recommended_subsidies:
            logger.info(f"Recommended subsidy types: {', '.join(recommended_subsidies)}")
        else:
            logger.info("No specific subsidy types recommended")
        
        # 3. Rechercher des subventions adaptées pour chaque type recommandé
        if recommended_subsidies:
            logger.info("Searching for matching subsidies")
            
            all_matching_subsidies = []
            
            for subsidy_type in recommended_subsidies:
                logger.info(f"Searching subsidies for type: {subsidy_type}")
                
                # Pour cet exemple, nous utilisons "reboisement" comme project_type générique
                # Dans une implémentation réelle, cela serait adapté selon le type de subvention
                subsidies_result = subsidy_agent.execute_action("search_subsidies", {
                    "project_type": "reboisement",
                    "region": "Provence-Alpes-Côte d'Azur",
                    "owner_type": parcel["owner_type"],
                    "priority_zones": priority_zones
                })
                
                if subsidies_result["status"] == "success":
                    matching_subsidies = subsidies_result["result"]
                    logger.info(f"Found {len(matching_subsidies)} matching subsidies for type {subsidy_type}")
                    all_matching_subsidies.extend(matching_subsidies)
                else:
                    logger.warning(f"Error searching subsidies for type {subsidy_type}: "
                                 f"{subsidies_result.get('error_message', 'Unknown error')}")
            
            # Éliminer les doublons (par ID)
            unique_subsidies = {}
            for subsidy in all_matching_subsidies:
                if subsidy["id"] not in unique_subsidies:
                    unique_subsidies[subsidy["id"]] = subsidy
            
            # Trier les subventions par score de priorité (si disponible)
            sorted_subsidies = sorted(
                unique_subsidies.values(),
                key=lambda s: s.get("priority_match", {}).get("score", 0),
                reverse=True
            )
            
            # Afficher les subventions trouvées
            logger.info(f"Found {len(sorted_subsidies)} unique matching subsidies")
            for i, subsidy in enumerate(sorted_subsidies, 1):
                logger.info(f"{i}. {subsidy['title']} ({subsidy['id']})")
                logger.info(f"   Amount: {subsidy['amount']}")
                logger.info(f"   Deadline: {subsidy['deadline']}")
                if "priority_match" in subsidy:
                    logger.info(f"   Priority bonus: {subsidy['priority_match']['score']}%")
            
            logger.info("Auto-detection example completed successfully")
        else:
            logger.info("No subsidy types recommended - example completed")
    
    except Exception as e:
        logger.exception(f"Error in auto-detection example: {str(e)}")
    
    finally:
        # Libérer les ressources
        geo_agent.unsubscribe_all()
        subsidy_agent.unsubscribe_all()
        logger.info("Agents unsubscribed from all topics")

if __name__ == "__main__":
    main()
