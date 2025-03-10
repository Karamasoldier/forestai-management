#!/usr/bin/env python3
"""
Module de gestion des données géographiques locales.
Fournit des fonctions pour charger, traiter et interroger des données géographiques stockées localement.
"""

import os
import logging
from pathlib import Path
import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import Point, Polygon, box
import json

logger = logging.getLogger(__name__)

class LocalDataManager:
    """
    Gestionnaire de données géographiques locales pour l'agent de géotraitement.
    Remplace l'accès via API Geoservices/IGN par des accès à des données téléchargées.
    """
    
    def __init__(self, data_path="./data", cache_path="./data/cache"):
        """
        Initialise le gestionnaire de données locales.
        
        Args:
            data_path (str): Chemin vers le répertoire des données brutes
            cache_path (str): Chemin vers le répertoire de cache
        """
        self.data_path = Path(data_path)
        self.cache_path = Path(cache_path)
        
        # Création des répertoires si nécessaires
        self.data_path.mkdir(exist_ok=True, parents=True)
        self.cache_path.mkdir(exist_ok=True, parents=True)
        
        # Dictionnaire des chemins de données par catégorie
        self.data_sources = {
            "cadastre": self.data_path / "raw" / "cadastre",
            "bdtopo": self.data_path / "raw" / "bdtopo",
            "mnt": self.data_path / "raw" / "mnt",
            "occupation_sol": self.data_path / "raw" / "occupation_sol",
            "orthophotos": self.data_path / "raw" / "orthophotos"
        }
        
        # Création des sous-répertoires
        for path in self.data_sources.values():
            path.mkdir(exist_ok=True, parents=True)
        
        # Vérification des données disponibles
        self._scan_available_data()
    
    def _scan_available_data(self):
        """Scanne les répertoires pour identifier les données disponibles"""
        self.data_index = {}
        
        for category, path in self.data_sources.items():
            self.data_index[category] = []
            
            if path.exists():
                for file in path.glob("**/*"):
                    if file.is_file() and file.suffix.lower() in ['.shp', '.tif', '.geojson', '.gpkg']:
                        # Stocker les métadonnées du fichier
                        self.data_index[category].append({
                            "path": str(file),
                            "name": file.name,
                            "format": file.suffix.lower(),
                            "size": file.stat().st_size,
                            "last_modified": file.stat().st_mtime
                        })
        
        # Écriture de l'index dans un fichier JSON pour référence
        with open(self.cache_path / "data_index.json", "w") as f:
            json.dump(self.data_index, f, indent=2, default=str)
        
        logger.info(f"Données disponibles: {sum(len(files) for files in self.data_index.values())} fichiers")
    
    def load_cadastre(self, commune_code=None, section=None):
        """
        Charge les données cadastrales pour une commune et section spécifiques.
        
        Args:
            commune_code (str): Code INSEE de la commune
            section (str): Code de la section cadastrale
            
        Returns:
            GeoDataFrame: Données cadastrales
        """
        if not commune_code:
            raise ValueError("Le code INSEE de la commune est requis")
        
        # Recherche du fichier approprié
        cadastre_files = [f for f in self.data_index.get("cadastre", []) 
                          if commune_code in f["name"] and 
                          (section is None or section in f["name"])]
        
        if not cadastre_files:
            logger.warning(f"Aucune donnée cadastrale trouvée pour {commune_code}")
            return None
        
        # Charger les données
        file_path = cadastre_files[0]["path"]
        try:
            gdf = gpd.read_file(file_path)
            logger.info(f"Données cadastrales chargées: {len(gdf)} parcelles")
            return gdf
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données cadastrales: {e}")
            return None
    
    def load_elevation(self, bbox):
        """
        Charge les données d'élévation pour une zone spécifique.
        
        Args:
            bbox (tuple): Boîte englobante (xmin, ymin, xmax, ymax)
            
        Returns:
            numpy.ndarray: Données d'élévation et métadonnées
        """
        # Trouver le fichier MNT couvrant la zone
        mnt_files = self.data_index.get("mnt", [])
        
        if not mnt_files:
            logger.warning("Aucune donnée d'élévation disponible")
            return None
        
        # TODO: Ajouter logique pour sélectionner le bon fichier MNT
        # Pour l'instant, utiliser le premier fichier disponible
        file_path = mnt_files[0]["path"]
        
        try:
            with rasterio.open(file_path) as src:
                # Vérifier l'intersection
                raster_bbox = box(*src.bounds)
                query_bbox = box(*bbox)
                
                if not raster_bbox.intersects(query_bbox):
                    logger.warning(f"La zone demandée n'est pas couverte par {file_path}")
                    return None
                
                # Découper selon la bbox
                window = src.window(*bbox)
                elevation_data = src.read(1, window=window)
                
                return {
                    "data": elevation_data,
                    "transform": src.window_transform(window),
                    "crs": src.crs
                }
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données d'élévation: {e}")
            return None
    
    def load_landcover(self, bbox):
        """
        Charge les données d'occupation du sol pour une zone spécifique.
        
        Args:
            bbox (tuple): Boîte englobante (xmin, ymin, xmax, ymax)
            
        Returns:
            GeoDataFrame: Données d'occupation du sol
        """
        landcover_files = self.data_index.get("occupation_sol", [])
        
        if not landcover_files:
            logger.warning("Aucune donnée d'occupation du sol disponible")
            return None
        
        file_path = landcover_files[0]["path"]
        
        try:
            # Créer un polygone pour la bbox
            bbox_polygon = box(*bbox)
            
            # Charger les données en filtrant spatialement
            gdf = gpd.read_file(file_path, bbox=bbox)
            
            logger.info(f"Données d'occupation du sol chargées: {len(gdf)} polygones")
            return gdf
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données d'occupation du sol: {e}")
            return None
    
    def get_public_urls(self):
        """
        Renvoie les URLs publiques des services web IGN qui ne nécessitent pas de clé.
        
        Returns:
            dict: Dictionnaire des URLs par type de service
        """
        return {
            "plan": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=PLAN.IGN&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}",
            "ortho": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}",
            "cadastre": "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}",
            "admin": "https://data.geopf.fr/wfs/ogc?service=wfs&version=2.0.0&request=getFeature&typenames=administrativeunits:{layer}&outputformat=application/json"
        }

    def download_and_save_data(self, url, output_path, params=None):
        """
        Télécharge des données depuis une URL et les sauvegarde localement.
        Cette fonction est utile pour mettre à jour les données locales.
        
        Args:
            url (str): URL des données à télécharger
            output_path (str): Chemin où sauvegarder les données
            params (dict): Paramètres additionnels pour la requête
            
        Returns:
            bool: True si le téléchargement a réussi, False sinon
        """
        # Cette méthode serait à implémenter pour récupérer des données
        # depuis les URL publiques et les stocker localement
        # Pour l'instant, c'est juste un placeholder
        logger.info(f"Téléchargement de données depuis {url} non implémenté")
        return False