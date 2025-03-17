#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base abstraite pour les processeurs de données de télédétection.

Ce module définit l'interface commune pour tous les processeurs de données.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

import geopandas as gpd

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.remote_sensing.models import RemoteSensingData

logger = get_logger(__name__)


class BaseDataProcessor(ABC):
    """Classe de base abstraite pour les processeurs de données de télédétection."""
    
    def __init__(self, work_dir: Optional[Path] = None):
        """
        Initialisation du processeur.
        
        Args:
            work_dir: Répertoire de travail pour les fichiers temporaires
        """
        # Répertoire de travail (pour les fichiers temporaires)
        if work_dir is None:
            work_dir = Path(os.environ.get("FORESTAI_WORK_DIR", ".")) / "temp"
        
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"{self.__class__.__name__} initialisé avec répertoire de travail: {self.work_dir}")
    
    @abstractmethod
    def process(self, data: RemoteSensingData, 
               aoi: Optional[Union[gpd.GeoDataFrame, Dict[str, Any]]] = None,
               **kwargs) -> RemoteSensingData:
        """
        Méthode principale de traitement des données.
        
        Args:
            data: Données de télédétection à traiter
            aoi: Zone d'intérêt pour découper les données (GeoDataFrame ou GeoJSON)
            **kwargs: Paramètres supplémentaires spécifiques au processeur
            
        Returns:
            Données de télédétection traitées
        """
        pass
    
    def _create_processed_data(self, original_data: RemoteSensingData, 
                             processed_content: Any = None) -> RemoteSensingData:
        """
        Crée une copie des données avec ajout du statut de traitement.
        
        Args:
            original_data: Données originales
            processed_content: Contenu traité (raster ou nuage de points)
            
        Returns:
            Données avec statut de traitement mis à jour
        """
        # Créer une nouvelle instance
        processed_data = RemoteSensingData(
            parcel_id=original_data.parcel_id,
            source=original_data.source,
            acquisition_date=original_data.acquisition_date,
            raster_path=original_data.raster_path,
            point_cloud_path=original_data.point_cloud_path,
            satellite_metadata=original_data.satellite_metadata,
            lidar_metadata=original_data.lidar_metadata,
            processed=True,
            processing_timestamp=datetime.now(),
            processing_version="1.0"
        )
        
        # Ajouter le contenu traité
        if processed_content is not None:
            if original_data.raster_path is not None:
                processed_data.raster_data = processed_content
            elif original_data.point_cloud_path is not None:
                processed_data.point_cloud_data = processed_content
        
        return processed_data
