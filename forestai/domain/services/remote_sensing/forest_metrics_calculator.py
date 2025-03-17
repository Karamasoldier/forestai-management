#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Calculateur de métriques forestières à partir de données de télédétection.

Ce module fournit des fonctionnalités pour extraire des métriques forestières
à partir des données de télédétection (images satellite, LIDAR).
"""

import os
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from scipy.stats import entropy
from scipy.ndimage import label, distance_transform_edt
from skimage import filters
from sklearn.cluster import DBSCAN
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.remote_sensing.models import (
    RemoteSensingData,
    ForestMetrics,
    VegetationIndex,
    RemoteSensingSource
)

logger = get_logger(__name__)


class ForestMetricsCalculator:
    """
    Calculateur de métriques forestières à partir de données de télédétection.
    
    Cette classe fournit des méthodes pour extraire des métriques forestières
    à partir d'images satellite et de données LIDAR.
    """
    
    def __init__(self, n_jobs: int = 1):
        """
        Initialise le calculateur de métriques forestières.
        
        Args:
            n_jobs: Nombre de tâches parallèles
        """
        self.n_jobs = n_jobs
        logger.info(f"ForestMetricsCalculator initialisé")
    
    def calculate_metrics(self, data: RemoteSensingData) -> ForestMetrics:
        """
        Calcule des métriques forestières à partir de données de télédétection.
        
        Args:
            data: Données de télédétection traitées
            
        Returns:
            Métriques forestières calculées
        """
        # Vérifier que les données ont été traitées
        if not data.processed:
            logger.warning(f"Les données {data.parcel_id} n'ont pas été traitées, les métriques peuvent être imprécises")
        
        # Initialiser les métriques de base
        metrics = ForestMetrics(
            parcel_id=data.parcel_id,
            date=data.acquisition_date,
            source=data.source
        )
        
        # Calculer les métriques selon le type de données
        if data.raster_data is not None:
            # Données raster (images satellite)
            self._calculate_satellite_metrics(data, metrics)
        
        if data.point_cloud_data is not None:
            # Données de nuage de points (LIDAR)
            self._calculate_lidar_metrics(data, metrics)
        
        return metrics
    
    def _calculate_satellite_metrics(self, data: RemoteSensingData, metrics: ForestMetrics):
        """
        Calcule des métriques forestières à partir d'images satellite.
        
        Args:
            data: Données satellite traitées
            metrics: Objet de métriques à compléter
        """
        # Vérifier si des indices de végétation sont disponibles
        vegetation_indices = {}
        
        if isinstance(data.raster_data, dict):
            # Extraire les indices de végétation calculés
            for index_name in VegetationIndex.__members__:
                if index_name in data.raster_data:
                    # Calcul de la valeur moyenne de l'indice
                    index_data = data.raster_data[index_name]
                    valid_data = index_data[~np.isnan(index_data)]
                    if len(valid_data) > 0:
                        vegetation_indices[VegetationIndex[index_name]] = float(np.mean(valid_data))
            
            if vegetation_indices:
                metrics.vegetation_indices = vegetation_indices
                logger.info(f"Indices de végétation calculés: {', '.join(index.name for index in vegetation_indices.keys())}")
            
            # Calculer le pourcentage de couvert forestier à partir du NDVI
            if 'NDVI' in data.raster_data:
                ndvi = data.raster_data['NDVI']
                # Appliquer un seuil pour définir la végétation forestière (NDVI > 0.5)
                forest_mask = ndvi > 0.5
                # Calculer le pourcentage de pixels forestiers
                valid_pixels = ~np.isnan(ndvi)
                if np.sum(valid_pixels) > 0:
                    metrics.canopy_cover_percentage = 100 * np.sum(forest_mask) / np.sum(valid_pixels)
                    logger.info(f"Pourcentage de couvert forestier calculé: {metrics.canopy_cover_percentage:.2f}%")
            
            # Calculer les indicateurs de stress à partir de divers indices
            stress_indicators = {}
            
            # Indicateur basé sur NDVI - valeurs faibles indiquent un stress
            if 'NDVI' in data.raster_data:
                ndvi = data.raster_data['NDVI']
                valid_data = ndvi[~np.isnan(ndvi)]
                if len(valid_data) > 0:
                    # Proportion de végétation stressée (NDVI entre 0.2 et 0.5)
                    stress_mask = (valid_data > 0.2) & (valid_data < 0.5)
                    stress_indicators['ndvi_stress_percentage'] = 100 * np.sum(stress_mask) / len(valid_data)
            
            # Indicateur basé sur NDMI - valeurs faibles indiquent un stress hydrique
            if 'NDMI' in data.raster_data:
                ndmi = data.raster_data['NDMI']
                valid_data = ndmi[~np.isnan(ndmi)]
                if len(valid_data) > 0:
                    # Proportion de végétation en stress hydrique (NDMI < 0.1)
                    stress_mask = valid_data < 0.1
                    stress_indicators['moisture_stress_percentage'] = 100 * np.sum(stress_mask) / len(valid_data)
            
            if stress_indicators:
                metrics.stress_indicators = stress_indicators
                logger.info(f"Indicateurs de stress calculés: {', '.join(stress_indicators.keys())}")
            
            # Calculer les indices de diversité horizontale (hétérogénéité spatiale)
            if 'NDVI' in data.raster_data:
                ndvi = data.raster_data['NDVI']
                # Calculer l'écart-type local (fenêtre glissante)
                try:
                    from scipy.ndimage import generic_filter
                    std_filter = generic_filter(ndvi, np.std, size=5)
                    valid_std = std_filter[~np.isnan(std_filter)]
                    if len(valid_std) > 0:
                        metrics.horizontal_heterogeneity = float(np.mean(valid_std))
                        logger.info(f"Indice d'hétérogénéité horizontale calculé: {metrics.horizontal_heterogeneity:.4f}")
                except Exception as e:
                    logger.error(f"Erreur lors du calcul de l'hétérogénéité horizontale: {str(e)}")
    
    def _calculate_lidar_metrics(self, data: RemoteSensingData, metrics: ForestMetrics):
        """
        Calcule des métriques forestières à partir de données LIDAR.
        
        Args:
            data: Données LIDAR traitées
            metrics: Objet de métriques à compléter
        """
        if data.point_cloud_data is None or len(data.point_cloud_data) == 0:
            logger.warning("Aucune donnée de nuage de points disponible pour le calcul de métriques")
            return
        
        try:
            point_cloud_df = data.point_cloud_data
            
            # Filtrer les points de végétation (classes 3, 4, 5)
            veg_points = point_cloud_df[point_cloud_df['classification'].isin([3, 4, 5])]
            
            if len(veg_points) == 0:
                logger.warning("Aucun point de végétation identifié, impossible de calculer des métriques")
                return
            
            # Calculer des métriques de hauteur (si nous avons un modèle numérique de terrain)
            sol_points = point_cloud_df[point_cloud_df['classification'] == 2]
            
            if len(sol_points) > 0:
                # Calculer les hauteurs relatives par rapport au sol
                heights = self._calculate_relative_heights(point_cloud_df, sol_points)
                veg_heights = heights[heights > 0.5]  # Hauteurs de végétation > 0.5m
                
                if len(veg_heights) > 0:
                    # Métriques de hauteur de la canopée
                    metrics.canopy_height_mean = float(np.mean(veg_heights))
                    metrics.canopy_height_max = float(np.max(veg_heights))
                    metrics.canopy_height_std = float(np.std(veg_heights))
                    logger.info(f"Métriques de hauteur calculées: moy={metrics.canopy_height_mean:.2f}m, max={metrics.canopy_height_max:.2f}m")
                    
                    # Calculer l'indice de complexité verticale (diversité des hauteurs)
                    # Utiliser l'entropie de Shannon sur les classes de hauteur
                    height_bins = np.histogram(veg_heights, bins=10)[0]
                    if np.sum(height_bins) > 0:
                        height_probs = height_bins / np.sum(height_bins)
                        metrics.vertical_complexity = float(entropy(height_probs))
                        logger.info(f"Indice de complexité verticale calculé: {metrics.vertical_complexity:.4f}")
            
            # Calculer la densité de tiges (détection d'arbres individuels)
            try:
                tree_positions = self._detect_trees(point_cloud_df)
                if tree_positions:
                    metrics.tree_count = len(tree_positions)
                    metrics.tree_positions = tree_positions
                    
                    # Calculer la densité de tiges par hectare
                    # Calculer la superficie approximative en hectares
                    area_m2 = self._calculate_area(point_cloud_df)
                    area_ha = area_m2 / 10000.0
                    
                    if area_ha > 0:
                        metrics.stem_density = metrics.tree_count / area_ha
                        logger.info(f"Densité de tiges calculée: {metrics.stem_density:.1f} tiges/ha ({metrics.tree_count} arbres sur {area_ha:.2f} ha)")
            except Exception as e:
                logger.error(f"Erreur lors de la détection d'arbres: {str(e)}")
            
            # Estimation de la surface terrière et du volume
            if metrics.canopy_height_mean is not None and metrics.stem_density is not None:
                # Estimation simple de la surface terrière moyenne par hectare
                # Basée sur une relation avec la hauteur moyenne et la densité de tiges
                estimated_dbh = 0.1 * metrics.canopy_height_mean  # Estimation grossière du diamètre (m)
                estimated_basal_area = (np.pi * (estimated_dbh/2)**2) * metrics.stem_density
                metrics.basal_area = float(estimated_basal_area)
                
                # Estimation simple du volume de bois par hectare
                # Volume = Surface terrière * Hauteur moyenne * Facteur de forme
                form_factor = 0.5  # Facteur de forme moyen
                estimated_volume = metrics.basal_area * metrics.canopy_height_mean * form_factor
                metrics.volume = float(estimated_volume)
                
                logger.info(f"Surface terrière estimée: {metrics.basal_area:.2f} m²/ha")
                logger.info(f"Volume estimé: {metrics.volume:.2f} m³/ha")
            
            # Estimer la biomasse (approximation simple basée sur le volume)
            if metrics.volume is not None:
                # Densité moyenne du bois (t/m³) - valeur générique
                wood_density = 0.5
                metrics.biomass = float(metrics.volume * wood_density)
                logger.info(f"Biomasse estimée: {metrics.biomass:.2f} t/ha")
            
            # Densité du sous-étage
            if len(sol_points) > 0 and len(veg_points) > 0:
                # Proportion de points de végétation basse (classe 3)
                understory_points = point_cloud_df[point_cloud_df['classification'] == 3]
                metrics.understory_density = float(len(understory_points) / len(veg_points))
                logger.info(f"Densité du sous-étage calculée: {metrics.understory_density:.2f}")
                
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques LIDAR: {str(e)}")
    
    def _calculate_relative_heights(self, point_cloud_df: pd.DataFrame, 
                                   sol_points: pd.DataFrame) -> np.ndarray:
        """
        Calcule les hauteurs relatives des points par rapport au modèle numérique de terrain.
        
        Args:
            point_cloud_df: DataFrame de tous les points
            sol_points: DataFrame des points du sol
            
        Returns:
            Tableau des hauteurs relatives
        """
        try:
            from scipy.interpolate import griddata
            
            # Créer une grille pour interpolation
            grid_size = 1.0  # 1 mètre
            x_min, x_max = sol_points['x'].min(), sol_points['x'].max()
            y_min, y_max = sol_points['y'].min(), sol_points['y'].max()
            
            # Créer les grilles X et Y
            xi = np.arange(x_min, x_max + grid_size, grid_size)
            yi = np.arange(y_min, y_max + grid_size, grid_size)
            xi, yi = np.meshgrid(xi, yi)
            
            # Interpoler les hauteurs du sol
            z_sol = griddata(
                (sol_points['x'], sol_points['y']), sol_points['z'], 
                (xi, yi), method='linear'
            )
            
            # Initialiser le tableau des hauteurs relatives
            heights = np.zeros(len(point_cloud_df))
            
            # Pour chaque point, calculer la hauteur relative
            for i, (idx, point) in enumerate(point_cloud_df.iterrows()):
                # Trouver l'emplacement dans la grille
                if point['x'] < x_min or point['x'] > x_max or point['y'] < y_min or point['y'] > y_max:
                    heights[i] = 0.0  # Points hors de la zone d'interpolation
                    continue
                    
                ix = int((point['x'] - x_min) / grid_size)
                iy = int((point['y'] - y_min) / grid_size)
                
                # Vérifier les limites (pour la sécurité)
                ix = max(0, min(ix, xi.shape[1]-1))
                iy = max(0, min(iy, yi.shape[0]-1))
                
                # Si la valeur du sol est valide, calculer la hauteur relative
                if not np.isnan(z_sol[iy, ix]):
                    heights[i] = point['z'] - z_sol[iy, ix]
            
            return heights
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des hauteurs relatives: {str(e)}")
            return np.zeros(len(point_cloud_df))
    
    def _detect_trees(self, point_cloud_df: pd.DataFrame, 
                     min_height: float = 5.0) -> List[Tuple[float, float, float]]:
        """
        Détecte les arbres individuels dans un nuage de points.
        
        Args:
            point_cloud_df: DataFrame contenant les points
            min_height: Hauteur minimale pour considérer un groupe comme un arbre
            
        Returns:
            Liste des positions d'arbres (x, y, hauteur)
        """
        try:
            # Filtrer les points de végétation haute (classe 4-5)
            high_veg = point_cloud_df[point_cloud_df['classification'].isin([4, 5])]
            
            if len(high_veg) == 0:
                return []
            
            # Regrouper les points en utilisant DBSCAN
            coords = high_veg[['x', 'y']].values
            clustering = DBSCAN(eps=2.0, min_samples=5).fit(coords)
            
            # Assigner les labels de cluster
            high_veg['cluster'] = clustering.labels_
            
            # Identifier les sommets des arbres
            tree_positions = []
            for cluster_id in set(high_veg['cluster']):
                if cluster_id == -1:  # Ignorer les points considérés comme du bruit
                    continue
                    
                # Points dans ce cluster
                cluster_points = high_veg[high_veg['cluster'] == cluster_id]
                
                # Trouver le point le plus haut
                highest_point = cluster_points.loc[cluster_points['z'].idxmax()]
                
                # Vérifier la hauteur minimale
                if highest_point['z'] > min_height:
                    tree_positions.append(
                        (float(highest_point['x']), float(highest_point['y']), float(highest_point['z']))
                    )
            
            logger.info(f"{len(tree_positions)} arbres détectés")
            return tree_positions
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'arbres: {str(e)}")
            return []
    
    def _calculate_area(self, point_cloud_df: pd.DataFrame) -> float:
        """
        Calcule l'aire approximative couverte par le nuage de points en m².
        
        Args:
            point_cloud_df: DataFrame contenant les points
            
        Returns:
            Aire en m²
        """
        if len(point_cloud_df) == 0:
            return 0.0
        
        try:
            # Trouver les limites du nuage de points
            x_min, x_max = point_cloud_df['x'].min(), point_cloud_df['x'].max()
            y_min, y_max = point_cloud_df['y'].min(), point_cloud_df['y'].max()
            
            # Calculer l'aire
            area = (x_max - x_min) * (y_max - y_min)
            
            # Appliquer un facteur de correction pour les zones irrégulières
            # En réalité, une analyse plus précise nécessiterait un calcul d'enveloppe convexe
            correction_factor = 0.9  # Estimation grossière
            
            return area * correction_factor
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'aire: {str(e)}")
            return 0.0
    
    def compare_metrics(self, metrics1: ForestMetrics, metrics2: ForestMetrics) -> Dict[str, Any]:
        """
        Compare deux jeux de métriques forestières et calcule les évolutions.
        
        Args:
            metrics1: Premières métriques (typiquement les plus anciennes)
            metrics2: Secondes métriques (typiquement les plus récentes)
            
        Returns:
            Dictionnaire des évolutions calculées
        """
        comparison = {
            "parcel_id": metrics1.parcel_id,
            "date1": metrics1.date,
            "date2": metrics2.date,
            "time_difference_days": (metrics2.date - metrics1.date).days,
            "changes": {},
            "growth_rates": {}
        }
        
        # Comparer les métriques numériques et calculer les évolutions
        for attr in [
            "canopy_cover_percentage", "canopy_height_mean", "canopy_height_max",
            "stem_density", "basal_area", "volume", "biomass",
            "vertical_complexity", "horizontal_heterogeneity"
        ]:
            value1 = getattr(metrics1, attr)
            value2 = getattr(metrics2, attr)
            
            if value1 is not None and value2 is not None:
                # Calculer la différence absolue
                abs_change = value2 - value1
                comparison["changes"][attr] = abs_change
                
                # Calculer le taux de croissance (si applicable)
                if attr in ["canopy_height_mean", "canopy_height_max", "basal_area", "volume", "biomass"]:
                    time_years = comparison["time_difference_days"] / 365.25
                    if time_years > 0 and value1 > 0:
                        annual_growth_rate = abs_change / time_years
                        relative_growth_rate = 100 * annual_growth_rate / value1  # % par an
                        
                        comparison["growth_rates"][attr] = {
                            "annual_absolute": annual_growth_rate,
                            "annual_relative": relative_growth_rate
                        }
        
        # Comparer les indices de végétation (si disponibles)
        if metrics1.vegetation_indices and metrics2.vegetation_indices:
            comparison["vegetation_indices_changes"] = {}
            
            # Trouver les indices communs
            common_indices = set(metrics1.vegetation_indices.keys()) & set(metrics2.vegetation_indices.keys())
            
            for idx in common_indices:
                value1 = metrics1.vegetation_indices[idx]
                value2 = metrics2.vegetation_indices[idx]
                
                comparison["vegetation_indices_changes"][idx.name] = value2 - value1
        
        # Comparer les indicateurs de stress (si disponibles)
        if metrics1.stress_indicators and metrics2.stress_indicators:
            comparison["stress_indicators_changes"] = {}
            
            # Trouver les indicateurs communs
            common_indicators = set(metrics1.stress_indicators.keys()) & set(metrics2.stress_indicators.keys())
            
            for indicator in common_indicators:
                value1 = metrics1.stress_indicators[indicator]
                value2 = metrics2.stress_indicators[indicator]
                
                comparison["stress_indicators_changes"][indicator] = value2 - value1
        
        return comparison
    
    def calculate_growth_rate(self, metrics_list: List[ForestMetrics]) -> Dict[str, Any]:
        """
        Calcule le taux de croissance à partir d'une série temporelle de métriques.
        
        Args:
            metrics_list: Liste de métriques triées par date
            
        Returns:
            Taux de croissance et tendances calculés
        """
        if len(metrics_list) < 2:
            logger.warning("Au moins deux jeux de métriques sont nécessaires pour calculer un taux de croissance")
            return {}
        
        # Trier les métriques par date
        sorted_metrics = sorted(metrics_list, key=lambda x: x.date)
        
        # Initialiser le résultat
        growth_analysis = {
            "parcel_id": sorted_metrics[0].parcel_id,
            "start_date": sorted_metrics[0].date,
            "end_date": sorted_metrics[-1].date,
            "total_period_years": (sorted_metrics[-1].date - sorted_metrics[0].date).days / 365.25,
            "height_growth": {},
            "volume_growth": {},
            "biomass_growth": {},
            "trends": {}
        }
        
        # Extraire les séries temporelles pour les métriques clés
        time_points = [(m.date - sorted_metrics[0].date).days / 365.25 for m in sorted_metrics]
        height_values = [m.canopy_height_mean for m in sorted_metrics if m.canopy_height_mean is not None]
        height_times = time_points[:len(height_values)]
        
        volume_values = [m.volume for m in sorted_metrics if m.volume is not None]
        volume_times = time_points[:len(volume_values)]
        
        biomass_values = [m.biomass for m in sorted_metrics if m.biomass is not None]
        biomass_times = time_points[:len(biomass_values)]
        
        # Calculer les taux de croissance si suffisamment de points
        if len(height_values) >= 2:
            growth_analysis["height_growth"]["total_change"] = height_values[-1] - height_values[0]
            growth_analysis["height_growth"]["average_annual_rate"] = growth_analysis["height_growth"]["total_change"] / growth_analysis["total_period_years"]
            
            # Calculer la tendance (régression linéaire)
            if len(height_values) >= 3:
                slope, intercept = np.polyfit(height_times, height_values, 1)
                growth_analysis["trends"]["height_slope"] = float(slope)
                growth_analysis["trends"]["height_r2"] = float(np.corrcoef(height_times, height_values)[0, 1] ** 2)
        
        if len(volume_values) >= 2:
            growth_analysis["volume_growth"]["total_change"] = volume_values[-1] - volume_values[0]
            growth_analysis["volume_growth"]["average_annual_rate"] = growth_analysis["volume_growth"]["total_change"] / growth_analysis["total_period_years"]
            
            # Calculer la tendance (régression linéaire)
            if len(volume_values) >= 3:
                slope, intercept = np.polyfit(volume_times, volume_values, 1)
                growth_analysis["trends"]["volume_slope"] = float(slope)
                growth_analysis["trends"]["volume_r2"] = float(np.corrcoef(volume_times, volume_values)[0, 1] ** 2)
        
        if len(biomass_values) >= 2:
            growth_analysis["biomass_growth"]["total_change"] = biomass_values[-1] - biomass_values[0]
            growth_analysis["biomass_growth"]["average_annual_rate"] = growth_analysis["biomass_growth"]["total_change"] / growth_analysis["total_period_years"]
            
            # Calculer la tendance (régression linéaire)
            if len(biomass_values) >= 3:
                slope, intercept = np.polyfit(biomass_times, biomass_values, 1)
                growth_analysis["trends"]["biomass_slope"] = float(slope)
                growth_analysis["trends"]["biomass_r2"] = float(np.corrcoef(biomass_times, biomass_values)[0, 1] ** 2)
        
        return growth_analysis
