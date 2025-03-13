"""
Agent de réglementation forestière pour ForestAI.

Cet agent est responsable de l'analyse de conformité réglementaire
des projets forestiers selon le Code Forestier français et autres
réglementations environnementales applicables.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
import datetime

from forestai.agents.base_agent import BaseAgent
from forestai.core.domain.models.regulation import Regulation, RegulatoryRequirement
from forestai.core.domain.models.parcel import Parcel, ParcelProject
from forestai.core.utils.logging_config import LoggingConfig
from forestai.core.domain.services.regulatory_framework_service import RegulatoryFrameworkService
from forestai.core.domain.services.compliance_checker_service import ComplianceCheckerService

# Configuration du logger
logger = LoggingConfig.get_instance().get_logger(__name__)

class ReglementationAgent(BaseAgent):
    """
    Agent spécialisé dans l'analyse réglementaire forestière.
    
    Cet agent permet de:
    - Vérifier la conformité d'un projet forestier avec les réglementations
    - Identifier les autorisations nécessaires
    - Générer des rapports de conformité
    - Proposer des ajustements pour être en conformité
    """
    
    def __init__(self, config: Dict[str, Any], use_messaging: bool = True):
        """
        Initialise l'agent de réglementation forestière.
        
        Args:
            config: Dictionnaire de configuration pour l'agent
            use_messaging: Si True, utilise le système de messagerie pour communiquer avec les autres agents
        """
        super().__init__(config, "ReglementationAgent", use_messaging)
        
        # Chemins des données réglementaires
        self.data_path = os.path.join(config.get("data_path", "./data"), "reglementation")
        os.makedirs(self.data_path, exist_ok=True)
        
        # Initialiser les services
        self.regulatory_service = RegulatoryFrameworkService(self.data_path)
        self.compliance_service = ComplianceCheckerService(self.regulatory_service)
        
        # Charger les réglementations
        self.regulations = self.regulatory_service.get_all_regulations()
        
        logger.info(f"Agent de réglementation initialisé avec {len(self.regulations)} réglementations")
    
    def run(self):
        """Exécute l'agent de réglementation."""
        logger.info("Démarrage de l'agent de réglementation")
        
        # S'abonner aux messages pertinents si le message bus est disponible
        if self.message_bus:
            self.message_bus.subscribe("PROJECT_CREATED", self._handle_project_created)
            self.message_bus.subscribe("PARCEL_ANALYZED", self._handle_parcel_analyzed)
            self.message_bus.subscribe("COMPLIANCE_CHECK_REQUESTED", self._handle_compliance_check_requested)
        
        logger.info("Agent de réglementation prêt à recevoir des demandes")
    
    def _handle_project_created(self, message: Dict[str, Any]):
        """
        Gère les notifications de création de projet.
        
        Args:
            message: Message contenant les informations du projet
        """
        logger.info(f"Notification de création de projet reçue: {message.get('project_id')}")
        
        # Vérifier automatiquement la conformité du projet
        if 'parcels' in message and 'project_type' in message:
            self.check_compliance(
                parcels=message['parcels'],
                project_type=message['project_type'],
                params=message.get('parameters', {})
            )
    
    def _handle_parcel_analyzed(self, message: Dict[str, Any]):
        """
        Gère les notifications d'analyse de parcelles.
        
        Args:
            message: Message contenant les informations d'analyse
        """
        logger.debug(f"Notification d'analyse de parcelle reçue: {message.get('parcel_id')}")
        
        # Stocker les données de parcelle dans la mémoire partagée si disponible
        if self.agent_memory and 'parcel_id' in message and 'data' in message:
            self.agent_memory.store(f"parcel:{message['parcel_id']}", message['data'])
    
    def _handle_compliance_check_requested(self, message: Dict[str, Any]):
        """
        Gère les demandes de vérification de conformité.
        
        Args:
            message: Message contenant les paramètres de vérification
        """
        logger.info(f"Demande de vérification de conformité reçue: {message}")
        
        # Vérifier que les paramètres nécessaires sont présents
        if 'parcels' in message and 'project_type' in message:
            report = self.check_compliance(
                parcels=message['parcels'],
                project_type=message['project_type'],
                params=message.get('parameters', {})
            )
            
            # Répondre à la demande si un callback est fourni
            if 'callback_topic' in message and self.message_bus:
                self.message_bus.publish(message['callback_topic'], {
                    'request_id': message.get('request_id'),
                    'report': report
                })
    
    def check_compliance(self, parcels: List[str], project_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Vérifie la conformité réglementaire d'un projet sur des parcelles.
        
        Args:
            parcels: Liste des identifiants de parcelles
            project_type: Type de projet (boisement, reboisement, defrichement, etc.)
            params: Paramètres additionnels du projet
        
        Returns:
            Rapport de conformité réglementaire
        """
        logger.info(f"Vérification de conformité pour {len(parcels)} parcelles, projet de type {project_type}")
        
        if params is None:
            params = {}
        
        # Récupérer les données des parcelles via le GeoAgent si nécessaire
        parcel_data = self._get_parcel_data(parcels)
        
        # Créer un objet projet
        project = ParcelProject(
            id=f"PROJ-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",
            parcels=[Parcel(**p) for p in parcel_data],
            project_type=project_type,
            parameters=params
        )
        
        # Déléguer la vérification au service de conformité
        compliance_results = self.compliance_service.check_project_compliance(project)
        
        # Agréger les résultats
        compliant_count = sum(1 for r in compliance_results if r["compliant"])
        non_compliant_count = len(compliance_results) - compliant_count
        
        # Générer le rapport
        report = {
            "project_id": project.id,
            "project_type": project_type,
            "parcels": parcels,
            "timestamp": datetime.datetime.now().isoformat(),
            "overall_compliant": non_compliant_count == 0,
            "compliance_summary": {
                "total_regulations": len(compliance_results),
                "compliant": compliant_count,
                "non_compliant": non_compliant_count
            },
            "detailed_results": compliance_results,
            "recommendations": self.compliance_service.generate_recommendations(compliance_results)
        }
        
        logger.info(f"Rapport de conformité généré pour le projet {project.id}: {report['overall_compliant']}")
        
        # Publier le rapport via le message bus si disponible
        if self.message_bus:
            self.message_bus.publish("COMPLIANCE_REPORT_GENERATED", {
                "project_id": project.id,
                "compliant": report["overall_compliant"],
                "report_summary": report["compliance_summary"]
            })
        
        return report
    
    def _get_parcel_data(self, parcel_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Récupère les données des parcelles via le GeoAgent ou depuis le cache.
        
        Args:
            parcel_ids: Liste des identifiants de parcelles
        
        Returns:
            Liste des données de parcelles
        """
        parcel_data = []
        
        # Vérifier si les données sont dans la mémoire partagée
        if self.agent_memory:
            for parcel_id in parcel_ids:
                data = self.agent_memory.get(f"parcel:{parcel_id}")
                if data:
                    parcel_data.append(data)
        
        # Si toutes les données ne sont pas disponibles, interroger le GeoAgent
        if not self.agent_memory or len(parcel_data) < len(parcel_ids):
            if self.message_bus:
                # Envoyer une requête au GeoAgent
                response = self.message_bus.request("PARCEL_DATA_REQUEST", {
                    "parcel_ids": parcel_ids
                }, "GeoAgent")
                
                if response and "parcels" in response:
                    parcel_data = response["parcels"]
                else:
                    logger.warning(f"Pas de réponse du GeoAgent pour les parcelles {parcel_ids}")
                    # Créer des données de parcelle minimales pour ne pas bloquer l'analyse
                    parcel_data = [{"id": pid, "area": 0, "region": "unknown"} for pid in parcel_ids]
            else:
                logger.warning("Message bus non disponible, impossible de récupérer les données des parcelles")
                # Créer des données de parcelle minimales
                parcel_data = [{"id": pid, "area": 0, "region": "unknown"} for pid in parcel_ids]
        
        return parcel_data
    
    def get_required_authorizations(self, project_type: str, area: float, region: str = "*") -> List[Dict[str, Any]]:
        """
        Identifie les autorisations nécessaires pour un type de projet.
        
        Args:
            project_type: Type de projet
            area: Surface concernée en hectares
            region: Région administrative concernée
        
        Returns:
            Liste des autorisations nécessaires
        """
        # Simuler un projet minimal
        dummy_parcel = Parcel(id="DUMMY", area=area, region=region)
        project = ParcelProject(
            id="TEMP",
            parcels=[dummy_parcel],
            project_type=project_type
        )
        
        # Utiliser le service pour obtenir les autorisations
        return self.compliance_service.get_required_authorizations(project)
    
    def generate_compliance_report(self, compliance_results: Dict[str, Any], output_format: str = "json") -> str:
        """
        Génère un rapport de conformité formaté.
        
        Args:
            compliance_results: Résultats de l'analyse de conformité
            output_format: Format de sortie (json, txt, html)
        
        Returns:
            Rapport formaté
        """
        return self.compliance_service.generate_formatted_report(compliance_results, output_format)
    
    def check_parcels_water_protection(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """
        Vérifie si les parcelles sont situées dans des zones de protection des eaux.
        
        Args:
            parcel_ids: Liste des identifiants de parcelles
        
        Returns:
            Rapport sur les protections des eaux
        """
        logger.info(f"Vérification des protections des eaux pour {len(parcel_ids)} parcelles")
        
        # Récupérer les données des parcelles
        parcel_data = self._get_parcel_data(parcel_ids)
        
        # Créer des objets Parcel
        parcels = [Parcel(**p) for p in parcel_data]
        
        # Utiliser le service pour vérifier les protections des eaux
        return self.compliance_service.check_water_protection(parcels)
    
    def search_regulation(self, query: str) -> List[Dict[str, Any]]:
        """
        Recherche des réglementations par mot-clé.
        
        Args:
            query: Terme de recherche
        
        Returns:
            Liste des réglementations correspondantes
        """
        logger.info(f"Recherche de réglementations pour: {query}")
        
        # Déléguer la recherche au service
        regulations = self.regulatory_service.search_regulations(query)
        
        # Convertir les objets en dictionnaires pour plus de facilité d'utilisation
        return [
            {
                "id": reg.id,
                "name": reg.name,
                "description": reg.description,
                "reference_text": reg.reference_text,
                "authority": reg.authority,
                "project_types": reg.project_types,
                "effective_date": reg.effective_date.isoformat(),
                "requirement_count": len(reg.requirements)
            }
            for reg in regulations
        ]
    
    def get_regulation_details(self, regulation_id: str) -> Dict[str, Any]:
        """
        Récupère les détails complets d'une réglementation.
        
        Args:
            regulation_id: Identifiant de la réglementation
        
        Returns:
            Détails de la réglementation
        """
        logger.info(f"Récupération des détails de la réglementation: {regulation_id}")
        
        try:
            # Récupérer la réglementation via le service
            regulation = self.regulatory_service.get_regulation_by_id(regulation_id)
            
            if not regulation:
                return {"error": f"Réglementation non trouvée: {regulation_id}"}
            
            # Convertir les exigences en dictionnaires
            requirements = [
                {
                    "id": req.id,
                    "description": req.description,
                    "condition": req.condition,
                    "threshold": req.threshold,
                    "category": req.category,
                    "reference": req.reference,
                    "severity": req.severity
                }
                for req in regulation.requirements
            ]
            
            # Retourner les détails complets
            return {
                "id": regulation.id,
                "name": regulation.name,
                "description": regulation.description,
                "reference_text": regulation.reference_text,
                "authority": regulation.authority,
                "project_types": regulation.project_types,
                "applicable_regions": regulation.applicable_regions,
                "effective_date": regulation.effective_date.isoformat(),
                "requirements": requirements
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails de la réglementation: {e}")
            return {"error": str(e)}
