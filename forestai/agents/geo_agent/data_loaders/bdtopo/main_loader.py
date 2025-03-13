# forestai/agents/geo_agent/data_loaders/bdtopo/main_loader.py

from typing import Dict, List, Any, Union, Optional
import geopandas as gpd
from shapely.geometry import shape, Polygon

from forestai.agents.geo_agent.data_loaders.bdtopo.potential_calculator import ForestryPotentialCalculator

class BDTopoLoader(ForestryPotentialCalculator):
    """
    Chargeur principal de données BD TOPO de l'IGN.
    
    Cette classe est le point d'entrée pour toutes les fonctionnalités liées à la BD TOPO.
    Elle hérite de ForestryPotentialCalculator qui lui-même hérite de tous les analyseurs spécialisés.
    
    Fonctionnalités principales :
    - Chargement de données géospatiales à partir des fichiers BD TOPO
    - Analyse du réseau routier
    - Analyse du réseau hydrographique
    - Analyse de la végétation
    - Analyse des bâtiments
    - Calcul du potentiel forestier
    """
    
    def __str__(self) -> str:
        """
        Représentation textuelle du chargeur BD TOPO.
        
        Returns:
            Description du chargeur avec le nombre de thèmes disponibles
        """
        themes_available = len(self.available_files) if hasattr(self, 'available_files') else 0
        return f"BDTopoLoader - {themes_available} thèmes disponibles dans '{self.data_dir}'"
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Fournit un résumé des données BD TOPO disponibles.
        
        Returns:
            Dictionnaire contenant un résumé des thèmes et fichiers disponibles
        """
        if not hasattr(self, 'available_files') or not self.available_files:
            return {"status": "error", "message": "Aucun fichier BD TOPO indexé"}
        
        summary = {
            "status": "success",
            "data_dir": str(self.data_dir),
            "themes_count": len(self.available_files),
            "total_files_count": sum(len(files) for files in self.available_files.values()),
            "themes_details": {}
        }
        
        for theme, files in self.available_files.items():
            theme_info = self.BDTOPO_THEMES.get(theme, {})
            summary["themes_details"][theme] = {
                "description": theme_info.get("description", "Inconnu"),
                "features": theme_info.get("features", []),
                "files_count": len(files),
                "file_examples": [os.path.basename(f) for f in files[:3]] if files else []
            }
        
        return summary
    
    def analyze_parcel(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                     buffer_distance: float = 100) -> Dict[str, Any]:
        """
        Réalise une analyse complète d'une parcelle.
        
        Cette méthode est un point d'entrée pratique pour réaliser toutes les analyses
        disponibles sur une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser (GeoJSON, GeoDataFrame ou Polygon)
            buffer_distance: Distance de buffer en mètres pour les analyses
            
        Returns:
            Dictionnaire contenant tous les résultats d'analyse
        """
        self.logger.info(f"Analyse complète de parcelle (buffer: {buffer_distance}m)")
        
        try:
            # Conversion de la géométrie en objet shapely pour obtenir les informations de base
            if isinstance(geometry, dict):
                geom = shape(geometry)
            elif isinstance(geometry, gpd.GeoDataFrame):
                geom = geometry.geometry.iloc[0]
            else:
                geom = geometry
            
            # Calculer la superficie en hectares
            area_ha = geom.area / 10000  # conversion de m² en ha
            
            # Réaliser toutes les analyses
            vegetation_analysis = self.analyze_vegetation(geometry)
            road_analysis = self.analyze_road_network(geometry, buffer_distance)
            hydro_analysis = self.analyze_hydro_network(geometry, buffer_distance)
            building_analysis = self.analyze_buildings(geometry, buffer_distance)
            
            # Calculer le potentiel forestier
            potential_analysis = self.calculate_forestry_potential(geometry, buffer_distance)
            
            # Assembler tous les résultats
            result = {
                "area_ha": round(area_ha, 2),
                "perimeter_m": round(geom.length, 2),
                "vegetation": vegetation_analysis,
                "roads": road_analysis,
                "hydrology": hydro_analysis,
                "buildings": building_analysis,
                "forestry_potential": potential_analysis
            }
            
            self.logger.info(f"Analyse complète de parcelle terminée: {area_ha:.2f} ha, potentiel={potential_analysis.get('potential_class', 'inconnu')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse complète de parcelle: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur lors de l'analyse: {str(e)}"
            }

# Import des modules standards nécessaires pour les fonctions de la classe
import os
