#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Connecteur pour les API de données de télédétection.

Ce module fournit des interfaces standardisées pour se connecter aux différentes 
API de fournisseurs de données de télédétection (ex: Copernicus, USGS) et 
télécharger les données.
"""

import os
import requests
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.remote_sensing.models import (
    RemoteSensingSource,
    SatelliteImageMetadata,
    LidarPointCloudMetadata,
    RemoteSensingData
)
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

logger = get_logger(__name__)


class DataAPI(ABC):
    """Interface abstraite pour les API de données de télédétection."""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authentifie l'application auprès de l'API."""
        pass
    
    @abstractmethod
    def search(self, bbox: Tuple[float, float, float, float], 
              start_date: datetime, end_date: datetime, 
              **kwargs) -> List[Dict[str, Any]]:
        """
        Recherche des données disponibles.
        
        Args:
            bbox: Tuple (min_lon, min_lat, max_lon, max_lat) définissant la zone d'intérêt
            start_date: Date de début pour la recherche
            end_date: Date de fin pour la recherche
            **kwargs: Arguments supplémentaires spécifiques à l'API
            
        Returns:
            Liste des résultats de recherche
        """
        pass
    
    @abstractmethod
    def download(self, product_id: str, output_dir: Path, **kwargs) -> Optional[Path]:
        """
        Télécharge un produit spécifique.
        
        Args:
            product_id: Identifiant du produit à télécharger
            output_dir: Répertoire de sortie pour le téléchargement
            **kwargs: Arguments supplémentaires spécifiques à l'API
            
        Returns:
            Chemin vers les données téléchargées ou None en cas d'échec
        """
        pass
    
    @abstractmethod
    def get_quota_status(self) -> Dict[str, Any]:
        """
        Récupère le statut des quotas pour cette API.
        
        Returns:
            Informations sur les quotas (restant, total, limitations)
        """
        pass


