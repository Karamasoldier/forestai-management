#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Processeur principal de données de télédétection.

Ce module fournit une interface unifiée pour le traitement des différents
types de données de télédétection (satellite, LIDAR).
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

import geopandas as gpd

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.remote_sensing.models import (
    RemoteSensingData,
    RemoteSensingSource
)
from forestai.domain.services.remote_sensing.processors import (
    SatelliteDataProcessor,
    LidarDataProcessor
)

logger = get_logger(__name__)


class RemoteSensingDataProcessor:
    """
    Interface unifiée pour le traitement des données de télédétection.
    
    Cette classe coordonne les différents processeurs spécialisés et fournit
    une interface simplifiée pour l'utilisateur.
    """
    
    def __init__(self, work_dir: Optional[Path] = None, n_jobs: int = 1):
        """
        Initialise le processeur de données de télédétection.
        
        Args:
            work_dir: Répertoire de travail pour les fichiers temporaires
            n_jobs: Nombre de tâches parallèles
        """
        # Répertoire de travail (pour les fichiers temporaires)
        if work_dir is None:
            work_dir = Path(os.environ.get("FORESTAI_WORK_DIR", ".")) / "temp"
        
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration pour le traitement parallèle
        self.n_jobs = n_jobs
        
        # Initialiser les processeurs spécialisés
        self.satellite_processor = SatelliteDataProcessor(work_dir)
        self.lidar_processor = LidarDataProcessor(work_dir)
        
        logger.info(f"RemoteSensingDataProcessor initialisé avec répertoire de travail: {self.work_dir}")
    
    def process(self, data: RemoteSensingData, 
               aoi: Optional[Union[gpd.GeoDataFrame, Dict[str, Any]]] = None,
               **kwargs) -> RemoteSensingData:
        """
        Traite des données de télédétection selon leur type.
        
        Args:
            data: Données de télédétection à traiter
            aoi: Zone d'intérêt pour découper les données (GeoDataFrame ou GeoJSON)
            **kwargs: Paramètres spécifiques au type de données
            
        Returns:
            Données de télédétection traitées
        """
        # Déterminer le type de données et utiliser le processeur approprié
        if self._is_satellite_data(data):
            logger.info(f"Traitement d'une image satellite pour {data.parcel_id}")
            return self.satellite_processor.process(data, aoi, **kwargs)
        
        elif self._is_lidar_data(data):
            logger.info(f"Traitement de données LIDAR pour {data.parcel_id}")
            return self.lidar_processor.process(data, aoi, **kwargs)
        
        else:
            logger.warning(f"Type de données de télédétection non reconnu pour {data.parcel_id}")
            return data
    
    def process_batch(self, data_list: List[RemoteSensingData], 
                     aoi: Optional[Union[gpd.GeoDataFrame, Dict[str, Any]]] = None,
                     **kwargs) -> List[RemoteSensingData]:
        """
        Traite un lot de données de télédétection.
        
        Args:
            data_list: Liste des données à traiter
            aoi: Zone d'intérêt commune (optionnel)
            **kwargs: Paramètres de traitement
            
        Returns:
            Liste des données traitées
        """
        if not data_list:
            return []
        
        processed_data = []
        
        # Traiter séquentiellement ou en parallèle selon le nombre de jobs
        if self.n_jobs <= 1:
            # Traitement séquentiel
            for data in data_list:
                processed_data.append(self.process(data, aoi, **kwargs))
        else:
            # Traitement parallèle
            from concurrent.futures import ProcessPoolExecutor, as_completed
            
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                # Soumettre les tâches
                future_to_data = {
                    executor.submit(self.process, data, aoi, **kwargs): data 
                    for data in data_list
                }
                
                # Récupérer les résultats au fur et à mesure
                for future in as_completed(future_to_data):
                    original_data = future_to_data[future]
                    try:
                        processed_result = future.result()
                        processed_data.append(processed_result)
                    except Exception as e:
                        logger.error(f"Erreur lors du traitement parallèle de {original_data.parcel_id}: {str(e)}")
                        # Ajouter les données non traitées pour maintenir l'ordre
                        processed_data.append(original_data)
        
        return processed_data
    
    def _is_satellite_data(self, data: RemoteSensingData) -> bool:
        """
        Détermine si les données sont de type satellite.
        
        Args:
            data: Données à vérifier
            
        Returns:
            True si les données sont de type satellite
        """
        # Vérifier la source
        is_satellite_source = (
            RemoteSensingSource.SENTINEL_1 <= data.source <= RemoteSensingSource.RAPIDEYE
        )
        
        # Vérifier la présence d'un chemin raster
        has_raster_path = data.raster_path is not None
        
        return is_satellite_source and has_raster_path
    
    def _is_lidar_data(self, data: RemoteSensingData) -> bool:
        """
        Détermine si les données sont de type LIDAR.
        
        Args:
            data: Données à vérifier
            
        Returns:
            True si les données sont de type LIDAR
        """
        # Vérifier la source
        is_lidar_source = (
            RemoteSensingSource.LIDAR_AERIEN <= data.source <= RemoteSensingSource.LIDAR_DRONE
        )
        
        # Vérifier la présence d'un chemin de nuage de points
        has_point_cloud_path = data.point_cloud_path is not None
        
        return is_lidar_source and has_point_cloud_path
