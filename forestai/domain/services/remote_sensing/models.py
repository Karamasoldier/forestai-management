#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modèles de données pour l'intégration de télédétection.

Ce module définit les structures de données utilisées pour représenter
et manipuler les données de télédétection dans le système ForestAI.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum, auto
import numpy as np
import pandas as pd
from pathlib import Path


class RemoteSensingSource(Enum):
    """Source des données de télédétection."""
    SENTINEL_2 = auto()  # Imagerie satellite optique Sentinel-2
    SENTINEL_1 = auto()  # Imagerie satellite radar Sentinel-1
    LANDSAT_8 = auto()   # Imagerie satellite Landsat 8
    LANDSAT_9 = auto()   # Imagerie satellite Landsat 9
    SPOT = auto()        # Imagerie SPOT
    MODIS = auto()       # Imagerie MODIS
    DRONE = auto()       # Imagerie par drone
    LIDAR_AERIEN = auto()  # LIDAR aéroporté
    LIDAR_TERRESTRE = auto()  # LIDAR terrestre
    LIDAR_DRONE = auto()  # LIDAR embarqué sur drone
    PLANET = auto()      # Imagerie PlanetScope
    RAPIDEYE = auto()    # Imagerie RapidEye
    AUTRE = auto()       # Autre source


class VegetationIndex(Enum):
    """Indices de végétation calculables à partir d'images satellite."""
    NDVI = "Normalized Difference Vegetation Index"  # (NIR - Red) / (NIR + Red)
    EVI = "Enhanced Vegetation Index"                # 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))
    NDMI = "Normalized Difference Moisture Index"    # (NIR - SWIR) / (NIR + SWIR)
    NBR = "Normalized Burn Ratio"                    # (NIR - SWIR) / (NIR + SWIR)
    LAI = "Leaf Area Index"                          # Indice de surface foliaire
    FAPAR = "Fraction of Absorbed Photosynthetically Active Radiation"  # Fraction du rayonnement absorbé
    GNDVI = "Green Normalized Difference Vegetation Index"  # (NIR - Green) / (NIR + Green)
    SAVI = "Soil Adjusted Vegetation Index"          # ((NIR - Red) / (NIR + Red + L)) * (1 + L), où L est un facteur d'ajustement
    MSAVI = "Modified Soil Adjusted Vegetation Index"  # 0.5 * (2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR - Red)))
    NDRE = "Normalized Difference Red Edge"          # (NIR - RedEdge) / (NIR + RedEdge)


@dataclass
class SatelliteImageMetadata:
    """Métadonnées associées à une image satellite."""
    source: RemoteSensingSource                  # Source de l'image
    acquisition_date: datetime                   # Date d'acquisition
    cloud_cover_percentage: float                # Pourcentage de couverture nuageuse
    spatial_resolution: float                    # Résolution spatiale en mètres
    bands: List[str]                             # Liste des bandes spectrales disponibles
    utm_zone: str                                # Zone UTM
    epsg_code: int                               # Code EPSG de la projection
    footprint: Optional[Dict[str, Any]] = None   # Empreinte géographique en GeoJSON
    sun_elevation: Optional[float] = None        # Élévation du soleil (degrés)
    sun_azimuth: Optional[float] = None          # Azimut du soleil (degrés)
    tile_id: Optional[str] = None                # Identifiant de la tuile
    metadata_url: Optional[str] = None           # URL des métadonnées complètes
    provider: Optional[str] = None               # Fournisseur de données
    processing_level: Optional[str] = None       # Niveau de traitement


@dataclass
class LidarPointCloudMetadata:
    """Métadonnées associées à un nuage de points LIDAR."""
    source: RemoteSensingSource                   # Source des données LIDAR
    acquisition_date: datetime                    # Date d'acquisition
    point_density: float                          # Densité de points (points/m²)
    num_returns: int                              # Nombre de retours
    classification_available: bool                # Indique si les points sont classifiés
    epsg_code: int                                # Code EPSG de la projection
    vertical_accuracy: Optional[float] = None     # Précision verticale (m)
    horizontal_accuracy: Optional[float] = None   # Précision horizontale (m)
    pulse_rate: Optional[float] = None            # Fréquence d'impulsion (kHz)
    scan_angle: Optional[float] = None            # Angle de balayage (degrés)
    footprint: Optional[Dict[str, Any]] = None    # Empreinte géographique en GeoJSON
    sensor_model: Optional[str] = None            # Modèle du capteur LIDAR
    flight_height: Optional[float] = None         # Hauteur de vol (m)
    provider: Optional[str] = None                # Fournisseur de données
    processing_level: Optional[str] = None        # Niveau de traitement


