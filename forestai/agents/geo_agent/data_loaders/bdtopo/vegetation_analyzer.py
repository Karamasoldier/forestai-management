# forestai/agents/geo_agent/data_loaders/bdtopo/vegetation_analyzer.py

from typing import Dict, List, Any, Union, Optional
import geopandas as gpd
from shapely.geometry import shape, Polygon

from forestai.agents.geo_agent.data_loaders.bdtopo.base_loader import BaseBDTopoLoader

class VegetationAnalyzer(BaseBDTopoLoader):
    """
    Classe spécialisée dans l'analyse de la végétation à partir des données BD TOPO.
    """
    
    # Mapping des catégories de végétation dans la BD TOPO
    VEGETATION_CATEGORIES = {
        "Forêt": ["Forêt fermée de feuillus", "Forêt fermée de conifères", "Forêt fermée mixte", 
                "Forêt ouverte", "Peupleraie"],
        "Boisement_lineaire": ["Haie", "Rangée d'arbres"],
        "Zone_arboree": ["Bois", "Forêt", "Bosquet"],
        "Lande": ["Lande ligneuse", "Lande herbacée"],
        "Zone_agricole": ["Culture", "Vigne", "Verger"]
    }
    
    # Mapping inverse pour retrouver la catégorie à partir du type
    VEGETATION_TYPE_TO_CATEGORY = {}
    for category, types in VEGETATION_CATEGORIES.items():
        for veg_type in types:
            VEGETATION_TYPE_TO_CATEGORY[veg_type] = category
    
    def analyze_vegetation(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                        buffer_distance: float = 0) -> Dict[str, Any]:
        """
        Analyse la végétation pour une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser
            buffer_distance: Distance de buffer en mètres pour la recherche de végétation
            
        Returns:
            Dictionnaire contenant les statistiques de végétation
        """
        self.logger.info(f"Analyse de la végétation (buffer: {buffer_distance}m)")
        
        result = {
            "has_vegetation": False,
            "vegetation_coverage": 0,
            "dominant_vegetation": None,
            "vegetation_types": {},
            "vegetation_areas": {}
        }
        
        try:
            # Charger les données de végétation
            vegetation_data = self.load_data_for_geometry("vegetation", geometry, buffer_distance)
            
            if vegetation_data is None or vegetation_data.empty:
                self.logger.warning("Aucune donnée de végétation trouvée")
                return result
            
            # Conversion de la géométrie en objet shapely
            if isinstance(geometry, dict):
                geom = shape(geometry)
            elif isinstance(geometry, gpd.GeoDataFrame):
                geom = geometry.geometry.iloc[0]
            else:
                geom = geometry
            
            # Choisir les colonnes de type de végétation
            type_columns = [col for col in vegetation_data.columns 
                         if 'type' in col.lower() or 'nature' in col.lower()]
            type_column = type_columns[0] if type_columns else None
            
            if not type_column:
                self.logger.warning("Colonne de type de végétation non trouvée")
            
            # Calculer les surfaces
            vegetation_data["area"] = vegetation_data.geometry.area
            total_area = geom.area
            vegetation_area = vegetation_data["area"].sum()
            
            # Calculer le taux de couverture
            result["has_vegetation"] = vegetation_area > 0
            result["vegetation_coverage"] = (vegetation_area / total_area) * 100 if total_area > 0 else 0
            
            # Types de végétation
            if type_column:
                # Agréger par type
                veg_types = vegetation_data.groupby(type_column).agg({
                    "area": "sum"
                }).reset_index()
                
                # Trouver le type dominant
                if not veg_types.empty:
                    dominant_type = veg_types.loc[veg_types["area"].idxmax()]
                    result["dominant_vegetation"] = {
                        "type": dominant_type[type_column],
                        "area": float(dominant_type["area"]),
                        "percentage": float(dominant_type["area"] / vegetation_area * 100) if vegetation_area > 0 else 0,
                        "category": self.VEGETATION_TYPE_TO_CATEGORY.get(dominant_type[type_column], "Autre")
                    }
                
                # Statistiques par type
                result["vegetation_types"] = veg_types[type_column].value_counts().to_dict()
                
                # Surface par type
                for _, row in veg_types.iterrows():
                    veg_type = row[type_column]
                    result["vegetation_areas"][veg_type] = float(row["area"])
            
            self.logger.info(f"Analyse de la végétation terminée: {len(vegetation_data)} zones trouvées")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de la végétation: {str(e)}")
            return result
