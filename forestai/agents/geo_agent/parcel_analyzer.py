# forestai/agents/geo_agent/parcel_analyzer.py

import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon
import rasterio
from rasterio.mask import mask
import os
from typing import Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)

def analyze_parcel_potential(
    parcel: gpd.GeoSeries,
    soil_types_gdf: gpd.GeoDataFrame,
    forest_areas_gdf: gpd.GeoDataFrame,
    max_slope: float = 30.0,
    dem_path: str = None
) -> Dict[str, Any]:
    """
    Analyse le potentiel forestier d'une parcelle.
    
    Args:
        parcel: GeoSeries de la parcelle à analyser
        soil_types_gdf: GeoDataFrame des types de sol
        forest_areas_gdf: GeoDataFrame des zones forestières existantes
        max_slope: Pente maximale en degrés
        dem_path: Chemin vers le modèle numérique de terrain (optionnel)
        
    Returns:
        Dictionnaire avec les métriques d'analyse
    """
    results = {}
    
    # 1. Récupérer la géométrie de la parcelle
    parcel_geom = parcel.geometry
    
    # 2. Analyser le type de sol
    soil_score = analyze_soil_suitability(parcel_geom, soil_types_gdf)
    results["soil_suitability"] = soil_score
    
    # 3. Analyser la proximité avec des forêts existantes
    forest_proximity = analyze_forest_proximity(parcel_geom, forest_areas_gdf)
    results["forest_proximity"] = forest_proximity
    
    # 4. Analyser la pente si MNT disponible
    if dem_path and os.path.exists(dem_path):
        slope_data = analyze_slope(parcel_geom, dem_path, max_slope)
        results["mean_slope"] = slope_data["mean_slope"]
        results["max_slope"] = slope_data["max_slope"]
        results["slope_suitability"] = slope_data["suitability"]
    else:
        # Sans données de pente, on fait une estimation par défaut
        results["slope_suitability"] = 0.8  # Valeur par défaut favorable
    
    # 5. Calculer le score global de potentiel forestier
    weights = {
        "soil_suitability": 0.4,
        "forest_proximity": 0.3,
        "slope_suitability": 0.3
    }
    
    forestry_potential = 0
    for key, weight in weights.items():
        forestry_potential += results[key] * weight
    
    results["forestry_potential"] = forestry_potential
    
    # 6. Recommandations d'essences adaptées
    results["recommended_species"] = recommend_species(
        soil_score, 
        forestry_potential, 
        results.get("mean_slope", 10)  # Valeur par défaut si non disponible
    )
    
    return results

def analyze_soil_suitability(
    parcel_geometry,
    soil_types_gdf: gpd.GeoDataFrame
) -> float:
    """
    Analyse la compatibilité du sol avec une utilisation forestière.
    
    Args:
        parcel_geometry: Géométrie de la parcelle
        soil_types_gdf: GeoDataFrame des types de sol
        
    Returns:
        Score de compatibilité du sol (0-1)
    """
    # Vérifier si le GeoDataFrame des sols est vide
    if soil_types_gdf.empty:
        logger.warning("Aucune donnée de sol disponible, utilisation d'une valeur par défaut")
        return 0.7  # Valeur par défaut modérément favorable
    
    try:
        # Intersection spatiale avec les types de sol
        intersection = gpd.overlay(
            gpd.GeoDataFrame(geometry=[parcel_geometry], crs=soil_types_gdf.crs),
            soil_types_gdf,
            how="intersection"
        )
        
        if intersection.empty:
            logger.warning("Aucune intersection avec les données de sol")
            return 0.7
        
        # Calculer la proportion de chaque type de sol
        intersection["area"] = intersection.geometry.area
        total_area = intersection["area"].sum()
        
        # Assigner un score de compatibilité à chaque type de sol
        # Note: Dans une implémentation réelle, ces scores seraient basés sur
        # une classification scientifique des types de sols pour la foresterie
        soil_scores = {
            "argileux": 0.8,
            "limoneux": 0.9,
            "sableux": 0.6,
            "calcaire": 0.5,
            "humide": 0.7,
            "tourbeux": 0.4
        }
        
        # Score par défaut si le type n'est pas reconnu
        default_score = 0.6
        
        # Calculer le score pondéré par la surface
        weighted_score = 0
        for idx, row in intersection.iterrows():
            soil_type = row.get("type", "inconnu")
            score = soil_scores.get(soil_type, default_score)
            proportion = row["area"] / total_area
            weighted_score += score * proportion
        
        return weighted_score
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du sol: {e}")
        return 0.7  # Valeur par défaut en cas d'erreur

