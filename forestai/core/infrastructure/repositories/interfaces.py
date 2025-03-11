"""
Interfaces abstraites pour les repositories de données.

Ce module définit les contrats que doivent implémenter les repositories
pour assurer une interface cohérente entre la couche domaine et la
couche infrastructure.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generic, TypeVar
from ...domain.models.parcel import Parcel, ParcelIdentifier
from ...domain.models.regulation import (
    RegionalRegulatoryFramework, 
    ProtectedZone,
    RegulatoryConstraint
)

T = TypeVar('T')
ID = TypeVar('ID')


class Repository(Generic[T, ID], ABC):
    """Interface générique pour tous les repositories."""
    
    @abstractmethod
    def get_by_id(self, id: ID) -> Optional[T]:
        """Récupère une entité par son identifiant."""
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """Sauvegarde une entité et retourne l'entité mise à jour."""
        pass
    
    @abstractmethod
    def delete(self, id: ID) -> bool:
        """Supprime une entité et retourne True si la suppression a réussi."""
        pass
    
    @abstractmethod
    def exists(self, id: ID) -> bool:
        """Vérifie si une entité existe pour l'identifiant donné."""
        pass


class ParcelRepository(Repository[Parcel, str], ABC):
    """Interface pour le repository des parcelles."""
    
    @abstractmethod
    def find_by_cadastral_reference(self, identifier: ParcelIdentifier) -> Optional[Parcel]:
        """Récupère une parcelle par sa référence cadastrale."""
        pass
    
    @abstractmethod
    def find_by_department(self, department_code: str, min_area: float = 0) -> List[Parcel]:
        """Récupère toutes les parcelles d'un département avec une surface minimale optionnelle."""
        pass
    
    @abstractmethod
    def find_by_commune(self, commune_code: str) -> List[Parcel]:
        """Récupère toutes les parcelles d'une commune."""
        pass
    
    @abstractmethod
    def find_by_owner(self, owner_id: str) -> List[Parcel]:
        """Récupère toutes les parcelles appartenant à un propriétaire."""
        pass
    
    @abstractmethod
    def find_by_bbox(self, min_x: float, min_y: float, max_x: float, max_y: float) -> List[Parcel]:
        """Récupère toutes les parcelles dans une boîte englobante."""
        pass
    
    @abstractmethod
    def find_by_forest_potential(self, min_score: float) -> List[Parcel]:
        """Récupère toutes les parcelles avec un potentiel forestier supérieur au score minimum."""
        pass
    
    @abstractmethod
    def save_batch(self, parcels: List[Parcel]) -> List[Parcel]:
        """Sauvegarde un lot de parcelles et retourne les parcelles mises à jour."""
        pass


class RegulatoryFrameworkRepository(Repository[RegionalRegulatoryFramework, str], ABC):
    """Interface pour le repository des cadres réglementaires régionaux."""
    
    @abstractmethod
    def find_by_region(self, region_code: str) -> Optional[RegionalRegulatoryFramework]:
        """Récupère le cadre réglementaire pour une région spécifique."""
        pass
    
    @abstractmethod
    def find_active_by_region(self, region_code: str) -> Optional[RegionalRegulatoryFramework]:
        """Récupère le cadre réglementaire actif pour une région spécifique."""
        pass
    
    @abstractmethod
    def find_all_active(self) -> List[RegionalRegulatoryFramework]:
        """Récupère tous les cadres réglementaires actifs."""
        pass


class ProtectedZoneRepository(Repository[ProtectedZone, str], ABC):
    """Interface pour le repository des zones protégées."""
    
    @abstractmethod
    def find_by_point(self, x: float, y: float) -> List[ProtectedZone]:
        """Récupère toutes les zones protégées contenant un point."""
        pass
    
    @abstractmethod
    def find_by_parcel(self, parcel: Parcel) -> List[ProtectedZone]:
        """Récupère toutes les zones protégées qui se superposent avec une parcelle."""
        pass
    
    @abstractmethod
    def find_by_type(self, zone_type: str) -> List[ProtectedZone]:
        """Récupère toutes les zones protégées d'un type spécifique."""
        pass


class RegulatoryConstraintRepository(Repository[RegulatoryConstraint, str], ABC):
    """Interface pour le repository des contraintes réglementaires."""
    
    @abstractmethod
    def find_by_type(self, constraint_type: str) -> List[RegulatoryConstraint]:
        """Récupère toutes les contraintes d'un type spécifique."""
        pass
    
    @abstractmethod
    def find_by_code_reference(self, code_reference: str) -> List[RegulatoryConstraint]:
        """Récupère toutes les contraintes faisant référence à un article de code spécifique."""
        pass
    
    @abstractmethod
    def find_by_geographic_scope(self, scope: str) -> List[RegulatoryConstraint]:
        """Récupère toutes les contraintes applicables à une portée géographique spécifique."""
        pass
    
    @abstractmethod
    def find_applicable_to_project(self, project_type: str, region_code: str) -> List[RegulatoryConstraint]:
        """Récupère toutes les contraintes applicables à un type de projet dans une région."""
        pass
