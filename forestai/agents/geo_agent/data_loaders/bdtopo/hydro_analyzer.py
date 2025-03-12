# forestai/agents/geo_agent/data_loaders/bdtopo/hydro_analyzer.py

from typing import Dict, List, Any, Union, Optional
import geopandas as gpd
from shapely.geometry import shape, Polygon

from forestai.agents.geo_agent.data_loaders.bdtopo.base_loader import BaseBDTopoLoader

class HydroAnalyzer(BaseBDTopoLoader):
    """
    Classe spécialisée dans l'analyse du réseau hydrographique à partir des données BD TOPO.
    """
    
    def analyze_hydro_network(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                           buffer_distance: float = 100) -> Dict[str, Any]:
        """
        Analyse le réseau hydrographique pour une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser
            buffer_distance: Distance de buffer en mètres pour la recherche des cours d'eau
            
        Returns:
            Dictionnaire contenant les statistiques du réseau hydrographique
        """
        self.logger.info(f"Analyse du réseau hydrographique (buffer: {buffer_distance}m)")
        
        result = {
            "has_water_access": False,
            "nearest_water_distance": None,
            "water_network_length": 0,
            "water_types": {},
            "water_bodies": []
        }
        
        try:
            # Charger les données hydrographiques
            hydro_data = self.load_data_for_geometry("hydrographie", geometry, buffer_distance)
            
            if hydro_data is None or hydro_data.empty:
                self.logger.warning("Aucun cours d'eau trouvé à proximité")
                return result
            
            # Conversion de la géométrie en objet shapely
            if isinstance(geometry, dict):
                geom = shape(geometry)
            elif isinstance(geometry, gpd.GeoDataFrame):
                geom = geometry.geometry.iloc[0]
            else:
                geom = geometry
            
            # Séparer les lignes (cours d'eau) et les polygones (plans d'eau)
            lines = hydro_data[hydro_data.geometry.type.isin(['LineString', 'MultiLineString'])]
            polygons = hydro_data[hydro_data.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            
            # Choisir les colonnes de type de cours d'eau
            type_columns = [col for col in hydro_data.columns 
                          if 'type' in col.lower() or 'nature' in col.lower()]
            type_column = type_columns[0] if type_columns else None
            
            # Statistiques sur les cours d'eau
            result["has_water_access"] = len(hydro_data) > 0
            
            if not lines.empty:
                # Longueur totale du réseau hydrographique
                lines["length"] = lines.geometry.length
                result["water_network_length"] = lines["length"].sum()
                
                # Types de cours d'eau
                if type_column and not lines.empty:
                    result["water_types"] = lines[type_column].value_counts().to_dict()
            
            # Statistiques sur les plans d'eau
            if not polygons.empty:
                polygons["area"] = polygons.geometry.area
                
                for _, water_body in polygons.iterrows():
                    water_body_info = {
                        "type": water_body.get(type_column, "Inconnu") if type_column else "Inconnu",
                        "area": float(water_body["area"]),
                        "perimeter": float(water_body.geometry.length)
                    }
                    result["water_bodies"].append(water_body_info)
            
            # Calculer la distance au cours d'eau le plus proche
            if not hydro_data.empty:
                min_distances = []
                boundary = geom.boundary
                for _, water in hydro_data.iterrows():
                    min_distances.append(boundary.distance(water.geometry))
                
                result["nearest_water_distance"] = min(min_distances) if min_distances else None
            
            self.logger.info(f"Analyse hydrographique terminée: {len(hydro_data)} entités trouvées")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse hydrographique: {str(e)}")
            return result
