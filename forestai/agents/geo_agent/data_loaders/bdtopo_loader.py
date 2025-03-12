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
