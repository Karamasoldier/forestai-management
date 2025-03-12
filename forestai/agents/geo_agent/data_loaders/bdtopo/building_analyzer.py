# forestai/agents/geo_agent/data_loaders/bdtopo/building_analyzer.py

from typing import Dict, List, Any, Union, Optional
import geopandas as gpd
from shapely.geometry import shape, Polygon

from forestai.agents.geo_agent.data_loaders.bdtopo.base_loader import BaseBDTopoLoader

class BuildingAnalyzer(BaseBDTopoLoader):
    """
    Classe spécialisée dans l'analyse des bâtiments à partir des données BD TOPO.
    """
    
    def analyze_buildings(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                       buffer_distance: float = 0) -> Dict[str, Any]:
        """
        Analyse les bâtiments pour une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser
            buffer_distance: Distance de buffer en mètres pour la recherche de bâtiments
            
        Returns:
            Dictionnaire contenant les statistiques sur les bâtiments
        """
        self.logger.info(f"Analyse des bâtiments (buffer: {buffer_distance}m)")
        
        result = {
            "has_buildings": False,
            "building_count": 0,
            "building_density": 0,
            "building_types": {},
            "nearest_building_distance": None,
            "total_building_area": 0
        }
        
        try:
            # Charger les données des bâtiments
            buildings_data = self.load_data_for_geometry("batiment", geometry, buffer_distance)
            
            if buildings_data is None or buildings_data.empty:
                self.logger.warning("Aucun bâtiment trouvé")
                return result
            
            # Conversion de la géométrie en objet shapely
            if isinstance(geometry, dict):
                geom = shape(geometry)
            elif isinstance(geometry, gpd.GeoDataFrame):
                geom = geometry.geometry.iloc[0]
            else:
                geom = geometry
            
            # Choisir les colonnes de type de bâtiment
            type_columns = [col for col in buildings_data.columns 
                          if 'type' in col.lower() or 'nature' in col.lower() or 'usage' in col.lower()]
            type_column = type_columns[0] if type_columns else None
            
            # Calculer les statistiques
            result["has_buildings"] = True
            result["building_count"] = len(buildings_data)
            
            # Calculer la surface des bâtiments
            buildings_data["area"] = buildings_data.geometry.area
            result["total_building_area"] = buildings_data["area"].sum()
            
            # Densité de bâtiments (nombre/km²)
            parcel_area = geom.area / 1_000_000  # en km²
            result["building_density"] = result["building_count"] / parcel_area if parcel_area > 0 else 0
            
            # Types de bâtiments
            if type_column:
                result["building_types"] = buildings_data[type_column].value_counts().to_dict()
            
            # Calculer la distance au bâtiment le plus proche
            if not buildings_data.empty:
                min_distances = []
                for _, building in buildings_data.iterrows():
                    min_distances.append(geom.distance(building.geometry))
                
                result["nearest_building_distance"] = min(min_distances) if min_distances else None
            
            self.logger.info(f"Analyse des bâtiments terminée: {result['building_count']} bâtiments trouvés")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des bâtiments: {str(e)}")
            return result
