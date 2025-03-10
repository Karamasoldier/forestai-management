# forestai/core/utils/geo_utils.py

import logging
import geopandas as gpd
import numpy as np
from pyproj import CRS
from shapely.geometry import Point, Polygon, MultiPolygon
from typing import Dict, Any, Union, List, Tuple

logger = logging.getLogger(__name__)

# Constantes pour les systèmes de coordonnées
LAMBERT_93 = CRS.from_epsg(2154)  # Lambert 93 (France métropolitaine)
WGS84 = CRS.from_epsg(4326)       # WGS84 (coordonnées GPS)
WEBMERCATOR = CRS.from_epsg(3857) # Web Mercator (Google Maps, etc.)

def reproject_geometry(
    geometry,
    source_crs: Union[CRS, str, int],
    target_crs: Union[CRS, str, int] = WGS84
) -> Union[Point, Polygon, MultiPolygon]:
    """
    Reprojette une géométrie d'un système de coordonnées à un autre.
    
    Args:
        geometry: Géométrie Shapely à reprojeter
        source_crs: Système de coordonnées source
        target_crs: Système de coordonnées cible (WGS84 par défaut)
        
    Returns:
        Géométrie reprojetée
    """
    try:
        # Créer un GeoDataFrame temporaire
        gdf = gpd.GeoDataFrame(geometry=[geometry], crs=source_crs)
        
        # Reprojeter vers le CRS cible
        gdf_reprojected = gdf.to_crs(target_crs)
        
        # Retourner la géométrie reprojetée
        return gdf_reprojected.geometry.iloc[0]
    
    except Exception as e:
        logger.error(f"Erreur lors de la reprojection: {e}")
        return geometry  # Retourner la géométrie d'origine en cas d'erreur

def calculate_area_ha(geometry, crs: Union[CRS, str, int] = None) -> float:
    """
    Calcule la surface en hectares d'une géométrie.
    
    Args:
        geometry: Géométrie Shapely
        crs: Système de coordonnées de la géométrie
        
    Returns:
        Surface en hectares
    """
    try:
        # Si un CRS est fourni et qu'il n'est pas projeté, reprojeter
        if crs:
            crs_obj = CRS.from_user_input(crs)
            if not crs_obj.is_projected:
                # Reprojeter vers Lambert 93 pour la France
                geometry = reproject_geometry(geometry, crs, LAMBERT_93)
                
        # Calculer la surface en m²
        area_m2 = geometry.area
        
        # Convertir en hectares
        return area_m2 / 10000
    
    except Exception as e:
        logger.error(f"Erreur lors du calcul de surface: {e}")
        return 0.0

def buffer_geometry(
    geometry,
    distance_m: float,
    crs: Union[CRS, str, int] = None
) -> Union[Point, Polygon, MultiPolygon]:
    """
    Crée une zone tampon autour d'une géométrie.
    
    Args:
        geometry: Géométrie Shapely
        distance_m: Distance de la zone tampon en mètres
        crs: Système de coordonnées de la géométrie
        
    Returns:
        Géométrie avec zone tampon
    """
    try:
        # Si un CRS est fourni et qu'il n'est pas projeté, reprojeter
        if crs:
            crs_obj = CRS.from_user_input(crs)
            if not crs_obj.is_projected:
                # Reprojeter vers un CRS projeté pour une zone tampon précise
                projected_geom = reproject_geometry(geometry, crs, LAMBERT_93)
                
                # Créer la zone tampon
                buffered = projected_geom.buffer(distance_m)
                
                # Reprojeter vers le CRS d'origine
                return reproject_geometry(buffered, LAMBERT_93, crs)
        
        # Si pas de CRS ou déjà projeté, créer directement la zone tampon
        return geometry.buffer(distance_m)
    
    except Exception as e:
        logger.error(f"Erreur lors de la création de zone tampon: {e}")
        return geometry  # Retourner la géométrie d'origine en cas d'erreur

