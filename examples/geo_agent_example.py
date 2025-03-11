#!/usr/bin/env python3
"""
Exemple d'utilisation du GeoAgent avec l'architecture en couches.

Ce script montre comment interagir avec le GeoAgent en utilisant:
1. L'API directe
2. Le message bus
3. L'interaction entre agents

Exécuter avec:
python examples/geo_agent_example.py
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any
import threading

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forestai.agents.geo_agent.geo_agent_v2 import GeoAgentV2
from forestai.core.infrastructure.messaging.message_bus import get_message_bus, Message, MessagePriority
from forestai.core.infrastructure.memory.agent_memory import get_agent_memory
from forestai.core.domain.models.parcel import (
    Parcel, 
    ParcelIdentifier, 
    ParcelGeometry, 
    TerrainCharacteristics,
    ParcelOwner
)


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("example")


def create_mock_data(config: Dict[str, Any]):
    """
    Crée des données de test pour l'exemple.
    
    Args:
        config: Configuration
    """
    from forestai.core.infrastructure.repositories.geopandas_parcel_repository import create_geopandas_parcel_repository
    
    # Créer le repository
    repository = create_geopandas_parcel_repository(config)
    
    # Vérifier si des données existent déjà
    test_parcel = repository.find_by_department("13", 0)
    if test_parcel:
        logger.info(f"Données de test déjà présentes ({len(test_parcel)} parcelles)")
        return
    
    # Créer des parcelles de test
    parcels = []
    
    # Parcelle 1
    parcel1 = Parcel(
        identifier=ParcelIdentifier(
            department_code="13",
            commune_code="001",
            section="A",
            number="101"
        ),
        geometry=ParcelGeometry(
            wkt="POLYGON((4.8 43.6, 4.8 43.61, 4.81 43.61, 4.81 43.6, 4.8 43.6))",
            area_ha=2.5,
            perimeter_m=400,
            centroid_x=4.805,
            centroid_y=43.605,
            bbox=[4.8, 43.6, 4.81, 43.61]
        ),
        owner=ParcelOwner(
            name="Jean Dupont",
            address="1 rue des Oliviers, 13100 Aix-en-Provence",
            is_company=False
        ),
        terrain=TerrainCharacteristics(
            avg_slope=5.0,
            max_slope=8.0,
            min_elevation=120.0,
            max_elevation=150.0,
            avg_elevation=135.0,
            aspect="S",
            soil_type="limon",
            water_presence=True,
            wetland_area_pct=5.0
        ),
        current_land_use="friche"
    )
    parcels.append(parcel1)
    
    # Parcelle 2
    parcel2 = Parcel(
        identifier=ParcelIdentifier(
            department_code="13",
            commune_code="001",
            section="A",
            number="102"
        ),
        geometry=ParcelGeometry(
            wkt="POLYGON((4.81 43.6, 4.81 43.61, 4.82 43.61, 4.82 43.6, 4.81 43.6))",
            area_ha=3.0,
            perimeter_m=450,
            centroid_x=4.815,
            centroid_y=43.605,
            bbox=[4.81, 43.6, 4.82, 43.61]
        ),
        owner=ParcelOwner(
            name="Marie Martin",
            address="2 avenue des Pins, 13090 Aix-en-Provence",
            is_company=False
        ),
        terrain=TerrainCharacteristics(
            avg_slope=8.0,
            max_slope=12.0,
            min_elevation=130.0,
            max_elevation=160.0,
            avg_elevation=145.0,
            aspect="SE",
            soil_type="argile",
            water_presence=False,
            wetland_area_pct=0.0
        ),
        current_land_use="culture"
    )
    parcels.append(parcel2)
    
    # Parcelle 3
    parcel3 = Parcel(
        identifier=ParcelIdentifier(
            department_code="13",
            commune_code="001",
            section="B",
            number="201"
        ),
        geometry=ParcelGeometry(
            wkt="POLYGON((4.83 43.62, 4.83 43.63, 4.84 43.63, 4.84 43.62, 4.83 43.62))",
            area_ha=5.0,
            perimeter_m=600,
            centroid_x=4.835,
            centroid_y=43.625,
            bbox=[4.83, 43.62, 4.84, 43.63]
        ),
        owner=ParcelOwner(
            name="Société Forestière du Sud",
            address="15 rue des Platanes, 13100 Aix-en-Provence",
            is_company=True
        ),
        terrain=TerrainCharacteristics(
            avg_slope=15.0,
            max_slope=20.0,
            min_elevation=200.0,
            max_elevation=250.0,
            avg_elevation=225.0,
            aspect="E",
            soil_type="calcaire",
            water_presence=True,
            wetland_area_pct=10.0
        ),
        current_land_use="forestier"
    )
    parcels.append(parcel3)
    
    # Sauvegarder les parcelles
    for parcel in parcels:
        repository.save(parcel)
    
    logger.info(f"Créé {len(parcels)} parcelles de test")


def demo_direct_api(geo_agent: GeoAgentV2):
    """
    Démontre l'utilisation directe de l'API de l'agent.
    
    Args:
        geo_agent: Instance de l'agent
    """
    logger.info("=== Démo de l'API directe ===")
    
    # Rechercher les parcelles dans le département 13
    result = geo_agent.find_profitable_parcels("13", 1.0)
    logger.info(f"Recherche de parcelles soumise: {result}")
    
    # Attendre un peu pour le traitement
    time.sleep(2)
    
    # Vérifier l'état de la tâche
    task_id = result["task_id"]
    task_status = get_agent_memory().retrieve(task_id)
    logger.info(f"État de la tâche: {task_status}")
    
    # Analyser le potentiel forestier des parcelles
    # Normalement, on utiliserait les IDs des parcelles trouvées,
    # mais pour simplifier la démo, on utilise des IDs factices
    parcels = [
        "1",  # ID factice pour la démo
        "2",
        "3"
    ]
    
    result = geo_agent.analyze_parcel_potential(parcels)
    logger.info(f"Analyse de potentiel soumise: {result}")
    
    # Attendre un peu pour le traitement
    time.sleep(2)


def handle_search_results(message: Message):
    """
    Gestionnaire pour les messages de résultats de recherche.
    
    Args:
        message: Message reçu
    """
    logger.info(f"Reçu résultats de recherche: {message.payload}")
    
    # Dans une application réelle, on pourrait traiter les résultats ici
    # Par exemple, en les affichant dans une interface utilisateur
    # ou en les transmettant à un autre agent pour traitement


def demo_message_bus(geo_agent: GeoAgentV2):
    """
    Démontre l'utilisation du message bus pour communiquer avec l'agent.
    
    Args:
        geo_agent: Instance de l'agent
    """
    logger.info("=== Démo du message bus ===")
    
    # Obtenir le message bus
    message_bus = get_message_bus()
    
    # S'abonner aux résultats
    message_bus.subscribe("parcel.search_results", handle_search_results)
    message_bus.subscribe("parcel.potential_analysis_results", 
                         lambda msg: logger.info(f"Reçu résultats d'analyse: {msg.payload}"))
    
    # Démarrer le message bus s'il n'est pas déjà en cours d'exécution
    if not message_bus.is_running:
        message_bus.start()
    
    # Envoyer une demande de recherche
    message_bus.create_and_publish(
        topic="parcel.search_request",
        payload={
            "department": "13",
            "min_area": 2.0
        },
        sender="Example"
    )
    
    # Attendre un peu pour le traitement
    time.sleep(3)
    
    # Envoyer une demande d'analyse de potentiel
    message_bus.create_and_publish(
        topic="parcel.analyze_request",
        payload={
            "parcel_ids": ["1", "2", "3"]  # IDs factices pour la démo
        },
        sender="Example"
    )
    
    # Attendre un peu pour le traitement
    time.sleep(3)


class MockReglementationAgent:
    """
    Agent de réglementation simplifié pour la démonstration.
    """
    
    def __init__(self):
        """Initialise l'agent de réglementation simulé."""
        self.logger = logging.getLogger("MockReglementationAgent")
        self.message_bus = get_message_bus()
        self.memory = get_agent_memory()
        
        # S'abonner aux messages pertinents
        self.message_bus.subscribe("parcel.potential_analysis_results", self._handle_analysis_results)
        self.logger.info("Agent de réglementation mock initialisé")
    
    def _handle_analysis_results(self, message: Message):
        """
        Traite les résultats d'analyse de potentiel.
        
        Args:
            message: Message reçu
        """
        self.logger.info(f"Reçu résultats d'analyse de potentiel")
        payload = message.payload
        
        # Simuler une analyse réglementaire
        time.sleep(1)
        
        # Publier les résultats de l'analyse réglementaire
        self.message_bus.create_and_publish(
            topic="regulation.compliance_results",
            payload={
                "parcel_count": payload.get("parcel_count", 0),
                "compliant_count": payload.get("parcel_count", 0) - 1,  # Simuler une non-conformité
                "message": "Analyse réglementaire terminée"
            },
            sender="ReglementationAgent"
        )


