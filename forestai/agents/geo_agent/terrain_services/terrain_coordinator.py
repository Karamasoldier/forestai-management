# forestai/agents/geo_agent/terrain_services/terrain_coordinator.py

import os
import concurrent.futures
from typing import Dict, Any, List, Tuple, Optional, Union
import geopandas as gpd
import numpy as np
import time

from forestai.core.utils.logging import get_logger
from forestai.core.utils.logging_config import LoggingMetrics

# Import des services de terrain
from forestai.agents.geo_agent.terrain_services.elevation_service import ElevationService
from forestai.agents.geo_agent.terrain_services.slope_service import SlopeService
from forestai.agents.geo_agent.terrain_services.hydrology_service import HydrologyService
from forestai.agents.geo_agent.terrain_services.risk_service import RiskService

class TerrainCoordinator:
    """
    Coordinateur qui orchestre les différents services d'analyse de terrain.
    
    Ce coordinateur permet de:
    - Centraliser l'accès aux différents services d'analyse
    - Paralléliser les analyses indépendantes
    - Séquencer les analyses dépendantes
    - Agréger les résultats de multiples analyses
    """
    
    def __init__(self, data_dir: str = None, log_level: str = "INFO", use_parallel: bool = True):
        """
        Initialise le coordinateur de terrain.
        
        Args:
            data_dir: Répertoire racine des données
            log_level: Niveau de journalisation
            use_parallel: Utiliser le traitement parallèle quand possible
        """
        self.data_dir = data_dir or os.environ.get("DATA_PATH", "./data")
        self.log_level = log_level
        self.use_parallel = use_parallel
        self.logger = get_logger(name="terrain.coordinator", level=log_level)
        self.metrics = LoggingMetrics.get_instance()
        
        # Initialiser les services
        self.elevation_service = ElevationService(data_dir, log_level)
        self.slope_service = SlopeService(data_dir, log_level)
        self.hydrology_service = HydrologyService(data_dir, log_level)
        self.risk_service = RiskService(data_dir, log_level)
        
        self.logger.info(f"Coordinateur d'analyse de terrain initialisé (parallélisation: {use_parallel})")
    
    def analyze_terrain(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                       analysis_types: List[str] = None, 
                       params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyse complète ou partielle du terrain pour une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON ou GeoDataFrame)
            analysis_types: Types d'analyses à effectuer (si None, toutes les analyses)
            params: Paramètres spécifiques aux analyses
            
        Returns:
            Dictionnaire avec les résultats combinés
        """
        start_time = time.time()
        params = params or {}
        
        # Par défaut, effectuer toutes les analyses
        if analysis_types is None:
            analysis_types = ["elevation", "slope", "hydrology", "risks"]
        
        self.logger.info(f"Analyse de terrain lancée pour {len(analysis_types)} types d'analyses")
        
        results = {}
        errors = []
        
        # Déterminer quelles analyses peuvent être parallélisées
        if self.use_parallel and len(analysis_types) > 1:
            # Analyses qui peuvent être exécutées en parallèle
            parallel_analyses = []
            sequential_analyses = []
            
            # Le calcul de pente dépend de l'élévation, donc il doit être exécuté après
            if "slope" in analysis_types and "elevation" in analysis_types:
                sequential_analyses.append("slope")
                parallel_analyses.extend([at for at in analysis_types if at != "slope"])
            else:
                parallel_analyses = analysis_types
            
            # Exécuter les analyses parallélisables
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_analysis = {}
                
                for analysis_type in parallel_analyses:
                    future = executor.submit(self._execute_analysis, analysis_type, geometry, params)
                    future_to_analysis[future] = analysis_type
                
                for future in concurrent.futures.as_completed(future_to_analysis):
                    analysis_type = future_to_analysis[future]
                    try:
                        analysis_result = future.result()
                        results[analysis_type] = analysis_result
                    except Exception as e:
                        errors.append(f"Erreur lors de l'analyse {analysis_type}: {str(e)}")
                        self.logger.error(f"Erreur lors de l'analyse parallèle {analysis_type}: {str(e)}")
            
            # Exécuter les analyses séquentielles qui dépendent des précédentes
            for analysis_type in sequential_analyses:
                try:
                    # Pour le cas de la pente, nous avons besoin des résultats d'élévation
                    if analysis_type == "slope" and "elevation" in results:
                        # Ajouter l'élévation aux paramètres
                        params_with_elevation = params.copy()
                        params_with_elevation["elevation_data"] = results["elevation"]
                        analysis_result = self._execute_analysis(analysis_type, geometry, params_with_elevation)
                    else:
                        analysis_result = self._execute_analysis(analysis_type, geometry, params)
                    
                    results[analysis_type] = analysis_result
                except Exception as e:
                    errors.append(f"Erreur lors de l'analyse {analysis_type}: {str(e)}")
                    self.logger.error(f"Erreur lors de l'analyse séquentielle {analysis_type}: {str(e)}")
        
        else:
            # Exécution séquentielle de toutes les analyses
            for analysis_type in analysis_types:
                try:
                    # Pour le cas de la pente, nous avons besoin des résultats d'élévation
                    if analysis_type == "slope" and "elevation" in results:
                        # Ajouter l'élévation aux paramètres
                        params_with_elevation = params.copy()
                        params_with_elevation["elevation_data"] = results["elevation"]
                        analysis_result = self._execute_analysis(analysis_type, geometry, params_with_elevation)
                    else:
                        analysis_result = self._execute_analysis(analysis_type, geometry, params)
                    
                    results[analysis_type] = analysis_result
                except Exception as e:
                    errors.append(f"Erreur lors de l'analyse {analysis_type}: {str(e)}")
                    self.logger.error(f"Erreur lors de l'analyse séquentielle {analysis_type}: {str(e)}")
        
        # Calculer les statistiques combinées si nécessaire
        if len(results) > 0:
            try:
                combined_stats = self._compute_combined_statistics(results)
                results["combined_stats"] = combined_stats
            except Exception as e:
                self.logger.error(f"Erreur lors du calcul des statistiques combinées: {str(e)}")
                errors.append(f"Erreur lors du calcul des statistiques combinées: {str(e)}")
        
        # Finaliser les résultats
        execution_time = time.time() - start_time
        output = {
            "success": len(errors) == 0,
            "execution_time": execution_time,
            "results": results
        }
        
        if errors:
            output["errors"] = errors
        
        self.logger.info(f"Analyse de terrain terminée en {execution_time:.2f}s avec {len(errors)} erreurs")
        
        # Enregistrer des métriques
        self.metrics.increment("terrain_analyses")
        if len(errors) > 0:
            self.metrics.increment("terrain_analysis_errors", len(errors))
        
        return output
    
    def _execute_analysis(self, analysis_type: str, geometry: Union[Dict, gpd.GeoDataFrame], 
                         params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un type d'analyse spécifique.
        
        Args:
            analysis_type: Type d'analyse à effectuer
            geometry: Géométrie à analyser
            params: Paramètres spécifiques
            
        Returns:
            Résultats de l'analyse
            
        Raises:
            ValueError: Si le type d'analyse est inconnu
        """
        self.logger.debug(f"Exécution de l'analyse {analysis_type}")
        
        if analysis_type == "elevation":
            return self._execute_elevation_analysis(geometry, params)
        elif analysis_type == "slope":
            return self._execute_slope_analysis(geometry, params)
        elif analysis_type == "hydrology":
            return self._execute_hydrology_analysis(geometry, params)
        elif analysis_type == "risks":
            return self._execute_risk_analysis(geometry, params)
        else:
            raise ValueError(f"Type d'analyse inconnu: {analysis_type}")
    
    def _execute_elevation_analysis(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute l'analyse d'élévation.
        
        Args:
            geometry: Géométrie à analyser
            params: Paramètres spécifiques
            
        Returns:
            Résultats de l'analyse d'élévation
        """
        # Extraire les paramètres spécifiques
        resolution = params.get("elevation_resolution", 10)  # résolution en mètres
        include_stats = params.get("include_elevation_stats", True)
        
        # Exécuter l'analyse
        elevation_data = self.elevation_service.analyze_elevation(geometry, resolution=resolution)
        
        # Calculer des statistiques supplémentaires si demandé
        if include_stats and "elevation_array" in elevation_data:
            elevation_array = elevation_data["elevation_array"]
            if elevation_array is not None and len(elevation_array) > 0:
                # Ajouter des statistiques avancées
                elevation_data["elevation_p10"] = np.percentile(elevation_array, 10)
                elevation_data["elevation_p90"] = np.percentile(elevation_array, 90)
                elevation_data["elevation_range"] = elevation_data["elevation_max"] - elevation_data["elevation_min"]
        
        return elevation_data
    
    def _execute_slope_analysis(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute l'analyse de pente.
        
        Args:
            geometry: Géométrie à analyser
            params: Paramètres spécifiques
            
        Returns:
            Résultats de l'analyse de pente
        """
        # Extraire les paramètres spécifiques
        compute_aspect = params.get("compute_aspect", True)
        
        # Vérifier si on a déjà les données d'élévation
        elevation_data = params.get("elevation_data")
        
        # Exécuter l'analyse
        if elevation_data and "elevation_array" in elevation_data:
            # Utiliser les données d'élévation existantes si disponibles
            slope_data = self.slope_service.calculate_slope_from_elevation(
                elevation_data["elevation_array"],
                elevation_data.get("transform"),
                compute_aspect=compute_aspect
            )
        else:
            # Sinon, faire l'analyse complète
            slope_data = self.slope_service.analyze_slope(geometry, compute_aspect=compute_aspect)
        
        return slope_data
    
    def _execute_hydrology_analysis(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute l'analyse hydrologique.
        
        Args:
            geometry: Géométrie à analyser
            params: Paramètres spécifiques
            
        Returns:
            Résultats de l'analyse hydrologique
        """
        # Extraire les paramètres spécifiques
        buffer_distance = params.get("hydro_buffer", 100)  # buffer en mètres
        include_water_bodies = params.get("include_water_bodies", True)
        
        # Exécuter l'analyse
        hydro_data = self.hydrology_service.analyze_hydrology(
            geometry, 
            buffer_distance=buffer_distance,
            include_water_bodies=include_water_bodies
        )
        
        return hydro_data
    
    def _execute_risk_analysis(self, geometry: Union[Dict, gpd.GeoDataFrame], 
                             params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute l'analyse des risques.
        
        Args:
            geometry: Géométrie à analyser
            params: Paramètres spécifiques
            
        Returns:
            Résultats de l'analyse des risques
        """
        # Paramètres spécifiques pour l'analyse des risques
        risk_types = params.get("risk_types", ["flood", "fire", "erosion", "landslide"])
        season = params.get("season", "summer")
        
        # Préparer les paramètres pour le service de risque
        risk_params = {
            "season": season,
            "include_slope_data": True,
            "flood_buffer": params.get("flood_buffer", 0)
        }
        
        # Exécuter l'analyse
        if len(risk_types) == 4:  # Tous les types de risques
            risk_data = self.risk_service.analyze_all_risks(geometry, risk_params)
        else:
            # Analyser les risques spécifiques demandés
            risk_data = {}
            
            if "flood" in risk_types:
                flood_risk = self.risk_service.analyze_flood_risk(
                    geometry, buffer_distance=risk_params["flood_buffer"]
                )
                risk_data["flood_risk"] = flood_risk
                
            if "fire" in risk_types:
                fire_risk = self.risk_service.analyze_fire_risk(
                    geometry, params={"season": risk_params["season"]}
                )
                risk_data["fire_risk"] = fire_risk
                
            if "erosion" in risk_types:
                erosion_risk = self.risk_service.analyze_erosion_risk(
                    geometry, include_slope_data=risk_params["include_slope_data"]
                )
                risk_data["erosion_risk"] = erosion_risk
                
            if "landslide" in risk_types:
                landslide_risk = self.risk_service.analyze_landslide_risk(geometry)
                risk_data["landslide_risk"] = landslide_risk
        
        return risk_data
    
    def _compute_combined_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule des statistiques combinées à partir des résultats des différentes analyses.
        
        Args:
            results: Résultats des différentes analyses
            
        Returns:
            Statistiques combinées
        """
        combined_stats = {
            "forestry_potential_score": None,
            "constraints": [],
            "opportunities": [],
            "recommended_species": []
        }
        
        # Scores de base pour chaque facteur
        elevation_score = 0.5  # neutre par défaut
        slope_score = 0.5
        hydro_score = 0.5
        risk_score = 0.5
        
        # Facteurs de pondération (doivent sommer à 1)
        weights = {
            "elevation": 0.15,
            "slope": 0.35,
            "hydrology": 0.25,
            "risk": 0.25
        }
        
        # Analyse d'élévation
        if "elevation" in results:
            elev_data = results["elevation"]
            
            # Score basé sur l'altitude moyenne (exemple simplifié)
            # Cela dépendrait en réalité des espèces envisagées et de la région
            mean_elevation = elev_data.get("elevation_mean", 0)
            
            if mean_elevation < 300:
                elevation_score = 0.8  # Favorable pour beaucoup d'espèces
                combined_stats["opportunities"].append("Altitude favorable pour la plupart des espèces forestières")
            elif mean_elevation < 800:
                elevation_score = 0.7  # Bon pour de nombreuses espèces
            elif mean_elevation < 1500:
                elevation_score = 0.5  # Convient à certaines espèces adaptées
                combined_stats["constraints"].append("Altitude moyenne - espèces adaptées à la montagne recommandées")
            else:
                elevation_score = 0.3  # Limitant pour beaucoup d'espèces
                combined_stats["constraints"].append("Haute altitude - forte limitation des espèces possibles")
        
        # Analyse de pente
        if "slope" in results:
            slope_data = results["slope"]
            
            # Score basé sur la pente moyenne
            mean_slope = slope_data.get("slope_mean", 0)
            
            if mean_slope < 5:
                slope_score = 0.9  # Très favorable (terrain plat)
                combined_stats["opportunities"].append("Terrain plat - exploitation forestière facilitée")
            elif mean_slope < 15:
                slope_score = 0.7  # Favorable
            elif mean_slope < 25:
                slope_score = 0.5  # Modérément contraignant
                combined_stats["constraints"].append("Pente modérée - techniques adaptées nécessaires")
            else:
                slope_score = 0.3  # Fortement contraignant
                combined_stats["constraints"].append("Forte pente - exploitation difficile et coûteuse")
                
            # Ajout des espèces recommandées selon l'exposition
            if "aspect_class" in slope_data:
                aspect = slope_data["aspect_class"]
                if aspect in ["S", "SE", "SW"]:
                    combined_stats["recommended_species"].extend(["chêne pubescent", "pin maritime"])
                elif aspect in ["N", "NE", "NW"]:
                    combined_stats["recommended_species"].extend(["hêtre", "douglas"])
        
        # Analyse hydrologique
        if "hydrology" in results:
            hydro_data = results["hydrology"]
            
            # Score basé sur différents facteurs hydrologiques
            if hydro_data.get("has_water_access", False):
                hydro_score = 0.8  # Accès à l'eau est un avantage
                combined_stats["opportunities"].append("Accès à des ressources en eau")
            
            if hydro_data.get("flood_risk", "low") == "high":
                hydro_score = max(0.2, hydro_score - 0.4)  # Pénalité pour risque d'inondation
                combined_stats["constraints"].append("Zone inondable - espèces tolérantes à l'humidité nécessaires")
                combined_stats["recommended_species"].extend(["aulne", "saule", "peuplier"])
        
        # Analyse des risques
        if "risks" in results:
            risk_data = results["risks"]
            
            # Agréger les scores de risque
            risk_factors = []
            
            if "fire_risk" in risk_data and "fire_risk_score" in risk_data["fire_risk"]:
                fire_risk_score = risk_data["fire_risk"]["fire_risk_score"]
                risk_factors.append(1.0 - fire_risk_score)  # Inverser pour que 1 soit bon (pas de risque)
                
                if fire_risk_score > 0.7:
                    combined_stats["constraints"].append("Risque d'incendie élevé - mesures préventives nécessaires")
            
            if "erosion_risk" in risk_data and "erosion_risk_score" in risk_data["erosion_risk"]:
                erosion_risk_score = risk_data["erosion_risk"]["erosion_risk_score"]
                risk_factors.append(1.0 - erosion_risk_score)
                
                if erosion_risk_score > 0.7:
                    combined_stats["constraints"].append("Risque d'érosion élevé - techniques anti-érosion recommandées")
            
            if "landslide_risk" in risk_data and "landslide_risk_score" in risk_data["landslide_risk"]:
                landslide_risk_score = risk_data["landslide_risk"]["landslide_risk_score"]
                risk_factors.append(1.0 - landslide_risk_score)
                
                if landslide_risk_score > 0.6:
                    combined_stats["constraints"].append("Risque de glissement de terrain - précautions particulières requises")
            
            # Moyenne des facteurs de risque (si disponibles)
            if risk_factors:
                risk_score = sum(risk_factors) / len(risk_factors)
            
            # Ajouter les recommandations de risque
            if "recommendations" in risk_data:
                combined_stats["risk_recommendations"] = risk_data["recommendations"]
        
        # Calculer le score de potentiel forestier (moyenne pondérée)
        forestry_potential = (
            elevation_score * weights["elevation"] +
            slope_score * weights["slope"] +
            hydro_score * weights["hydrology"] +
            risk_score * weights["risk"]
        )
        
        # Normaliser entre 0 et 1
        combined_stats["forestry_potential_score"] = round(min(max(forestry_potential, 0), 1), 2)
        
        # Déterminer la classe de potentiel
        if combined_stats["forestry_potential_score"] < 0.3:
            combined_stats["forestry_potential_class"] = "low"
        elif combined_stats["forestry_potential_score"] < 0.6:
            combined_stats["forestry_potential_class"] = "medium"
        else:
            combined_stats["forestry_potential_class"] = "high"
        
        # Dédupliquer les espèces recommandées
        combined_stats["recommended_species"] = list(set(combined_stats["recommended_species"]))
        
        return combined_stats
