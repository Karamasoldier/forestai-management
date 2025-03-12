# forestai/agents/geo_agent/data_loaders/bdtopo/road_analyzer.py

from typing import Dict, List, Any, Union, Optional
import geopandas as gpd
from shapely.geometry import shape, Polygon

from forestai.agents.geo_agent.data_loaders.bdtopo.base_loader import BaseBDTopoLoader

class RoadAnalyzer(BaseBDTopoLoader):
    """
    Classe spécialisée dans l'analyse du réseau routier à partir des données BD TOPO.
    """
    
    def analyze_road_network(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                          buffer_distance: float = 100) -> Dict[str, Any]:
        """
        Analyse le réseau routier pour une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser
            buffer_distance: Distance de buffer en mètres pour la recherche des routes
            
        Returns:
            Dictionnaire contenant les statistiques du réseau routier
        """
        self.logger.info(f"Analyse du réseau routier (buffer: {buffer_distance}m)")
        
        result = {
            "has_road_access": False,
            "nearest_road_distance": None,
            "road_density": 0,
            "road_types": {},
            "road_network_length": 0
        }
        
        try:
            # Charger les données du réseau routier
            roads_data = self.load_data_for_geometry("reseau_routier", geometry, buffer_distance)
            
            if roads_data is None or roads_data.empty:
                self.logger.warning("Aucune route trouvée à proximité")
                return result
            
            # Conversion de la géométrie en objet shapely
            if isinstance(geometry, dict):
                geom = shape(geometry)
            elif isinstance(geometry, gpd.GeoDataFrame):
                geom = geometry.geometry.iloc[0]
            else:
                geom = geometry
            
            # Calculer la distance à la route la plus proche
            search_area = geom.buffer(buffer_distance) if buffer_distance > 0 else geom
            search_area_gdf = gpd.GeoDataFrame(geometry=[search_area], crs="EPSG:2154")
            
            # Choisir les colonnes de type de route
            type_columns = [col for col in roads_data.columns if 'type' in col.lower() or 'nature' in col.lower()]
            type_column = type_columns[0] if type_columns else None
            
            # Calculer les statistiques
            result["has_road_access"] = True
            
            # Longueur totale du réseau routier
            roads_data["length"] = roads_data.geometry.length
            result["road_network_length"] = roads_data["length"].sum()
            
            # Densité du réseau routier (m/km²)
            parcel_area = geom.area / 1_000_000  # en km²
            result["road_density"] = result["road_network_length"] / parcel_area if parcel_area > 0 else 0
            
            # Types de routes
            if type_column:
                road_types_counts = roads_data[type_column].value_counts().to_dict()
                result["road_types"] = road_types_counts
            
            # Calculer la distance à la route la plus proche
            if not roads_data.empty:
                min_distances = []
                boundary = geom.boundary
                for _, road in roads_data.iterrows():
                    min_distances.append(boundary.distance(road.geometry))
                
                result["nearest_road_distance"] = min(min_distances) if min_distances else None
            
            self.logger.info(f"Analyse du réseau routier terminée: {len(roads_data)} routes trouvées")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du réseau routier: {str(e)}")
            return result
