#!/usr/bin/env python3
"""
Module de préparation des données pour l'analyse forestière avancée.

Ce module contient les fonctions pour:
1. Créer des géométries de test
2. Créer des parcelles basées sur des cas réels
3. Structurer les données pour l'analyse
"""

import os
import sys
import logging
from pathlib import Path
from shapely.geometry import box, Point, Polygon
import geopandas as gpd
import numpy as np

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
    
    return config.get_logger("examples.climate_geo_advanced.data")

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
    
    logger = logging.getLogger(__name__)
    logger.info(f"Créé {len(gdf)} parcelles forestières pour l'analyse")
    
    return gdf

def create_test_geometry(region="Centre"):
    """
    Crée une géométrie de test pour les exemples.
    
    Args:
        region: Nom de la région pour ajuster les coordonnées

    Returns:
        Géométrie Shapely (Polygon)
    """
    # Coordonnées Lambert 93 pour différentes régions de France
    regions = {
        "Bretagne": box(200000, 6800000, 250000, 6850000),
        "Alsace": box(1000000, 6800000, 1050000, 6850000),
        "Provence": box(850000, 6250000, 900000, 6300000),
        "Alpes": box(950000, 6400000, 1000000, 6450000),
        "Centre": box(600000, 6650000, 650000, 6700000)
    }
    
    # Utiliser la région spécifiée ou par défaut "Centre"
    if region in regions:
        geometry = regions[region]
    else:
        # Si région non reconnue, utiliser le Centre de la France
        geometry = regions["Centre"]
    
    logger = logging.getLogger(__name__)
    logger.info(f"Géométrie de test créée pour la région {region}: Rectangle de {geometry.area / 10000:.2f} hectares")
    
    return geometry

def create_output_directories(base_dir="data/outputs"):
    """
    Crée les répertoires nécessaires pour les sorties.
    
    Args:
        base_dir: Répertoire de base pour les sorties
        
    Returns:
        Dictionnaire des chemins de répertoires créés
    """
    # Définir les répertoires
    dirs = {
        "base": Path(base_dir),
        "reports": Path(f"{base_dir}/reports"),
        "charts": Path(f"{base_dir}/charts"),
        "json": Path(f"{base_dir}/json"),
        "csv": Path(f"{base_dir}/csv")
    }
    
    # Créer les répertoires
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Répertoires de sortie créés sous {base_dir}")
    
    return dirs

if __name__ == "__main__":
    # Test du module
    logger = setup_logging()
    logger.info("Test du module de préparation des données")
    
    # Créer des parcelles
    parcels = create_real_world_parcels()
    print(f"Parcelles créées: {len(parcels)}")
    
    # Créer une géométrie de test
    geometry = create_test_geometry("Provence")
    print(f"Géométrie créée avec une superficie de {geometry.area / 10000:.2f} hectares")
    
    # Créer les répertoires de sortie
    dirs = create_output_directories("data/outputs/test")
    print(f"Répertoires créés: {', '.join([str(p) for p in dirs.values()])}")
