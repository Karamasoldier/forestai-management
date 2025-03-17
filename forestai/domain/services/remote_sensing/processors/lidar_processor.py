#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Processeur de données LIDAR pour l'analyse forestière.

Ce module fournit des fonctionnalités pour traiter les données LIDAR
(nuages de points) en préparation pour l'analyse forestière.
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging

import geopandas as gpd
from scipy.interpolate import griddata

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.remote_sensing.models import (
    RemoteSensingData,
    RemoteSensingSource,
    LidarPointCloudMetadata
)
from forestai.domain.services.remote_sensing.processors.base_processor import BaseDataProcessor

logger = get_logger(__name__)


class LidarDataProcessor(BaseDataProcessor):
    """Processeur de données LIDAR pour l'analyse forestière."""
    
    def process(self, data: RemoteSensingData,
               aoi: Optional[Union[gpd.GeoDataFrame, Dict[str, Any]]] = None,
               classify_points: bool = False,
               filter_noise: bool = True,
               reproject_to_epsg: Optional[int] = None,
               **kwargs) -> RemoteSensingData:
        """
        Traite des données LIDAR pour l'analyse forestière.
        
        Args:
            data: Données de télédétection à traiter
            aoi: Zone d'intérêt pour découper les données (GeoDataFrame ou GeoJSON)
            classify_points: Si True, classifie les points LIDAR (sol, végétation, etc.)
            filter_noise: Si True, filtre les points aberrants
            reproject_to_epsg: Code EPSG pour la reprojection (optionnel)
            
        Returns:
            Données de télédétection traitées
        """
        if data.point_cloud_path is None:
            logger.error("Aucun chemin de nuage de points défini dans les données")
            return data
        
        if not data.point_cloud_path.exists():
            logger.error(f"Le fichier de nuage de points n'existe pas: {data.point_cloud_path}")
            return data
        
        try:
            # Importer les bibliothèques LIDAR
            try:
                import laspy
                import pylas
            except ImportError:
                logger.error("Les bibliothèques laspy et pylas sont requises pour traiter les données LIDAR")
                return data
            
            # Vérifier que c'est bien des données LIDAR
            is_lidar = (RemoteSensingSource.LIDAR_AERIEN <= data.source <= RemoteSensingSource.LIDAR_DRONE)
            if not is_lidar:
                logger.warning(f"Source inattendue pour des données LIDAR: {data.source}")
            
            # Lire le fichier LAS/LAZ
            las = laspy.read(data.point_cloud_path)
            
            # Convertir en DataFrame pour faciliter le traitement
            point_cloud_df = self._las_to_dataframe(las)
            
            # Appliquer les traitements
            point_cloud_df = self._clip_to_aoi(point_cloud_df, aoi, las, data.lidar_metadata)
            
            if filter_noise:
                point_cloud_df = self._filter_noise(point_cloud_df)
            
            point_cloud_df = self._reproject(point_cloud_df, reproject_to_epsg, las, data.lidar_metadata)
            
            if classify_points:
                point_cloud_df = self._classify_points(point_cloud_df)
            
            # Créer un nouveau RemoteSensingData avec les données traitées
            return self._create_processed_data(data, point_cloud_df)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données LIDAR: {str(e)}")
            return data
    
    def _las_to_dataframe(self, las) -> pd.DataFrame:
        """
        Convertit un objet LAS en DataFrame pandas.
        
        Args:
            las: Objet LAS/LAZ chargé
            
        Returns:
            DataFrame contenant les points du nuage
        """
        # Extraire les attributs de base
        point_cloud_df = pd.DataFrame({
            'x': las.x,
            'y': las.y,
            'z': las.z,
            'intensity': las.intensity if hasattr(las, 'intensity') else np.zeros_like(las.x),
            'return_number': las.return_number if hasattr(las, 'return_number') else np.ones_like(las.x),
            'number_of_returns': las.number_of_returns if hasattr(las, 'number_of_returns') else np.ones_like(las.x),
            'classification': las.classification if hasattr(las, 'classification') else np.zeros_like(las.x)
        })
        
        # Ajouter d'autres attributs si disponibles
        if hasattr(las, 'scan_angle_rank'):
            point_cloud_df['scan_angle_rank'] = las.scan_angle_rank
        
        if hasattr(las, 'scan_angle'):
            point_cloud_df['scan_angle'] = las.scan_angle
            
        if hasattr(las, 'user_data'):
            point_cloud_df['user_data'] = las.user_data
            
        return point_cloud_df
    
    def _clip_to_aoi(self, point_cloud_df: pd.DataFrame, 
                   aoi: Optional[Union[gpd.GeoDataFrame, Dict[str, Any]]],
                   las, metadata: Optional[LidarPointCloudMetadata]) -> pd.DataFrame:
        """
        Découpe le nuage de points selon une zone d'intérêt.
        
        Args:
            point_cloud_df: DataFrame contenant les points
            aoi: Zone d'intérêt
            las: Objet LAS d'origine (pour les métadonnées)
            metadata: Métadonnées LIDAR
            
        Returns:
            DataFrame filtré
        """
        if aoi is None:
            return point_cloud_df
        
        try:
            # Convertir en GeoDataFrame
            point_gdf = gpd.GeoDataFrame(
                point_cloud_df,
                geometry=gpd.points_from_xy(point_cloud_df.x, point_cloud_df.y)
            )
            
            # Configurer la projection
            if hasattr(las, 'header') and hasattr(las.header, 'srs') and las.header.srs:
                point_gdf.crs = las.header.srs
            elif metadata and metadata.epsg_code:
                point_gdf.crs = f"EPSG:{metadata.epsg_code}"
            else:
                logger.warning("Impossible de déterminer la projection du nuage de points")
                return point_cloud_df
            
            # Convertir AOI en GeoDataFrame si nécessaire
            if not isinstance(aoi, gpd.GeoDataFrame):
                if isinstance(aoi, dict):  # GeoJSON
                    aoi_gdf = gpd.GeoDataFrame.from_features([aoi])
                else:
                    logger.error("Format AOI non supporté")
                    return point_cloud_df
            else:
                aoi_gdf = aoi
            
            # Assurer que les deux GeoDataFrames ont la même projection
            if point_gdf.crs and aoi_gdf.crs and point_gdf.crs != aoi_gdf.crs:
                aoi_gdf = aoi_gdf.to_crs(point_gdf.crs)
            
            # Filtrer les points à l'intérieur de l'AOI
            point_gdf = gpd.sjoin(point_gdf, aoi_gdf, predicate='within')
            
            # Reconvertir en DataFrame
            return point_gdf.drop(columns=['geometry', 'index_right'])
        
        except Exception as e:
            logger.error(f"Erreur lors du découpage selon l'AOI: {str(e)}")
            return point_cloud_df
    
    def _filter_noise(self, point_cloud_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtre les points aberrants du nuage de points.
        
        Args:
            point_cloud_df: DataFrame contenant les points
            
        Returns:
            DataFrame filtré
        """
        if len(point_cloud_df) == 0:
            return point_cloud_df
        
        initial_count = len(point_cloud_df)
        
        # Méthode simple: éliminer les points avec une hauteur aberrante
        z_mean = point_cloud_df['z'].mean()
        z_std = point_cloud_df['z'].std()
        
        # Filtrer les points au-delà de 3 écarts-types
        filtered_df = point_cloud_df[(point_cloud_df['z'] > z_mean - 3*z_std) & 
                                    (point_cloud_df['z'] < z_mean + 3*z_std)]
        
        # Si le filtrage a retiré trop de points, revenir à l'original
        if len(filtered_df) < initial_count * 0.5:
            logger.warning(f"Le filtrage du bruit a retiré plus de 50% des points, annulation")
            return point_cloud_df
        
        logger.info(f"{initial_count - len(filtered_df)} points de bruit filtrés sur {initial_count}")
        return filtered_df
    
    def _reproject(self, point_cloud_df: pd.DataFrame, reproject_to_epsg: Optional[int],
                 las, metadata: Optional[LidarPointCloudMetadata]) -> pd.DataFrame:
        """
        Reprojette le nuage de points vers un autre système de coordonnées.
        
        Args:
            point_cloud_df: DataFrame contenant les points
            reproject_to_epsg: Code EPSG cible
            las: Objet LAS d'origine (pour les métadonnées)
            metadata: Métadonnées LIDAR
            
        Returns:
            DataFrame reprojeté
        """
        if reproject_to_epsg is None or len(point_cloud_df) == 0:
            return point_cloud_df
        
        current_epsg = None
        
        # Obtenir le code EPSG actuel
        if hasattr(las, 'header') and hasattr(las.header, 'srs') and las.header.srs:
            current_epsg = las.header.srs.to_epsg()
        elif metadata and metadata.epsg_code:
            current_epsg = metadata.epsg_code
        
        if current_epsg is None:
            logger.warning("Impossible de déterminer la projection actuelle, reprojection impossible")
            return point_cloud_df
        
        if current_epsg == reproject_to_epsg:
            return point_cloud_df
        
        try:
            # Créer un GeoDataFrame pour la reprojection
            temp_gdf = gpd.GeoDataFrame(
                point_cloud_df,
                geometry=gpd.points_from_xy(point_cloud_df.x, point_cloud_df.y),
                crs=f"EPSG:{current_epsg}"
            )
            
            # Reprojeter
            temp_gdf = temp_gdf.to_crs(f"EPSG:{reproject_to_epsg}")
            
            # Mettre à jour les coordonnées
            reprojected_df = point_cloud_df.copy()
            reprojected_df['x'] = temp_gdf.geometry.x
            reprojected_df['y'] = temp_gdf.geometry.y
            
            logger.info(f"Nuage de points reprojeté de EPSG:{current_epsg} vers EPSG:{reproject_to_epsg}")
            return reprojected_df
        
        except Exception as e:
            logger.error(f"Erreur lors de la reprojection: {str(e)}")
            return point_cloud_df
    
    def _classify_points(self, point_cloud_df: pd.DataFrame) -> pd.DataFrame:
        """
        Classifie les points LIDAR (sol, végétation, etc.).
        
        Args:
            point_cloud_df: DataFrame contenant les points
            
        Returns:
            DataFrame avec points classifiés
        """
        if len(point_cloud_df) == 0:
            return point_cloud_df
        
        # Vérifier si la classification existe déjà
        if 'classification' in point_cloud_df and point_cloud_df['classification'].max() > 1:
            logger.info("Les points sont déjà classifiés, conservation des classes existantes")
            return point_cloud_df
        
        # Copier le DataFrame pour ne pas modifier l'original
        classified_df = point_cloud_df.copy()
        
        # Initialiser tous les points comme non classifiés (classe 1)
        classified_df['classification'] = 1
        
        # Identifier les points potentiels de sol (dernier retour)
        sol_candidats = classified_df[classified_df['return_number'] == classified_df['number_of_returns']]
        
        if len(sol_candidats) == 0:
            logger.warning("Impossible d'identifier des candidats pour les points de sol")
            return classified_df
        
        try:
            # Utiliser un algorithme de grille pour la détection du sol
            grid_size = 5  # mètres
            x_min, x_max = sol_candidats['x'].min(), sol_candidats['x'].max()
            y_min, y_max = sol_candidats['y'].min(), sol_candidats['y'].max()
            
            # Créer les grilles
            x_grid = np.arange(x_min, x_max + grid_size, grid_size)
            y_grid = np.arange(y_min, y_max + grid_size, grid_size)
            
            # Pour chaque cellule de la grille, trouver le point le plus bas
            sol_points = []
            for i in range(len(x_grid)-1):
                for j in range(len(y_grid)-1):
                    cell_points = sol_candidats[
                        (sol_candidats['x'] >= x_grid[i]) & (sol_candidats['x'] < x_grid[i+1]) &
                        (sol_candidats['y'] >= y_grid[j]) & (sol_candidats['y'] < y_grid[j+1])
                    ]
                    if len(cell_points) > 0:
                        lowest_idx = cell_points['z'].idxmin()
                        sol_points.append(lowest_idx)
            
            # Marquer les points de sol (classe 2)
            classified_df.loc[sol_points, 'classification'] = 2
            
            # Construire un MNT simple par interpolation
            pts_sol = classified_df[classified_df['classification'] == 2]
            
            if len(pts_sol) >= 3:  # Minimum pour l'interpolation
                # Créer une grille pour l'interpolation
                xi = np.linspace(x_min, x_max, int((x_max - x_min) / grid_size) + 1)
                yi = np.linspace(y_min, y_max, int((y_max - y_min) / grid_size) + 1)
                xi, yi = np.meshgrid(xi, yi)
                
                # Interpoler la hauteur du sol
                z_sol = griddata(
                    (pts_sol['x'], pts_sol['y']), pts_sol['z'], 
                    (xi, yi), method='linear'
                )
                
                # Classifier les points en fonction de leur hauteur relative
                for idx, point in classified_df.iterrows():
                    if point['classification'] != 2:  # Ne pas reclassifier les points de sol
                        # Trouver la position dans la grille
                        ix = np.clip(int((point['x'] - x_min) / grid_size), 0, xi.shape[1] - 1)
                        iy = np.clip(int((point['y'] - y_min) / grid_size), 0, yi.shape[0] - 1)
                        
                        # Si nous avons une valeur de sol à cette position
                        if not np.isnan(z_sol[iy, ix]):
                            hauteur_relative = point['z'] - z_sol[iy, ix]
                            
                            # Classifier en fonction de la hauteur relative
                            if hauteur_relative < 0.5:
                                classified_df.loc[idx, 'classification'] = 2  # Sol
                            elif hauteur_relative < 3.0:
                                classified_df.loc[idx, 'classification'] = 3  # Végétation basse
                            elif hauteur_relative < 15.0:
                                classified_df.loc[idx, 'classification'] = 4  # Végétation moyenne
                            else:
                                classified_df.loc[idx, 'classification'] = 5  # Végétation haute
            
            # Ajouter une classification spéciale pour les points isolés (potentiellement du bruit)
            classified_df = self._identify_isolated_points(classified_df)
            
            logger.info(f"Classification terminée: {len(classified_df[classified_df['classification'] == 2])} points de sol, "
                       f"{len(classified_df[classified_df['classification'] == 3])} points de végétation basse, "
                       f"{len(classified_df[classified_df['classification'] == 4])} points de végétation moyenne, "
                       f"{len(classified_df[classified_df['classification'] == 5])} points de végétation haute")
            
            return classified_df
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {str(e)}")
            return point_cloud_df
    
    def _identify_isolated_points(self, point_cloud_df: pd.DataFrame, radius: float = 1.0, 
                                min_neighbors: int = 3) -> pd.DataFrame:
        """
        Identifie les points isolés qui pourraient être du bruit.
        
        Args:
            point_cloud_df: DataFrame contenant les points
            radius: Rayon de recherche des voisins
            min_neighbors: Nombre minimum de voisins pour ne pas être isolé
            
        Returns:
            DataFrame avec identification des points isolés
        """
        try:
            from sklearn.neighbors import BallTree
            
            # Créer un BallTree pour la recherche de voisins efficace
            coords = point_cloud_df[['x', 'y', 'z']].values
            tree = BallTree(coords, leaf_size=40)
            
            # Pour chaque point, compter les voisins dans le rayon
            indices = tree.query_radius(coords, r=radius)
            neighbors_count = np.array([len(idx) - 1 for idx in indices])  # -1 car le point lui-même est inclus
            
            # Marquer les points isolés (classe 7 - noise)
            isolated_mask = neighbors_count < min_neighbors
            point_cloud_df.loc[isolated_mask, 'classification'] = 7
            
            logger.info(f"Points isolés identifiés: {isolated_mask.sum()}")
            
        except ImportError:
            logger.warning("sklearn non disponible, l'identification des points isolés est ignorée")
        except Exception as e:
            logger.error(f"Erreur lors de l'identification des points isolés: {str(e)}")
        
        return point_cloud_df