@dataclass
class ForestMetrics:
    """Métriques forestières calculées à partir des données de télédétection."""
    parcel_id: str                                  # Identifiant de la parcelle
    date: datetime                                  # Date des métriques
    source: RemoteSensingSource                     # Source de données
    
    # Métriques de couvert forestier
    canopy_cover_percentage: Optional[float] = None  # Pourcentage de couvert forestier
    canopy_height_mean: Optional[float] = None       # Hauteur moyenne de la canopée (m)
    canopy_height_max: Optional[float] = None        # Hauteur maximale de la canopée (m)
    canopy_height_std: Optional[float] = None        # Écart type des hauteurs de canopée (m)
    
    # Métriques de structure
    stem_density: Optional[float] = None             # Densité de tiges (tiges/ha)
    basal_area: Optional[float] = None               # Surface terrière (m²/ha)
    volume: Optional[float] = None                   # Volume de bois (m³/ha)
    biomass: Optional[float] = None                  # Biomasse (t/ha)
    
    # Métriques de santé et vigueur
    vegetation_indices: Optional[Dict[VegetationIndex, float]] = None  # Indices de végétation
    stress_indicators: Optional[Dict[str, float]] = None              # Indicateurs de stress
    
    # Métriques de diversité
    vertical_complexity: Optional[float] = None      # Indice de complexité verticale
    horizontal_heterogeneity: Optional[float] = None # Indice d'hétérogénéité horizontale
    
    # Métriques spécifiques au LIDAR
    tree_count: Optional[int] = None                 # Nombre d'arbres détectés
    tree_positions: Optional[List[Tuple[float, float, float]]] = None  # Positions des arbres (x, y, hauteur)
    understory_density: Optional[float] = None       # Densité du sous-étage
    
    # Métriques d'évolution temporelle (si disponibles)
    growth_rate: Optional[float] = None              # Taux de croissance (m/an)
    
    # Métriques de qualité des données
    quality_score: Optional[float] = None            # Score de qualité des métriques (0-1)
    processing_notes: Optional[str] = None           # Notes sur le traitement
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit les métriques en dictionnaire."""
        result = {k: v for k, v in self.__dict__.items() if v is not None}
        
        # Convertir les dictionnaires d'enum en dictionnaires de chaînes de caractères
        if self.vegetation_indices:
            result['vegetation_indices'] = {k.name: v for k, v in self.vegetation_indices.items()}
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForestMetrics':
        """Crée une instance de ForestMetrics à partir d'un dictionnaire."""
        
        # Convertir la source en Enum
        if isinstance(data.get('source'), str):
            data['source'] = RemoteSensingSource[data['source']]
        
        # Convertir les indices de végétation en Enum
        if 'vegetation_indices' in data and data['vegetation_indices']:
            data['vegetation_indices'] = {
                VegetationIndex[k]: v for k, v in data['vegetation_indices'].items()
            }
        
        # Convertir la date si nécessaire
        if isinstance(data.get('date'), str):
            data['date'] = datetime.fromisoformat(data['date'])
        
        return cls(**data)


@dataclass
class RemoteSensingData:
    """Données de télédétection pour une parcelle forestière."""
    parcel_id: str                                   # Identifiant de la parcelle
    source: RemoteSensingSource                      # Source de données
    acquisition_date: datetime                       # Date d'acquisition
    # Un des types de données suivants sera non-None
    raster_path: Optional[Path] = None               # Chemin vers les données raster
    point_cloud_path: Optional[Path] = None          # Chemin vers le nuage de points
    
    # Métadonnées associées
    satellite_metadata: Optional[SatelliteImageMetadata] = None  # Métadonnées satellite
    lidar_metadata: Optional[LidarPointCloudMetadata] = None     # Métadonnées LIDAR
    
    # Métriques forestières calculées
    metrics: Optional[ForestMetrics] = None          # Métriques forestières calculées
    
    # Données en mémoire (optionnel, pour le traitement)
    raster_data: Optional[np.ndarray] = None         # Données raster en mémoire
    point_cloud_data: Optional[pd.DataFrame] = None  # Nuage de points en mémoire
    
    # Informations sur le traitement
    processed: bool = False                          # Indique si les données ont été traitées
    processing_timestamp: Optional[datetime] = None  # Date du dernier traitement
    processing_version: Optional[str] = None         # Version du traitement
    
    def __post_init__(self):
        """Validation après initialisation."""
        # Vérifier qu'au moins un type de données est spécifié
        if self.raster_path is None and self.point_cloud_path is None:
            raise ValueError("Au moins un chemin de données (raster ou nuage de points) doit être spécifié")
        
        # Vérifier la cohérence des métadonnées
        is_satellite = self.source in (RemoteSensingSource.SENTINEL_2, RemoteSensingSource.SENTINEL_1,
                                      RemoteSensingSource.LANDSAT_8, RemoteSensingSource.LANDSAT_9,
                                      RemoteSensingSource.SPOT, RemoteSensingSource.MODIS,
                                      RemoteSensingSource.PLANET, RemoteSensingSource.RAPIDEYE)
        
        is_lidar = self.source in (RemoteSensingSource.LIDAR_AERIEN, RemoteSensingSource.LIDAR_TERRESTRE,
                                  RemoteSensingSource.LIDAR_DRONE)
        
        if is_satellite and self.satellite_metadata is None:
            raise ValueError(f"Les métadonnées satellite sont requises pour la source {self.source}")
        
        if is_lidar and self.lidar_metadata is None:
            raise ValueError(f"Les métadonnées LIDAR sont requises pour la source {self.source}")
