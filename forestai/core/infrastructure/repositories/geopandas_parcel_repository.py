"""
Implémentation du ParcelRepository utilisant GeoPandas comme stockage.

Ce module fournit une implémentation concrète de l'interface ParcelRepository
en utilisant GeoPandas pour stocker et manipuler les données spatiales des parcelles.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import geopandas as gpd
import pandas as pd
import json
from shapely.geometry import box, Point, Polygon, shape
from shapely.wkt import loads
from datetime import datetime

from ..repositories.interfaces import ParcelRepository
from ...domain.models.parcel import (
    Parcel, 
    ParcelIdentifier, 
    ParcelGeometry, 
    ParcelOwner,
    TerrainCharacteristics,
    ForestPotential
)


class GeoPandasParcelRepository(ParcelRepository):
    """
    Implémentation du repository de parcelles utilisant GeoPandas.
    Stocke les parcelles dans des fichiers GeoPackage (GPKG).
    """
    
    def __init__(self, data_path: str, municipality_data_path: Optional[str] = None):
        """
        Initialise le repository avec les chemins des fichiers de données.
        
        Args:
            data_path: Chemin vers le répertoire des données
            municipality_data_path: Chemin optionnel vers les données de communes
        """
        self.logger = logging.getLogger(__name__)
        self.data_path = data_path
        self.municipality_data_path = municipality_data_path
        
        # Fichier principal de stockage des parcelles
        self.parcels_file = os.path.join(data_path, "parcels.gpkg")
        
        # Initialiser le GeoDataFrame des parcelles s'il n'existe pas
        self._initialize_datastore()
    
    def _initialize_datastore(self):
        """Initialise le stockage de données si nécessaire."""
        if not os.path.exists(self.parcels_file):
            self.logger.info(f"Création du fichier de stockage des parcelles: {self.parcels_file}")
            
            # Créer un GeoDataFrame vide avec la structure attendue
            schema = {
                "id": [],
                "dept_code": [],
                "commune_code": [],
                "section": [],
                "number": [],
                "area_ha": [],
                "perimeter_m": [],
                "owner_id": [],
                "owner_name": [],
                "owner_address": [],
                "owner_is_company": [],
                "creation_date": [],
                "last_updated": [],
                "current_land_use": [],
                "avg_slope": [],
                "max_slope": [],
                "min_elevation": [],
                "max_elevation": [],
                "avg_elevation": [],
                "aspect": [],
                "soil_type": [],
                "water_presence": [],
                "wetland_area_pct": [],
                "forest_potential_score": [],
                "suitable_species": [],
                "carbon_potential": [],
                "timber_potential": [],
                "biodiversity_score": [],
                "geometry": []
            }
            
            # Créer le DataFrame vide
            df = pd.DataFrame(schema)
            
            # Créer un GeoDataFrame avec une géométrie vide
            empty_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
            
            # Sauvegarder le GeoDataFrame vide
            self._save_gdf(empty_gdf)
            
            self.logger.info("Fichier de stockage des parcelles initialisé")
    
    def _save_gdf(self, gdf: gpd.GeoDataFrame):
        """
        Sauvegarde le GeoDataFrame dans le fichier de stockage.
        
        Args:
            gdf: GeoDataFrame à sauvegarder
        """
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(self.parcels_file), exist_ok=True)
            
            # Sauvegarder le GeoDataFrame
            gdf.to_file(self.parcels_file, driver="GPKG")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du GeoDataFrame: {str(e)}")
            raise
    
    def _load_gdf(self) -> gpd.GeoDataFrame:
        """
        Charge le GeoDataFrame depuis le fichier de stockage.
        
        Returns:
            GeoDataFrame des parcelles
        """
        try:
            if not os.path.exists(self.parcels_file):
                return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
            
            return gpd.read_file(self.parcels_file)
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du GeoDataFrame: {str(e)}")
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    
    def _parcel_to_gdf_row(self, parcel: Parcel) -> Dict[str, Any]:
        """
        Convertit une entité Parcel en ligne de GeoDataFrame.
        
        Args:
            parcel: Objet Parcel à convertir
            
        Returns:
            Dictionnaire représentant une ligne de GeoDataFrame
        """
        row = {
            "id": parcel.id,
            "dept_code": parcel.identifier.department_code,
            "commune_code": parcel.identifier.commune_code,
            "section": parcel.identifier.section,
            "number": parcel.identifier.number,
            "area_ha": parcel.geometry.area_ha,
            "perimeter_m": parcel.geometry.perimeter_m,
            "creation_date": parcel.creation_date.isoformat(),
            "last_updated": parcel.last_updated.isoformat(),
            "current_land_use": parcel.current_land_use,
            "geometry": loads(parcel.geometry.wkt)
        }
        
        # Ajouter les informations sur le propriétaire si disponibles
        if parcel.owner:
            row.update({
                "owner_id": parcel.owner.id,
                "owner_name": parcel.owner.name,
                "owner_address": parcel.owner.address,
                "owner_is_company": parcel.owner.is_company
            })
        
        # Ajouter les caractéristiques du terrain si disponibles
        if parcel.terrain:
            row.update({
                "avg_slope": parcel.terrain.avg_slope,
                "max_slope": parcel.terrain.max_slope,
                "min_elevation": parcel.terrain.min_elevation,
                "max_elevation": parcel.terrain.max_elevation,
                "avg_elevation": parcel.terrain.avg_elevation,
                "aspect": parcel.terrain.aspect,
                "soil_type": parcel.terrain.soil_type,
                "water_presence": parcel.terrain.water_presence,
                "wetland_area_pct": parcel.terrain.wetland_area_pct
            })
        
        # Ajouter les informations sur le potentiel forestier si disponibles
        if parcel.forest_potential:
            row.update({
                "forest_potential_score": parcel.forest_potential.score,
                "suitable_species": json.dumps(parcel.forest_potential.suitable_species),
                "carbon_potential": parcel.forest_potential.carbon_potential,
                "timber_potential": parcel.forest_potential.timber_potential,
                "biodiversity_score": parcel.forest_potential.biodiversity_score
            })
        
        return row
    
    def _gdf_row_to_parcel(self, row: pd.Series) -> Parcel:
        """
        Convertit une ligne de GeoDataFrame en entité Parcel.
        
        Args:
            row: Ligne de GeoDataFrame (Series)
            
        Returns:
            Objet Parcel
        """
        # Créer l'identifiant
        identifier = ParcelIdentifier(
            department_code=row.get("dept_code", ""),
            commune_code=row.get("commune_code", ""),
            section=row.get("section", ""),
            number=row.get("number", "")
        )
        
        # Créer la géométrie
        geometry = ParcelGeometry(
            wkt=row["geometry"].wkt,
            area_ha=row.get("area_ha", 0.0),
            perimeter_m=row.get("perimeter_m", 0.0),
            centroid_x=row["geometry"].centroid.x,
            centroid_y=row["geometry"].centroid.y,
            bbox=list(row["geometry"].bounds)
        )
        
        # Créer le propriétaire si les informations sont disponibles
        owner = None
        if "owner_id" in row and row["owner_id"]:
            owner = ParcelOwner(
                id=row["owner_id"],
                name=row.get("owner_name", ""),
                address=row.get("owner_address", ""),
                is_company=row.get("owner_is_company", False)
            )
        
        # Créer les caractéristiques du terrain si disponibles
        terrain = None
        if "avg_slope" in row and not pd.isna(row["avg_slope"]):
            terrain = TerrainCharacteristics(
                avg_slope=row.get("avg_slope", 0.0),
                max_slope=row.get("max_slope", 0.0),
                min_elevation=row.get("min_elevation", 0.0),
                max_elevation=row.get("max_elevation", 0.0),
                avg_elevation=row.get("avg_elevation", 0.0),
                aspect=row.get("aspect", ""),
                soil_type=row.get("soil_type", ""),
                water_presence=row.get("water_presence", False),
                wetland_area_pct=row.get("wetland_area_pct", 0.0)
            )
        
        # Créer le potentiel forestier si disponible
        forest_potential = None
        if "forest_potential_score" in row and not pd.isna(row["forest_potential_score"]):
            suitable_species = []
            if "suitable_species" in row and row["suitable_species"]:
                try:
                    suitable_species = json.loads(row["suitable_species"])
                except:
                    pass
                
            forest_potential = ForestPotential(
                score=row["forest_potential_score"],
                suitable_species=suitable_species,
                carbon_potential=row.get("carbon_potential"),
                timber_potential=row.get("timber_potential"),
                biodiversity_score=row.get("biodiversity_score")
            )
        
        # Créer et retourner la parcelle
        creation_date = datetime.fromisoformat(row["creation_date"]) if "creation_date" in row and row["creation_date"] else datetime.now()
        last_updated = datetime.fromisoformat(row["last_updated"]) if "last_updated" in row and row["last_updated"] else datetime.now()
        
        return Parcel(
            id=row["id"],
            identifier=identifier,
            owner=owner,
            geometry=geometry,
            terrain=terrain,
            current_land_use=row.get("current_land_use", ""),
            creation_date=creation_date,
            last_updated=last_updated,
            forest_potential=forest_potential
        )
    
    def get_by_id(self, id: str) -> Optional[Parcel]:
        """
        Récupère une parcelle par son identifiant.
        
        Args:
            id: Identifiant unique de la parcelle
            
        Returns:
            Parcelle ou None si non trouvée
        """
        gdf = self._load_gdf()
        
        # Filtrer par ID
        filtered = gdf[gdf["id"] == id]
        
        if len(filtered) == 0:
            return None
        
        # Convertir la première ligne en Parcel
        return self._gdf_row_to_parcel(filtered.iloc[0])
    
    def save(self, parcel: Parcel) -> Parcel:
        """
        Sauvegarde une parcelle.
        
        Args:
            parcel: Parcelle à sauvegarder
            
        Returns:
            Parcelle mise à jour
        """
        # Mettre à jour la date de dernière modification
        parcel.last_updated = datetime.now()
        
        # Charger le GeoDataFrame existant
        gdf = self._load_gdf()
        
        # Convertir la parcelle en ligne de GeoDataFrame
        row_dict = self._parcel_to_gdf_row(parcel)
        
        # Vérifier si la parcelle existe déjà
        exists_mask = gdf["id"] == parcel.id
        
        if exists_mask.any():
            # Mise à jour d'une parcelle existante
            for key, value in row_dict.items():
                if key in gdf.columns:
                    gdf.loc[exists_mask, key] = value
        else:
            # Ajout d'une nouvelle parcelle
            new_row = pd.DataFrame([row_dict])
            new_gdf = gpd.GeoDataFrame(new_row, geometry='geometry', crs=gdf.crs)
            gdf = pd.concat([gdf, new_gdf], ignore_index=True)
        
        # Sauvegarder le GeoDataFrame mis à jour
        self._save_gdf(gdf)
        
        return parcel
    
    def delete(self, id: str) -> bool:
        """
        Supprime une parcelle.
        
        Args:
            id: Identifiant de la parcelle à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        # Charger le GeoDataFrame existant
        gdf = self._load_gdf()
        
        # Vérifier si la parcelle existe
        exists_mask = gdf["id"] == id
        
        if not exists_mask.any():
            return False
        
        # Supprimer la parcelle
        gdf = gdf[~exists_mask]
        
        # Sauvegarder le GeoDataFrame mis à jour
        self._save_gdf(gdf)
        
        return True
    
    def exists(self, id: str) -> bool:
        """
        Vérifie si une parcelle existe.
        
        Args:
            id: Identifiant de la parcelle
            
        Returns:
            True si la parcelle existe, False sinon
        """
        gdf = self._load_gdf()
        return (gdf["id"] == id).any()
    
    def find_by_cadastral_reference(self, identifier: ParcelIdentifier) -> Optional[Parcel]:
        """
        Récupère une parcelle par sa référence cadastrale.
        
        Args:
            identifier: Identifiant cadastral
            
        Returns:
            Parcelle ou None si non trouvée
        """
        gdf = self._load_gdf()
        
        # Filtrer par référence cadastrale
        filtered = gdf[
            (gdf["dept_code"] == identifier.department_code) &
            (gdf["commune_code"] == identifier.commune_code) &
            (gdf["section"] == identifier.section) &
            (gdf["number"] == identifier.number)
        ]
        
        if len(filtered) == 0:
            return None
        
        # Convertir la première ligne en Parcel
        return self._gdf_row_to_parcel(filtered.iloc[0])
    
    def find_by_department(self, department_code: str, min_area: float = 0) -> List[Parcel]:
        """
        Récupère toutes les parcelles d'un département avec une surface minimale optionnelle.
        
        Args:
            department_code: Code du département
            min_area: Surface minimale en hectares
            
        Returns:
            Liste des parcelles correspondantes
        """
        gdf = self._load_gdf()
        
        # Filtrer par département et surface minimale
        filtered = gdf[
            (gdf["dept_code"] == department_code) &
            (gdf["area_ha"] >= min_area)
        ]
        
        # Convertir les lignes en Parcel
        return [self._gdf_row_to_parcel(row) for _, row in filtered.iterrows()]
    
    def find_by_commune(self, commune_code: str) -> List[Parcel]:
        """
        Récupère toutes les parcelles d'une commune.
        
        Args:
            commune_code: Code de la commune
            
        Returns:
            Liste des parcelles correspondantes
        """
        gdf = self._load_gdf()
        
        # Filtrer par commune
        filtered = gdf[gdf["commune_code"] == commune_code]
        
        # Convertir les lignes en Parcel
        return [self._gdf_row_to_parcel(row) for _, row in filtered.iterrows()]
    
    def find_by_owner(self, owner_id: str) -> List[Parcel]:
        """
        Récupère toutes les parcelles appartenant à un propriétaire.
        
        Args:
            owner_id: Identifiant du propriétaire
            
        Returns:
            Liste des parcelles correspondantes
        """
        gdf = self._load_gdf()
        
        # Filtrer par propriétaire
        filtered = gdf[gdf["owner_id"] == owner_id]
        
        # Convertir les lignes en Parcel
        return [self._gdf_row_to_parcel(row) for _, row in filtered.iterrows()]
    
    def find_by_bbox(self, min_x: float, min_y: float, max_x: float, max_y: float) -> List[Parcel]:
        """
        Récupère toutes les parcelles dans une boîte englobante.
        
        Args:
            min_x: Coordonnée X minimale
            min_y: Coordonnée Y minimale
            max_x: Coordonnée X maximale
            max_y: Coordonnée Y maximale
            
        Returns:
            Liste des parcelles correspondantes
        """
        gdf = self._load_gdf()
        
        # Créer la boîte englobante
        bbox = box(min_x, min_y, max_x, max_y)
        
        # Filtrer par intersection avec la boîte englobante
        filtered = gdf[gdf.geometry.intersects(bbox)]
        
        # Convertir les lignes en Parcel
        return [self._gdf_row_to_parcel(row) for _, row in filtered.iterrows()]
    
    def find_by_forest_potential(self, min_score: float) -> List[Parcel]:
        """
        Récupère toutes les parcelles avec un potentiel forestier supérieur au score minimum.
        
        Args:
            min_score: Score minimum de potentiel forestier
            
        Returns:
            Liste des parcelles correspondantes
        """
        gdf = self._load_gdf()
        
        # Filtrer par score de potentiel forestier
        filtered = gdf[
            gdf["forest_potential_score"].notna() &
            (gdf["forest_potential_score"] >= min_score)
        ]
        
        # Convertir les lignes en Parcel
        return [self._gdf_row_to_parcel(row) for _, row in filtered.iterrows()]
    
    def save_batch(self, parcels: List[Parcel]) -> List[Parcel]:
        """
        Sauvegarde un lot de parcelles.
        
        Args:
            parcels: Liste des parcelles à sauvegarder
            
        Returns:
            Liste des parcelles mises à jour
        """
        if not parcels:
            return []
        
        # Charger le GeoDataFrame existant
        gdf = self._load_gdf()
        
        # Convertir chaque parcelle en ligne de GeoDataFrame
        rows = []
        for parcel in parcels:
            # Mettre à jour la date de dernière modification
            parcel.last_updated = datetime.now()
            rows.append(self._parcel_to_gdf_row(parcel))
        
        # Créer un nouveau GeoDataFrame avec les lignes
        new_gdf = gpd.GeoDataFrame(rows, geometry='geometry', crs=gdf.crs)
        
        # Supprimer les parcelles existantes
        existing_ids = [p.id for p in parcels]
        gdf = gdf[~gdf["id"].isin(existing_ids)]
        
        # Concaténer avec les nouvelles parcelles
        gdf = pd.concat([gdf, new_gdf], ignore_index=True)
        
        # Sauvegarder le GeoDataFrame mis à jour
        self._save_gdf(gdf)
        
        return parcels


# Factory pour créer une instance du repository
def create_geopandas_parcel_repository(config: Dict[str, Any]) -> ParcelRepository:
    """
    Crée une instance de GeoPandasParcelRepository avec la configuration fournie.
    
    Args:
        config: Dictionnaire de configuration
        
    Returns:
        Instance de ParcelRepository
    """
    data_path = config.get("data_path", "./data")
    municipality_data_path = config.get("municipality_data_path")
    
    return GeoPandasParcelRepository(data_path, municipality_data_path)
