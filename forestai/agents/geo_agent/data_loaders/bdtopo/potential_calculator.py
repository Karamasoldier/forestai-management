# forestai/agents/geo_agent/data_loaders/bdtopo/potential_calculator.py

from typing import Dict, List, Any, Union, Optional
import geopandas as gpd
from shapely.geometry import shape, Polygon

from forestai.agents.geo_agent.data_loaders.bdtopo.base_loader import BaseBDTopoLoader
from forestai.agents.geo_agent.data_loaders.bdtopo.vegetation_analyzer import VegetationAnalyzer
from forestai.agents.geo_agent.data_loaders.bdtopo.road_analyzer import RoadAnalyzer
from forestai.agents.geo_agent.data_loaders.bdtopo.hydro_analyzer import HydroAnalyzer
from forestai.agents.geo_agent.data_loaders.bdtopo.building_analyzer import BuildingAnalyzer

class ForestryPotentialCalculator(VegetationAnalyzer, RoadAnalyzer, HydroAnalyzer, BuildingAnalyzer):
    """
    Classe pour calculer le potentiel forestier d'une parcelle à partir de l'analyse des données BD TOPO.
    
    Cette classe combine les fonctionnalités des différents analyseurs pour évaluer le potentiel global.
    """
    
    def calculate_forestry_potential(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                                  buffer_distance: float = 100) -> Dict[str, Any]:
        """
        Calcule le potentiel forestier basé sur les données BD TOPO.
        
        Args:
            geometry: Géométrie à analyser
            buffer_distance: Distance de buffer en mètres pour les analyses
            
        Returns:
            Dictionnaire contenant le score de potentiel et les analyses détaillées
        """
        self.logger.info(f"Calcul du potentiel forestier (buffer: {buffer_distance}m)")
        
        # Initialiser le résultat
        result = {
            "potential_score": 0.5,  # Score par défaut (neutre)
            "potential_class": "Moyen",
            "constraints": [],
            "opportunities": [],
            "recommended_species": [],
            "vegetation_analysis": None,
            "hydro_analysis": None,
            "road_analysis": None,
            "building_analysis": None
        }
        
        try:
            # Réaliser les différentes analyses
            vegetation_analysis = self.analyze_vegetation(geometry)
            hydro_analysis = self.analyze_hydro_network(geometry, buffer_distance)
            road_analysis = self.analyze_road_network(geometry, buffer_distance)
            building_analysis = self.analyze_buildings(geometry, buffer_distance)
            
            # Stocker les analyses
            result["vegetation_analysis"] = vegetation_analysis
            result["hydro_analysis"] = hydro_analysis
            result["road_analysis"] = road_analysis
            result["building_analysis"] = building_analysis
            
            # Calcul du score de potentiel forestier
            score_components = []
            
            # 1. Végétation existante
            if vegetation_analysis["has_vegetation"]:
                veg_score = min(1.0, vegetation_analysis["vegetation_coverage"] / 70.0)
                score_components.append(veg_score)
                
                # Analyser le type de végétation dominant
                if vegetation_analysis["dominant_vegetation"]:
                    dom_veg = vegetation_analysis["dominant_vegetation"]
                    veg_type = dom_veg["type"]
                    veg_category = dom_veg["category"]
                    
                    # Ajuster selon la catégorie
                    if veg_category == "Forêt":
                        result["opportunities"].append(f"Présence de forêt existante ({dom_veg['percentage']:.1f}%)")
                        # Suggérer des espèces adaptées
                        result["recommended_species"].extend(["chêne", "hêtre", "pin sylvestre"])
                    elif veg_category == "Lande":
                        result["opportunities"].append(f"Présence de landes ({dom_veg['percentage']:.1f}%), bon potentiel de reboisement")
                        result["recommended_species"].extend(["pin maritime", "bouleau", "chêne tauzin"])
                    elif veg_category == "Zone_agricole":
                        result["constraints"].append(f"Zone agricole ({dom_veg['percentage']:.1f}%), conversion nécessaire")
                        result["recommended_species"].extend(["noyer", "merisier", "alisier"])
            else:
                result["constraints"].append("Absence de végétation identifiée dans les données BD TOPO")
            
            # 2. Accès aux routes
            if road_analysis["has_road_access"]:
                road_distance = road_analysis.get("nearest_road_distance")
                if road_distance is not None:
                    if road_distance < 100:
                        result["opportunities"].append(f"Accès routier très proche ({road_distance:.1f}m)")
                        road_score = 0.8
                    elif road_distance < 500:
                        result["opportunities"].append(f"Accès routier proche ({road_distance:.1f}m)")
                        road_score = 0.7
                    else:
                        result["constraints"].append(f"Accès routier éloigné ({road_distance:.1f}m)")
                        road_score = 0.4
                    score_components.append(road_score)
            else:
                result["constraints"].append("Absence d'accès routier dans la zone de buffer")
                score_components.append(0.3)  # Pénalité pour l'absence d'accès
            
            # 3. Accès à l'eau
            if hydro_analysis["has_water_access"]:
                water_distance = hydro_analysis.get("nearest_water_distance")
                if water_distance is not None:
                    if water_distance < 200:
                        result["opportunities"].append(f"Accès à l'eau très proche ({water_distance:.1f}m)")
                        water_score = 0.8
                    elif water_distance < 1000:
                        result["opportunities"].append(f"Accès à l'eau relativement proche ({water_distance:.1f}m)")
                        water_score = 0.7
                    else:
                        water_score = 0.5
                    score_components.append(water_score)
                
                if hydro_analysis["water_bodies"]:
                    result["opportunities"].append(f"Présence de {len(hydro_analysis['water_bodies'])} plan(s) d'eau")
            
            # 4. Présence de bâtiments
            if building_analysis["has_buildings"]:
                building_count = building_analysis["building_count"]
                building_density = building_analysis["building_density"]
                
                if building_density > 50:  # > 50 bâtiments/km²
                    result["constraints"].append(f"Zone fortement construite ({building_count} bâtiments, {building_density:.1f}/km²)")
                    score_components.append(0.2)
                elif building_density > 10:  # > 10 bâtiments/km²
                    result["constraints"].append(f"Présence significative de bâtiments ({building_count} bâtiments)")
                    score_components.append(0.4)
            
            # Calculer le score moyen si des composantes existent
            if score_components:
                result["potential_score"] = sum(score_components) / len(score_components)
            
            # Déterminer la classe de potentiel
            if result["potential_score"] >= 0.8:
                result["potential_class"] = "Excellent"
            elif result["potential_score"] >= 0.6:
                result["potential_class"] = "Bon"
            elif result["potential_score"] >= 0.4:
                result["potential_class"] = "Moyen"
            elif result["potential_score"] >= 0.2:
                result["potential_class"] = "Faible"
            else:
                result["potential_class"] = "Très faible"
            
            # Dédupliquer les espèces recommandées
            result["recommended_species"] = list(set(result["recommended_species"]))
            
            # Si peu de recommendations, ajouter des espèces polyvalentes
            if len(result["recommended_species"]) < 3:
                additional_species = ["chêne sessile", "pin sylvestre", "châtaignier", "érable champêtre"]
                # Ajouter uniquement les espèces qui ne sont pas déjà présentes
                for species in additional_species:
                    if species not in result["recommended_species"]:
                        result["recommended_species"].append(species)
                        if len(result["recommended_species"]) >= 5:
                            break
            
            self.logger.info(f"Calcul du potentiel forestier terminé: score={result['potential_score']:.2f}, classe={result['potential_class']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul du potentiel forestier: {str(e)}")
            return result