def create_grid(
    bbox: Tuple[float, float, float, float],
    cell_size_m: float,
    crs: Union[CRS, str, int] = LAMBERT_93
) -> gpd.GeoDataFrame:
    """
    Crée une grille régulière à partir d'une boîte englobante.
    
    Args:
        bbox: Tuple (minx, miny, maxx, maxy) définissant la boîte englobante
        cell_size_m: Taille de cellule en mètres
        crs: Système de coordonnées (doit être projeté)
        
    Returns:
        GeoDataFrame contenant les cellules de la grille
    """
    try:
        # S'assurer que le CRS est projeté
        crs_obj = CRS.from_user_input(crs)
        if not crs_obj.is_projected:
            logger.warning("CRS non projeté fourni pour create_grid, utilisation de Lambert 93")
            crs = LAMBERT_93
        
        minx, miny, maxx, maxy = bbox
        
        # Créer les coordonnées de grille
        x_coords = list(range(int(minx), int(maxx), int(cell_size_m)))
        y_coords = list(range(int(miny), int(maxy), int(cell_size_m)))
        
        # Créer les polygones de cellules
        cells = []
        for x in x_coords:
            for y in y_coords:
                cells.append(Polygon([
                    (x, y),
                    (x + cell_size_m, y),
                    (x + cell_size_m, y + cell_size_m),
                    (x, y + cell_size_m),
                    (x, y)
                ]))
        
        # Créer le GeoDataFrame
        grid_gdf = gpd.GeoDataFrame(geometry=cells, crs=crs)
        
        # Ajouter des identifiants
        grid_gdf["cell_id"] = range(len(grid_gdf))
        
        return grid_gdf
    
    except Exception as e:
        logger.error(f"Erreur lors de la création de grille: {e}")
        return gpd.GeoDataFrame(geometry=[], crs=crs)  # Retourner un GDF vide

def get_bbox_from_geometry(
    geometry,
    buffer_pct: float = 0.1
) -> Tuple[float, float, float, float]:
    """
    Récupère la boîte englobante d'une géométrie avec une marge optionnelle.
    
    Args:
        geometry: Géométrie Shapely
        buffer_pct: Pourcentage de marge à ajouter (0.1 = 10%)
        
    Returns:
        Tuple (minx, miny, maxx, maxy)
    """
    try:
        # Obtenir les bounds
        minx, miny, maxx, maxy = geometry.bounds
        
        # Calculer le buffer
        width = maxx - minx
        height = maxy - miny
        
        buffer_x = width * buffer_pct
        buffer_y = height * buffer_pct
        
        # Appliquer le buffer
        return (
            minx - buffer_x,
            miny - buffer_y,
            maxx + buffer_x,
            maxy + buffer_y
        )
    
    except Exception as e:
        logger.error(f"Erreur lors du calcul de la boîte englobante: {e}")
        return geometry.bounds  # Retourner les bounds sans buffer en cas d'erreur

def spatial_join(
    left_gdf: gpd.GeoDataFrame,
    right_gdf: gpd.GeoDataFrame,
    how: str = "inner",
    predicate: str = "intersects"
) -> gpd.GeoDataFrame:
    """
    Effectue une jointure spatiale entre deux GeoDataFrames.
    
    Args:
        left_gdf: GeoDataFrame de gauche
        right_gdf: GeoDataFrame de droite
        how: Type de jointure ('inner', 'left', 'right')
        predicate: Prédicat spatial ('intersects', 'contains', 'within', etc.)
        
    Returns:
        GeoDataFrame résultant de la jointure
    """
    try:
        # Vérifier que les deux GDF ont un CRS défini
        if left_gdf.crs is None or right_gdf.crs is None:
            logger.warning("CRS manquant dans un des GeoDataFrames")
            if left_gdf.crs is None and right_gdf.crs is not None:
                left_gdf.set_crs(right_gdf.crs, inplace=True)
            elif left_gdf.crs is not None and right_gdf.crs is None:
                right_gdf.set_crs(left_gdf.crs, inplace=True)
            else:
                # Les deux sont None, utiliser WGS84 par défaut
                left_gdf.set_crs(WGS84, inplace=True)
                right_gdf.set_crs(WGS84, inplace=True)
        
        # Harmoniser les CRS si nécessaire
        if left_gdf.crs != right_gdf.crs:
            right_gdf = right_gdf.to_crs(left_gdf.crs)
        
        # Effectuer la jointure spatiale
        result = gpd.sjoin(left_gdf, right_gdf, how=how, predicate=predicate)
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de la jointure spatiale: {e}")
        return left_gdf.copy()  # Retourner une copie du GDF de gauche en cas d'erreur

def calculate_slope(
    dem_array: np.ndarray,
    cell_size: float
) -> np.ndarray:
    """
    Calcule la pente en degrés à partir d'un array d'élévation.
    
    Args:
        dem_array: Array NumPy contenant les valeurs d'élévation
        cell_size: Taille de cellule en mètres
        
    Returns:
        Array NumPy contenant les valeurs de pente en degrés
    """
    try:
        # Calculer les gradients
        dy, dx = np.gradient(dem_array, cell_size, cell_size)
        
        # Calculer la pente en degrés
        slope_rad = np.arctan(np.sqrt(dx*dx + dy*dy))
        slope_deg = np.degrees(slope_rad)
        
        return slope_deg
    
    except Exception as e:
        logger.error(f"Erreur lors du calcul de pente: {e}")
        return np.zeros_like(dem_array)  # Retourner un array de zéros en cas d'erreur