def analyze_forest_proximity(
    parcel_geometry,
    forest_areas_gdf: gpd.GeoDataFrame
) -> float:
    """
    Analyse la proximité avec des zones forestières existantes.
    
    Args:
        parcel_geometry: Géométrie de la parcelle
        forest_areas_gdf: GeoDataFrame des zones forestières
        
    Returns:
        Score de proximité forestière (0-1)
    """
    # Vérifier si le GeoDataFrame des forêts est vide
    if forest_areas_gdf.empty:
        logger.warning("Aucune donnée de zones forestières disponible, utilisation d'une valeur par défaut")
        return 0.5  # Valeur par défaut neutre
    
    try:
        # Mesurer la distance à la forêt la plus proche
        distances = forest_areas_gdf.geometry.apply(lambda geom: parcel_geometry.distance(geom))
        min_distance = distances.min()
        
        # Normaliser le score de proximité
        # Plus la distance est faible, plus le score est élevé
        # Distance de référence: 3000m (3km)
        max_reference_distance = 3000
        
        if min_distance == 0:  # La parcelle touche ou est dans une forêt
            return 1.0
        else:
            normalized_score = max(0, 1 - (min_distance / max_reference_distance))
            return normalized_score
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de proximité forestière: {e}")
        return 0.5  # Valeur par défaut en cas d'erreur

def analyze_slope(
    parcel_geometry,
    dem_path: str,
    max_slope: float
) -> Dict[str, Any]:
    """
    Analyse la pente du terrain sur la parcelle.
    
    Args:
        parcel_geometry: Géométrie de la parcelle
        dem_path: Chemin vers le modèle numérique de terrain (MNT)
        max_slope: Pente maximale acceptable en degrés
        
    Returns:
        Dictionnaire avec les statistiques de pente
    """
    try:
        # Ouvrir le MNT
        with rasterio.open(dem_path) as dem:
            # Extraire les valeurs d'élévation pour la parcelle
            masked, mask_transform = mask(dem, [parcel_geometry], crop=True)
            
            # Calculer la pente
            # Note: Dans une implémentation réelle, on utiliserait une fonction comme
            # la suivante, disponible dans certaines bibliothèques SIG:
            # slope = calculate_slope(masked, mask_transform, dem.crs)
            
            # Pour cette simulation, générer des valeurs aléatoires
            mean_slope = float(np.random.uniform(2, 18))  # Pente moyenne entre 2% et 18%
            max_slope_value = float(np.random.uniform(mean_slope, min(mean_slope * 2, 35)))
            
            # Calculer le score d'adéquation de la pente
            # 0% est idéal, >max_slope% est inutilisable
            suitability = max(0, 1 - (mean_slope / max_slope))
            
            return {
                "mean_slope": mean_slope,
                "max_slope": max_slope_value,
                "suitability": suitability
            }
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de la pente: {e}")
        return {
            "mean_slope": 10.0,  # Valeur par défaut modérée
            "max_slope": 15.0,
            "suitability": 0.7
        }

def recommend_species(
    soil_score: float,
    forestry_potential: float,
    mean_slope: float
) -> List[Dict[str, Any]]:
    """
    Recommande des essences forestières adaptées aux caractéristiques de la parcelle.
    
    Args:
        soil_score: Score de compatibilité du sol (0-1)
        forestry_potential: Potentiel forestier global (0-1)
        mean_slope: Pente moyenne en degrés
        
    Returns:
        Liste d'essences recommandées avec scores de compatibilité
    """
    # Liste d'essences avec leurs caractéristiques et préférences
    # Dans une version réelle, ceci viendrait d'une base de données
    species_database = [
        {
            "name": "Chêne sessile",
            "latin_name": "Quercus petraea",
            "min_soil_score": 0.6,
            "max_slope": 25,
            "economic_value": 0.85,
            "growth_time_years": 120
        },
        {
            "name": "Pin maritime",
            "latin_name": "Pinus pinaster",
            "min_soil_score": 0.5,
            "max_slope": 30,
            "economic_value": 0.75,
            "growth_time_years": 50
        },
        {
            "name": "Douglas",
            "latin_name": "Pseudotsuga menziesii",
            "min_soil_score": 0.65,
            "max_slope": 35,
            "economic_value": 0.9,
            "growth_time_years": 60
        },
        {
            "name": "Châtaignier",
            "latin_name": "Castanea sativa",
            "min_soil_score": 0.55,
            "max_slope": 20,
            "economic_value": 0.8,
            "growth_time_years": 70
        },
        {
            "name": "Frêne commun",
            "latin_name": "Fraxinus excelsior",
            "min_soil_score": 0.7,
            "max_slope": 15,
            "economic_value": 0.75,
            "growth_time_years": 80
        }
    ]
    
    # Filtrer les essences adaptées
    suitable_species = []
    
    for species in species_database:
        if (soil_score >= species["min_soil_score"] and 
            mean_slope <= species["max_slope"]):
            
            # Calculer un score de compatibilité
            soil_compatibility = (soil_score - species["min_soil_score"]) / (1 - species["min_soil_score"])
            slope_compatibility = 1 - (mean_slope / species["max_slope"])
            
            compatibility_score = (
                0.5 * soil_compatibility + 
                0.3 * slope_compatibility +
                0.2 * species["economic_value"]
            ) * forestry_potential
            
            suitable_species.append({
                "name": species["name"],
                "latin_name": species["latin_name"],
                "compatibility_score": round(compatibility_score, 2),
                "growth_time_years": species["growth_time_years"],
                "economic_value": species["economic_value"]
            })
    
    # Trier par score de compatibilité
    suitable_species.sort(key=lambda x: x["compatibility_score"], reverse=True)
    
    return suitable_species[:3]  # Retourner les 3 meilleures essences
