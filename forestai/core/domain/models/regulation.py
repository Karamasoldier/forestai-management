"""
Module contenant les modèles de domaine relatifs aux réglementations forestières.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from enum import Enum


class ProjectType(str, Enum):
    """Types de projets forestiers."""
    AFFORESTATION = "boisement"  # Boisement de terres non forestières
    REFORESTATION = "reboisement"  # Reboisement après coupe
    MAINTENANCE = "entretien"  # Entretien de forêt existante
    HARVEST = "coupe"  # Coupe de bois
    FOREST_ROAD = "route_forestiere"  # Création de route forestière
    CONSERVATION = "conservation"  # Conservation et protection
    AGROFORESTRY = "agroforesterie"  # Système agroforestier


class ProtectedZoneType(str, Enum):
    """Types de zones protégées impactant la gestion forestière."""
    NATURA_2000 = "natura_2000"
    ZNIEFF = "znieff"  # Zone Naturelle d'Intérêt Écologique, Faunistique et Floristique
    FOREST_PROTECTION = "foret_protection"  # Forêt de protection
    WATER_PROTECTION = "eau_protection"  # Zone de protection des captages d'eau
    FLOOD_ZONE = "zone_inondable"  # Zone inondable
    COASTAL_PROTECTION = "littoral"  # Loi littoral
    MOUNTAIN_PROTECTION = "montagne"  # Loi montagne
    NATURAL_PARK = "parc_naturel"  # Parc naturel
    BIOTOPE_PROTECTION = "arrete_biotope"  # Arrêté de protection de biotope


@dataclass
class RegulatoryConstraint:
    """Contrainte réglementaire applicable à une parcelle ou un projet."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # Type de contrainte (protection, urbanisme, etc.)
    code_reference: str  # Référence à l'article du code forestier ou autre
    description: str
    severity: str  # 'bloquant', 'restriction', 'information'
    geographic_scope: str  # 'national', 'regional', 'local'
    conditions: List[str] = field(default_factory=list)
    exemptions: List[str] = field(default_factory=list)
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProtectedZone:
    """Zone protégée avec réglementation spécifique."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    zone_type: ProtectedZoneType
    description: str = ""
    legal_reference: str = ""
    constraints: List[RegulatoryConstraint] = field(default_factory=list)
    wkt_geometry: Optional[str] = None  # Well-Known Text representation


@dataclass
class RequiredAuthorization:
    """Autorisation requise pour un projet forestier."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    authority: str  # Organisme délivrant l'autorisation
    description: str
    document_template: Optional[str] = None
    required_documents: List[str] = field(default_factory=list)
    submission_process: str = ""
    processing_time_days: int = 60
    validity_years: Optional[int] = None


@dataclass
class ComplianceVerification:
    """Résultat de vérification de conformité réglementaire."""
    parcel_id: str
    project_type: ProjectType
    timestamp: datetime = field(default_factory=datetime.now)
    is_compliant: bool = False
    applicable_constraints: List[RegulatoryConstraint] = field(default_factory=list)
    required_authorizations: List[RequiredAuthorization] = field(default_factory=list)
    overlapping_protected_zones: List[ProtectedZone] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    explanation: str = ""
    
    def get_constraint_severity_count(self) -> Dict[str, int]:
        """Compte le nombre de contraintes par niveau de sévérité."""
        severity_count = {"bloquant": 0, "restriction": 0, "information": 0}
        for constraint in self.applicable_constraints:
            if constraint.severity in severity_count:
                severity_count[constraint.severity] += 1
        return severity_count


@dataclass
class RegionalRegulatoryFramework:
    """Cadre réglementaire spécifique à une région."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    region_code: str
    region_name: str
    description: str
    effective_date: datetime
    expiration_date: Optional[datetime] = None
    specific_constraints: List[RegulatoryConstraint] = field(default_factory=list)
    protected_zones: List[ProtectedZone] = field(default_factory=list)
    authorizations: List[RequiredAuthorization] = field(default_factory=list)
    additional_documents: Dict[str, str] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Vérifie si le cadre réglementaire est actuellement actif."""
        now = datetime.now()
        return (now >= self.effective_date and 
                (self.expiration_date is None or now <= self.expiration_date))
