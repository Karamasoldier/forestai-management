"""
Module d'analyse climatique pour l'intégration des données Climessences de l'ONF.

Version simplifiée qui permet la recommandation d'essences adaptées
au changement climatique.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape

class ClimateAnalyzer:
    """
    Analyseur climatique pour la recommandation d'essences forestières adaptées.
    
    Fonctionnalités principales:
    - Identification des zones climatiques
    - Recommandation d'espèces adaptées au climat actuel et futur
    """
    
    DEFAULT_DATA_DIR = "data/climate"
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialise l'analyseur climatique."""
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir) if data_dir else Path(self.DEFAULT_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Données d'exemple hardcodées pour simplifier
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialise les données d'exemple directement en mémoire."""
        # Zones climatiques d'exemple (remplace le fichier GeoJSON)
        self.climate_zones = gpd.GeoDataFrame([
            {
                "id": "MED1",
                "name": "Méditerranéen - Basse altitude",
                "climate_type": "mediterraneen",
                "annual_temp": 15.2,
                "annual_precip": 650,
                "summer_drought_days": 45,
                "frost_days": 5,
                "geometry": Polygon([
                    (830000, 6250000), (930000, 6250000), 
                    (930000, 6150000), (830000, 6150000), 
                    (830000, 6250000)
                ])
            },
            {
                "id": "CONT1",
                "name": "Continental - Collinéen",
                "climate_type": "continental",
                "annual_temp": 10.5,
                "annual_precip": 950,
                "summer_drought_days": 10,
                "frost_days": 60,
                "geometry": Polygon([
                    (650000, 6800000), (750000, 6800000), 
                    (750000, 6700000), (650000, 6700000), 
                    (650000, 6800000)
                ])
            }
        ], crs="EPSG:2154")
        
        # Compatibilité des espèces (remplace le fichier JSON)
        self.species_compatibility = {
            "Pinus pinaster": {
                "common_name": "Pin maritime",
                "climate_compatibility": {
                    "MED1": {"current": "optimal", "2