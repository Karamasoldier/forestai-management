"""
Module d'analyse des zones climatiques.

Ce module est responsable de l'identification des zones climatiques
correspondant à une géométrie donnée.
"""

import logging
from typing import Dict, Any, Union, Optional, List
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point, shape

class ClimateZoneAnalyzer:
    """
    Analyseur de zones climatiques.
    
    Responsabilités:
    - Identifier la zone climatique correspondant à une géométrie
    - Fournir des informations sur les caractéristiques climatiques de la zone
    """
    
    def __init__(self, climate_zones: gpd.GeoDataFrame):
        """
        Initialise l'analyseur de zones climatiques.
        
        Args:
            climate_zones: GeoDataFrame contenant les zones climatiques
        """
        self.logger = logging.getLogger(__name__)
        self.climate_zones = climate_zones
        
        # Vérifier que les zones climatiques ont un CRS valide
        if self.climate_zones.crs is None:
            self.logger.warning("Les zones climatiques n'ont pas de CRS défini, utilisation de EPSG:2154 (Lambert 93)")
            self.climate_zones.set_crs("EPSG:2154", inplace=True)
        
        self.logger.info(f"ClimateZoneAnalyzer initialisé avec {len(climate_zones)} zones climatiques")
    
    def get_climate_zone(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon, Point]) -> Dict[str, Any]:
        """
        Identifie la zone climatique qui contient la géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON, GeoDataFrame, Polygon ou Point)
            
        Returns:
            Dictionnaire contenant les informations de la zone climatique identifiée
            Retourne un dictionnaire vide si aucune zone ne correspond
        """
        try:
            # Convertir la géométrie en format standardisé
            geom = self._standardize_geometry(geometry)
            
            if geom is None:
                self.logger.error("Impossible de standardiser la géométrie fournie")
                return {}
            
            # Trouver la zone climatique qui contient ce point ou cette géométrie
            # Pour une géométrie complexe (polygone), on utilise le centroïde
            if isinstance(geom, Polygon):
                point = geom.centroid
                self.logger.info(f"Utilisation du centroïde ({point.x:.1f}, {point.y:.1f}) pour l'identification de la zone")
            else:
                point = geom
            
            # Recherche de la zone climatique
            zone_index = self.climate_zones.sindex.query(point, predicate="contains")
            
            if len(zone_index) == 0:
                # Si aucune correspondance exacte, trouver la zone la plus proche
                self.logger.info("Aucune zone ne contient directement la géométrie, recherche de la zone la plus proche")
                distances = self.climate_zones.geometry.distance(point)
                closest_idx = distances.idxmin()
                
                zone = self.climate_zones.iloc[closest_idx]
                result = self._zone_to_dict(zone)
                result["distance"] = distances.min()
                result["exact_match"] = False
                
                self.logger.info(f"Zone la plus proche identifiée: {result['name']} (distance: {result['distance']:.1f}m)")
                return result
            else:
                # Zone correspondante trouvée
                zone = self.climate_zones.iloc[zone_index[0]]
                result = self._zone_to_dict(zone)
                result["exact_match"] = True
                
                self.logger.info(f"Zone climatique identifiée: {result['name']}")
                return result
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'identification de la zone climatique: {str(e)}")
            return {}
    
    def get_all_zones(self) -> List[Dict[str, Any]]:
        """
        Retourne toutes les zones climatiques disponibles.
        
        Returns:
            Liste des zones climatiques avec leurs informations
        """
        zones = []
        for _, row in self.climate_zones.iterrows():
            zones.append(self._zone_to_dict(row))
        
        return zones
    
    def get_zone_by_id(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """
        Recherche une zone climatique par son identifiant.
        
        Args:
            zone_id: Identifiant de la zone climatique
            
        Returns:
            Informations sur la zone climatique ou None si non trouvée
        """
        try:
            zone = self.climate_zones[self.climate_zones["id"] == zone_id]
            if len(zone) == 0:
                self.logger.warning(f"Aucune zone climatique trouvée avec l'ID '{zone_id}'")
                return None
            
            return self._zone_to_dict(zone.iloc[0])
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de la zone '{zone_id}': {str(e)}")
            return None
    
    def get_zones_in_bounds(self, bbox: List[float]) -> List[Dict[str, Any]]:
        """
        Récupère les zones climatiques dans une boîte englobante.
        
        Args:
            bbox: Boîte englobante [minx, miny, maxx, maxy]
            
        Returns:
            Liste des zones climatiques dans la boîte englobante
        """
        try:
            # Créer la géométrie de la boîte englobante
            minx, miny, maxx, maxy = bbox
            box = Polygon([
                (minx, miny), (maxx, miny),
                (maxx, maxy), (minx, maxy),
                (minx, miny)
            ])
            
            # Sélectionner les zones qui intersectent la boîte
            intersecting = self.climate_zones[self.climate_zones.intersects(box)]
            
            zones = []
            for _, row in intersecting.iterrows():
                zones.append(self._zone_to_dict(row))
            
            self.logger.info(f"Trouvé {len(zones)} zones climatiques dans la boîte englobante")
            return zones
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de zones dans la boîte englobante: {str(e)}")
            return []
    
    def _standardize_geometry(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon, Point]) -> Optional[Union[Polygon, Point]]:
        """
        Standardise la géométrie fournie en entrée.
        
        Args:
            geometry: Géométrie à standardiser (GeoJSON, GeoDataFrame, Polygon ou Point)
            
        Returns:
            Géométrie standardisée (Polygon ou Point)
        """
        try:
            if isinstance(geometry, dict):
                # GeoJSON
                return shape(geometry)
            
            elif isinstance(geometry, gpd.GeoDataFrame):
                # GeoDataFrame
                if len(geometry) == 0:
                    self.logger.error("GeoDataFrame vide")
                    return None
                return geometry.geometry.iloc[0]
            
            elif isinstance(geometry, (Polygon, Point)):
                # Déjà en format shapely
                return geometry
            
            else:
                self.logger.error(f"Format de géométrie non pris en charge: {type(geometry)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur de standardisation de la géométrie: {str(e)}")
            return None
    
    def _zone_to_dict(self, zone: gpd.GeoSeries) -> Dict[str, Any]:
        """
        Convertit une ligne de GeoDataFrame en dictionnaire.
        
        Args:
            zone: Ligne du GeoDataFrame représentant une zone climatique
            
        Returns:
            Dictionnaire avec les informations de la zone climatique
        """
        # Convertir toutes les propriétés de la zone en dictionnaire
        result = {}
        for col in self.climate_zones.columns:
            if col != "geometry":  # Exclure la géométrie
                result[col] = zone[col]
        
        return result
