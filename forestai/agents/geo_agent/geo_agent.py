"""
Module GeoAgent - Agent de géotraitement pour ForestAI.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union

from forestai.core.domain.base_agent import BaseAgent
from forestai.core.domain.services.geo_service import GeoService
from forestai.core.domain.services.priority_zone_service import PriorityZoneService
from forestai.core.communication.message_bus import Message
from forestai.core.utils.logging_config import log_function

logger = logging.getLogger(__name__)

class GeoAgent(BaseAgent):
    """
    Agent de géotraitement pour l'analyse géospatiale des parcelles forestières.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, agent_id: Optional[str] = None,
                 subscribe_topics: Optional[List[str]] = None):
        """
        Initialise l'agent de géotraitement.
        
        Args:
            config: Configuration de l'agent (optionnel)
            agent_id: Identifiant de l'agent (optionnel)
            subscribe_topics: Liste des sujets auxquels s'abonner (optionnel)
        """
        # Sujets par défaut
        default_topics = [
            "PARCEL_ANALYSIS_REQUESTED",
            "MAP_GENERATION_REQUESTED",
            "PRIORITY_ZONE_DETECTION_REQUESTED"
        ]
        
        # Combiner les sujets par défaut et les sujets spécifiés
        all_topics = list(set(default_topics + (subscribe_topics or [])))
        
        # Initialiser la classe parent
        super().__init__(config, agent_id, all_topics)
        
        # Initialiser les services
        self.geo_service = GeoService(self.config.as_dict())
        self.priority_zone_service = PriorityZoneService(self.config.as_dict())
        
        logger.info(f"GeoAgent initialized: {self.agent_id}")
    
    @log_function
    def handle_message(self, message: Message) -> None:
        """
        Gère les messages reçus.
        
        Args:
            message: Message reçu
        """
        topic = message.topic
        data = message.data
        
        logger.info(f"GeoAgent handling message: {topic}")
        
        if topic == "PARCEL_ANALYSIS_REQUESTED":
            # Analyser une parcelle
            parcel_id = data.get("parcel_id")
            geometry = data.get("geometry")
            
            try:
                analysis_result = self.geo_service.analyze_potential(parcel_id, geometry)
                
                # Publier le résultat
                self.publish_message("PARCEL_ANALYSIS_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "parcel_id": parcel_id,
                    "result": analysis_result,
                    "status": "success"
                })
            except Exception as e:
                logger.exception(f"Error analyzing parcel: {str(e)}")
                
                # Publier l'erreur
                self.publish_message("PARCEL_ANALYSIS_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "parcel_id": parcel_id,
                    "status": "error",
                    "error_message": str(e)
                })
        
        elif topic == "MAP_GENERATION_REQUESTED":
            # Générer une carte
            parcel_id = data.get("parcel_id")
            map_type = data.get("map_type", "vegetation")
            output_format = data.get("output_format", "png")
            include_basemap = data.get("include_basemap", True)
            
            try:
                map_path = self.geo_service.generate_map(
                    parcel_id, map_type, output_format, include_basemap
                )
                
                # Publier le résultat
                self.publish_message("MAP_GENERATION_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "parcel_id": parcel_id,
                    "map_path": map_path,
                    "status": "success"
                })
            except Exception as e:
                logger.exception(f"Error generating map: {str(e)}")
                
                # Publier l'erreur
                self.publish_message("MAP_GENERATION_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "parcel_id": parcel_id,
                    "status": "error",
                    "error_message": str(e)
                })
        
        elif topic == "PRIORITY_ZONE_DETECTION_REQUESTED":
            # Détecter les zones prioritaires
            parcel_id = data.get("parcel_id")
            region = data.get("region")
            
            try:
                # Récupérer la géométrie de la parcelle
                parcel_data = self.geo_service.get_parcel_geometry(parcel_id)
                geometry = json.loads(parcel_data["geometry"])
                
                # Détecter les zones prioritaires
                priority_zones = self.detect_priority_zones(parcel_id, geometry, region)
                
                # Calculer l'impact sur les subventions
                subsidy_impact = self.priority_zone_service.get_subsidy_impact(priority_zones)
                
                # Publier le résultat
                self.publish_message("PRIORITY_ZONE_DETECTION_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "parcel_id": parcel_id,
                    "priority_zones": priority_zones,
                    "subsidy_impact": subsidy_impact,
                    "status": "success"
                })
            except Exception as e:
                logger.exception(f"Error detecting priority zones: {str(e)}")
                
                # Publier l'erreur
                self.publish_message("PRIORITY_ZONE_DETECTION_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "parcel_id": parcel_id,
                    "status": "error",
                    "error_message": str(e)
                })
    
    @log_function
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une action.
        
        Args:
            action: Action à exécuter
            params: Paramètres de l'action
            
        Returns:
            Résultat de l'action
        """
        logger.info(f"GeoAgent executing action: {action}")
        
        try:
            if action == "search_parcels":
                # Rechercher des parcelles
                commune = params.get("commune")
                section = params.get("section")
                
                if not commune:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: commune"
                    }
                
                result = self.geo_service.search_parcels(commune, section)
                return {
                    "status": "success",
                    "result": result
                }
            
            elif action == "get_parcel_geometry":
                # Récupérer la géométrie d'une parcelle
                parcel_id = params.get("parcel_id")
                
                if not parcel_id:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: parcel_id"
                    }
                
                result = self.geo_service.get_parcel_geometry(parcel_id)
                return {
                    "status": "success",
                    "result": result
                }
            
            elif action == "get_parcel_data":
                # Récupérer les données d'une parcelle
                parcel_id = params.get("parcel_id")
                
                if not parcel_id:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: parcel_id"
                    }
                
                result = self.geo_service.get_parcel_data(parcel_id)
                return {
                    "status": "success",
                    "result": result
                }
            
            elif action == "analyze_potential":
                # Analyser le potentiel forestier
                parcel_id = params.get("parcel_id")
                geometry = params.get("geometry")
                
                if not parcel_id and not geometry:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: either parcel_id or geometry must be provided"
                    }
                
                result = self.geo_service.analyze_potential(parcel_id, geometry)
                return {
                    "status": "success",
                    "result": result
                }
            
            elif action == "detect_priority_zones":
                # Détecter les zones prioritaires
                parcel_id = params.get("parcel_id")
                region = params.get("region")
                
                if not parcel_id:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: parcel_id"
                    }
                
                # Récupérer la géométrie de la parcelle
                parcel_data = self.geo_service.get_parcel_geometry(parcel_id)
                geometry = json.loads(parcel_data["geometry"])
                
                # Détecter les zones prioritaires
                result = self.detect_priority_zones(parcel_id, geometry, region)
                return {
                    "status": "success",
                    "result": result
                }
            
            elif action == "auto_detect_subsidies":
                # Détecter automatiquement les subventions potentielles
                parcel_id = params.get("parcel_id")
                region = params.get("region")
                
                if not parcel_id:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: parcel_id"
                    }
                
                # Récupérer la géométrie de la parcelle
                parcel_data = self.geo_service.get_parcel_geometry(parcel_id)
                geometry = json.loads(parcel_data["geometry"])
                
                # Détecter les zones prioritaires
                priority_zones = self.detect_priority_zones(parcel_id, geometry, region)
                
                # Calculer l'impact sur les subventions
                subsidy_impact = self.priority_zone_service.get_subsidy_impact(priority_zones)
                
                return {
                    "status": "success",
                    "result": {
                        "priority_zones": priority_zones,
                        "subsidy_impact": subsidy_impact
                    }
                }
            
            elif action == "generate_map":
                # Générer une carte
                parcel_id = params.get("parcel_id")
                map_type = params.get("map_type", "vegetation")
                output_format = params.get("output_format", "png")
                include_basemap = params.get("include_basemap", True)
                
                if not parcel_id:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: parcel_id"
                    }
                
                result = self.geo_service.generate_map(
                    parcel_id, map_type, output_format, include_basemap
                )
                return {
                    "status": "success",
                    "result": result
                }
            
            else:
                # Action inconnue
                return {
                    "status": "error",
                    "error_message": f"Unknown action: {action}"
                }
        
        except Exception as e:
            logger.exception(f"Error executing action {action}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def detect_priority_zones(self, parcel_id: str, geometry: Dict[str, Any], region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Détecte les zones prioritaires pour une parcelle.
        
        Args:
            parcel_id: Identifiant de la parcelle
            geometry: Géométrie de la parcelle
            region: Région administrative (optionnel)
            
        Returns:
            Liste des zones prioritaires
        """
        # Si aucune région n'est spécifiée, essayer de la récupérer depuis les données de la parcelle
        if not region:
            try:
                parcel_data = self.geo_service.get_parcel_data(parcel_id)
                region = parcel_data.get("region")
            except Exception as e:
                logger.warning(f"Failed to get region from parcel data: {str(e)}")
        
        # Détecter les zones prioritaires
        priority_zones = self.priority_zone_service.detect_priority_zones(geometry, region)
        logger.info(f"Detected {len(priority_zones)} priority zones for parcel {parcel_id}")
        
        return priority_zones
