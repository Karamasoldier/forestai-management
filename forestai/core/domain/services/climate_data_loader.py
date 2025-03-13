"""
Module de chargement des données climatiques.

Ce module gère le chargement des données climatiques depuis les fichiers de données,
ou leur création si nécessaire.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

class ClimateDataLoader:
    """
    Gère le chargement des données climatiques (zones, espèces, scénarios).
    
    Responsabilités:
    - Charger les données depuis les fichiers
    - Créer des données par défaut si nécessaires
    - Formater les données pour l'analyse
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialise le chargeur de données climatiques.
        
        Args:
            data_dir: Chemin vers le répertoire contenant les données climatiques
                     (Si None, utilise le répertoire data/climate par défaut)
        """
        self.logger = logging.getLogger(__name__)
        
        # Définir le répertoire de données
        if data_dir is None:
            self.data_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))))) / "data" / "climate"
        else:
            self.data_dir = Path(data_dir)
        
        # Créer le répertoire s'il n'existe pas
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Définir les chemins des fichiers
        self.climate_zones_file = self.data_dir / "climate_zones.geojson"
        self.species_compatibility_file = self.data_dir / "species_compatibility.json"
        self.climate_scenarios_file = self.data_dir / "climate_scenarios.json"
        
        self.logger.info(f"ClimateDataLoader initialisé avec répertoire de données: {self.data_dir}")
    
    def load_or_create_data(self) -> Dict[str, Any]:
        """
        Charge les données climatiques depuis les fichiers ou crée des données par défaut.
        
        Returns:
            Dictionnaire contenant les données climatiques chargées:
                - climate_zones: GeoDataFrame des zones climatiques
                - species_compatibility: Dict des espèces et leur compatibilité
                - climate_scenarios: Dict des scénarios climatiques
        """
        # Charger ou créer les zones climatiques
        climate_zones = self._load_or_create_climate_zones()
        
        # Charger ou créer la compatibilité des espèces
        species_compatibility = self._load_or_create_species_compatibility()
        
        # Charger ou créer les scénarios climatiques
        climate_scenarios = self._load_or_create_climate_scenarios()
        
        return {
            "climate_zones": climate_zones,
            "species_compatibility": species_compatibility,
            "climate_scenarios": climate_scenarios
        }
    
    def _load_or_create_climate_zones(self) -> gpd.GeoDataFrame:
        """
        Charge ou crée les zones climatiques.
        
        Returns:
            GeoDataFrame contenant les zones climatiques
        """
        try:
            if self.climate_zones_file.exists():
                self.logger.info(f"Chargement des zones climatiques depuis {self.climate_zones_file}")
                return gpd.read_file(self.climate_zones_file)
            else:
                self.logger.warning(f"Fichier {self.climate_zones_file} non trouvé, création de données par défaut")
                climate_zones = self._create_default_climate_zones()
                
                # Sauvegarder pour utilisation future
                climate_zones.to_file(self.climate_zones_file, driver="GeoJSON")
                
                return climate_zones
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des zones climatiques: {str(e)}")
            return self._create_default_climate_zones()
    
    def _load_or_create_species_compatibility(self) -> Dict[str, Dict[str, Any]]:
        """
        Charge ou crée les données de compatibilité des espèces.
        
        Returns:
            Dictionnaire des espèces et leur compatibilité par zone et scénario
        """
        try:
            if self.species_compatibility_file.exists():
                self.logger.info(f"Chargement des compatibilités d'espèces depuis {self.species_compatibility_file}")
                with open(self.species_compatibility_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Fichier {self.species_compatibility_file} non trouvé, création de données par défaut")
                species_compatibility = self._create_default_species_compatibility()
                
                # Sauvegarder pour utilisation future
                with open(self.species_compatibility_file, 'w', encoding='utf-8') as f:
                    json.dump(species_compatibility, f, ensure_ascii=False, indent=2)
                
                return species_compatibility
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des compatibilités d'espèces: {str(e)}")
            return self._create_default_species_compatibility()
    
    def _load_or_create_climate_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        Charge ou crée les données de scénarios climatiques.
        
        Returns:
            Dictionnaire des scénarios climatiques avec leurs descriptions
        """
        try:
            if self.climate_scenarios_file.exists():
                self.logger.info(f"Chargement des scénarios climatiques depuis {self.climate_scenarios_file}")
                with open(self.climate_scenarios_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Fichier {self.climate_scenarios_file} non trouvé, création de données par défaut")
                climate_scenarios = self._create_default_climate_scenarios()
                
                # Sauvegarder pour utilisation future
                with open(self.climate_scenarios_file, 'w', encoding='utf-8') as f:
                    json.dump(climate_scenarios, f, ensure_ascii=False, indent=2)
                
                return climate_scenarios
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des scénarios climatiques: {str(e)}")
            return self._create_default_climate_scenarios()
    
    def _create_default_climate_zones(self) -> gpd.GeoDataFrame:
        """
        Crée des zones climatiques par défaut pour la France.
        
        Returns:
            GeoDataFrame contenant les zones climatiques par défaut
        """
        # Créer quelques zones climatiques simplifiées pour la France
        zones_data = [
            {
                "id": "CONTINENTAL",
                "name": "Zone continentale de l'Est",
                "climate_type": "continental",
                "annual_temp": 10.5,
                "annual_precip": 900,
                "summer_drought_days": 10,
                "frost_days": 90,
                "geometry": Polygon([
                    (860000, 6800000), (960000, 6800000),
                    (960000, 6700000), (860000, 6700000),
                    (860000, 6800000)
                ])
            },
            {
                "id": "OCEANIQUE",
                "name": "Zone océanique de l'Ouest",
                "climate_type": "oceanic",
                "annual_temp": 11.8,
                "annual_precip": 950,
                "summer_drought_days": 5,
                "frost_days": 35,
                "geometry": Polygon([
                    (650000, 6800000), (750000, 6800000),
                    (750000, 6700000), (650000, 6700000),
                    (650000, 6800000)
                ])
            },
            {
                "id": "MEDITERRANEEN",
                "name": "Zone méditerranéenne du Sud",
                "climate_type": "mediterranean",
                "annual_temp": 14.2,
                "annual_precip": 650,
                "summer_drought_days": 45,
                "frost_days": 10,
                "geometry": Polygon([
                    (750000, 6250000), (850000, 6250000),
                    (850000, 6150000), (750000, 6150000),
                    (750000, 6250000)
                ])
            },
            {
                "id": "MONTAGNARD",
                "name": "Zone de montagne",
                "climate_type": "mountain",
                "annual_temp": 7.5,
                "annual_precip": 1200,
                "summer_drought_days": 5,
                "frost_days": 120,
                "geometry": Polygon([
                    (950000, 6400000), (1050000, 6400000),
                    (1050000, 6300000), (950000, 6300000),
                    (950000, 6400000)
                ])
            }
        ]
        
        # Créer un GeoDataFrame
        gdf = gpd.GeoDataFrame(zones_data, crs="EPSG:2154")
        
        self.logger.info(f"Créé {len(gdf)} zones climatiques par défaut")
        return gdf
    
    def _create_default_species_compatibility(self) -> Dict[str, Dict[str, Any]]:
        """
        Crée des données de compatibilité d'espèces par défaut.
        
        Returns:
            Dictionnaire des espèces et leur compatibilité
        """
        # Créer des données de compatibilité d'espèces simplifiées
        return {
            "Quercus robur": {
                "common_name": "Chêne pédonculé",
                "climate_compatibility": {
                    "CONTINENTAL": {
                        "current": "optimal",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "marginal"
                    },
                    "OCEANIQUE": {
                        "current": "optimal",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "suitable"
                    },
                    "MEDITERRANEEN": {
                        "current": "marginal",
                        "2050_rcp45": "unsuitable",
                        "2050_rcp85": "unsuitable"
                    },
                    "MONTAGNARD": {
                        "current": "suitable",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "optimal"
                    }
                },
                "risks": {
                    "drought": "medium",
                    "frost": "low",
                    "pests": ["chenille processionnaire", "oïdium"],
                    "fire": "low"
                },
                "growth_rate": "slow",
                "economic_value": "high",
                "ecological_value": "high"
            },
            "Quercus pubescens": {
                "common_name": "Chêne pubescent",
                "climate_compatibility": {
                    "CONTINENTAL": {
                        "current": "suitable",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "optimal"
                    },
                    "OCEANIQUE": {
                        "current": "suitable",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "suitable"
                    },
                    "MEDITERRANEEN": {
                        "current": "optimal",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "suitable"
                    },
                    "MONTAGNARD": {
                        "current": "marginal",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "suitable"
                    }
                },
                "risks": {
                    "drought": "low",
                    "frost": "medium",
                    "pests": ["bupreste"],
                    "fire": "medium"
                },
                "growth_rate": "slow",
                "economic_value": "medium",
                "ecological_value": "high"
            },
            "Pinus sylvestris": {
                "common_name": "Pin sylvestre",
                "climate_compatibility": {
                    "CONTINENTAL": {
                        "current": "optimal",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "marginal"
                    },
                    "OCEANIQUE": {
                        "current": "suitable",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "marginal"
                    },
                    "MEDITERRANEEN": {
                        "current": "marginal",
                        "2050_rcp45": "marginal",
                        "2050_rcp85": "unsuitable"
                    },
                    "MONTAGNARD": {
                        "current": "optimal",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "suitable"
                    }
                },
                "risks": {
                    "drought": "medium",
                    "frost": "low",
                    "pests": ["scolyte", "processionnaire"],
                    "fire": "high"
                },
                "growth_rate": "medium",
                "economic_value": "medium",
                "ecological_value": "medium"
            },
            "Pinus pinaster": {
                "common_name": "Pin maritime",
                "climate_compatibility": {
                    "CONTINENTAL": {
                        "current": "marginal",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "suitable"
                    },
                    "OCEANIQUE": {
                        "current": "optimal",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "optimal"
                    },
                    "MEDITERRANEEN": {
                        "current": "optimal",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "suitable"
                    },
                    "MONTAGNARD": {
                        "current": "unsuitable",
                        "2050_rcp45": "marginal",
                        "2050_rcp85": "suitable"
                    }
                },
                "risks": {
                    "drought": "low",
                    "frost": "medium",
                    "pests": ["processionnaire", "matsucoccus"],
                    "fire": "high"
                },
                "growth_rate": "fast",
                "economic_value": "medium",
                "ecological_value": "medium"
            },
            "Cedrus atlantica": {
                "common_name": "Cèdre de l'Atlas",
                "climate_compatibility": {
                    "CONTINENTAL": {
                        "current": "suitable",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "optimal"
                    },
                    "OCEANIQUE": {
                        "current": "suitable",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "suitable"
                    },
                    "MEDITERRANEEN": {
                        "current": "optimal",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "optimal"
                    },
                    "MONTAGNARD": {
                        "current": "marginal",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "optimal"
                    }
                },
                "risks": {
                    "drought": "low",
                    "frost": "medium",
                    "pests": ["scolyte"],
                    "fire": "medium"
                },
                "growth_rate": "medium",
                "economic_value": "high",
                "ecological_value": "medium"
            },
            "Fagus sylvatica": {
                "common_name": "Hêtre",
                "climate_compatibility": {
                    "CONTINENTAL": {
                        "current": "optimal",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "marginal"
                    },
                    "OCEANIQUE": {
                        "current": "optimal",
                        "2050_rcp45": "suitable",
                        "2050_rcp85": "marginal"
                    },
                    "MEDITERRANEEN": {
                        "current": "marginal",
                        "2050_rcp45": "unsuitable",
                        "2050_rcp85": "unsuitable"
                    },
                    "MONTAGNARD": {
                        "current": "optimal",
                        "2050_rcp45": "optimal",
                        "2050_rcp85": "suitable"
                    }
                },
                "risks": {
                    "drought": "high",
                    "frost": "low",
                    "pests": ["scolyte"],
                    "fire": "low"
                },
                "growth_rate": "medium",
                "economic_value": "high",
                "ecological_value": "high"
            }
        }
    
    def _create_default_climate_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        Crée des scénarios climatiques par défaut.
        
        Returns:
            Dictionnaire des scénarios climatiques
        """
        return {
            "current": {
                "description": "Climat actuel (période de référence 1990-2020)",
                "time_horizon": "present",
                "details": "Données climatiques de la période actuelle, servant de référence pour les projections futures."
            },
            "2050_rcp45": {
                "description": "Scénario modéré (RCP 4.5) à l'horizon 2050",
                "time_horizon": "2050",
                "rcp": 4.5,
                "details": "Scénario intermédiaire avec stabilisation des émissions de gaz à effet de serre d'ici 2050, hausse de température modérée."
            },
            "2050_rcp85": {
                "description": "Scénario pessimiste (RCP 8.5) à l'horizon 2050",
                "time_horizon": "2050",
                "rcp": 8.5,
                "details": "Scénario de continuité avec des émissions croissantes de gaz à effet de serre, hausse de température élevée."
            }
        }
