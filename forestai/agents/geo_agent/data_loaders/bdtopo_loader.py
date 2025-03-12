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
