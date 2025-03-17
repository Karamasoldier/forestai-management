#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Processeur d'images satellite pour l'analyse forestière.

Ce module fournit des fonctionnalités pour traiter les données d'imagerie 
satellite en préparation pour l'analyse forestière.
"""

import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
from shapely.geometry import mapping

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.remote_sensing.models import (
    RemoteSensingData,
    RemoteSensingSource,
    SatelliteImageMetadata
)
from forestai.domain.services.remote_sensing.processors.base_processor import BaseDataProcessor
from forestai.domain.services.remote_sensing.processors.index_calculator import VegetationIndexCalculator

logger = get_logger(__name__)


class SatelliteDataProcessor(BaseDataProcessor):
    """Processeur d'images satellite pour l'analyse forestière."""
    
    def process(self, data: RemoteSensingData, 
               aoi: Optional[Union[gpd.GeoDataFrame, Dict[str, Any]]] = None,
               calculate_indices: bool = True,
               reproject_to_epsg: Optional[int] = None,
               resample_resolution: Optional[float] = None,
               **kwargs) -> RemoteSensingData:
        """
        Traite une image satellite pour l'analyse forestière.
        
        Args:
            data: Données de télédétection à traiter
            aoi: Zone d'intérêt pour découper l'image (GeoDataFrame ou GeoJSON)
            calculate_indices: Si True, calcule les indices de végétation
            reproject_to_epsg: Code EPSG pour la reprojection (optionnel)
            resample_resolution: Résolution pour le rééchantillonnage (optionnel)
            
        Returns:
            Données de télédétection traitées
        """
        if data.raster_path is None:
            logger.error("Aucun chemin raster défini dans les données")
            return data
        
        if not data.raster_path.exists():
            logger.error(f"Le fichier raster n'existe pas: {data.raster_path}")
            return data
        
        try:
            # Vérifier que c'est bien une image satellite
            is_satellite = (RemoteSensingSource.SENTINEL_1 <= data.source <= RemoteSensingSource.RAPIDEYE)
            if not is_satellite:
                logger.warning(f"Source inattendue pour une image satellite: {data.source}")
            
            # Ouvrir le fichier raster
            with rasterio.open(data.raster_path) as src:
                raster_data = src.read()
                profile = src.profile.copy()
                
                # Appliquer les traitements
                raster_data, profile = self._clip_to_aoi(src, raster_data, profile, aoi)
                raster_data, profile = self._reproject(src, raster_data, profile, reproject_to_epsg)
                raster_data, profile = self._resample(raster_data, profile, resample_resolution, src.res[0] if resample_resolution else None)
                
                # Calculer les indices de végétation si demandé
                processed_data = {"original": raster_data}
                
                if calculate_indices:
                    # Obtenir les informations de bandes pour traiter correctement les indices
                    band_info = VegetationIndexCalculator.get_band_info(data.source, data.satellite_metadata)
                    
                    # Calculer les indices de végétation
                    indices = VegetationIndexCalculator.calculate_indices(raster_data, band_info)
                    processed_data.update(indices)
                
                # Créer un nouveau RemoteSensingData avec les données traitées
                return self._create_processed_data(data, processed_data)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image satellite: {str(e)}")
            return data
    
    def _clip_to_aoi(self, src, raster_data: np.ndarray, profile: Dict[str, Any], 
                    aoi: Optional[Union[gpd.GeoDataFrame, Dict[str, Any]]]) -> tuple:
        """
        Découpe le raster selon une zone d'intérêt.
        
        Args:
            src: Source rasterio ouverte
            raster_data: Données raster
            profile: Profil raster
            aoi: Zone d'intérêt
            
        Returns:
            Tuple (raster découpé, profil mis à jour)
        """
        if aoi is None:
            return raster_data, profile
        
        # Convertir GeoDataFrame en features GeoJSON
        if isinstance(aoi, gpd.GeoDataFrame):
            aoi_geom = [mapping(geom) for geom in aoi.geometry]
        else:
            aoi_geom = [aoi]
        
        # Découper le raster selon la géométrie
        clipped_data, transform = mask(src, aoi_geom, crop=True)
        
        # Mettre à jour le profil
        clipped_profile = profile.copy()
        clipped_profile.update({
            'height': clipped_data.shape[1],
            'width': clipped_data.shape[2],
            'transform': transform
        })
        
        return clipped_data, clipped_profile
    
    def _reproject(self, src, raster_data: np.ndarray, profile: Dict[str, Any],
                  reproject_to_epsg: Optional[int]) -> tuple:
        """
        Reprojette le raster vers un système de coordonnées cible.
        
        Args:
            src: Source rasterio ouverte
            raster_data: Données raster
            profile: Profil raster
            reproject_to_epsg: Code EPSG cible
            
        Returns:
            Tuple (raster reprojeté, profil mis à jour)
        """
        if reproject_to_epsg is None or reproject_to_epsg == profile['crs'].to_epsg():
            return raster_data, profile
        
        # Calculer la transformation pour la reprojection
        dst_crs = f'EPSG:{reproject_to_epsg}'
        transform, width, height = calculate_default_transform(
            profile['crs'], dst_crs, 
            profile['width'], profile['height'], 
            *src.bounds
        )
        
        # Mettre à jour le profil
        reprojected_profile = profile.copy()
        reprojected_profile.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })
        
        # Allouer mémoire pour le raster reprojeté
        reprojected = np.zeros((src.count, height, width), dtype=raster_data.dtype)
        
        # Reprojeter chaque bande
        for i in range(src.count):
            reproject(
                source=raster_data[i],
                destination=reprojected[i],
                src_transform=profile['transform'],
                src_crs=profile['crs'],
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )
        
        return reprojected, reprojected_profile
    
    def _resample(self, raster_data: np.ndarray, profile: Dict[str, Any],
                resample_resolution: Optional[float], 
                orig_resolution: Optional[float]) -> tuple:
        """
        Rééchantillonne le raster à une résolution cible.
        
        Args:
            raster_data: Données raster
            profile: Profil raster
            resample_resolution: Résolution cible
            orig_resolution: Résolution originale
            
        Returns:
            Tuple (raster rééchantillonné, profil mis à jour)
        """
        if resample_resolution is None or orig_resolution is None or resample_resolution == orig_resolution:
            return raster_data, profile
        
        scale_factor = orig_resolution / resample_resolution
        new_width = int(profile['width'] * scale_factor)
        new_height = int(profile['height'] * scale_factor)
        
        # Mettre à jour la transformation
        src_bounds = rasterio.transform.array_bounds(
            profile['height'], profile['width'], profile['transform']
        )
        new_transform = rasterio.transform.from_bounds(
            *src_bounds, new_width, new_height
        )
        
        # Mettre à jour le profil
        resampled_profile = profile.copy()
        resampled_profile.update({
            'transform': new_transform,
            'width': new_width,
            'height': new_height
        })
        
        # Rééchantillonner chaque bande
        resampled = np.zeros((raster_data.shape[0], new_height, new_width), dtype=raster_data.dtype)
        
        for i in range(raster_data.shape[0]):
            reproject(
                source=raster_data[i],
                destination=resampled[i],
                src_transform=profile['transform'],
                src_crs=profile['crs'],
                dst_transform=new_transform,
                dst_crs=profile['crs'],
                resampling=Resampling.bilinear
            )
        
        return resampled, resampled_profile
