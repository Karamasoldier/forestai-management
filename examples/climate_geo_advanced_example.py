#!/usr/bin/env python3
"""
Exemple avancé d'intégration du module d'analyse climatique avec le GeoAgent.

Cet exemple montre comment:
1. Utiliser les deux modules ensemble pour une analyse complète
2. Filtrer intelligemment les recommandations d'espèces en fonction des contraintes terrain
3. Générer des visualisations et rapports combinés
4. Exporter les données pour une utilisation dans d'autres systèmes
"""

import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from shapely.geometry import box, Point, Polygon
import geopandas as gpd

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules nécessaires
from forestai.core.domain.services import ClimateAnalyzer
from forestai.core.utils.logging_config import LoggingConfig

def setup_logging():
    """Configure le système de logging."""
    config = LoggingConfig.get_instance()
    config.init({
        "level": "INFO",
        "log_dir": "logs/advanced_example",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    return config.get_logger("examples.climate_geo_advanced")

def create_real_world_parcels():
    """
    Crée un ensemble de parcelles forestières basées sur des cas réels.
    
    Returns:
        GeoDataFrame avec les parcelles et leurs informations
    """
    # Définir quelques parcelles forestières fictives mais réalistes
    parcels_data = [
        {
            "id": "F001",
            "name": "Forêt de Brocéliande",
            "region": "Bretagne",
            "area_ha": 75.4,
            "soil_type": "argileux",
            "elevation_mean": 145,
            "slope_mean": 3.2,
            "constraints": ["humidité_élevée", "zone_touristique"],
            "geometry": Polygon([
                (350000, 6780000), (351500, 6780000), 
                (351500, 6781500), (350000, 6781500),
                (350000, 6780000)
            ])
        },
        {
            "id": "F002",
            "name": "Parcelle des Vosges",
            "region": "Grand Est",
            "area_ha": 32.7,
            "soil_type": "acide",
            "elevation_mean": 820,
            "slope_mean": 15.6,
            "constraints": ["pente_forte", "enneigement_hivernal"],
            "geometry": Polygon([
                (985000, 6790000), (986200, 6790000),
                (986200, 6791200), (985000, 6791200),
                (985000, 6790000)
            ])
        },
        {
            "id": "F003",
            "name": "Garrigue Méditerranéenne",
            "region": "Provence",
            "area_ha": 48.2,
            "soil_type": "calcaire",
            "elevation_mean": 280,
            "slope_mean": 8.4,
            "constraints": ["sécheresse_estivale", "risque_incendie_élevé", "sol_sec"],
            "geometry": Polygon([
                (850000, 6250000), (851200, 6250000),
                (851200, 6251000), (850000, 6251000),
                (850000, 6250000)
            ])
        },
        {
            "id": "F004",
            "name": "Plateau Central",
            "region": "Auvergne",
            "area_ha": 64.1,
            "soil_type": "limoneux",
            "elevation_mean": 520,
            "slope_mean": 6.3,
            "constraints": ["gel_tardif", "précipitations_variables"],
            "geometry": Polygon([
                (650000, 6500000), (651000, 6500000),
                (651000, 6501500), (650000, 6501500),
                (650000, 6500000)
            ])
        },
        {
            "id": "F005",
            "name": "Landes Atlantiques",
            "region": "Nouvelle-Aquitaine",
            "area_ha": 110.5,
            "soil_type": "sableux",
            "elevation_mean": 60,
            "slope_mean": 1.2,
            "constraints": ["nappe_phréatique_haute", "sols_pauvres"],
            "geometry": Polygon([
                (380000, 6400000), (382000, 6400000),
                (382000, 6402000), (380000, 6402000),
                (380000, 6400000)
            ])
        }
    ]
    
    # Créer un GeoDataFrame
    gdf = gpd.GeoDataFrame(parcels_data, crs="EPSG:2154")
    
    print(f"Créé {len(gdf)} parcelles forestières pour l'analyse")
    
    return gdf

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