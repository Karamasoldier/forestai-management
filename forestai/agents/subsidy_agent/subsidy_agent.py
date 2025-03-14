"""
Module SubsidyAgent - Agent de gestion des subventions pour ForestAI.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union

from forestai.core.domain.base_agent import BaseAgent
from forestai.core.domain.services.subsidy_service import SubsidyService
from forestai.core.communication.message_bus import Message
from forestai.core.utils.logging_config import log_function

logger = logging.getLogger(__name__)

class SubsidyAgent(BaseAgent):
    """
    Agent de gestion des subventions pour la recherche, l'analyse d'éligibilité
    et la génération de documents de demande.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, agent_id: Optional[str] = None,
                 subscribe_topics: Optional[List[str]] = None):
        """
        Initialise l'agent de subventions.
        
        Args:
            config: Configuration de l'agent (optionnel)
            agent_id: Identifiant de l'agent (optionnel)
            subscribe_topics: Liste des sujets auxquels s'abonner (optionnel)
        """
        # Sujets par défaut
        default_topics = [
            "SUBSIDIES_SEARCH_REQUESTED",
            "ELIGIBILITY_ANALYSIS_REQUESTED",
            "APPLICATION_GENERATION_REQUESTED",
            "PARCEL_ANALYSIS_COMPLETED",  # Pour intégration avec GeoAgent
            "PRIORITY_ZONE_DETECTION_COMPLETED"  # Pour intégration avec GeoAgent
        ]
        
        # Combiner les sujets par défaut et les sujets spécifiés
        all_topics = list(set(default_topics + (subscribe_topics or [])))
        
        # Initialiser la classe parent
        super().__init__(config, agent_id, all_topics)
        
        # Initialiser le service de subventions
        self.subsidy_service = SubsidyService(self.config.as_dict())
        
        # Cache des résultats d'analyse de parcelles
        self.parcel_analysis_cache = {}
        self.priority_zone_cache = {}
        
        logger.info(f"SubsidyAgent initialized: {self.agent_id}")
    
    @log_function
    def handle_message(self, message: Message) -> None:
        """
        Gère les messages reçus.
        
        Args:
            message: Message reçu
        """
        topic = message.topic
        data = message.data
        
        logger.info(f"SubsidyAgent handling message: {topic}")
        
        if topic == "SUBSIDIES_SEARCH_REQUESTED":
            # Rechercher des subventions
            project_type = data.get("project_type")
            region = data.get("region")
            owner_type = data.get("owner_type")
            priority_zones = data.get("priority_zones")
            
            try:
                subsidies = self.subsidy_service.search_subsidies(
                    project_type=project_type,
                    region=region,
                    owner_type=owner_type,
                    priority_zones=priority_zones
                )
                
                # Publier le résultat
                self.publish_message("SUBSIDIES_SEARCH_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "subsidies": subsidies,
                    "status": "success"
                })
            except Exception as e:
                logger.exception(f"Error searching subsidies: {str(e)}")
                
                # Publier l'erreur
                self.publish_message("SUBSIDIES_SEARCH_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "status": "error",
                    "error_message": str(e)
                })
        
        elif topic == "ELIGIBILITY_ANALYSIS_REQUESTED":
            # Analyser l'éligibilité
            project = data.get("project", {})
            subsidy_id = data.get("subsidy_id")
            
            try:
                eligibility = self.subsidy_service.analyze_eligibility(
                    project=project,
                    subsidy_id=subsidy_id
                )
                
                # Publier le résultat
                self.publish_message("ELIGIBILITY_ANALYSIS_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "subsidy_id": subsidy_id,
                    "eligibility": eligibility,
                    "status": "success"
                })
            except Exception as e:
                logger.exception(f"Error analyzing eligibility: {str(e)}")
                
                # Publier l'erreur
                self.publish_message("ELIGIBILITY_ANALYSIS_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "subsidy_id": subsidy_id,
                    "status": "error",
                    "error_message": str(e)
                })
        
        elif topic == "APPLICATION_GENERATION_REQUESTED":
            # Générer une demande de subvention
            project = data.get("project", {})
            subsidy_id = data.get("subsidy_id")
            applicant = data.get("applicant", {})
            output_formats = data.get("output_formats", ["pdf"])
            
            try:
                output_files = self.subsidy_service.generate_application(
                    project=project,
                    subsidy_id=subsidy_id,
                    applicant=applicant,
                    output_formats=output_formats
                )
                
                # Publier le résultat
                self.publish_message("APPLICATION_GENERATION_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "subsidy_id": subsidy_id,
                    "output_files": output_files,
                    "status": "success"
                })
            except Exception as e:
                logger.exception(f"Error generating application: {str(e)}")
                
                # Publier l'erreur
                self.publish_message("APPLICATION_GENERATION_COMPLETED", {
                    "request_id": data.get("request_id"),
                    "subsidy_id": subsidy_id,
                    "status": "error",
                    "error_message": str(e)
                })
        
        elif topic == "PARCEL_ANALYSIS_COMPLETED":
            # Traiter les résultats d'analyse de parcelle du GeoAgent
            if data.get("status") == "success":
                parcel_id = data.get("parcel_id")
                result = data.get("result", {})
                
                # Stocker les données d'analyse dans le cache
                self.parcel_analysis_cache[parcel_id] = result
                
                logger.info(f"Received parcel analysis for {parcel_id} from GeoAgent")
                
                # Vérifier s'il y a une demande de subvention en attente pour cette parcelle
                pending_request_id = self._check_pending_subsidy_requests(parcel_id)
                if pending_request_id:
                    self._process_pending_subsidy_request(pending_request_id, parcel_id)
        
        elif topic == "PRIORITY_ZONE_DETECTION_COMPLETED":
            # Traiter les résultats de détection de zones prioritaires du GeoAgent
            if data.get("status") == "success":
                parcel_id = data.get("parcel_id")
                priority_zones = data.get("priority_zones", [])
                
                # Stocker les données de zones prioritaires dans le cache
                self.priority_zone_cache[parcel_id] = priority_zones
                
                logger.info(f"Received priority zones for {parcel_id} from GeoAgent")
                
                # Vérifier s'il y a une demande de subvention en attente pour cette parcelle
                pending_request_id = self._check_pending_subsidy_requests(parcel_id)
                if pending_request_id:
                    self._process_pending_subsidy_request(pending_request_id, parcel_id)
    
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
        logger.info(f"SubsidyAgent executing action: {action}")
        
        try:
            if action == "search_subsidies":
                # Rechercher des subventions
                project_type = params.get("project_type")
                region = params.get("region")
                owner_type = params.get("owner_type")
                
                if not project_type:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: project_type"
                    }
                
                # Si une parcelle est spécifiée, enrichir les données avec les zones prioritaires
                parcel_id = params.get("parcel_id")
                priority_zones = None
                
                if parcel_id:
                    # Vérifier si les zones prioritaires sont déjà dans le cache
                    if parcel_id in self.priority_zone_cache:
                        priority_zones = self.priority_zone_cache[parcel_id]
                    else:
                        # Demander l'analyse des zones prioritaires au GeoAgent
                        request_id = str(uuid.uuid4())
                        self.publish_message("PRIORITY_ZONE_DETECTION_REQUESTED", {
                            "request_id": request_id,
                            "parcel_id": parcel_id
                        })
                        
                        logger.info(f"Requested priority zone detection for {parcel_id} from GeoAgent")
                
                result = self.subsidy_service.search_subsidies(
                    project_type=project_type,
                    region=region,
                    owner_type=owner_type,
                    priority_zones=priority_zones
                )
                
                return {
                    "status": "success",
                    "result": result
                }
            
            elif action == "analyze_eligibility":
                # Analyser l'éligibilité
                project = params.get("project", {})
                subsidy_id = params.get("subsidy_id")
                
                if not project:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: project"
                    }
                
                if not subsidy_id:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: subsidy_id"
                    }
                
                # Si une parcelle est spécifiée, enrichir les données du projet
                parcel_id = project.get("location")
                if parcel_id:
                    enhanced_project = self._enhance_project_with_geo_data(project, parcel_id)
                    if enhanced_project:
                        project = enhanced_project
                
                result = self.subsidy_service.analyze_eligibility(
                    project=project,
                    subsidy_id=subsidy_id
                )
                
                return {
                    "status": "success",
                    "result": result
                }
            
            elif action == "generate_application":
                # Générer une demande de subvention
                project = params.get("project", {})
                subsidy_id = params.get("subsidy_id")
                applicant = params.get("applicant", {})
                output_formats = params.get("output_formats", ["pdf"])
                
                if not project:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: project"
                    }
                
                if not subsidy_id:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: subsidy_id"
                    }
                
                if not applicant:
                    return {
                        "status": "error",
                        "error_message": "Missing required parameter: applicant"
                    }
                
                # Si une parcelle est spécifiée, enrichir les données du projet
                parcel_id = project.get("location")
                if parcel_id:
                    enhanced_project = self._enhance_project_with_geo_data(project, parcel_id)
                    if enhanced_project:
                        project = enhanced_project
                
                result = self.subsidy_service.generate_application(
                    project=project,
                    subsidy_id=subsidy_id,
                    applicant=applicant,
                    output_formats=output_formats
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
    
    def _enhance_project_with_geo_data(self, project: Dict[str, Any], parcel_id: str) -> Optional[Dict[str, Any]]:
        """
        Enrichit les données du projet avec les données géospatiales.
        
        Args:
            project: Données du projet
            parcel_id: Identifiant de la parcelle
            
        Returns:
            Projet enrichi ou None si les données ne sont pas disponibles
        """
        enhanced_project = project.copy()
        
        # Vérifier si les données d'analyse sont dans le cache
        if parcel_id in self.parcel_analysis_cache:
            analysis = self.parcel_analysis_cache[parcel_id]
            
            # Ajouter les données d'analyse au projet
            if "area_ha" not in enhanced_project and "area_ha" in analysis:
                enhanced_project["area_ha"] = analysis["area_ha"]
            
            if "average_slope" not in enhanced_project and "average_slope" in analysis:
                enhanced_project["slope"] = analysis["average_slope"]
            
            if "average_elevation" not in enhanced_project and "average_elevation" in analysis:
                enhanced_project["elevation"] = analysis["average_elevation"]
            
            if "dominant_soil_type" not in enhanced_project and "dominant_soil_type" in analysis:
                enhanced_project["soil_type"] = analysis["dominant_soil_type"]
            
            if "risks" not in enhanced_project and "risks" in analysis:
                enhanced_project["risks"] = analysis["risks"]
            
            logger.info(f"Enhanced project with parcel analysis data for {parcel_id}")
        
        # Vérifier si les données de zones prioritaires sont dans le cache
        if parcel_id in self.priority_zone_cache:
            priority_zones = self.priority_zone_cache[parcel_id]
            
            # Ajouter les zones prioritaires au projet
            enhanced_project["priority_zones"] = priority_zones
            
            logger.info(f"Enhanced project with priority zones data for {parcel_id}")
        
        # Si aucune donnée n'a été ajoutée, retourner None
        if enhanced_project == project:
            return None
        
        return enhanced_project
    
    def _check_pending_subsidy_requests(self, parcel_id: str) -> Optional[str]:
        """
        Vérifie s'il y a une demande de subvention en attente pour une parcelle.
        
        Args:
            parcel_id: Identifiant de la parcelle
            
        Returns:
            Identifiant de la demande en attente ou None
        """
        # Dans une vraie implémentation, cela vérifierait une file d'attente de demandes
        return None
    
    def _process_pending_subsidy_request(self, request_id: str, parcel_id: str) -> None:
        """
        Traite une demande de subvention en attente.
        
        Args:
            request_id: Identifiant de la demande
            parcel_id: Identifiant de la parcelle
        """
        # Dans une vraie implémentation, cela traiterait la demande en attente
        pass
