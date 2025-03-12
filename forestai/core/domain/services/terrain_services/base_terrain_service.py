# forestai/core/domain/services/terrain_services/base_terrain_service.py

import os
from pathlib import Path
from typing import Optional, Dict, Any
import pyproj
from shapely.ops import transform

from forestai.core.domain.models.parcel import Parcel
from forestai.core.utils.logging_config import setup_agent_logging

class BaseTerrainService:
    """
    Classe de base pour les services d'analyse de terrain.
    Fournit les fonctionnalités communes utilisées par les services spécialisés.
    """
    
    def __init__(self, data_dir: Optional[str] = None, logger_name: str = "TerrainService"):
        """
        Initialise le service de base.
        
        Args:
            data_dir: Répertoire contenant les données géographiques
            logger_name: Nom du logger à utiliser
        """
        # Configuration du logger
        self.logger = setup_agent_logging(
            agent_name=logger_name, 
            level="INFO",
            context={"module": "domain.services.terrain"}
        )
        
        # Répertoire des données
        if data_dir is None:
            data_dir = os.getenv("GEODATA_DIR", "data/raw")
        self.data_dir = Path(data_dir)
        
        # Système de coordonnées de référence: Lambert 93 pour la France
        self.reference_crs = "EPSG:2154"  # Lambert 93
        
        self.logger.info(f"Service {logger_name} initialisé avec data_dir={self.data_dir}")
    
    def _ensure_crs(self, geometry, source_crs=None, target_crs="EPSG:2154"):
        """Assure que la géométrie est dans le système de coordonnées cible (Lambert 93 par défaut)."""
        if not source_crs:
            source_crs = "EPSG:4326"  # WGS84 par défaut
        
        if source_crs != target_crs:
            project = pyproj.Transformer.from_crs(
                source_crs,
                target_crs,
                always_xy=True
            ).transform
            transformed_geom = transform(project, geometry)
            return transformed_geom
        
        return geometry
    
    def get_standardized_parcel(self, parcel: Parcel) -> Parcel:
        """
        Standardise une parcelle en projetant sa géométrie en Lambert 93 si nécessaire.
        
        Args:
            parcel: Parcelle à standardiser
        
        Returns:
            Parcelle avec géométrie en Lambert 93
        """
        if parcel.geometry is None:
            self.logger.error(f"Parcelle {parcel.id} sans géométrie")
            return parcel
        
        # S'assurer que la géométrie est en Lambert 93
        if parcel.crs != self.reference_crs:
            parcel_geometry = self._ensure_crs(parcel.geometry, parcel.crs, self.reference_crs)
            
            # Créer une copie de la parcelle avec la géométrie projetée
            standardized_parcel = Parcel(
                id=parcel.id,
                commune=parcel.commune,
                section=parcel.section,
                numero=parcel.numero,
                surface=parcel.surface,
                geometry=parcel_geometry,
                crs=self.reference_crs
            )
            return standardized_parcel
        
        return parcel
