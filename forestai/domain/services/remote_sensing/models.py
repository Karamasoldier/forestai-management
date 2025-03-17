#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modèles de données pour le module de télédétection.

Ce module définit les classes et structures de données utilisées
par le module de télédétection.
"""

from typing import Dict, List, Tuple, Union, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class RemoteSensingSource(Enum):
    """Énumération des sources de données de télédétection."""
    SENTINEL_2 = "sentinel2"
    LANDSAT_8 = "landsat8"
    LANDSAT_9 = "landsat9"
    LIDAR = "lidar"
    AERIAL = "aerial"
    PLANETSCOPE = "planetscope"
    DRONE = "drone"
    OTHER = "other"


class VegetationIndex(Enum):
    """Énumération des indices de végétation."""
    NDVI = "ndvi"  # Normalized Difference Vegetation Index
    EVI = "evi"    # Enhanced Vegetation Index
    NDMI = "ndmi"  # Normalized Difference Moisture Index
    NDWI = "ndwi"  # Normalized Difference Water Index
    LAI = "lai"    # Leaf Area Index
    SAVI = "savi"  # Soil Adjusted Vegetation Index
    MSAVI = "msavi"  # Modified Soil Adjusted Vegetation Index
    GNDVI = "gndvi"  # Green Normalized Difference Vegetation Index
    NBR = "nbr"    # Normalized Burn Ratio
    NDRE = "ndre"  # Normalized Difference Red Edge


@dataclass
class SatelliteImageMetadata:
    """Métadonnées d'une image satellite."""
    acquisition_date: datetime
    source: RemoteSensingSource
    cloud_cover_percentage: float
    spatial_resolution: float  # en mètres
    scene_id: str
    bands: List[str]
    path: Optional[str] = None
    utm_zone: Optional[str] = None
    epsg_code: Optional[int] = None
    processing_level: Optional[str] = None
    sensor: Optional[str] = None
    sun_azimuth: Optional[float] = None
    sun_elevation: Optional[float] = None


@dataclass
class LidarPointCloudMetadata:
    """Métadonnées d'un nuage de points LIDAR."""
    acquisition_date: datetime
    point_density: float  # points par m²
    vertical_accuracy: float  # en mètres
    horizontal_accuracy: float  # en mètres
    classification_scheme: Optional[Dict[int, str]] = None
    epsg_code: Optional[int] = None
    sensor: Optional[str] = None
    platform: Optional[str] = None
    processing_level: Optional[str] = None
    path: Optional[str] = None
    point_formats: Optional[List[str]] = None
    return_types: Optional[List[str]] = None


@dataclass
class ForestMetrics:
    """Métriques forestières dérivées des données de télédétection."""
    canopy_height: Optional[float] = None  # hauteur moyenne de la canopée (m)
    basal_area: Optional[float] = None  # surface terrière (m²/ha)
    stem_density: Optional[float] = None  # densité des tiges (tiges/ha)
    canopy_cover: Optional[float] = None  # couverture de la canopée (%)
    leaf_area_index: Optional[float] = None  # indice de surface foliaire
    biomass: Optional[float] = None  # biomasse (kg/ha)
    carbon_stock: Optional[float] = None  # stock de carbone (kg/ha)
    height_variation: Optional[float] = None  # variation de hauteur (coefficient)


@dataclass
class RemoteSensingData:
    """
    Représente un ensemble de données de télédétection pour une parcelle forestière.
    """
    parcel_id: str
    acquisition_date: datetime
    source: RemoteSensingSource
    metrics: ForestMetrics
    vegetation_indices: Optional[Dict[VegetationIndex, float]] = None
    metadata: Optional[Union[SatelliteImageMetadata, LidarPointCloudMetadata]] = None
    processing_history: Optional[List[str]] = None
    quality_flags: Optional[Dict[str, bool]] = None


@dataclass
class ForestGrowthPrediction:
    """
    Représente une prédiction de croissance forestière sur une période future.
    """
    parcel_id: str
    prediction_date: datetime
    # Liste de tuples (date, métriques, intervalles de confiance)
    predictions: List[Tuple[datetime, ForestMetrics, Dict[str, Tuple[float, float]]]]
    model_type: str  # Type de modèle utilisé (sarima, exp_smoothing, random_forest)
    confidence_level: float  # Niveau de confiance pour les intervalles (ex: 0.95)
    metrics: Dict[str, Dict[str, any]]  # Métriques de performance du modèle
    climate_scenario: Optional[str] = None  # Scénario climatique utilisé (si applicable)
    
    def get_prediction_at_date(self, target_date: datetime) -> Tuple[Optional[ForestMetrics], Optional[Dict[str, Tuple[float, float]]]]:
        """
        Récupère la prédiction pour une date spécifique.
        
        Args:
            target_date: Date cible pour la prédiction
        
        Returns:
            Tuple contenant les métriques forestières prédites et les intervalles de confiance,
            ou (None, None) si aucune prédiction n'est disponible pour cette date
        """
        # Trouver la date la plus proche si la date exacte n'existe pas
        closest_prediction = None
        min_diff = float('inf')
        
        for date, metrics, intervals in self.predictions:
            diff = abs((target_date - date).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_prediction = (metrics, intervals)
        
        return closest_prediction if closest_prediction else (None, None)
    
    def get_growth_rate(self, metric_name: str) -> Optional[Dict[str, float]]:
        """
        Calcule le taux de croissance pour une métrique spécifique.
        
        Args:
            metric_name: Nom de la métrique (ex: 'canopy_height', 'basal_area')
        
        Returns:
            Dictionnaire avec les taux de croissance annuels, ou None si impossible à calculer
        """
        if not self.predictions or len(self.predictions) < 2:
            return None
        
        # Trier les prédictions par date
        sorted_predictions = sorted(self.predictions, key=lambda x: x[0])
        
        # Extraire les valeurs de la métrique à chaque date
        metric_values = []
        dates = []
        
        for date, metrics, _ in sorted_predictions:
            value = getattr(metrics, metric_name, None)
            if value is not None:
                metric_values.append(value)
                dates.append(date)
        
        if len(metric_values) < 2:
            return None
        
        # Calculer les taux de croissance
        growth_rates = {}
        first_date = dates[0]
        first_value = metric_values[0]
        
        for i, (date, value) in enumerate(zip(dates[1:], metric_values[1:])):
            # Calcul du nombre d'années entre la date initiale et la date courante
            years = (date - first_date).days / 365.25
            
            if years > 0 and first_value > 0:
                # Taux de croissance annuel composé
                cagr = ((value / first_value) ** (1 / years) - 1) * 100
                growth_rates[date.strftime("%Y-%m-%d")] = cagr
        
        return growth_rates
