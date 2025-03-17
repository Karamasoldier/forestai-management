#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Calculateur d'indices de végétation pour les images satellites.

Ce module fournit des fonctionnalités pour calculer divers indices de végétation
à partir des bandes spectrales d'images satellites.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.remote_sensing.models import (
    VegetationIndex,
    SatelliteImageMetadata,
    RemoteSensingSource
)

logger = get_logger(__name__)


class VegetationIndexCalculator:
    """Classe utilitaire pour calculer les indices de végétation à partir d'images satellites."""
    
    @staticmethod
    def get_band_info(source: RemoteSensingSource, 
                     metadata: Optional[SatelliteImageMetadata] = None) -> Dict[str, int]:
        """
        Obtient les informations de bandes pour une source satellite spécifique.
        
        Args:
            source: Source des données satellite
            metadata: Métadonnées satellite (si disponibles)
            
        Returns:
            Dictionnaire mappant les noms de bandes (Red, NIR, etc.) aux indices
        """
        # Définitions par défaut pour les sources communes
        if source == RemoteSensingSource.SENTINEL_2:
            return {
                "Blue": 0,      # Bande 2
                "Green": 1,     # Bande 3
                "Red": 2,       # Bande 4
                "RedEdge1": 3,  # Bande 5
                "RedEdge2": 4,  # Bande 6
                "RedEdge3": 5,  # Bande 7
                "NIR": 6,       # Bande 8
                "SWIR1": 9,     # Bande 11
                "SWIR2": 10     # Bande 12
            }
        elif source == RemoteSensingSource.LANDSAT_8 or source == RemoteSensingSource.LANDSAT_9:
            return {
                "Blue": 1,      # Bande 2
                "Green": 2,     # Bande 3
                "Red": 3,       # Bande 4
                "NIR": 4,       # Bande 5
                "SWIR1": 5,     # Bande 6
                "SWIR2": 6      # Bande 7
            }
        
        # Si les métadonnées sont disponibles, essayer de déduire à partir des noms de bandes
        if metadata and metadata.bands:
            band_map = {}
            band_names = [b.lower() for b in metadata.bands]
            
            for i, name in enumerate(band_names):
                if "blue" in name:
                    band_map["Blue"] = i
                elif "green" in name:
                    band_map["Green"] = i
                elif "nir" in name or "near" in name:
                    band_map["NIR"] = i
                elif "red" in name:
                    if "edge" in name:
                        if "1" in name or "first" in name:
                            band_map["RedEdge1"] = i
                        elif "2" in name or "second" in name:
                            band_map["RedEdge2"] = i
                        elif "3" in name or "third" in name:
                            band_map["RedEdge3"] = i
                        else:
                            band_map["RedEdge"] = i
                    else:
                        band_map["Red"] = i
                elif "swir" in name:
                    if "1" in name or "first" in name:
                        band_map["SWIR1"] = i
                    elif "2" in name or "second" in name:
                        band_map["SWIR2"] = i
                    else:
                        band_map["SWIR"] = i
            
            if band_map:
                return band_map
        
        # En cas d'échec, retourner une correspondance générique
        logger.warning(f"Impossible de déterminer la correspondance des bandes pour {source}, utilisation de valeurs génériques")
        return {
            "Blue": 0,
            "Green": 1,
            "Red": 2,
            "NIR": 3
        }
    
    @staticmethod
    def calculate_indices(raster_data: np.ndarray, 
                         band_info: Dict[str, int]) -> Dict[str, np.ndarray]:
        """
        Calcule les indices de végétation à partir des données raster.
        
        Args:
            raster_data: Données raster multi-bandes
            band_info: Correspondance entre noms de bandes et indices
            
        Returns:
            Dictionnaire des indices calculés
        """
        indices = {}
        
        # Vérifier la disponibilité des bandes nécessaires
        bands_available = set(band_info.keys())
        required_bands_ndvi = {"Red", "NIR"}
        required_bands_evi = {"Red", "NIR", "Blue"}
        required_bands_ndmi = {"NIR", "SWIR1"}
        required_bands_nbr = {"NIR", "SWIR2"}
        
        # Créer des masques pour les valeurs nulles ou invalides
        valid_mask = np.ones((raster_data.shape[1], raster_data.shape[2]), dtype=bool)
        for band_idx in band_info.values():
            if band_idx < raster_data.shape[0]:
                band_valid = (raster_data[band_idx] > 0) & (raster_data[band_idx] < 10000)  # Seuil arbitraire
                valid_mask = valid_mask & band_valid
        
        # Calculer NDVI - Normalized Difference Vegetation Index
        VegetationIndexCalculator._calculate_ndvi(raster_data, band_info, bands_available, 
                                                 required_bands_ndvi, valid_mask, indices)
        
        # Calculer EVI - Enhanced Vegetation Index
        VegetationIndexCalculator._calculate_evi(raster_data, band_info, bands_available, 
                                               required_bands_evi, valid_mask, indices)
        
        # Calculer NDMI - Normalized Difference Moisture Index
        VegetationIndexCalculator._calculate_ndmi(raster_data, band_info, bands_available, 
                                                required_bands_ndmi, valid_mask, indices)
        
        # Calculer NBR - Normalized Burn Ratio
        VegetationIndexCalculator._calculate_nbr(raster_data, band_info, bands_available, 
                                               required_bands_nbr, valid_mask, indices)
        
        return indices
    
    @staticmethod
    def _calculate_ndvi(raster_data: np.ndarray, band_info: Dict[str, int],
                       bands_available: set, required_bands: set,
                       valid_mask: np.ndarray, indices: Dict[str, np.ndarray]):
        """Calcule l'indice NDVI et l'ajoute au dictionnaire des indices."""
        if not required_bands.issubset(bands_available):
            return
        
        red_idx = band_info["Red"]
        nir_idx = band_info["NIR"]
        
        # S'assurer que les indices sont valides
        if red_idx >= raster_data.shape[0] or nir_idx >= raster_data.shape[0]:
            return
        
        red = raster_data[red_idx].astype(np.float32)
        nir = raster_data[nir_idx].astype(np.float32)
        
        # Calculer NDVI avec gestion des divisions par zéro
        ndvi = np.zeros_like(red, dtype=np.float32)
        mask = (nir + red) > 0
        ndvi[mask] = (nir[mask] - red[mask]) / (nir[mask] + red[mask])
        
        # Appliquer le masque de validité
        ndvi[~valid_mask] = np.nan
        
        # Borner les valeurs entre -1 et 1
        ndvi = np.clip(ndvi, -1.0, 1.0)
        
        indices[VegetationIndex.NDVI.name] = ndvi
        logger.info("NDVI calculé avec succès")
    
    @staticmethod
    def _calculate_evi(raster_data: np.ndarray, band_info: Dict[str, int],
                      bands_available: set, required_bands: set,
                      valid_mask: np.ndarray, indices: Dict[str, np.ndarray]):
        """Calcule l'indice EVI et l'ajoute au dictionnaire des indices."""
        if not required_bands.issubset(bands_available):
            return
        
        red_idx = band_info["Red"]
        nir_idx = band_info["NIR"]
        blue_idx = band_info["Blue"]
        
        # S'assurer que les indices sont valides
        if (red_idx >= raster_data.shape[0] or 
            nir_idx >= raster_data.shape[0] or 
            blue_idx >= raster_data.shape[0]):
            return
        
        red = raster_data[red_idx].astype(np.float32)
        nir = raster_data[nir_idx].astype(np.float32)
        blue = raster_data[blue_idx].astype(np.float32)
        
        # Coefficients EVI standard
        G = 2.5  # Gain factor
        C1 = 6.0  # Coefficient for atmospheric resistance
        C2 = 7.5  # Coefficient for atmospheric resistance
        L = 1.0   # Canopy background adjustment
        
        # Calculer EVI avec gestion des divisions par zéro
        denom = nir + C1 * red - C2 * blue + L
        evi = np.zeros_like(red, dtype=np.float32)
        mask = denom > 0
        evi[mask] = G * (nir[mask] - red[mask]) / denom[mask]
        
        # Appliquer le masque de validité
        evi[~valid_mask] = np.nan
        
        # Borner les valeurs
        evi = np.clip(evi, -1.0, 1.0)
        
        indices[VegetationIndex.EVI.name] = evi
        logger.info("EVI calculé avec succès")
    
    @staticmethod
    def _calculate_ndmi(raster_data: np.ndarray, band_info: Dict[str, int],
                       bands_available: set, required_bands: set,
                       valid_mask: np.ndarray, indices: Dict[str, np.ndarray]):
        """Calcule l'indice NDMI et l'ajoute au dictionnaire des indices."""
        if not required_bands.issubset(bands_available):
            return
        
        nir_idx = band_info["NIR"]
        swir_idx = band_info["SWIR1"]
        
        # S'assurer que les indices sont valides
        if nir_idx >= raster_data.shape[0] or swir_idx >= raster_data.shape[0]:
            return
        
        nir = raster_data[nir_idx].astype(np.float32)
        swir = raster_data[swir_idx].astype(np.float32)
        
        # Calculer NDMI avec gestion des divisions par zéro
        ndmi = np.zeros_like(nir, dtype=np.float32)
        mask = (nir + swir) > 0
        ndmi[mask] = (nir[mask] - swir[mask]) / (nir[mask] + swir[mask])
        
        # Appliquer le masque de validité
        ndmi[~valid_mask] = np.nan
        
        # Borner les valeurs
        ndmi = np.clip(ndmi, -1.0, 1.0)
        
        indices[VegetationIndex.NDMI.name] = ndmi
        logger.info("NDMI calculé avec succès")
    
    @staticmethod
    def _calculate_nbr(raster_data: np.ndarray, band_info: Dict[str, int],
                      bands_available: set, required_bands: set,
                      valid_mask: np.ndarray, indices: Dict[str, np.ndarray]):
        """Calcule l'indice NBR et l'ajoute au dictionnaire des indices."""
        if not required_bands.issubset(bands_available):
            return
        
        nir_idx = band_info["NIR"]
        swir2_idx = band_info["SWIR2"]
        
        # S'assurer que les indices sont valides
        if nir_idx >= raster_data.shape[0] or swir2_idx >= raster_data.shape[0]:
            return
        
        nir = raster_data[nir_idx].astype(np.float32)
        swir2 = raster_data[swir2_idx].astype(np.float32)
        
        # Calculer NBR avec gestion des divisions par zéro
        nbr = np.zeros_like(nir, dtype=np.float32)
        mask = (nir + swir2) > 0
        nbr[mask] = (nir[mask] - swir2[mask]) / (nir[mask] + swir2[mask])
        
        # Appliquer le masque de validité
        nbr[~valid_mask] = np.nan
        
        # Borner les valeurs
        nbr = np.clip(nbr, -1.0, 1.0)
        
        indices[VegetationIndex.NBR.name] = nbr
        logger.info("NBR calculé avec succès")
