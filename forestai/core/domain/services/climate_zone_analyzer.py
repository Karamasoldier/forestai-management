"""
Module d'analyse des zones climatiques.

S'occupe d'identifier la zone climatique correspondant à une géométrie donnée.
"""

import logging
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, Union
from shapely.geometry import Polygon, Point, shape

class ClimateZoneAnalyzer:
    """
    Analyseur de zones climatiques pour les géométries.
    
    Fonctionnalités:
    - Conversion et normalisation des géométries
    - Identification des zones climatiques par intersection spatiale
    - Calcul des distances aux zones climatiques pour les points hors zones
    """
    
    def __init__(self, climate_zones: gpd.GeoDataFrame):
        """
        Initialise l'analyseur de zones climatiques.
        
        Args:
            climate_zones: GeoDataFrame contenant les zones climatiques
        """
        self.logger = logging.getLogger(__name__)
        self.climate_zones = climate_zones
    
    def get_climate_zone(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon, Point]) -> Dict[str, Any]:
        """
        Identifie la zone climatique correspondant à une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON, GeoDataFrame, Polygon ou Point)
            
        Returns:
            Dictionnaire contenant les informations de la zone climatique
        """
        try:
            # Conversion de la géométrie en objet shapely
            geom = self._convert_to_shapely(geometry)
            
            # Conversion en point si nécessaire (centroïde pour les polygones)
            point = self._convert_to_point(geom)
            
            # Création d'un GeoDataFrame avec le point
            point_gdf = gpd.GeoDataFrame(geometry=[point], crs=self.climate_zones.crs)
            
            # Recherche de la zone climatique par intersection spatiale
            zone_data = self._find_climate_zone(point_gdf)
            
            return zone_data
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de la zone climatique: {str(e)}")
            return {
                'id': None,
                'name': "Inconnu",
                'climate_type': "Inconnu",
                'exact_match': False,
                'error': str(e)
            }
    
    def _convert_to_shapely(self, geometry):
        """
        Convertit une géométrie en objet shapely.
        
        Args:
            geometry: Géométrie à convertir (dict, GeoDataFrame, Polygon, Point)
            
        Returns:
            Objet géométrique shapely
        """
        if isinstance(geometry, dict):
            return shape(geometry)
        elif isinstance(geometry, gpd.GeoDataFrame):
            return geometry.geometry.iloc[0]
        else:
            return geometry
    
    def _convert_to_point(self, geom):
        """
        Convertit une géométrie en point (utilise le centroïde pour les polygones).
        
        Args:
            geom: Géométrie à convertir
            
        Returns:
            Point
        """
        if isinstance(geom, Polygon):
            return geom.centroid
        elif isinstance(geom, Point):
            return geom
        else:
            return geom.centroid
    
    def _find_climate_zone(self, point_gdf):
        """
        Trouve la zone climatique par intersection spatiale.
        
        Args:
            point_gdf: GeoDataFrame contenant le point à localiser
            
        Returns:
            Dictionnaire avec les données de la zone climatique
        """
        # Recherche de la zone climatique par intersection spatiale
        joined = gpd.sjoin(point_gdf, self.climate_zones, predicate='within', how='left')
        
        if joined.empty or pd.isna(joined.iloc[0]['id']):
            # Si pas d'intersection, trouver la zone la plus proche
            self.logger.warning("Point hors des zones climatiques connues, recherche de la zone la plus proche")
            return self._find_nearest_zone(point_gdf.geometry.iloc[0])
        else:
            # Prendre les données de la zone trouvée
            zone_data = joined.iloc[0].to_dict()
            zone_data['exact_match'] = True
            zone_data['distance_m'] = 0.0
            
            return zone_data
    
    def _find_nearest_zone(self, point):
        """
        Trouve la zone climatique la plus proche d'un point.
        
        Args:
            point: Point à localiser
            
        Returns:
            Dictionnaire avec les données de la zone climatique la plus proche
        """
        # Calculer la distance à chaque zone
        distances = self.climate_zones.distance(point)
        nearest_idx = distances.idxmin()
        zone_data = self.climate_zones.iloc[nearest_idx].to_dict()
        
        # Ajouter des informations sur la distance
        zone_data['exact_match'] = False
        zone_data['distance_m'] = float(distances.iloc[nearest_idx])
        
        return zone_data
