# forestai/agents/geo_agent/terrain_services/risk_service.py

import os
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import shape, mapping, box
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from forestai.agents.geo_agent.terrain_services.base_terrain_service import BaseTerrainService
from forestai.core.utils.logging import get_logger

class RiskService(BaseTerrainService):
    """
    Service pour l'analyse des risques naturels sur les parcelles forestières.
    
    Ce service évalue différents risques naturels comme:
    - Risques d'inondation
    - Risques d'incendie
    - Risques d'érosion
    - Risques liés aux mouvements de terrain
    """
    
    def __init__(self, data_dir: str = None, log_level: str = "INFO"):
        """
        Initialise le service d'analyse des risques.
        
        Args:
            data_dir: Répertoire racine des données
            log_level: Niveau de journalisation
        """
        super().__init__(data_dir, log_level)
        self.logger = get_logger(name="terrain.risk", level=log_level)
        
        # Chemins des données de risques
        self.flood_risk_path = os.path.join(self.data_dir, "risks", "flood")
        self.fire_risk_path = os.path.join(self.data_dir, "risks", "fire")
        self.erosion_risk_path = os.path.join(self.data_dir, "risks", "erosion")
        self.landslide_risk_path = os.path.join(self.data_dir, "risks", "landslide")
        
        self.logger.info(f"Service d'analyse des risques initialisé")
        
    def analyze_flood_risk(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                          buffer_distance: float = 0) -> Dict[str, Any]:
        """
        Analyse le risque d'inondation sur une géométrie.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON ou GeoDataFrame)
            buffer_distance: Distance de buffer en mètres autour de la géométrie
            
        Returns:
            Dictionnaire avec les résultats d'analyse
        """
        self.logger.debug(f"Analyse du risque d'inondation avec buffer de {buffer_distance}m")
        
        try:
            # Préparation de la géométrie
            geom = self._prepare_geometry(geometry, buffer_distance)
            
            # Si aucune donnée de risque d'inondation n'est disponible, retourner une estimation basique
            if not os.path.exists(self.flood_risk_path):
                self.logger.warning(f"Données de risque d'inondation non disponibles, estimation basique utilisée")
                
                # Estimation approximative basée sur l'altitude et la proximité des cours d'eau
                # (Cette partie dépendrait d'autres services comme hydrology_service)
                return {
                    "flood_risk_level": "unknown",
                    "estimated": True,
                    "message": "Estimation basique - Données précises non disponibles"
                }
            
            # Sinon, procéder à l'analyse des données existantes
            # Exemple: lire les données et calculer le niveau de risque
            # Pour cet exemple, nous simulons simplement un résultat
            
            risk_levels = ["low", "medium", "high"]
            risk_level = risk_levels[np.random.randint(0, 3)]
            
            return {
                "flood_risk_level": risk_level,
                "flood_risk_score": np.random.uniform(0, 1),
                "flood_risk_details": {
                    "source": "simulation",
                    "return_period_years": 100,
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du risque d'inondation: {str(e)}")
            return {
                "flood_risk_level": "error",
                "error": str(e)
            }
    
    def analyze_fire_risk(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                         params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyse le risque d'incendie sur une géométrie.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON ou GeoDataFrame)
            params: Paramètres additionnels (saison, etc.)
            
        Returns:
            Dictionnaire avec les résultats d'analyse
        """
        params = params or {}
        season = params.get("season", "summer")
        
        self.logger.debug(f"Analyse du risque d'incendie pour la saison {season}")
        
        try:
            # Préparation de la géométrie
            geom = self._prepare_geometry(geometry)
            
            # Simuler l'analyse du risque d'incendie
            # Dans une implémentation réelle, on accéderait à des données de risque d'incendie
            
            # Facteurs influençant le risque d'incendie:
            # - Type de végétation
            # - Densité de végétation
            # - Conditions climatiques (température, précipitations)
            # - Topographie (pente, exposition)
            # - Historique des incendies
            
            # Pour l'exemple, on simule un calcul de risque
            base_risk = np.random.uniform(0.1, 0.9)
            
            # Ajuster selon la saison
            season_multipliers = {
                "winter": 0.3,
                "spring": 0.7,
                "summer": 1.5,
                "autumn": 0.8
            }
            
            risk_score = base_risk * season_multipliers.get(season, 1.0)
            risk_score = min(risk_score, 1.0)  # Plafonner à 1.0
            
            # Déterminer le niveau de risque
            if risk_score < 0.3:
                risk_level = "low"
            elif risk_score < 0.7:
                risk_level = "medium"
            else:
                risk_level = "high"
            
            return {
                "fire_risk_level": risk_level,
                "fire_risk_score": risk_score,
                "fire_risk_details": {
                    "season": season,
                    "vegetation_factor": np.random.uniform(0.5, 1.5),
                    "climate_factor": np.random.uniform(0.5, 1.5)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du risque d'incendie: {str(e)}")
            return {
                "fire_risk_level": "error",
                "error": str(e)
            }
    
    def analyze_erosion_risk(self, geometry: Union[Dict, gpd.GeoDataFrame],
                            include_slope_data: bool = True) -> Dict[str, Any]:
        """
        Analyse le risque d'érosion sur une géométrie.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON ou GeoDataFrame)
            include_slope_data: Inclure les données de pente dans l'analyse
            
        Returns:
            Dictionnaire avec les résultats d'analyse
        """
        self.logger.debug(f"Analyse du risque d'érosion (avec données de pente: {include_slope_data})")
        
        try:
            # Préparation de la géométrie
            geom = self._prepare_geometry(geometry)
            
            # Pour une implémentation réelle, on combinerait:
            # - Données de pente (du SlopeService)
            # - Type de sol
            # - Couverture végétale
            # - Précipitations moyennes et intensité
            
            # Simulation d'une analyse de risque d'érosion
            risk_factors = {
                "slope_factor": np.random.uniform(0.5, 1.5) if include_slope_data else 1.0,
                "soil_factor": np.random.uniform(0.5, 1.5),
                "vegetation_factor": np.random.uniform(0.5, 1.5),
                "precipitation_factor": np.random.uniform(0.5, 1.5)
            }
            
            # Calcul du score de risque
            risk_score = (
                risk_factors["slope_factor"] * 
                risk_factors["soil_factor"] * 
                risk_factors["vegetation_factor"] * 
                risk_factors["precipitation_factor"]
            ) / 4.0
            
            # Normaliser entre 0 et 1
            risk_score = min(max(risk_score / 1.5, 0), 1)
            
            # Déterminer le niveau de risque
            if risk_score < 0.3:
                risk_level = "low"
            elif risk_score < 0.7:
                risk_level = "medium"
            else:
                risk_level = "high"
            
            return {
                "erosion_risk_level": risk_level,
                "erosion_risk_score": risk_score,
                "erosion_risk_factors": risk_factors
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du risque d'érosion: {str(e)}")
            return {
                "erosion_risk_level": "error",
                "error": str(e)
            }
    
    def analyze_landslide_risk(self, geometry: Union[Dict, gpd.GeoDataFrame]) -> Dict[str, Any]:
        """
        Analyse le risque de glissement de terrain sur une géométrie.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON ou GeoDataFrame)
            
        Returns:
            Dictionnaire avec les résultats d'analyse
        """
        self.logger.debug(f"Analyse du risque de glissement de terrain")
        
        try:
            # Préparation de la géométrie
            geom = self._prepare_geometry(geometry)
            
            # Simuler l'analyse
            # Dans une implémentation réelle, on utiliserait:
            # - Cartes des risques géologiques
            # - Données de pente et d'orientation
            # - Historique des glissements de terrain
            # - Type de sol et stabilité
            
            # Simulation pour l'exemple
            risk_score = np.random.uniform(0, 1)
            
            if risk_score < 0.3:
                risk_level = "low"
                recommendations = ["Surveillance périodique standard"]
            elif risk_score < 0.7:
                risk_level = "medium"
                recommendations = ["Surveillance régulière", "Éviter les coupes rases étendues"]
            else:
                risk_level = "high"
                recommendations = [
                    "Étude géotechnique recommandée",
                    "Limiter les interventions lourdes",
                    "Maintenir un couvert forestier permanent",
                    "Gestion des eaux de ruissellement"
                ]
            
            return {
                "landslide_risk_level": risk_level,
                "landslide_risk_score": risk_score,
                "recommendations": recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du risque de glissement de terrain: {str(e)}")
            return {
                "landslide_risk_level": "error",
                "error": str(e)
            }
    
    def analyze_all_risks(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                         params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyse complète des risques sur une géométrie.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON ou GeoDataFrame)
            params: Paramètres additionnels pour les analyses
            
        Returns:
            Dictionnaire avec tous les résultats d'analyse
        """
        params = params or {}
        self.logger.info(f"Analyse complète des risques naturels")
        
        # Exécuter toutes les analyses de risque
        flood_risk = self.analyze_flood_risk(geometry, params.get("flood_buffer", 0))
        fire_risk = self.analyze_fire_risk(geometry, params)
        erosion_risk = self.analyze_erosion_risk(geometry, params.get("include_slope_data", True))
        landslide_risk = self.analyze_landslide_risk(geometry)
        
        # Calculer un indice de risque global
        risk_scores = [
            flood_risk.get("flood_risk_score", 0),
            fire_risk.get("fire_risk_score", 0),
            erosion_risk.get("erosion_risk_score", 0),
            landslide_risk.get("landslide_risk_score", 0)
        ]
        
        # Filtrer les valeurs None
        valid_scores = [score for score in risk_scores if score is not None]
        
        if valid_scores:
            global_risk_score = sum(valid_scores) / len(valid_scores)
            
            # Déterminer le niveau de risque global
            if global_risk_score < 0.3:
                global_risk_level = "low"
            elif global_risk_score < 0.7:
                global_risk_level = "medium"
            else:
                global_risk_level = "high"
        else:
            global_risk_score = None
            global_risk_level = "unknown"
        
        # Compiler toutes les recommandations
        all_recommendations = []
        if "recommendations" in flood_risk:
            all_recommendations.extend(flood_risk["recommendations"])
        if "recommendations" in fire_risk:
            all_recommendations.extend(fire_risk["recommendations"])
        if "recommendations" in erosion_risk:
            all_recommendations.extend(erosion_risk["recommendations"])
        if "recommendations" in landslide_risk:
            all_recommendations.extend(landslide_risk["recommendations"])
        
        # Résultats compilés
        return {
            "global_risk_level": global_risk_level,
            "global_risk_score": global_risk_score,
            "flood_risk": flood_risk,
            "fire_risk": fire_risk,
            "erosion_risk": erosion_risk,
            "landslide_risk": landslide_risk,
            "recommendations": list(set(all_recommendations))  # Éliminer les doublons
        }
