"""
Module principal d'analyse climatique pour l'intégration des données Climessences de l'ONF.

Ce module orchestre l'analyse climatique et la recommandation d'espèces forestières
adaptées au changement climatique.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, Point

from forestai.core.domain.services.climate_data_loader import ClimateDataLoader
from forestai.core.domain.services.climate_zone_analyzer import ClimateZoneAnalyzer
from forestai.core.domain.services.species_recommender import SpeciesRecommender

class ClimateAnalyzer:
    """
    Analyseur climatique pour la recommandation d'essences forestières adaptées.
    
    Cette classe orchestre:
    - Le chargement des données climatiques
    - L'identification des zones climatiques
    - La recommandation d'espèces adaptées au climat actuel et futur
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialise l'analyseur climatique.
        
        Args:
            data_dir: Chemin vers le répertoire contenant les données climatiques
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialiser le chargeur de données
        self.data_loader = ClimateDataLoader(data_dir)
        
        # Charger les données climatiques
        self.logger.info("Chargement des données climatiques...")
        climate_data = self.data_loader.load_or_create_data()
        
        # Extraire les données climatiques
        self.climate_zones = climate_data["climate_zones"]
        self.species_compatibility = climate_data["species_compatibility"]
        self.climate_scenarios = climate_data["climate_scenarios"]
        
        # Initialiser les analyseurs spécialisés
        self.zone_analyzer = ClimateZoneAnalyzer(self.climate_zones)
        self.species_recommender = SpeciesRecommender(self.species_compatibility)
        
        self.logger.info("Analyseur climatique initialisé avec succès")
    
    def get_climate_zone(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon, Point]) -> Dict[str, Any]:
        """
        Identifie la zone climatique correspondant à une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON, GeoDataFrame, Polygon ou Point)
            
        Returns:
            Dictionnaire contenant les informations de la zone climatique
        """
        return self.zone_analyzer.get_climate_zone(geometry)
    
    def get_species_compatibility(self, zone_id: str, 
                                  scenario: str = "current") -> Dict[str, Dict[str, Any]]:
        """
        Retourne la compatibilité des espèces pour une zone climatique et un scénario donnés.
        
        Args:
            zone_id: Identifiant de la zone climatique
            scenario: Scénario climatique à utiliser (défaut: climat actuel)
            
        Returns:
            Dictionnaire des espèces avec leur compatibilité
        """
        return self.species_recommender.get_compatible_species(zone_id, scenario)
    
    def recommend_species(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                         scenario: str = "current",
                         min_compatibility: str = "suitable",
                         criteria: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Recommande des espèces adaptées pour une géométrie donnée et un scénario climatique.
        
        Args:
            geometry: Géométrie à analyser
            scenario: Scénario climatique à utiliser
            min_compatibility: Niveau minimal de compatibilité ("optimal", "suitable", "marginal")
            criteria: Poids des critères pour le classement (economic_value, ecological_value, growth_rate)
            
        Returns:
            Liste des espèces recommandées avec leurs scores et détails
        """
        try:
            # Trouver la zone climatique
            climate_zone = self.get_climate_zone(geometry)
            
            if not climate_zone.get('id'):
                self.logger.warning("Aucune zone climatique identifiée, impossible de recommander des espèces")
                return []
            
            # Recommander des espèces pour cette zone
            return self.species_recommender.recommend_species(
                climate_zone['id'], 
                scenario, 
                min_compatibility, 
                criteria
            )
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recommandation d'espèces: {str(e)}")
            return []
    
    def compare_scenarios(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                         scenarios: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compare les recommandations d'espèces pour différents scénarios climatiques.
        
        Args:
            geometry: Géométrie à analyser
            scenarios: Liste des scénarios à comparer (défaut: current, 2050_rcp45, 2050_rcp85)
            
        Returns:
            Dictionnaire avec les recommandations par scénario
        """
        if scenarios is None:
            scenarios = ["current", "2050_rcp45", "2050_rcp85"]
        
        results = {}
        
        for scenario in scenarios:
            self.logger.info(f"Analyse du scénario: {scenario}")
            recommendations = self.recommend_species(geometry, scenario)
            results[scenario] = recommendations
            
            # Récupérer les informations du scénario depuis les données
            if scenario in self.climate_scenarios:
                results[f"{scenario}_info"] = self.climate_scenarios[scenario]
        
        return results
    
    def filter_recommendations_by_risks(self, recommendations: List[Dict[str, Any]], 
                                      excluded_risks: List[str] = None) -> List[Dict[str, Any]]:
        """
        Filtre les recommandations en fonction des risques à éviter.
        
        Args:
            recommendations: Liste des recommandations à filtrer
            excluded_risks: Liste des risques à éviter (drought, frost, fire)
            
        Returns:
            Liste filtrée des recommandations
        """
        return self.species_recommender.filter_recommendations_by_risks(recommendations, excluded_risks)
    
    def get_available_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne les scénarios climatiques disponibles.
        
        Returns:
            Dictionnaire des scénarios climatiques avec leurs détails
        """
        return self.climate_scenarios
