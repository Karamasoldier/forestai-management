"""
Module de chargement des données climatiques pour le ClimateAnalyzer.

S'occupe de charger ou créer les données nécessaires pour l'analyse climatique.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon

class ClimateDataLoader:
    """
    Gestionnaire de données climatiques pour l'analyseur.
    
    Responsable du chargement et de la création des données d'exemple
    pour les zones climatiques, la compatibilité des espèces et les scénarios climatiques.
    """
    
    # Constantes pour les fichiers de données
    DEFAULT_DATA_DIR = "data/climate"
    CLIMATE_ZONES_FILE = "climate_zones.geojson"
    SPECIES_COMPATIBILITY_FILE = "species_compatibility.json"
    CLIMATE_SCENARIOS_FILE = "climate_scenarios.json"
    
    def __init__(self, data_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir) if data_dir else Path(self.DEFAULT_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_or_create_data(self) -> Dict[str, Any]:
        """
        Charge les données climatiques ou crée des données d'exemple si nécessaire.
        
        Returns:
            Dict contenant les données chargées
        """
        climate_zones_path = self.data_dir / self.CLIMATE_ZONES_FILE
        species_compat_path = self.data_dir / self.SPECIES_COMPATIBILITY_FILE
        scenarios_path = self.data_dir / self.CLIMATE_SCENARIOS_FILE
        
        # Vérifier et créer les fichiers si nécessaire
        if not climate_zones_path.exists():
            self.logger.warning(f"Fichier de zones climatiques non trouvé: {climate_zones_path}")
            self._create_sample_climate_zones(climate_zones_path)
        
        if not species_compat_path.exists():
            self.logger.warning(f"Fichier de compatibilité des espèces non trouvé: {species_compat_path}")
            self._create_sample_species_compatibility(species_compat_path)
        
        if not scenarios_path.exists():
            self.logger.warning(f"Fichier de scénarios climatiques non trouvé: {scenarios_path}")
            self._create_sample_climate_scenarios(scenarios_path)
        
        # Charger les données
        try:
            climate_zones = gpd.read_file(climate_zones_path)
            self.logger.info(f"Zones climatiques chargées: {len(climate_zones)} zones")
            
            with open(species_compat_path, 'r', encoding='utf-8') as f:
                species_compatibility = json.load(f)
            self.logger.info(f"Compatibilité des espèces chargée: {len(species_compatibility)} espèces")
            
            with open(scenarios_path, 'r', encoding='utf-8') as f:
                climate_scenarios = json.load(f)
            self.logger.info(f"Scénarios climatiques chargés: {len(climate_scenarios)} scénarios")
            
            return {
                "climate_zones": climate_zones,
                "species_compatibility": species_compatibility,
                "climate_scenarios": climate_scenarios
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données climatiques: {str(e)}")
            return self._create_and_load_sample_data()
    
    def _create_and_load_sample_data(self) -> Dict[str, Any]:
        """
        Crée et charge des données d'exemple en cas d'erreur avec les fichiers.
        
        Returns:
            Dict contenant les données d'exemple
        """
        climate_zones_path = self.data_dir / self.CLIMATE_ZONES_FILE
        species_compat_path = self.data_dir / self.SPECIES_COMPATIBILITY_FILE
        scenarios_path = self.data_dir / self.CLIMATE_SCENARIOS_FILE
        
        self._create_sample_climate_zones(climate_zones_path)
        self._create_sample_species_compatibility(species_compat_path)
        self._create_sample_climate_scenarios(scenarios_path)
        
        # Recharger les données
        climate_zones = gpd.read_file(climate_zones_path)
        
        with open(species_compat_path, 'r', encoding='utf-8') as f:
            species_compatibility = json.load(f)
            
        with open(scenarios_path, 'r', encoding='utf-8') as f:
            climate_scenarios = json.load(f)
            
        return {
            "climate_zones": climate_zones,
            "species_compatibility": species_compatibility,
            "climate_scenarios": climate_scenarios
        }
    
    def _create_sample_climate_zones(self, file_path: Path) -> None:
        """
        Crée un fichier GeoJSON d'exemple avec des zones climatiques.
        
        Args:
            file_path: Chemin où sauvegarder le fichier
        """
        # Création de 4 zones climatiques d'exemple
        zones = [
            {
                "id": "MED1",
                "name": "Méditerranéen - Basse altitude",
                "climate_type": "mediterraneen",
                "annual_temp": 15.2,
                "annual_precip": 650,
                "summer_drought_days": 45,
                "frost_days": 5,
                "elevation_range": "0-400m",
                "geometry": Polygon([
                    (830000, 6250000), (930000, 6250000), 
                    (930000, 6150000), (830000, 6150000), 
                    (830000, 6250000)
                ])
            },
            {
                "id": "ATL1",
                "name": "Atlantique - Plaine",
                "climate_type": "atlantique",
                "annual_temp": 12.8,
                "annual_precip": 850,
                "summer_drought_days": 15,
                "frost_days": 25,
                "elevation_range": "0-200m",
                "geometry": Polygon([
                    (350000, 6700000), (450000, 6700000), 
                    (450000, 6600000), (350000, 6600000), 
                    (350000, 6700000)
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
                "elevation_range": "200-600m",
                "geometry": Polygon([
                    (650000, 6800000), (750000, 6800000), 
                    (750000, 6700000), (650000, 6700000), 
                    (650000, 6800000)
                ])
            },
            {
                "id": "MONT1",
                "name": "Montagnard - Alpes",
                "climate_type": "montagnard",
                "annual_temp": 7.2,
                "annual_precip": 1200,
                "summer_drought_days": 5,
                "frost_days": 100,
                "elevation_range": "800-1600m",
                "geometry": Polygon([
                    (900000, 6400000), (1000000, 6400000), 
                    (1000000, 6300000), (900000, 6300000), 
                    (900000, 6400000)
                ])
            }
        ]
        
        # Création et sauvegarde du GeoDataFrame
        gdf = gpd.GeoDataFrame(zones, crs="EPSG:2154")
        gdf.to_file(file_path, driver="GeoJSON")
        self.logger.info(f"Fichier de zones climatiques d'exemple créé: {file_path}")
    
    def _create_sample_species_compatibility(self, file_path: Path) -> None:
        """
        Crée un fichier JSON d'exemple avec la compatibilité des espèces.
        
        Args:
            file_path: Chemin où sauvegarder le fichier
        """
        # Données d'exemple pour 5 espèces avec leur compatibilité climatique
        species_data = {
            "Pinus pinaster": {
                "common_name": "Pin maritime",
                "climate_compatibility": {
                    "MED1": {"current": "optimal", "2050_rcp45": "optimal", "2050_rcp85": "suitable"},
                    "ATL1": {"current": "optimal", "2050_rcp45": "optimal", "2050_rcp85": "optimal"},
                    "CONT1": {"current": "marginal", "2050_rcp45": "suitable", "2050_rcp85": "suitable"},
                    "MONT1": {"current": "unsuitable", "2050_rcp45": "marginal", "2050_rcp85": "marginal"}
                },
                "risks": {
                    "drought": "medium",
                    "frost": "high",
                    "pests": ["processionnaire du pin"],
                    "fire": "very high"
                },
                "growth_rate": "fast",
                "economic_value": "high",
                "ecological_value": "medium"
            },
            "Quercus ilex": {
                "common_name": "Chêne vert",
                "climate_compatibility": {
                    "MED1": {"current": "optimal", "2050_rcp45": "optimal", "2050_rcp85": "optimal"},
                    "ATL1": {"current": "suitable", "2050_rcp45": "optimal", "2050_rcp85": "optimal"},
                    "CONT1": {"current": "marginal", "2050_rcp45": "suitable", "2050_rcp85": "suitable"},
                    "MONT1": {"current": "unsuitable", "2050_rcp45": "unsuitable", "2050_rcp85": "marginal"}
                },
                "risks": {
                    "drought": "low",
                    "frost": "medium",
                    "pests": ["chenille processionnaire"],
                    "fire": "medium"
                },
                "growth_rate": "slow",
                "economic_value": "medium",
                "ecological_value": "very high"
            },
            "Cedrus atlantica": {
                "common_name": "Cèdre de l'Atlas",
                "climate_compatibility": {
                    "MED1": {"current": "optimal", "2050_rcp45": "optimal", "2050_rcp85": "optimal"},
                    "ATL1": {"current": "suitable", "2050_rcp45": "optimal", "2050_rcp85": "optimal"},
                    "CONT1": {"current": "suitable", "2050_rcp45": "suitable", "2050_rcp85": "optimal"},
                    "MONT1": {"current": "marginal", "2050_rcp45": "suitable", "2050_rcp85": "suitable"}
                },
                "risks": {
                    "drought": "low",
                    "frost": "medium",
                    "pests": ["scolytes"],
                    "fire": "medium"
                },
                "growth_rate": "medium",
                "economic_value": "high",
                "ecological_value": "medium"
            }
        }
        
        # Sauvegarde au format JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(species_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Fichier de compatibilité des espèces d'exemple créé: {file_path}")
    
    def _create_sample_climate_scenarios(self, file_path: Path) -> None:
        """
        Crée un fichier JSON d'exemple avec des scénarios climatiques.
        
        Args:
            file_path: Chemin où sauvegarder le fichier
        """
        # Scénarios climatiques d'exemple
        scenarios_data = {
            "baseline": {
                "name": "Climat actuel (1990-2020)",
                "description": "Conditions climatiques moyennes observées sur la période 1990-2020",
                "source": "Météo-France",
                "reference": "baseline"
            },
            "2050_rcp45": {
                "name": "Scénario RCP 4.5 - Horizon 2050",
                "description": "Scénario modéré de changement climatique (RCP 4.5) à l'horizon 2050",
                "source": "GIEC/Météo-France",
                "reference": "RCP 4.5",
                "changes": {
                    "temperature": {"annual": "+1.5°C"},
                    "precipitation": {"annual": "-5%"},
                    "extreme_events": {"drought_days": "+10 jours"}
                }
            },
            "2050_rcp85": {
                "name": "Scénario RCP 8.5 - Horizon 2050",
                "description": "Scénario pessimiste de changement climatique (RCP 8.5) à l'horizon 2050",
                "source": "GIEC/Météo-France",
                "reference": "RCP 8.5",
                "changes": {
                    "temperature": {"annual": "+2.2°C"},
                    "precipitation": {"annual": "-10%"},
                    "extreme_events": {"drought_days": "+20 jours"}
                }
            }
        }
        
        # Sauvegarde au format JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenarios_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Fichier de scénarios climatiques d'exemple créé: {file_path}")
