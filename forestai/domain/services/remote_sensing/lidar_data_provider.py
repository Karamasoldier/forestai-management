#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module de gestion des données LIDAR pour la télédétection.

Ce module fournit les fonctionnalités pour récupérer, traiter et analyser
les données LIDAR (nuages de points) pour la gestion forestière.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import geopandas as gpd
from shapely.geometry import shape

from forestai.core.utils.logging_utils import get_logger
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

from forestai.domain.services.remote_sensing.models import (
    RemoteSensingSource, 
    LidarPointCloudMetadata,
    RemoteSensingData,
    ForestMetrics
)
from forestai.domain.services.remote_sensing.remote_data_connector import RemoteDataConnector
from forestai.domain.services.remote_sensing.processors.lidar_processor import LidarProcessor
from forestai.domain.services.remote_sensing.lidar_metrics_extractor import LidarMetricsExtractor
from forestai.domain.services.remote_sensing.lidar_temporal_analyzer import LidarTemporalAnalyzer

logger = get_logger(__name__)


class LidarDataProvider:
    """
    Fournisseur de données LIDAR pour ForestAI.
    
    Cette classe gère l'acquisition, le stockage et le prétraitement 
    des données LIDAR pour l'analyse forestière.
    """
    
    def __init__(self, data_dir: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le fournisseur de données LIDAR.
        
        Args:
            data_dir: Répertoire pour stocker les données téléchargées (par défaut: ./data/lidar)
            config: Configuration supplémentaire
        """
        self.data_dir = data_dir or Path("./data/lidar")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or {}
        self.connector = RemoteDataConnector()
        self.connector.initialize(self.config.get("api_config"))
        
        # Initialiser les composants
        self.lidar_processor = LidarProcessor()
        self.metrics_extractor = LidarMetricsExtractor()
        self.temporal_analyzer = LidarTemporalAnalyzer()
        
        logger.info(f"LidarDataProvider initialisé avec répertoire de données: {self.data_dir}")
    
    @cached(data_type=CacheType.GEODATA, policy=CachePolicy.MONTHLY)
    def search_available_data(self, 
                            geometry: Union[Dict[str, Any], gpd.GeoDataFrame],
                            start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None,
                            sources: List[RemoteSensingSource] = None,
                            point_density_min: float = 1.0,
                            limit: int = 10,
                            **kwargs) -> List[Dict[str, Any]]:
        """
        Recherche les données LIDAR disponibles pour une zone géographique.
        
        Args:
            geometry: Géométrie de la zone d'intérêt (GeoJSON ou GeoDataFrame)
            start_date: Date de début de la période de recherche (optionnel)
            end_date: Date de fin de la période de recherche (optionnel)
            sources: Liste des sources à interroger (par défaut: toutes les sources LIDAR)
            point_density_min: Densité de points minimale (pts/m²)
            limit: Nombre maximal de résultats à retourner
            **kwargs: Arguments supplémentaires pour la recherche
            
        Returns:
            Liste des métadonnées de données LIDAR disponibles
        """
        if sources is None:
            # Par défaut, utiliser toutes les sources LIDAR
            sources = [
                RemoteSensingSource.LIDAR_AERIEN,
                RemoteSensingSource.LIDAR_TERRESTRE,
                RemoteSensingSource.LIDAR_DRONE
            ]
        
        # Convertir la géométrie en bbox
        if isinstance(geometry, gpd.GeoDataFrame):
            # Utiliser les limites de la GeoDataFrame
            bounds = geometry.total_bounds  # [minx, miny, maxx, maxy]
            bbox = (bounds[0], bounds[1], bounds[2], bounds[3])
        else:
            # Convertir le GeoJSON en objet shapely puis obtenir les limites
            geom_shape = shape(geometry)
            bbox = geom_shape.bounds  # (minx, miny, maxx, maxy)
        
        # Définir les dates par défaut si non spécifiées
        if start_date is None:
            # Par défaut, chercher les données des 10 dernières années
            start_date = datetime.now() - timedelta(days=365 * 10)
        
        if end_date is None:
            end_date = datetime.now()
        
        all_results = []
        
        # Interroger chaque source configurée
        for source in sources:
            try:
                logger.info(f"Recherche de données {source.name} du {start_date} au {end_date}")
                
                # Paramètres spécifiques selon la source
                search_params = kwargs.copy()
                search_params.update({
                    "point_density_min": point_density_min
                })
                
                # Effectuer la recherche
                results = self.connector.search_data(
                    source=source,
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    **search_params
                )
                
                # Ajouter la source aux résultats pour garder la trace
                for result in results:
                    result["source"] = source.name
                
                all_results.extend(results)
                logger.info(f"Trouvé {len(results)} jeux de données {source.name}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la recherche de données {source.name}: {str(e)}")
        
        # Trier par date d'acquisition (plus récentes en premier) et limiter le nombre
        all_results.sort(key=lambda x: x.get("date", ""), reverse=True)
        return all_results[:limit]
    
    def download_data(self, 
                    product_id: str, 
                    source: RemoteSensingSource,
                    output_dir: Optional[Path] = None,
                    **kwargs) -> Optional[Path]:
        """
        Télécharge un jeu de données LIDAR spécifique.
        
        Args:
            product_id: Identifiant du produit à télécharger
            source: Source des données
            output_dir: Répertoire de sortie (si None, utilise le répertoire par défaut)
            **kwargs: Arguments supplémentaires pour le téléchargement
            
        Returns:
            Chemin vers les données téléchargées ou None si échec
        """
        output_path = output_dir or self.data_dir / source.name.lower()
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Téléchargement des données LIDAR {product_id} depuis {source.name}")
        
        try:
            # Télécharger via le connecteur
            downloaded_path = self.connector.download_data(
                source=source,
                product_id=product_id,
                output_dir=output_path,
                **kwargs
            )
            
            if downloaded_path and downloaded_path.exists():
                logger.info(f"Données LIDAR téléchargées avec succès: {downloaded_path}")
                return downloaded_path
            else:
                logger.error(f"Échec du téléchargement des données LIDAR {product_id}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de {product_id}: {str(e)}")
            return None
    
    def process_point_cloud(self, 
                          point_cloud_path: Path,
                          source: RemoteSensingSource,
                          parcel_geometry: Union[Dict[str, Any], gpd.GeoDataFrame],
                          metadata: Optional[LidarPointCloudMetadata] = None,
                          **kwargs) -> Optional[RemoteSensingData]:
        """
        Traite un nuage de points LIDAR pour l'analyse forestière.
        
        Args:
            point_cloud_path: Chemin vers le nuage de points à traiter
            source: Source des données
            parcel_geometry: Géométrie de la parcelle à extraire (GeoJSON ou GeoDataFrame)
            metadata: Métadonnées du nuage de points (optionnel)
            **kwargs: Arguments supplémentaires pour le traitement
            
        Returns:
            Données de télédétection traitées ou None en cas d'échec
        """
        logger.info(f"Traitement du nuage de points {point_cloud_path.name}")
        
        try:
            # Vérifier que le fichier existe
            if not point_cloud_path.exists():
                logger.error(f"Fichier introuvable: {point_cloud_path}")
                return None
            
            # Préparer les métadonnées si elles ne sont pas fournies
            if metadata is None:
                logger.warning(f"Aucune métadonnée fournie pour {point_cloud_path.name}, utilisation de valeurs par défaut")
                # Extraire le nom du produit à partir du nom de fichier
                product_id = point_cloud_path.stem
                
                # Créer des métadonnées par défaut
                metadata = LidarPointCloudMetadata(
                    source=source,
                    acquisition_date=datetime.now(),  # Date par défaut
                    point_density=5.0,  # Valeur par défaut
                    num_returns=4,  # Valeur par défaut
                    classification_available=True,
                    epsg_code=4326  # WGS84 par défaut
                )
            
            # Créer l'objet de données
            data = RemoteSensingData(
                parcel_id=f"parcel_{point_cloud_path.stem}",
                source=source,
                acquisition_date=metadata.acquisition_date,
                point_cloud_path=point_cloud_path,
                lidar_metadata=metadata
            )
            
            # Traiter le nuage de points avec le processeur LIDAR
            processed_data = self.lidar_processor.process(
                data,
                geometry=parcel_geometry,
                **kwargs
            )
            
            logger.info(f"Traitement de {point_cloud_path.name} terminé avec succès")
            return processed_data
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de {point_cloud_path.name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def extract_forest_metrics(self, 
                             data: RemoteSensingData,
                             calculate_tree_positions: bool = True,
                             calculate_understory: bool = True) -> Optional[ForestMetrics]:
        """
        Extrait des métriques forestières à partir de données LIDAR traitées.
        
        Args:
            data: Données LIDAR traitées
            calculate_tree_positions: Calculer les positions individuelles des arbres
            calculate_understory: Calculer les métriques du sous-étage forestier
            
        Returns:
            Métriques forestières extraites ou None en cas d'échec
        """
        if not data or not data.processed or data.point_cloud_data is None:
            logger.error("Données LIDAR invalides ou non traitées")
            return None
        
        logger.info(f"Extraction des métriques forestières pour {data.parcel_id}")
        
        try:
            # Déléguer l'extraction des métriques au composant spécialisé
            metrics = self.metrics_extractor.extract_metrics(
                data, 
                calculate_tree_positions=calculate_tree_positions,
                calculate_understory=calculate_understory
            )
            
            logger.info(f"Extraction des métriques forestières terminée pour {data.parcel_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des métriques forestières: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def analyze_multitemporal(self,
                            lidar_data_list: List[RemoteSensingData],
                            metrics_list: Optional[List[ForestMetrics]] = None) -> Dict[str, Any]:
        """
        Analyse multitemporelle des données LIDAR pour suivre l'évolution forestière.
        
        Args:
            lidar_data_list: Liste de données LIDAR traitées pour une même zone (triées chronologiquement)
            metrics_list: Liste des métriques forestières précalculées (optionnel)
            
        Returns:
            Résultats de l'analyse d'évolution (croissance, changements structuraux)
        """
        if not lidar_data_list:
            logger.error("Aucune donnée LIDAR fournie pour l'analyse multitemporelle")
            return {"error": "Données insuffisantes"}
        
        if len(lidar_data_list) < 2:
            logger.warning("Au moins 2 acquisitions sont nécessaires pour l'analyse multitemporelle")
            return {"warning": "Données insuffisantes pour l'analyse temporelle"}
        
        logger.info(f"Analyse multitemporelle sur {len(lidar_data_list)} acquisitions LIDAR")
        
        # Trier les données par date si nécessaire
        sorted_data = sorted(lidar_data_list, key=lambda x: x.acquisition_date)
        
        # Si les métriques ne sont pas fournies, les calculer
        if metrics_list is None or len(metrics_list) != len(sorted_data):
            logger.info("Calcul des métriques forestières pour toutes les acquisitions")
            metrics_list = []
            for data in sorted_data:
                metrics = self.extract_forest_metrics(data)
                if metrics:
                    metrics_list.append(metrics)
                else:
                    logger.error(f"Impossible de calculer les métriques pour {data.parcel_id} à la date {data.acquisition_date}")
                    return {"error": "Échec du calcul des métriques"}
        
        # S'assurer qu'il y a suffisamment de métriques
        if len(metrics_list) < 2:
            logger.warning("Métriques insuffisantes pour l'analyse temporelle")
            return {"warning": "Métriques insuffisantes"}
        
        # Déléguer l'analyse temporelle au composant spécialisé
        results = self.temporal_analyzer.analyze(metrics_list)
        
        logger.info("Analyse multitemporelle terminée avec succès")
        return results
