"""
Nouvelle implémentation du GeoAgent utilisant l'architecture en couches.

Cette implémentation s'appuie sur les services de domaine, les repositories
et le message bus pour une meilleure séparation des responsabilités.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import json
import time

from ...agents.base_agent import BaseAgent
from ...core.domain.services.forest_potential_service import ForestPotentialService
from ...core.infrastructure.repositories.interfaces import ParcelRepository
from ...core.infrastructure.repositories.geopandas_parcel_repository import create_geopandas_parcel_repository
from ...core.infrastructure.messaging.message_bus import get_message_bus, Message, MessagePriority
from ...core.infrastructure.memory.agent_memory import get_agent_memory
from ...core.domain.models.parcel import Parcel, ParcelIdentifier, TerrainCharacteristics


class GeoAgentV2(BaseAgent):
    """
    Agent de géotraitement basé sur l'architecture en couches.
    
    Cette nouvelle version utilise:
    - Les services de domaine pour la logique métier
    - Les repositories pour l'accès aux données
    - Le message bus pour la communication
    - La mémoire partagée pour le contexte
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'agent de géotraitement.
        
        Args:
            config: Configuration de l'agent
        """
        super().__init__(name="GeoAgent", config=config)
        
        # Configuration
        self.data_path = config.get("data_path", "./data")
        
        # Initialiser les repositories
        self.parcel_repository = create_geopandas_parcel_repository(config)
        
        # Initialiser les services de domaine
        self.forest_potential_service = ForestPotentialService()
        
        # Accès au message bus et à la mémoire partagée
        self.message_bus = get_message_bus()
        self.memory = get_agent_memory()
        
        # S'abonner aux topics pertinents
        self._subscribe_to_topics()
    
    def _subscribe_to_topics(self):
        """S'abonne aux topics du message bus pertinents pour l'agent."""
        self.message_bus.subscribe("parcel.analyze_request", self._handle_analyze_request)
        self.message_bus.subscribe("parcel.search_request", self._handle_search_request)
        self.message_bus.subscribe("parcel.clustering_request", self._handle_clustering_request)
        
        self.logger.info("GeoAgent subscribed to relevant topics")
    
    def _execute(self):
        """
        Implémentation de la méthode d'exécution de l'agent.
        """
        self.logger.info("Démarrage de l'agent GeoAgent (v2)")
        
        # Démarrer le message bus s'il n'est pas déjà en cours d'exécution
        if not self.message_bus.is_running:
            self.message_bus.start()
        
        # Traiter les tâches en attente
        while self.is_running:
            if self.tasks_queue:
                task = self.tasks_queue.pop(0)
                
                try:
                    task_type = task.get("type")
                    
                    if task_type == "find_parcels":
                        self._process_find_parcels_task(task)
                    elif task_type == "analyze_potential":
                        self._process_analyze_potential_task(task)
                    elif task_type == "analyze_clustering":
                        self._process_analyze_clustering_task(task)
                    else:
                        self.logger.warning(f"Type de tâche inconnu: {task_type}")
                
                except Exception as e:
                    self.logger.error(f"Erreur lors du traitement de la tâche: {str(e)}", exc_info=True)
            
            # Courte pause pour éviter de surcharger le CPU
            time.sleep(0.1)
    
    def _process_find_parcels_task(self, task: Dict[str, Any]):
        """
        Traite une tâche de recherche de parcelles.
        
        Args:
            task: Tâche à traiter
        """
        self.logger.info(f"Traitement de la tâche de recherche de parcelles")
        
        department = task.get("department")
        min_area = task.get("min_area", 1.0)
        
        if not department:
            self.logger.error("Département non spécifié dans la tâche")
            return
        
        # Rechercher les parcelles
        parcels = self.parcel_repository.find_by_department(department, min_area)
        
        # Enregistrer les résultats
        output_path = os.path.join(
            self.config["output_path"], 
            f"parcels_{department}.json"
        )
        
        # Créer une représentation sérialisable
        serializable_parcels = []
        for parcel in parcels:
            serializable_parcels.append({
                "id": parcel.id,
                "identifier": parcel.identifier.to_string(),
                "area_ha": parcel.geometry.area_ha,
                "current_land_use": parcel.current_land_use,
                "forest_potential_score": parcel.forest_potential.score if parcel.forest_potential else None
            })
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(serializable_parcels, f, indent=2)
        
        self.logger.info(f"Résultats enregistrés dans {output_path}")
        
        # Publier les résultats
        self.message_bus.create_and_publish(
            topic="parcel.search_results",
            payload={
                "department": department,
                "min_area": min_area,
                "count": len(parcels),
                "output_path": output_path
            },
            sender="GeoAgent"
        )
    
    def _process_analyze_potential_task(self, task: Dict[str, Any]):
        """
        Traite une tâche d'analyse de potentiel forestier.
        
        Args:
            task: Tâche à traiter
        """
        self.logger.info(f"Traitement de la tâche d'analyse de potentiel forestier")
        
        parcel_ids = task.get("parcel_ids", [])
        
        if not parcel_ids:
            self.logger.error("Aucun identifiant de parcelle spécifié dans la tâche")
            return
        
        # Récupérer les parcelles
        parcels = []
        for parcel_id in parcel_ids:
            parcel = self.parcel_repository.get_by_id(parcel_id)
            if parcel:
                parcels.append(parcel)
        
        if not parcels:
            self.logger.warning("Aucune parcelle trouvée avec les identifiants spécifiés")
            return
        
        # Analyser chaque parcelle
        analyzed_parcels = []
        for parcel in parcels:
            # Analyser le potentiel forestier
            forest_potential = self.forest_potential_service.analyze_parcel_potential(parcel)
            
            # Mettre à jour la parcelle
            parcel.update_forest_potential(forest_potential)
            
            # Sauvegarder la parcelle mise à jour
            self.parcel_repository.save(parcel)
            
            analyzed_parcels.append(parcel)
        
        # Enregistrer les résultats
        output_path = os.path.join(
            self.config["output_path"], 
            f"potential_analysis_{int(time.time())}.json"
        )
        
        # Créer une représentation sérialisable
        serializable_results = []
        for parcel in analyzed_parcels:
            serializable_results.append({
                "id": parcel.id,
                "identifier": parcel.identifier.to_string(),
                "area_ha": parcel.geometry.area_ha,
                "forest_potential_score": parcel.forest_potential.score,
                "suitable_species": parcel.forest_potential.suitable_species,
                "limitations": parcel.forest_potential.limitations,
                "opportunities": parcel.forest_potential.opportunities,
                "carbon_potential": parcel.forest_potential.carbon_potential,
                "timber_potential": parcel.forest_potential.timber_potential
            })
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        self.logger.info(f"Résultats d'analyse enregistrés dans {output_path}")
        
        # Publier les résultats
        self.message_bus.create_and_publish(
            topic="parcel.potential_analysis_results",
            payload={
                "parcel_count": len(analyzed_parcels),
                "output_path": output_path
            },
            sender="GeoAgent"
        )
    
    def _process_analyze_clustering_task(self, task: Dict[str, Any]):
        """
        Traite une tâche d'analyse de regroupement de parcelles.
        
        Args:
            task: Tâche à traiter
        """
        self.logger.info(f"Traitement de la tâche d'analyse de regroupement")
        
        parcel_ids = task.get("parcel_ids", [])
        max_distance = task.get("max_distance", 100.0)
        min_cluster_size = task.get("min_cluster_size", 3)
        
        if not parcel_ids:
            self.logger.error("Aucun identifiant de parcelle spécifié dans la tâche")
            return
        
        # Récupérer les parcelles
        parcels = []
        for parcel_id in parcel_ids:
            parcel = self.parcel_repository.get_by_id(parcel_id)
            if parcel:
                parcels.append(parcel)
        
        if len(parcels) < 2:
            self.logger.warning("Pas assez de parcelles pour une analyse de regroupement")
            return
        
        # Analyse de regroupement
        clusters = self._analyze_parcel_clustering(parcels, max_distance, min_cluster_size)
        
        # Enregistrer les résultats
        output_path = os.path.join(
            self.config["output_path"], 
            f"clustering_analysis_{int(time.time())}.json"
        )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(clusters, f, indent=2)
        
        self.logger.info(f"Résultats de clustering enregistrés dans {output_path}")
        
        # Publier les résultats
        self.message_bus.create_and_publish(
            topic="parcel.clustering_results",
            payload={
                "cluster_count": len(clusters["clusters"]),
                "parcel_count": clusters["metrics"]["total_parcels"],
                "output_path": output_path
            },
            sender="GeoAgent"
        )
    
    def _analyze_parcel_clustering(self, parcels: List[Parcel], max_distance: float, min_cluster_size: int) -> Dict[str, Any]:
        """
        Analyse les possibilités de regroupement des parcelles.
        
        Args:
            parcels: Liste des parcelles à analyser
            max_distance: Distance maximale (m) entre parcelles pour former un groupe
            min_cluster_size: Taille minimale d'un groupe
            
        Returns:
            Dictionnaire avec les clusters et métriques
        """
        # Simulation - Dans une implémentation réelle, cette méthode utiliserait
        # un service de domaine pour effectuer l'analyse de regroupement
        
        # Exemple de résultat
        clusters = [{
            "id": 1,
            "parcel_ids": [p.id for p in parcels[:min(len(parcels), min_cluster_size)]],
            "area_ha": sum(p.geometry.area_ha for p in parcels[:min(len(parcels), min_cluster_size)]),
            "owner_count": len(set(p.owner.id for p in parcels[:min(len(parcels), min_cluster_size)] if p.owner)),
            "centroid": {
                "x": sum(p.geometry.centroid_x for p in parcels[:min(len(parcels), min_cluster_size)]) / min(len(parcels), min_cluster_size),
                "y": sum(p.geometry.centroid_y for p in parcels[:min(len(parcels), min_cluster_size)]) / min(len(parcels), min_cluster_size)
            },
            "analysis": "Ce groupe de parcelles présente un bon potentiel de regroupement forestier."
        }]
        
        return {
            "clusters": clusters,
            "metrics": {
                "cluster_count": len(clusters),
                "total_parcels": len(parcels),
                "total_area_ha": sum(p.geometry.area_ha for p in parcels)
            }
        }
    
    def _handle_analyze_request(self, message: Message):
        """
        Gestionnaire pour les messages de demande d'analyse de parcelles.
        
        Args:
            message: Message reçu
        """
        self.logger.info(f"Reçu message 'parcel.analyze_request': {message.message_id}")
        
        payload = message.payload
        if not payload or "parcel_ids" not in payload:
            self.logger.warning("Message 'parcel.analyze_request' invalide: manque parcel_ids")
            return
        
        # Créer une tâche pour l'analyse
        task = {
            "type": "analyze_potential",
            "parcel_ids": payload["parcel_ids"],
            "correlation_id": message.message_id
        }
        
        # Ajouter la tâche à la file d'attente
        self.add_task(task)
    
    def _handle_search_request(self, message: Message):
        """
        Gestionnaire pour les messages de demande de recherche de parcelles.
        
        Args:
            message: Message reçu
        """
        self.logger.info(f"Reçu message 'parcel.search_request': {message.message_id}")
        
        payload = message.payload
        if not payload or "department" not in payload:
            self.logger.warning("Message 'parcel.search_request' invalide: manque department")
            return
        
        # Créer une tâche pour la recherche
        task = {
            "type": "find_parcels",
            "department": payload["department"],
            "min_area": payload.get("min_area", 1.0),
            "correlation_id": message.message_id
        }
        
        # Ajouter la tâche à la file d'attente
        self.add_task(task)
    
    def _handle_clustering_request(self, message: Message):
        """
        Gestionnaire pour les messages de demande d'analyse de regroupement.
        
        Args:
            message: Message reçu
        """
        self.logger.info(f"Reçu message 'parcel.clustering_request': {message.message_id}")
        
        payload = message.payload
        if not payload or "parcel_ids" not in payload:
            self.logger.warning("Message 'parcel.clustering_request' invalide: manque parcel_ids")
            return
        
        # Créer une tâche pour l'analyse de regroupement
        task = {
            "type": "analyze_clustering",
            "parcel_ids": payload["parcel_ids"],
            "max_distance": payload.get("max_distance", 100.0),
            "min_cluster_size": payload.get("min_cluster_size", 3),
            "correlation_id": message.message_id
        }
        
        # Ajouter la tâche à la file d'attente
        self.add_task(task)
    
    # Méthodes d'API publique pour une utilisation directe (sans message bus)
    
    def find_profitable_parcels(self, department_code: str, min_area: float = 1.0) -> List[Dict[str, Any]]:
        """
        Recherche les parcelles à potentiel forestier dans un département.
        
        Args:
            department_code: Code du département
            min_area: Surface minimale en hectares
            
        Returns:
            Liste des parcelles avec leur potentiel forestier
        """
        # Créer une tâche
        task = {
            "type": "find_parcels",
            "department": department_code,
            "min_area": min_area
        }
        
        # Ajouter la tâche à la file d'attente
        self.add_task(task)
        
        # Stocker l'identifiant de tâche dans la mémoire
        task_id = f"find_parcels_{department_code}_{time.time()}"
        self.memory.store(task_id, {"status": "pending", "department": department_code})
        
        # Retourner une représentation pour le suivi
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"Tâche de recherche soumise pour le département {department_code}"
        }
    
    def analyze_parcel_potential(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """
        Analyse le potentiel forestier des parcelles spécifiées.
        
        Args:
            parcel_ids: Liste des identifiants de parcelles
            
        Returns:
            Informations sur la tâche soumise
        """
        # Créer une tâche
        task = {
            "type": "analyze_potential",
            "parcel_ids": parcel_ids
        }
        
        # Ajouter la tâche à la file d'attente
        self.add_task(task)
        
        # Stocker l'identifiant de tâche dans la mémoire
        task_id = f"analyze_potential_{time.time()}"
        self.memory.store(task_id, {"status": "pending", "parcel_count": len(parcel_ids)})
        
        # Retourner une représentation pour le suivi
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"Tâche d'analyse soumise pour {len(parcel_ids)} parcelles"
        }
    
    def analyze_small_parcels_clustering(self, parcel_ids: List[str], max_distance: float = 100.0) -> Dict[str, Any]:
        """
        Analyse les possibilités de regroupement des parcelles spécifiées.
        
        Args:
            parcel_ids: Liste des identifiants de parcelles
            max_distance: Distance maximale entre parcelles pour former un groupe
            
        Returns:
            Informations sur la tâche soumise
        """
        # Créer une tâche
        task = {
            "type": "analyze_clustering",
            "parcel_ids": parcel_ids,
            "max_distance": max_distance
        }
        
        # Ajouter la tâche à la file d'attente
        self.add_task(task)
        
        # Stocker l'identifiant de tâche dans la mémoire
        task_id = f"analyze_clustering_{time.time()}"
        self.memory.store(task_id, {"status": "pending", "parcel_count": len(parcel_ids)})
        
        # Retourner une représentation pour le suivi
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"Tâche de clustering soumise pour {len(parcel_ids)} parcelles"
        }
