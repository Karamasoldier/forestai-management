"""
Module contenant les modèles de domaine relatifs aux parcelles forestières.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class ParcelIdentifier:
    """Identifiant cadastral d'une parcelle."""
    department_code: str
    commune_code: str
    section: str
    number: str
    
    def to_string(self) -> str:
        """Convertit l'identifiant en chaîne formatée."""
        return f"{self.department_code}-{self.commune_code}-{self.section}-{self.number}"
    
    @classmethod
    def from_string(cls, identifier: str) -> "ParcelIdentifier":
        """Crée un identifiant à partir d'une chaîne formatée."""
        parts = identifier.split("-")
        if len(parts) != 4:
            raise ValueError(f"Format d'identifiant de parcelle invalide: {identifier}")
        
        return cls(
            department_code=parts[0],
            commune_code=parts[1],
            section=parts[2],
            number=parts[3]
        )


@dataclass
class ParcelOwner:
    """Propriétaire d'une parcelle forestière."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    address: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    is_company: bool = False
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParcelGeometry:
    """Géométrie et caractéristiques spatiales d'une parcelle."""
    wkt: str  # Well-Known Text representation
    area_ha: float
    perimeter_m: float
    centroid_x: float
    centroid_y: float
    bbox: List[float] = field(default_factory=list)  # [minx, miny, maxx, maxy]
    
    def get_area_acres(self) -> float:
        """Convertit la surface en acres."""
        return self.area_ha * 2.47105


@dataclass
class TerrainCharacteristics:
    """Caractéristiques du terrain d'une parcelle."""
    avg_slope: float = 0.0
    max_slope: float = 0.0
    min_elevation: float = 0.0
    max_elevation: float = 0.0
    avg_elevation: float = 0.0
    aspect: str = ""  # N, NE, E, SE, S, SW, W, NW
    soil_type: str = ""
    soil_quality: Optional[str] = None
    water_presence: bool = False
    wetland_area_pct: float = 0.0


@dataclass
class ForestPotential:
    """Potentiel forestier d'une parcelle."""
    score: float  # 0-1
    suitable_species: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    carbon_potential: Optional[float] = None
    timber_potential: Optional[float] = None
    biodiversity_score: Optional[float] = None


@dataclass
class Parcel:
    """
    Modèle de domaine représentant une parcelle forestière.
    Contient toutes les informations relatives à une parcelle.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    identifier: ParcelIdentifier = None
    owner: Optional[ParcelOwner] = None
    geometry: ParcelGeometry = None
    terrain: Optional[TerrainCharacteristics] = None
    current_land_use: str = ""
    creation_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    forest_potential: Optional[ForestPotential] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation après initialisation."""
        if self.identifier is None:
            raise ValueError("L'identifiant de parcelle est requis")
        if self.geometry is None:
            raise ValueError("La géométrie de parcelle est requise")
            
    def update_forest_potential(self, forest_potential: ForestPotential) -> None:
        """Met à jour le potentiel forestier de la parcelle."""
        self.forest_potential = forest_potential
        self.last_updated = datetime.now()
