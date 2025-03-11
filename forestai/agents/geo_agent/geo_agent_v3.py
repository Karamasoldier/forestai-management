# forestai/agents/geo_agent/geo_agent_v3.py

import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon

from forestai.agents.base_agent import BaseAgent
from forestai.agents.geo_agent.cadastre import CadastreHandler
from forestai.agents.geo_agent.parcel_analyzer import ParcelAnalyzer
from forestai.core.domain.models.parcel import Parcel, ParcelAnalysisResult
from forestai.core.domain.services.forest_potential_service import ForestPotentialService
from forestai.core.infrastructure.messaging.message_bus import MessageBus
from forestai.core.infrastructure.memory.agent_memory import AgentMemory
from forestai.core.utils.logging_config import setup_agent_logging, log_function, LoggingMetrics

class GeoAgentV3(BaseAgent):
    """
    Version 3 du GeoAgent avec intégration complète de l'infrastructure de logging.
    
    Cette version améliore le GeoAgentV2 en ajoutant:
    - Intégration avec l'infrastructure de logging avancée
    - Métriques de performance et d'utilisation
    - Journalisation détaillée des opérations
    - Gestion standardisée des exceptions
    - Traçabilité des appels API
    """
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        memory: Optional[AgentMemory] = None,
        message_bus: Optional[MessageBus] = None,
        log_level: str = "INFO"
    ):
        """
        Initialise le GeoAgent v3.
        
        Args:
            data_dir: Répertoire des données géospatiales
            memory: Instance d'AgentMemory pour le stockage contextuel
            message_bus: Instance de MessageBus pour la communication inter-agents
            log_level: Niveau de log pour cet agent
        """
        super().__init__(name="GeoAgent", memory=memory, message_bus=message_bus)
        
        # Configuration du logger
        self.logger = setup_agent_logging(
            agent_name="GeoAgent", 
            level=log_level,
            context={"version": "3.0", "data_dir": data_dir}
        )
        
        # Accès aux métriques
        self.metrics = LoggingMetrics.get_instance()
        
        # Configurer le répertoire de données
        if data_dir is None:
            data_dir = os.getenv("GEODATA_DIR", "data/raw")
        self.data_dir = Path(data_dir)
        
        self.logger.info(f"Initialisation du GeoAgent avec répertoire de données: {self.data_dir}")
        
        # Initialiser les composants
        try:
            start_time = time.time()
            self.cadastre_handler = CadastreHandler(data_dir=self.data_dir)
            self.parcel_analyzer = ParcelAnalyzer(data_dir=self.data_dir)
            self.forest_potential_service = ForestPotentialService()
            
            # Log le temps d'initialisation
            init_time = time.time() - start_time
            self.logger.info(f"Initialisation des composants terminée en {init_time:.2f}s")
            
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'initialisation des composants: {str(e)}")
            raise
        
        # Déclarer les actions disponibles
        self.available_actions = {
            "search_parcels": self.search_parcels,
            "get_parcel_info": self.get_parcel_info,
            "analyze_parcel": self.analyze_parcel,
            "find_forest_parcels": self.find_forest_parcels,
            "calculate_potential": self.calculate_forest_potential
        }
        
        self.logger.info("GeoAgent initialisé et prêt")
    
    @log_function(level="DEBUG")
    def search_parcels(self, commune: str, section: Optional[str] = None, 
                      numero: Optional[str] = None) -> Dict[str, Any]:
        """
        Recherche des parcelles cadastrales par commune, section et numéro.
        
        Args:
            commune: Nom de la commune
            section: Code de section cadastrale (optionnel)
            numero: Numéro de parcelle (optionnel)
            
        Returns:
            Dictionnaire contenant les résultats de recherche
        """
        task_id = str(uuid.uuid4())
        
        # Log le début de la tâche
        self.logger.log_task(
            task_id=task_id,
            task_type="search_parcels",
            agent_name="GeoAgent",
            status="started",
            details={"commune": commune, "section": section, "numero": numero}
        )
        
        try:
            start_time = time.time()
            
            # Appel API cadastre (loggé par le décorateur)
            results = self.cadastre_handler.search_parcels(
                commune=commune, 
                section=section, 
                numero=numero
            )
            
            # Log l'appel à l'API
            self.logger.log_api_call(
                api_name="Cadastre", 
                endpoint="search_parcels",
                params={"commune": commune, "section": section, "numero": numero},
                success=True,
                response_time=time.time() - start_time
            )
            
            # Enregistrer l'opération dans les métriques
            self.metrics.increment("cadastre_searches")
            self.metrics.record_api_call(success=True, response_time=time.time() - start_time)
            
            # Log le résultat
            parcels_count = len(results.get("parcels", []))
            self.logger.info(f"Recherche terminée: {parcels_count} parcelles trouvées")
            
            # Sauvegarder les résultats dans la mémoire de l'agent
            if self.memory:
                self.memory.store(
                    key=f"search_result:{commune}:{section or '*'}:{numero or '*'}",
                    value=results,
                    ttl=3600  # Expire après 1 heure
                )
            
            # Log la fin de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="search_parcels",
                agent_name="GeoAgent",
                status="completed",
                details={"count": parcels_count, "execution_time": time.time() - start_time}
            )
            
            # Publier un événement sur le bus de messages
            if self.message_bus:
                self.message_bus.publish(
                    topic="PARCELS_FOUND",
                    message={
                        "task_id": task_id,
                        "commune": commune,
                        "count": parcels_count,
                        "timestamp": time.time()
                    }
                )
            
            return {
                "success": True,
                "task_id": task_id,
                "count": parcels_count,
                "results": results
            }
            
        except Exception as e:
            # Log l'erreur
            self.logger.exception(f"Erreur lors de la recherche de parcelles: {str(e)}")
            
            # Log l'échec de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="search_parcels",
                agent_name="GeoAgent",
                status="failed",
                details={"error": str(e)}
            )
            
            # Enregistrer l'erreur dans les métriques
            self.metrics.increment("errors")
            self.metrics.record_api_call(success=False)
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    @log_function(level="DEBUG")
    def get_parcel_info(self, parcel_id: str) -> Dict[str, Any]:
        """
        Récupère les informations détaillées d'une parcelle par son identifiant.
        
        Args:
            parcel_id: Identifiant unique de la parcelle
            
        Returns:
            Dictionnaire contenant les informations de la parcelle
        """
        task_id = str(uuid.uuid4())
        
        # Log le début de la tâche
        self.logger.log_task(
            task_id=task_id,
            task_type="get_parcel_info",
            agent_name="GeoAgent",
            status="started",
            details={"parcel_id": parcel_id}
        )
        
        try:
            start_time = time.time()
            
            # Essayer d'abord de récupérer depuis la mémoire
            if self.memory:
                cached_info = self.memory.retrieve(f"parcel:{parcel_id}")
                if cached_info:
                    self.logger.info(f"Informations de parcelle {parcel_id} récupérées depuis le cache")
                    
                    # Log la fin de la tâche (depuis cache)
                    self.logger.log_task(
                        task_id=task_id,
                        task_type="get_parcel_info",
                        agent_name="GeoAgent",
                        status="completed",
                        details={"from_cache": True}
                    )
                    
                    return {
                        "success": True,
                        "task_id": task_id,
                        "from_cache": True,
                        "parcel": cached_info
                    }
            
            # Récupérer les informations de la parcelle
            parcel_info = self.cadastre_handler.get_parcel_by_id(parcel_id)
            
            # Log l'appel à l'API
            self.logger.log_api_call(
                api_name="Cadastre", 
                endpoint="get_parcel_by_id",
                params={"parcel_id": parcel_id},
                success=True,
                response_time=time.time() - start_time
            )
            
            # Sauvegarder dans la mémoire
            if self.memory and parcel_info:
                self.memory.store(
                    key=f"parcel:{parcel_id}",
                    value=parcel_info,
                    ttl=86400  # Expire après 24 heures
                )
            
            # Log la fin de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="get_parcel_info",
                agent_name="GeoAgent",
                status="completed",
                details={"found": parcel_info is not None}
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "parcel": parcel_info
            }
            
        except Exception as e:
            # Log l'erreur
            self.logger.exception(f"Erreur lors de la récupération des informations de parcelle: {str(e)}")
            
            # Log l'échec de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="get_parcel_info",
                agent_name="GeoAgent",
                status="failed",
                details={"error": str(e)}
            )
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    @log_function(level="INFO")
    def analyze_parcel(self, parcel_id: str) -> Dict[str, Any]:
        """
        Analyse complète d'une parcelle avec calcul de potentiel forestier.
        
        Args:
            parcel_id: Identifiant unique de la parcelle
            
        Returns:
            Résultats d'analyse de la parcelle
        """
        task_id = str(uuid.uuid4())
        
        # Log le début de la tâche
        self.logger.log_task(
            task_id=task_id,
            task_type="analyze_parcel",
            agent_name="GeoAgent",
            status="started",
            details={"parcel_id": parcel_id}
        )
        
        try:
            start_time = time.time()
            
            # Récupérer les informations de la parcelle
            parcel_info = self.get_parcel_info(parcel_id)
            if not parcel_info.get("success", False):
                raise ValueError(f"Impossible de récupérer les informations de la parcelle {parcel_id}")
            
            parcel_data = parcel_info.get("parcel")
            if not parcel_data:
                raise ValueError(f"Parcelle {parcel_id} non trouvée")
            
            # Créer un objet Parcel
            parcel = Parcel(
                id=parcel_id,
                commune=parcel_data.get("commune", ""),
                section=parcel_data.get("section", ""),
                numero=parcel_data.get("numero", ""),
                surface=parcel_data.get("surface", 0),
                geometry=parcel_data.get("geometry")
            )
            
            # Analyser la parcelle
            analysis_result = self.parcel_analyzer.analyze(parcel)
            
            # Log l'analyse
            self.logger.info(f"Analyse de la parcelle {parcel_id} terminée en {time.time() - start_time:.2f}s")
            
            # Calculer le potentiel forestier
            potential_result = self.forest_potential_service.calculate_potential(
                parcel=parcel,
                analysis_result=analysis_result
            )
            
            # Sauvegarder les résultats dans la mémoire
            if self.memory:
                self.memory.store(
                    key=f"analysis:{parcel_id}",
                    value={
                        "parcel": parcel_data,
                        "analysis": analysis_result.to_dict(),
                        "potential": potential_result.to_dict()
                    },
                    ttl=86400  # Expire après 24 heures
                )
            
            # Résultats finaux
            result = {
                "success": True,
                "task_id": task_id,
                "parcel_id": parcel_id,
                "analysis": analysis_result.to_dict(),
                "potential": potential_result.to_dict(),
                "execution_time": time.time() - start_time
            }
            
            # Log la fin de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="analyze_parcel",
                agent_name="GeoAgent",
                status="completed",
                details={"potential_score": potential_result.score}
            )
            
            # Publier un événement sur le bus de messages
            if self.message_bus:
                self.message_bus.publish(
                    topic="PARCEL_ANALYZED",
                    message={
                        "task_id": task_id,
                        "parcel_id": parcel_id,
                        "potential_score": potential_result.score,
                        "timestamp": time.time()
                    }
                )
            
            return result
            
        except Exception as e:
            # Log l'erreur
            self.logger.exception(f"Erreur lors de l'analyse de la parcelle {parcel_id}: {str(e)}")
            
            # Log l'échec de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="analyze_parcel",
                agent_name="GeoAgent",
                status="failed",
                details={"error": str(e)}
            )
            
            # Incrémenter le compteur d'erreurs
            self.metrics.increment("errors")
            
            return {
                "success": False,
                "task_id": task_id,
                "parcel_id": parcel_id,
                "error": str(e)
            }
    
    @log_function(level="INFO")
    def find_forest_parcels(self, commune: str, min_size: float = 5000, 
                           min_potential: float = 0.6) -> Dict[str, Any]:
        """
        Trouve les parcelles à potentiel forestier dans une commune.
        
        Args:
            commune: Nom de la commune
            min_size: Surface minimale en m² (par défaut 5000 m²)
            min_potential: Score potentiel forestier minimum (0-1)
            
        Returns:
            Liste des parcelles à potentiel forestier
        """
        task_id = str(uuid.uuid4())
        
        # Log le début de la tâche
        self.logger.log_task(
            task_id=task_id,
            task_type="find_forest_parcels",
            agent_name="GeoAgent",
            status="started",
            details={"commune": commune, "min_size": min_size, "min_potential": min_potential}
        )
        
        try:
            start_time = time.time()
            
            # Rechercher toutes les parcelles de la commune
            search_results = self.search_parcels(commune=commune)
            if not search_results.get("success", False):
                raise ValueError(f"Erreur lors de la recherche des parcelles pour {commune}")
            
            parcels = search_results.get("results", {}).get("parcels", [])
            
            self.logger.info(f"Analyse de {len(parcels)} parcelles dans {commune} pour potentiel forestier")
            
            # Filtrer par taille
            filtered_parcels = [p for p in parcels if p.get("surface", 0) >= min_size]
            self.logger.info(f"{len(filtered_parcels)} parcelles de taille suffisante")
            
            # Analyser chaque parcelle pour son potentiel
            forest_parcels = []
            
            for i, parcel in enumerate(filtered_parcels[:50]):  # Limiter à 50 pour l'exemple
                parcel_id = parcel.get("id")
                try:
                    # Log l'avancement
                    if i % 10 == 0:
                        self.logger.info(f"Progression: {i}/{len(filtered_parcels)} parcelles analysées")
                    
                    # Analyser la parcelle
                    analysis = self.analyze_parcel(parcel_id)
                    
                    # Vérifier le potentiel
                    if (analysis.get("success", False) and 
                        analysis.get("potential", {}).get("score", 0) >= min_potential):
                        forest_parcels.append({
                            "parcel_id": parcel_id,
                            "commune": parcel.get("commune"),
                            "surface": parcel.get("surface"),
                            "potential_score": analysis.get("potential", {}).get("score", 0),
                            "recommended_species": analysis.get("potential", {}).get("recommended_species", [])
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Erreur lors de l'analyse de la parcelle {parcel_id}: {str(e)}")
                    continue
            
            # Log les résultats
            self.logger.info(f"Recherche terminée: {len(forest_parcels)} parcelles à potentiel forestier trouvées")
            
            # Log la fin de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="find_forest_parcels",
                agent_name="GeoAgent",
                status="completed",
                details={
                    "count": len(forest_parcels),
                    "execution_time": time.time() - start_time
                }
            )
            
            # Enregistrer les résultats dans la mémoire
            if self.memory:
                self.memory.store(
                    key=f"forest_parcels:{commune}",
                    value=forest_parcels,
                    ttl=86400 * 7  # Expire après 7 jours
                )
            
            # Publier un événement sur le bus de messages
            if self.message_bus:
                self.message_bus.publish(
                    topic="FOREST_PARCELS_FOUND",
                    message={
                        "task_id": task_id,
                        "commune": commune,
                        "count": len(forest_parcels),
                        "timestamp": time.time()
                    }
                )
            
            return {
                "success": True,
                "task_id": task_id,
                "count": len(forest_parcels),
                "parcels": forest_parcels,
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            # Log l'erreur
            self.logger.exception(f"Erreur lors de la recherche de parcelles forestières: {str(e)}")
            
            # Log l'échec de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="find_forest_parcels",
                agent_name="GeoAgent",
                status="failed",
                details={"error": str(e)}
            )
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    @log_function(level="INFO")
    def calculate_forest_potential(self, parcel_id: str) -> Dict[str, Any]:
        """
        Calcule uniquement le potentiel forestier d'une parcelle.
        
        Args:
            parcel_id: Identifiant unique de la parcelle
            
        Returns:
            Score de potentiel forestier et recommandations
        """
        task_id = str(uuid.uuid4())
        
        # Log le début de la tâche
        self.logger.log_task(
            task_id=task_id,
            task_type="calculate_forest_potential",
            agent_name="GeoAgent",
            status="started",
            details={"parcel_id": parcel_id}
        )
        
        try:
            start_time = time.time()
            
            # Vérifier si une analyse existe déjà dans la mémoire
            if self.memory:
                cached_analysis = self.memory.retrieve(f"analysis:{parcel_id}")
                if cached_analysis:
                    self.logger.info(f"Analyse existante trouvée pour la parcelle {parcel_id}")
                    
                    # Log la fin de la tâche (depuis cache)
                    self.logger.log_task(
                        task_id=task_id,
                        task_type="calculate_forest_potential",
                        agent_name="GeoAgent",
                        status="completed",
                        details={"from_cache": True}
                    )
                    
                    return {
                        "success": True,
                        "task_id": task_id,
                        "from_cache": True,
                        "potential": cached_analysis.get("potential", {})
                    }
            
            # Sinon, effectuer une analyse complète
            analysis_result = self.analyze_parcel(parcel_id)
            if not analysis_result.get("success", False):
                raise ValueError(f"Erreur lors de l'analyse de la parcelle {parcel_id}")
            
            # Log les résultats
            potential_data = analysis_result.get("potential", {})
            self.logger.info(
                f"Potentiel forestier calculé pour {parcel_id}: " +
                f"score={potential_data.get('score', 0):.2f}, " +
                f"espèces={potential_data.get('recommended_species', [])}"
            )
            
            # Log la fin de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="calculate_forest_potential",
                agent_name="GeoAgent",
                status="completed",
                details={"potential_score": potential_data.get("score", 0)}
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "potential": potential_data,
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            # Log l'erreur
            self.logger.exception(f"Erreur lors du calcul du potentiel forestier: {str(e)}")
            
            # Log l'échec de la tâche
            self.logger.log_task(
                task_id=task_id,
                task_type="calculate_forest_potential",
                agent_name="GeoAgent",
                status="failed",
                details={"error": str(e)}
            )
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques actuelles de l'agent.
        
        Returns:
            Dictionnaire des métriques collectées
        """
        agent_metrics = self.metrics.get_metrics()
        
        # Ajouter des métriques spécifiques à l'agent si nécessaire
        agent_metrics["agent_name"] = "GeoAgent"
        agent_metrics["agent_version"] = "3.0"
        
        return agent_metrics
    
    def log_performance(self) -> None:
        """
        Journalise les métriques de performance actuelles.
        """
        self.logger.info("Logging des métriques de performance du GeoAgent")
        self.metrics.log_current_metrics()
    
    def reset_metrics(self) -> None:
        """
        Réinitialise les métriques collectées.
        """
        self.logger.info("Réinitialisation des métriques du GeoAgent")
        self.metrics.reset()
