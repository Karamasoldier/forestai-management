#!/usr/bin/env python
"""
Exemple d'intégration entre le GeoAgent et le SubsidyAgent.

Cet exemple montre comment:
1. Rechercher une parcelle forestière
2. Analyser son potentiel forestier via le GeoAgent
3. Détecter les zones prioritaires
4. Rechercher des subventions adaptées avec le SubsidyAgent
5. Analyser l'éligibilité à une subvention spécifique
6. Générer un dossier de demande de subvention

Usage:
    python examples/subsidy_geo_integration_example.py
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

logger = logging.getLogger("subsidy_geo_integration")

def main():
    """
    Fonction principale de l'exemple.
    """
    logger.info("Starting SubsidyAgent-GeoAgent integration example")
    
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
        
        # 2. Analyser le potentiel forestier
        logger.info(f"Analyzing forestry potential for parcel: {parcel_id}")
        potential_result = geo_agent.execute_action("analyze_potential", {
            "parcel_id": parcel_id
        })
        
        if potential_result["status"] != "success":
            logger.error(f"Error analyzing potential: {potential_result.get('error_message', 'Unknown error')}")
            return
        
        potential = potential_result["result"]
        logger.info(f"Potential score: {potential['potential_score']} ({potential['potential_class']})")
        logger.info(f"Recommended species: {', '.join(potential['recommended_species'])}")
        
        # 3. Détecter les zones prioritaires
        logger.info(f"Detecting priority zones for parcel: {parcel_id}")
        priority_zones_result = geo_agent.execute_action("detect_priority_zones", {
            "parcel_id": parcel_id
        })
        
        if priority_zones_result["status"] != "success":
            logger.error(f"Error detecting priority zones: {priority_zones_result.get('error_message', 'Unknown error')}")
            return
        
        priority_zones = priority_zones_result["result"]
        logger.info(f"Detected {len(priority_zones)} priority zones")
        for zone in priority_zones:
            logger.info(f"- {zone['zone_type']} ({zone['coverage_percentage']}% coverage)")
        
        # 4. Rechercher des subventions adaptées
        logger.info("Searching suitable subsidies")
        subsidies_result = subsidy_agent.execute_action("search_subsidies", {
            "project_type": "reboisement",
            "region": "Provence-Alpes-Côte d'Azur",
            "owner_type": parcel["owner_type"],
            "priority_zones": priority_zones
        })
        
        if subsidies_result["status"] != "success":
            logger.error(f"Error searching subsidies: {subsidies_result.get('error_message', 'Unknown error')}")
            return
        
        subsidies = subsidies_result["result"]
        if not subsidies:
            logger.error("No suitable subsidies found")
            return
        
        logger.info(f"Found {len(subsidies)} suitable subsidies")
        
        # Afficher les subventions trouvées
        for i, subsidy in enumerate(subsidies, 1):
            logger.info(f"{i}. {subsidy['title']} ({subsidy['id']})")
            logger.info(f"   Amount: {subsidy['amount']}")
            logger.info(f"   Deadline: {subsidy['deadline']}")
            if "priority_match" in subsidy:
                logger.info(f"   Priority bonus: {subsidy['priority_match']['score']}%")
        
        # Sélectionner la première subvention
        selected_subsidy = subsidies[0]
        subsidy_id = selected_subsidy["id"]
        logger.info(f"Selected subsidy: {selected_subsidy['title']} ({subsidy_id})")
        
        # 5. Analyser l'éligibilité
        logger.info(f"Analyzing eligibility for subsidy: {subsidy_id}")
        
        # Créer un projet à partir des données de la parcelle et de l'analyse
        project = {
            "type": "reboisement",
            "area_ha": potential["area_ha"],
            "location": parcel_id,
            "species": potential["recommended_species"][:2],  # Sélectionner les 2 premières espèces recommandées
            "priority_zones": priority_zones
        }
        
        eligibility_result = subsidy_agent.execute_action("analyze_eligibility", {
            "project": project,
            "subsidy_id": subsidy_id
        })
        
        if eligibility_result["status"] != "success":
            logger.error(f"Error analyzing eligibility: {eligibility_result.get('error_message', 'Unknown error')}")
            return
        
        eligibility = eligibility_result["result"]
        if eligibility["eligible"]:
            logger.info(f"Project is eligible for subsidy with score: {eligibility['eligibility_score']}%")
            if "priority_bonus" in eligibility:
                logger.info(f"Priority zone bonus: {eligibility['priority_bonus']}%")
        else:
            logger.warning("Project is not eligible for subsidy")
            return
        
        # 6. Générer un dossier de demande
        logger.info("Generating subsidy application")
        
        # Données du demandeur (fictives pour l'exemple)
        applicant = {
            "name": "Domaine Forestier du Sud",
            "address": "Route des Pins 13200 Arles",
            "contact": "contact@domaineforestier.fr",
            "siret": "12345678900012"
        }
        
        application_result = subsidy_agent.execute_action("generate_application", {
            "project": project,
            "subsidy_id": subsidy_id,
            "applicant": applicant,
            "output_formats": ["pdf", "html", "docx"]
        })
        
        if application_result["status"] != "success":
            logger.error(f"Error generating application: {application_result.get('error_message', 'Unknown error')}")
            return
        
        # Afficher les fichiers générés
        output_files = application_result["result"]
        logger.info("Application documents generated successfully")
        for format_type, file_path in output_files.items():
            logger.info(f"- {format_type.upper()}: {file_path}")
        
        logger.info("Integration example completed successfully")
    
    except Exception as e:
        logger.exception(f"Error in integration example: {str(e)}")
    
    finally:
        # Libérer les ressources
        geo_agent.unsubscribe_all()
        subsidy_agent.unsubscribe_all()
        logger.info("Agents unsubscribed from all topics")

if __name__ == "__main__":
    main()
