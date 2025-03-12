# forestai/agents/geo_agent/data_loaders/bdtopo_loader.py

import os
import json
from typing import Dict, List, Any, Union, Optional, Tuple
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, box, Polygon, MultiPolygon, Point, LineString
import glob
from pathlib import Path

from forestai.core.utils.logging import get_logger

class BDTopoLoader:
    """
    Chargeur de données BD TOPO de l'IGN.
    
    Ce loader permet d'extraire des données topographiques pour une géométrie donnée
    à partir des fichiers BD TOPO stockés localement. Il gère notamment :
    - Le réseau routier
    - Le réseau hydrographique
    - Les bâtiments
    - La végétation
    - L'occupation du sol
    - Les zones d'activités
    """
    
    # Structure et noms de fichiers standards de la BD TOPO
    BDTOPO_THEMES = {
        "reseau_routier": {
            "pattern": "*ROUTE*.shp",
            "description": "Réseau routier",
            "features": ["TRONCON_ROUTE", "ROUTE_NOMMEE", "ROUTE_NUMEROTEE"]
        },
        "reseau_ferre": {
            "pattern": "*FERRE*.shp",
            "description": "Réseau ferroviaire",
            "features": ["TRONCON_VOIE_FERREE", "AIRE_TRIAGE"]
        },
        "hydrographie": {
            "pattern": "*HYDROGRAPHIE*.shp",
            "description": "Réseau hydrographique",
            "features": ["TRONCON_COURS_EAU", "SURFACE_EAU", "PLAN_EAU"]
        },
        "batiment": {
            "pattern": "*BATI*.shp",
            "description": "Bâtiments",
            "features": ["BATIMENT", "CONSTRUCTION_LINEAIRE", "CONSTRUCTION_PONCTUELLE"]
        },
        "vegetation": {
            "pattern": "*VEGETATION*.shp",
            "description": "Végétation",
            "features": ["ZONE_VEGETATION", "HAIE"]
        },
        "occupation_sol": {
            "pattern": "*OCCUPATION_SOL*.shp",
            "description": "Occupation du sol",
            "features": ["ZONE_ACTIVITE_INTERET"]
        },
        "relief": {
            "pattern": "*RELIEF*.shp",
            "description": "Relief",
            "features": ["COURBE_NIVEAU", "POINT_COTE"]
        },
        "toponymes": {
            "pattern": "*LIEUX_NOMMES*.shp",
            "description": "Toponymes",
            "features": ["LIEU_DIT_NON_HABITE", "DETAIL_OROGRAPHIQUE", "PAI_NATUREL"]
        }
    }
    
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
    
    def __init__(self, data_dir: str = None):
        """
        Initialise le chargeur de données BD TOPO.
        
        Args:
            data_dir: Répertoire contenant les données BD TOPO (si None, utilise la variable d'env BDTOPO_DIR)
        """
        # Initialiser le logger
        self.logger = get_logger(name="loader.bdtopo", level="INFO")
        
        # Définir le répertoire de données
        if data_dir is None:
            data_dir = os.environ.get("BDTOPO_DIR", "data/raw/bdtopo")
        
        self.data_dir = Path(data_dir)
        
        if not os.path.exists(self.data_dir):
            self.logger.warning(f"Le répertoire de données BD TOPO n'existe pas: {self.data_dir}")
        else:
            self.logger.info(f"Utilisation du répertoire BD TOPO: {self.data_dir}")
            # Indexer les fichiers disponibles
            self._index_files()
    
    def _index_files(self) -> None:
        """
        Indexe les fichiers BD TOPO disponibles dans le répertoire de données.
        """
        self.available_files = {}
        
        for theme, theme_info in self.BDTOPO_THEMES.items():
            pattern = theme_info["pattern"]
            found_files = list(glob.glob(str(self.data_dir / "**" / pattern), recursive=True))
            
            if found_files:
                self.available_files[theme] = found_files
                self.logger.info(f"Thème '{theme}': {len(found_files)} fichier(s) trouvé(s)")
            else:
                self.logger.warning(f"Aucun fichier trouvé pour le thème '{theme}' (pattern: {pattern})")
        
        if not self.available_files:
            self.logger.error(f"Aucun fichier BD TOPO trouvé dans {self.data_dir}")
        else:
            self.logger.info(f"Indexation terminée: {sum(len(files) for files in self.available_files.values())} fichier(s) au total")
    
    def get_available_themes(self) -> List[str]:
        """
        Retourne la liste des thèmes disponibles dans les données indexées.
        
        Returns:
            Liste des thèmes disponibles
        """
        return list(self.available_files.keys())
    
    def load_data_for_geometry(self, theme: str, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                              buffer_distance: float = 0) -> Optional[gpd.GeoDataFrame]:
        """
        Charge les données BD TOPO pour un thème et une géométrie donnés.
        
        Args:
            theme: Thème BD TOPO à charger
            geometry: Géométrie pour laquelle charger les données (GeoJSON, GeoDataFrame ou Polygon)
            buffer_distance: Distance de buffer en mètres à appliquer à la géométrie
            
        Returns:
            GeoDataFrame contenant les données BD TOPO, ou None en cas d'erreur
        """
        if theme not in self.available_files or not self.available_files[theme]:
            self.logger.error(f"Thème '{theme}' non disponible ou sans fichiers")
            return None
        
        try:
            # Conversion de la géométrie en objet shapely
            if isinstance(geometry, dict):  # GeoJSON
                geom = shape(geometry)
            elif isinstance(geometry, gpd.GeoDataFrame):
                geom = geometry.geometry.iloc[0]
            else:
                geom = geometry
            
            # Appliquer le buffer si nécessaire
            if buffer_distance > 0:
                search_geom = geom.buffer(buffer_distance)
            else:
                search_geom = geom
            
            # Enveloppe pour recherche rapide
            bounds = search_geom.bounds
            
            results = []
            
            # Parcourir tous les fichiers du thème
            for file_path in self.available_files[theme]:
                self.logger.debug(f"Chargement du fichier {file_path}")
                
                try:
                    # Charger le shapefile avec GeoPandas
                    gdf = gpd.read_file(file_path, bbox=bounds)
                    
                    # Si des données ont été trouvées dans l'enveloppe
                    if not gdf.empty:
                        # Filtrer par intersection avec la géométrie de recherche
                        # Assurer que la projection est en Lambert 93 (EPSG:2154)
                        if gdf.crs is None:
                            self.logger.warning(f"Le fichier {file_path} n'a pas de CRS défini, on suppose EPSG:2154")
                            gdf.set_crs("EPSG:2154", inplace=True)
                        elif gdf.crs != "EPSG:2154":
                            gdf = gdf.to_crs("EPSG:2154")
                        
                        # Ajouter le nom du fichier source comme attribut
                        gdf['source_file'] = os.path.basename(file_path)
                        
                        # Filtrer par intersection spatiale
                        mask = gdf.intersects(search_geom)
                        filtered_gdf = gdf[mask].copy()
                        
                        if not filtered_gdf.empty:
                            results.append(filtered_gdf)
                            self.logger.debug(f"Fichier {file_path}: {len(filtered_gdf)} entités trouvées")
                
                except Exception as e:
                    self.logger.error(f"Erreur lors du chargement du fichier {file_path}: {str(e)}")
                    continue
            
            # Combiner tous les résultats
            if results:
                combined_gdf = pd.concat(results, ignore_index=True)
                self.logger.info(f"Thème '{theme}': {len(combined_gdf)} entités trouvées au total")
                return combined_gdf
            else:
                self.logger.warning(f"Aucune donnée trouvée pour le thème '{theme}' et la géométrie spécifiée")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données: {str(e)}")
            return None
            
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