class CopernicusOpenAccessHubAPI(DataAPI):
    """Connecteur pour l'API Copernicus Open Access Hub (Sentinel)."""
    
    BASE_URL = "https://scihub.copernicus.eu/dhus"
    SEARCH_URL = f"{BASE_URL}/search"
    
    def __init__(self, username: str = None, password: str = None):
        """
        Initialise le connecteur Copernicus.
        
        Args:
            username: Nom d'utilisateur (si None, utilise COPERNICUS_USERNAME de l'env)
            password: Mot de passe (si None, utilise COPERNICUS_PASSWORD de l'env)
        """
        self.username = username or os.environ.get("COPERNICUS_USERNAME")
        self.password = password or os.environ.get("COPERNICUS_PASSWORD")
        self.session = requests.Session()
        self.token = None
        self.token_expiry = None
        
        if not self.username or not self.password:
            logger.warning("Identifiants Copernicus non définis. Utilisez authenticate() avec les paramètres.")
    
    def authenticate(self, username: str = None, password: str = None) -> bool:
        """
        Authentifie auprès de l'API Copernicus.
        
        Args:
            username: Nom d'utilisateur (si None, utilise celui fourni au constructeur)
            password: Mot de passe (si None, utilise celui fourni au constructeur)
            
        Returns:
            True si l'authentification a réussi, False sinon
        """
        # Utiliser les identifiants fournis ou ceux du constructeur
        auth_username = username or self.username
        auth_password = password or self.password
        
        if not auth_username or not auth_password:
            logger.error("Identifiants Copernicus manquants")
            return False
        
        try:
            # Se connecter avec Basic Auth
            self.session.auth = (auth_username, auth_password)
            response = self.session.get(f"{self.BASE_URL}/api/stub/version")
            
            if response.status_code == 200:
                # Mettre à jour les identifiants si fournis en paramètres
                if username:
                    self.username = username
                if password:
                    self.password = password
                
                self.token_expiry = datetime.now() + timedelta(hours=1)
                logger.info("Authentification Copernicus réussie")
                return True
            else:
                logger.error(f"Échec de l'authentification Copernicus: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification Copernicus: {str(e)}")
            return False
    
    @cached(data_type=CacheType.API_RESPONSE, policy=CachePolicy.DAILY)
    def search(self, bbox: Tuple[float, float, float, float], 
              start_date: datetime, end_date: datetime, 
              platform: str = "Sentinel-2", 
              product_type: str = "S2MSI2A",
              cloud_cover_max: int = 30,
              **kwargs) -> List[Dict[str, Any]]:
        """
        Recherche des produits Sentinel.
        
        Args:
            bbox: Tuple (min_lon, min_lat, max_lon, max_lat) délimitant la zone
            start_date: Date de début de la période
            end_date: Date de fin de la période
            platform: Plateforme (Sentinel-1, Sentinel-2, etc.)
            product_type: Type de produit
            cloud_cover_max: Couverture nuageuse maximale (%)
            **kwargs: Arguments supplémentaires (offset, limit, etc.)
            
        Returns:
            Liste des produits correspondants aux critères
        """
        # Vérifier que l'utilisateur est authentifié
        if not self.session.auth:
            if not self.authenticate():
                logger.error("Impossible de rechercher sans authentification")
                return []
        
        # Formatage des dates pour l'API
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Formatage du BBox pour l'API (format: min_lon,min_lat,max_lon,max_lat)
        bbox_str = ",".join(map(str, bbox))
        
        # Construction de la requête OpenSearch
        query = f"platformname:{platform} AND producttype:{product_type} AND cloudcoverpercentage:[0 TO {cloud_cover_max}]"
        query += f" AND beginposition:[{start_str} TO {end_str}]"
        query += f' AND footprint:"Intersects(POLYGON(({bbox[0]} {bbox[1]}, {bbox[0]} {bbox[3]}, {bbox[2]} {bbox[3]}, {bbox[2]} {bbox[1]}, {bbox[0]} {bbox[1]}))"'
        
        # Pagination
        offset = kwargs.get('offset', 0)
        limit = kwargs.get('limit', 100)
        
        # Paramètres de la requête
        params = {
            'q': query,
            'format': 'json',
            'start': offset,
            'rows': limit,
            'orderby': 'beginposition asc'
        }
        
        try:
            response = self.session.get(self.SEARCH_URL, params=params)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'feed' in result and 'entry' in result['feed']:
                    entries = result['feed']['entry']
                    # Gérer le cas où un seul résultat est retourné (pas dans une liste)
                    if not isinstance(entries, list):
                        entries = [entries]
                    
                    # Formater les résultats
                    products = []
                    for entry in entries:
                        product = {
                            'id': entry.get('id', ''),
                            'title': entry.get('title', ''),
                            'date': entry.get('date', {}).get('content', ''),
                            'link': next((link.get('href', '') for link in entry.get('link', []) 
                                        if link.get('rel') == 'alternative'), ''),
                            'download_link': next((link.get('href', '') for link in entry.get('link', []) 
                                                if link.get('rel') == 'self'), ''),
                            'summary': entry.get('summary', {}).get('content', ''),
                            'cloud_cover': float(entry.get('double', {}).get('content', 0)) 
                                          if 'double' in entry else 0
                        }
                        products.append(product)
                    
                    logger.info(f"Recherche réussie: {len(products)} produits trouvés")
                    return products
                else:
                    logger.warning("Aucun résultat trouvé ou format de réponse inattendu")
                    return []
            else:
                logger.error(f"Échec de la recherche: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return []
    
    def download(self, product_id: str, output_dir: Path, **kwargs) -> Optional[Path]:
        """
        Télécharge un produit Sentinel.
        
        Args:
            product_id: Identifiant du produit à télécharger
            output_dir: Répertoire de sortie
            **kwargs: Paramètres supplémentaires
            
        Returns:
            Chemin vers le fichier téléchargé ou None si échec
        """
        # Vérifier que l'utilisateur est authentifié
        if not self.session.auth:
            if not self.authenticate():
                logger.error("Impossible de télécharger sans authentification")
                return None
        
        # S'assurer que le répertoire de sortie existe
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Obtenir l'URL de téléchargement
            download_url = f"{self.BASE_URL}/odata/v1/Products('{product_id}')/$value"
            
            # Nom du fichier de sortie (utiliser l'ID du produit)
            output_file = output_dir / f"{product_id}.zip"
            
            # Télécharger le fichier par blocs
            with self.session.get(download_url, stream=True) as response:
                if response.status_code == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    logger.info(f"Téléchargement de {product_id} ({total_size / (1024*1024):.2f} MB)")
                    
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Afficher la progression toutes les 10%
                                if total_size > 0 and downloaded % (total_size // 10) < 8192:
                                    progress = (downloaded / total_size) * 100
                                    logger.info(f"Progression: {progress:.1f}%")
                    
                    logger.info(f"Téléchargement terminé: {output_file}")
                    return output_file
                else:
                    logger.error(f"Échec du téléchargement: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement: {str(e)}")
            return None
    
    def get_quota_status(self) -> Dict[str, Any]:
        """
        Récupère le statut des quotas Copernicus.
        
        Returns:
            Informations sur les quotas (restant, utilisé, limite)
        """
        # Vérifier que l'utilisateur est authentifié
        if not self.session.auth:
            if not self.authenticate():
                logger.error("Impossible d'obtenir le statut des quotas sans authentification")
                return {"error": "Non authentifié"}
        
        try:
            # Obtenir les informations de quota en interrogeant l'API utilisateur
            response = self.session.get(f"{self.BASE_URL}/api/stub/quota")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Échec de la récupération des quotas: {response.status_code}")
                return {"error": f"Code d'erreur: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des quotas: {str(e)}")
            return {"error": str(e)}


class RemoteDataConnector:
    """
    Gestionnaire central des connexions aux API de données de télédétection.
    
    Cette classe permet d'unifier l'accès aux différentes sources de données
    de télédétection à travers une interface commune.
    """
    
    def __init__(self):
        """Initialise le connecteur de données de télédétection."""
        self.apis = {}
        self.initialized = False
        logger.info("RemoteDataConnector initialisé")
    
    def initialize(self, config: Dict[str, Any] = None):
        """
        Initialise les connexions aux API configurées.
        
        Args:
            config: Configuration des API à initialiser (si None, utilise la config par défaut)
        """
        if config is None:
            # Utiliser la configuration par défaut (variables d'environnement)
            config = {
                "copernicus": {
                    "username": os.environ.get("COPERNICUS_USERNAME"),
                    "password": os.environ.get("COPERNICUS_PASSWORD")
                }
                # Autres API peuvent être ajoutées ici
            }
        
        # Initialiser les API configurées
        if "copernicus" in config:
            self.apis["copernicus"] = CopernicusOpenAccessHubAPI(
                username=config["copernicus"].get("username"),
                password=config["copernicus"].get("password")
            )
        
        # Authentifier chaque API
        for name, api in self.apis.items():
            authenticated = api.authenticate()
            logger.info(f"API {name}: {'authentifiée' if authenticated else 'échec d\'authentification'}")
        
        self.initialized = True
        logger.info(f"RemoteDataConnector initialisé avec {len(self.apis)} API")
    
    def get_api(self, source: Union[str, RemoteSensingSource]) -> Optional[DataAPI]:
        """
        Récupère une API par son nom ou type de source.
        
        Args:
            source: Nom de l'API ou type de source
            
        Returns:
            Instance de l'API ou None si non disponible
        """
        if not self.initialized:
            logger.warning("RemoteDataConnector non initialisé. Appelez initialize() d'abord.")
            return None
        
        # Conversion de RemoteSensingSource en nom d'API
        if isinstance(source, RemoteSensingSource):
            source_map = {
                RemoteSensingSource.SENTINEL_1: "copernicus",
                RemoteSensingSource.SENTINEL_2: "copernicus",
                RemoteSensingSource.LANDSAT_8: "usgs", 
                RemoteSensingSource.LANDSAT_9: "usgs",
                # Mappings supplémentaires à ajouter
            }
            source = source_map.get(source)
            
            if source is None:
                logger.error(f"Aucune API disponible pour la source {source}")
                return None
        
        # Récupérer l'API par son nom
        api = self.apis.get(source.lower())
        
        if api is None:
            logger.error(f"API {source} non disponible")
        
        return api
    
    def search_data(self, source: Union[str, RemoteSensingSource],
                  bbox: Tuple[float, float, float, float],
                  start_date: datetime, end_date: datetime,
                  **kwargs) -> List[Dict[str, Any]]:
        """
        Recherche des données de télédétection.
        
        Args:
            source: Source des données
            bbox: Tuple (min_lon, min_lat, max_lon, max_lat)
            start_date: Date de début
            end_date: Date de fin
            **kwargs: Paramètres spécifiques à la source
            
        Returns:
            Liste des résultats de recherche
        """
        api = self.get_api(source)
        
        if api is None:
            return []
        
        return api.search(bbox, start_date, end_date, **kwargs)
    
    def download_data(self, source: Union[str, RemoteSensingSource],
                    product_id: str, output_dir: Path,
                    **kwargs) -> Optional[Path]:
        """
        Télécharge des données de télédétection.
        
        Args:
            source: Source des données
            product_id: Identifiant du produit
            output_dir: Répertoire de sortie
            **kwargs: Paramètres spécifiques à la source
            
        Returns:
            Chemin vers les données téléchargées ou None si échec
        """
        api = self.get_api(source)
        
        if api is None:
            return None
        
        return api.download(product_id, output_dir, **kwargs)
    
    def create_metadata_from_search_result(self, source: RemoteSensingSource,
                                          result: Dict[str, Any]) -> Union[SatelliteImageMetadata, LidarPointCloudMetadata]:
        """
        Crée des métadonnées à partir d'un résultat de recherche.
        
        Args:
            source: Source des données
            result: Résultat de recherche
            
        Returns:
            Métadonnées créées
        """
        # Déterminer le type de métadonnées à créer selon la source
        is_satellite = source in (RemoteSensingSource.SENTINEL_2, RemoteSensingSource.SENTINEL_1,
                                 RemoteSensingSource.LANDSAT_8, RemoteSensingSource.LANDSAT_9,
                                 RemoteSensingSource.SPOT, RemoteSensingSource.MODIS,
                                 RemoteSensingSource.PLANET, RemoteSensingSource.RAPIDEYE)
        
        is_lidar = source in (RemoteSensingSource.LIDAR_AERIEN, RemoteSensingSource.LIDAR_TERRESTRE,
                             RemoteSensingSource.LIDAR_DRONE)
        
        if is_satellite:
            # Créer des métadonnées satellite
            try:
                acquisition_date = datetime.fromisoformat(result.get('date', '').replace('Z', '+00:00'))
            except (ValueError, TypeError):
                acquisition_date = datetime.now()
            
            return SatelliteImageMetadata(
                source=source,
                acquisition_date=acquisition_date,
                cloud_cover_percentage=result.get('cloud_cover', 0),
                spatial_resolution=10.0,  # Valeur par défaut, à ajuster selon la source
                bands=[],  # À extraire des métadonnées détaillées
                utm_zone="",  # À extraire des métadonnées détaillées
                epsg_code=0,  # À extraire des métadonnées détaillées
                tile_id=result.get('id', ''),
                metadata_url=result.get('link', ''),
                provider="Copernicus" if source in (RemoteSensingSource.SENTINEL_1, RemoteSensingSource.SENTINEL_2) else ""
            )
        
        elif is_lidar:
            # Créer des métadonnées LIDAR (exemple simplifié)
            return LidarPointCloudMetadata(
                source=source,
                acquisition_date=datetime.now(),
                point_density=0.0,
                num_returns=0,
                classification_available=False,
                epsg_code=0
            )
        
        else:
            # Type non supporté
            raise ValueError(f"Type de source non supporté pour les métadonnées: {source}")
