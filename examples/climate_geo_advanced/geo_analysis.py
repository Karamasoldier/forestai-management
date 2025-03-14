#!/usr/bin/env python3
"""
Module d'analyse géographique pour les parcelles forestières.

Ce module contient les fonctions pour:
1. Analyser les caractéristiques géographiques des parcelles
2. Calculer les potentiels forestiers
3. Identifier les contraintes et opportunités terrain
"""

import os
import sys
import logging
import numpy as np
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from forestai.core.utils.logging_config import LoggingConfig

def setup_logging():
    """Configure le système de logging."""
    config = LoggingConfig.get_instance()
    config.init({
        "level": "INFO",
        "log_dir": "logs/advanced_example",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    return config.get_logger("examples.climate_geo_advanced.geo")

def simulate_detailed_geo_analysis(parcel):
    """
    Simule une analyse géospatiale détaillée d'une parcelle.
    
    Dans un cas réel, cela utiliserait les modules du GeoAgent pour analyser
    la parcelle (BDTopoLoader, TerrainCoordinator, etc.)
    
    Args:
        parcel: Une ligne du GeoDataFrame de parcelles
        
    Returns:
        Dictionnaire avec les résultats de l'analyse géospatiale
    """
    # Simuler l'analyse du GeoAgent avec des valeurs réalistes
    geo_analysis = {
        "id": parcel["id"],
        "name": parcel["name"],
        "region": parcel["region"],
        "area_ha": parcel["area_ha"],
        "geometry": parcel["geometry"],
        "soil_analysis": {
            "type": parcel["soil_type"],
            "ph": np.random.uniform(4.5, 7.5),
            "organic_matter": np.random.uniform(1.0, 5.0)
        },
        "terrain_analysis": {
            "elevation": {
                "min": parcel["elevation_mean"] - np.random.uniform(10, 50),
                "max": parcel["elevation_mean"] + np.random.uniform(10, 50),
                "mean": parcel["elevation_mean"]
            },
            "slope": {
                "min": max(0, parcel["slope_mean"] - np.random.uniform(1, 5)),
                "max": parcel["slope_mean"] + np.random.uniform(1, 10),
                "mean": parcel["slope_mean"]
            },
            "aspect": np.random.choice(["North", "South", "East", "West", "Northeast", "Southeast", "Southwest", "Northwest"])
        },
        "hydrology": {
            "water_bodies": int(np.random.poisson(1)),
            "streams_length_m": np.random.uniform(0, 500),
            "distance_to_nearest_water_m": np.random.uniform(50, 2000)
        },
        "land_cover": {
            "dominant": np.random.choice(["Forêt mixte", "Forêt de conifères", "Forêt de feuillus", "Végétation arbustive"]),
            "forest_percentage": np.random.uniform(60, 95)
        },
        "infrastructure": {
            "roads_length_m": np.random.uniform(0, 1000),
            "distance_to_nearest_road_m": np.random.uniform(20, 1000),
            "buildings_count": int(np.random.poisson(0.5))
        },
        "forestry_potential": {
            "potential_score": np.random.uniform(0.55, 0.90),
            "constraints": parcel["constraints"],
            "opportunities": [
                np.random.choice(["bonne_accessibilité", "présence_cours_eau", "exposition_favorable"]),
                np.random.choice(["sol_adapté", "climat_tempéré", "protection_vent"])
            ]
        }
    }
    
    # Déterminer la classe de potentiel en fonction du score
    score = geo_analysis["forestry_potential"]["potential_score"]
    if score >= 0.80:
        geo_analysis["forestry_potential"]["potential_class"] = "Excellent"
    elif score >= 0.70:
        geo_analysis["forestry_potential"]["potential_class"] = "Très bon"
    elif score >= 0.60:
        geo_analysis["forestry_potential"]["potential_class"] = "Bon"
    elif score >= 0.50:
        geo_analysis["forestry_potential"]["potential_class"] = "Moyen"
    else:
        geo_analysis["forestry_potential"]["potential_class"] = "Faible"
    
    return geo_analysis

def batch_analyze_parcels(parcels):
    """
    Analyse un ensemble de parcelles et retourne les résultats.
    
    Args:
        parcels: GeoDataFrame contenant les parcelles à analyser
        
    Returns:
        Liste des résultats d'analyse par parcelle
    """
    results = []
    logger = logging.getLogger(__name__)
    
    for i, parcel in parcels.iterrows():
        logger.info(f"Analyse de la parcelle {parcel['id']} ({parcel['name']})")
        analysis = simulate_detailed_geo_analysis(parcel)
        results.append(analysis)
        logger.info(f"Potentiel forestier: {analysis['forestry_potential']['potential_class']} "
                   f"({analysis['forestry_potential']['potential_score']:.2f})")
    
    return results

def calculate_regional_statistics(geo_analyses):
    """
    Calcule des statistiques régionales basées sur les analyses géospatiales.
    
    Args:
        geo_analyses: Liste des résultats d'analyse géospatiale
        
    Returns:
        Dictionnaire contenant les statistiques régionales
    """
    # Regrouper par région
    regions = {}
    
    for analysis in geo_analyses:
        region = analysis["region"]
        if region not in regions:
            regions[region] = []
        
        regions[region].append(analysis)
    
    # Calculer les statistiques par région
    regional_stats = {}
    
    for region, analyses in regions.items():
        stats = {
            "region": region,
            "parcel_count": len(analyses),
            "total_area_ha": sum(a["area_ha"] for a in analyses),
            "avg_potential_score": np.mean([a["forestry_potential"]["potential_score"] for a in analyses]),
            "avg_elevation": np.mean([a["terrain_analysis"]["elevation"]["mean"] for a in analyses]),
            "avg_slope": np.mean([a["terrain_analysis"]["slope"]["mean"] for a in analyses]),
            "common_constraints": _most_common([c for a in analyses for c in a["forestry_potential"]["constraints"]]),
            "common_opportunities": _most_common([o for a in analyses for o in a["forestry_potential"]["opportunities"]])
        }
        
        regional_stats[region] = stats
    
    return regional_stats

def _most_common(items, top_n=3):
    """
    Identifie les éléments les plus fréquents dans une liste.
    
    Args:
        items: Liste d'éléments
        top_n: Nombre d'éléments les plus fréquents à retourner
        
    Returns:
        Liste des éléments les plus fréquents
    """
    if not items:
        return []
    
    # Compter les occurrences
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    
    # Trier par occurrences décroissantes
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    # Retourner les plus fréquents
    return [item[0] for item in sorted_items[:top_n]]

if __name__ == "__main__":
    # Test du module
    logger = setup_logging()
    logger.info("Test du module d'analyse géographique")
    
    # Importer le module de préparation des données
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_preparation import create_real_world_parcels
    
    # Créer des parcelles
    parcels = create_real_world_parcels()
    print(f"Parcelles créées: {len(parcels)}")
    
    # Analyser les parcelles
    results = batch_analyze_parcels(parcels)
    print(f"Analyses effectuées: {len(results)}")
    
    # Calculer les statistiques régionales
    stats = calculate_regional_statistics(results)
    for region, region_stats in stats.items():
        print(f"\nRégion: {region}")
        print(f"Nombre de parcelles: {region_stats['parcel_count']}")
        print(f"Surface totale: {region_stats['total_area_ha']:.2f} ha")
        print(f"Score potentiel moyen: {region_stats['avg_potential_score']:.2f}")
        print(f"Contraintes principales: {', '.join(region_stats['common_constraints'])}")