def demo_agent_interaction(geo_agent: GeoAgentV2):
    """
    Démontre l'interaction entre agents via le message bus.
    
    Args:
        geo_agent: Instance de GeoAgent
    """
    logger.info("=== Démo d'interaction entre agents ===")
    
    # Créer un agent de réglementation simulé
    reglementation_agent = MockReglementationAgent()
    
    # Obtenir le message bus
    message_bus = get_message_bus()
    
    # S'abonner aux résultats de l'analyse réglementaire
    message_bus.subscribe(
        "regulation.compliance_results",
        lambda msg: logger.info(f"Résultats de conformité réglementaire: {msg.payload}")
    )
    
    # Envoyer une demande d'analyse qui déclenchera une chaîne de traitement
    message_bus.create_and_publish(
        topic="parcel.analyze_request",
        payload={
            "parcel_ids": ["1", "2", "3"]  # IDs factices pour la démo
        },
        sender="Example"
    )
    
    # Attendre que la chaîne de traitement se termine
    time.sleep(5)


def main():
    """Point d'entrée principal."""
    logger.info("Démarrage de l'exemple GeoAgent")
    
    # Configuration
    config = {
        "data_path": "./data",
        "output_path": "./data/outputs"
    }
    
    # Créer les répertoires nécessaires
    os.makedirs(config["data_path"], exist_ok=True)
    os.makedirs(config["output_path"], exist_ok=True)
    
    # Créer des données de test
    create_mock_data(config)
    
    # Créer et démarrer l'agent
    geo_agent = GeoAgentV2(config)
    agent_thread = threading.Thread(target=geo_agent.run)
    agent_thread.daemon = True
    agent_thread.start()
    
    # Attendre que l'agent soit prêt
    time.sleep(1)
    
    try:
        # Démontrer l'API directe
        demo_direct_api(geo_agent)
        
        # Démontrer l'utilisation du message bus
        demo_message_bus(geo_agent)
        
        # Démontrer l'interaction entre agents
        demo_agent_interaction(geo_agent)
        
    except KeyboardInterrupt:
        logger.info("Interruption de l'utilisateur")
    finally:
        # Arrêter l'agent
        geo_agent.stop()
        
        # Attendre que le thread se termine
        time.sleep(1)
    
    logger.info("Exemple terminé")


if __name__ == "__main__":
    main()
