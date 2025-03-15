"""
Modèles Pydantic pour l'API REST ForestAI.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date

# Modèles génériques
class ErrorResponse(BaseModel):
    """Modèle de réponse en cas d'erreur."""
    status: str = Field("error", description="Statut de la réponse")
    error_message: str = Field(..., description="Message d'erreur")

class SuccessResponse(BaseModel):
    """Modèle de réponse en cas de succès."""
    status: str = Field("success", description="Statut de la réponse")
    result: Any = Field(..., description="Résultat de l'opération")

# Modèles pour GeoAgent
class ParcelSearchRequest(BaseModel):
    """Modèle pour la recherche de parcelles."""
    commune: str = Field(..., description="Nom ou code INSEE de la commune")
    section: Optional[str] = Field(None, description="Section cadastrale")
    numero: Optional[str] = Field(None, description="Numéro de parcelle")
    
    class Config:
        schema_extra = {
            "example": {
                "commune": "Saint-Martin-de-Crau",
                "section": "B",
                "numero": None
            }
        }

class AnalysisType(str, Enum):
    """Type d'analyse de parcelle."""
    BASIC = "basic"
    TERRAIN = "terrain"
    FOREST_POTENTIAL = "forest_potential"
    CLIMATE = "climate"
    RISKS = "risks"
    COMPLETE = "complete"

class ParcelAnalysisRequest(BaseModel):
    """Modèle pour l'analyse de parcelle."""
    parcel_id: str = Field(..., description="Identifiant de la parcelle (format: codeINSEE+section+numero)")
    analyses: Optional[List[AnalysisType]] = Field(None, description="Types d'analyses à effectuer")
    
    class Config:
        schema_extra = {
            "example": {
                "parcel_id": "13097000B0012",
                "analyses": ["terrain", "forest_potential"]
            }
        }

# Modèles pour SubsidyAgent
class SubsidySearchRequest(BaseModel):
    """Modèle pour la recherche de subventions."""
    project_type: str = Field(..., description="Type de projet (reboisement, boisement, etc.)")
    region: Optional[str] = Field(None, description="Région concernée")
    owner_type: Optional[str] = Field(None, description="Type de propriétaire (private, public, etc.)")
    parcel_id: Optional[str] = Field(None, description="Identifiant de parcelle pour enrichissement des données")
    
    class Config:
        schema_extra = {
            "example": {
                "project_type": "reboisement",
                "region": "Provence-Alpes-Côte d'Azur",
                "owner_type": "private",
                "parcel_id": None
            }
        }

class ProjectModel(BaseModel):
    """Modèle pour les données de projet forestier."""
    type: str = Field(..., description="Type de projet (reboisement, boisement, etc.)")
    area_ha: float = Field(..., description="Surface en hectares")
    species: List[str] = Field(..., description="Liste des espèces prévues")
    region: str = Field(..., description="Région concernée")
    location: str = Field(..., description="Identifiant de parcelle")
    owner_type: str = Field(..., description="Type de propriétaire")
    planting_density: Optional[int] = Field(None, description="Densité de plantation (arbres/ha)")
    slope: Optional[float] = Field(None, description="Pente moyenne (%)")
    protected_areas: Optional[List[str]] = Field(None, description="Zones protégées")
    has_management_document: Optional[bool] = Field(None, description="Présence d'un document de gestion")
    maintenance_commitment_years: Optional[int] = Field(None, description="Engagement d'entretien (années)")
    priority_zones: Optional[List[str]] = Field(None, description="Zones prioritaires")
    certifications: Optional[List[str]] = Field(None, description="Certifications forestières")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "reboisement",
                "area_ha": 5.2,
                "species": ["pinus_pinea", "quercus_suber"],
                "region": "Provence-Alpes-Côte d'Azur",
                "location": "13097000B0012",
                "owner_type": "private",
                "planting_density": 1200,
                "slope": 15,
                "protected_areas": [],
                "has_management_document": True,
                "maintenance_commitment_years": 5,
                "priority_zones": ["france_relance"],
                "certifications": ["PEFC"]
            }
        }

class EligibilityRequest(BaseModel):
    """Modèle pour l'analyse d'éligibilité."""
    project: ProjectModel = Field(..., description="Données du projet forestier")
    subsidy_id: str = Field(..., description="Identifiant de la subvention à analyser")
    
    class Config:
        schema_extra = {
            "example": {
                "project": {
                    "type": "reboisement",
                    "area_ha": 5.2,
                    "species": ["pinus_pinea", "quercus_suber"],
                    "region": "Provence-Alpes-Côte d'Azur",
                    "location": "13097000B0012",
                    "owner_type": "private",
                    "planting_density": 1200
                },
                "subsidy_id": "fr_reforest_2025"
            }
        }

class ApplicantModel(BaseModel):
    """Modèle pour les données du demandeur de subvention."""
    name: str = Field(..., description="Nom du demandeur")
    address: str = Field(..., description="Adresse")
    contact: str = Field(..., description="Email de contact")
    siret: Optional[str] = Field(None, description="Numéro SIRET")
    contact_name: Optional[str] = Field(None, description="Nom du contact")
    contact_phone: Optional[str] = Field(None, description="Téléphone de contact")
    owner_since: Optional[date] = Field(None, description="Date d'acquisition de la propriété")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Domaine Forestier du Sud",
                "address": "Route des Pins 13200 Arles",
                "contact": "contact@domaineforestier.fr",
                "siret": "12345678900012",
                "contact_name": "Jean Dupont",
                "contact_phone": "0612345678"
            }
        }

class ApplicationRequest(BaseModel):
    """Modèle pour la génération de demande de subvention."""
    project: ProjectModel = Field(..., description="Données du projet forestier")
    subsidy_id: str = Field(..., description="Identifiant de la subvention")
    applicant: ApplicantModel = Field(..., description="Données du demandeur")
    output_formats: List[str] = Field(["pdf"], description="Formats de sortie souhaités")
    
    class Config:
        schema_extra = {
            "example": {
                "project": {
                    "type": "reboisement",
                    "area_ha": 5.2,
                    "species": ["pinus_pinea", "quercus_suber"],
                    "region": "Provence-Alpes-Côte d'Azur",
                    "location": "13097000B0012",
                    "owner_type": "private"
                },
                "subsidy_id": "fr_reforest_2025",
                "applicant": {
                    "name": "Domaine Forestier du Sud",
                    "address": "Route des Pins 13200 Arles",
                    "contact": "contact@domaineforestier.fr",
                    "siret": "12345678900012",
                    "contact_name": "Jean Dupont",
                    "contact_phone": "0612345678"
                },
                "output_formats": ["pdf", "html"]
            }
        }

# Modèles pour DiagnosticAgent
class InventoryItem(BaseModel):
    """Modèle pour un arbre dans l'inventaire forestier."""
    species: str = Field(..., description="Espèce de l'arbre")
    diameter: float = Field(..., description="Diamètre de l'arbre (en cm)")
    height: float = Field(..., description="Hauteur de l'arbre (en m)")
    age: Optional[int] = Field(None, description="Âge estimé de l'arbre (en années)")
    health_status: Optional[str] = Field(None, description="État sanitaire (bon, moyen, mauvais)")
    x: Optional[float] = Field(None, description="Coordonnée X (optionnelle)")
    y: Optional[float] = Field(None, description="Coordonnée Y (optionnelle)")
    notes: Optional[str] = Field(None, description="Notes supplémentaires")

class InventoryData(BaseModel):
    """Modèle pour les données d'inventaire forestier."""
    items: List[InventoryItem] = Field(..., description="Liste des arbres inventoriés")
    area: Optional[float] = Field(None, description="Surface inventoriée (ha)")
    date: Optional[date] = Field(None, description="Date de l'inventaire")
    method: Optional[str] = Field(None, description="Méthode d'inventaire")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "species": "quercus_ilex",
                        "diameter": 25.5,
                        "height": 12.0,
                        "health_status": "bon"
                    },
                    {
                        "species": "pinus_pinea",
                        "diameter": 35.0,
                        "height": 18.5,
                        "health_status": "moyen"
                    }
                ],
                "area": 1.5,
                "date": "2025-03-01",
                "method": "placettes"
            }
        }

class DiagnosticRequest(BaseModel):
    """Modèle pour la demande de diagnostic forestier."""
    parcel_id: str = Field(..., description="Identifiant de la parcelle")
    inventory_data: Optional[InventoryData] = Field(None, description="Données d'inventaire forestier (optionnel)")
    include_health_analysis: bool = Field(True, description="Inclure l'analyse sanitaire")
    
    class Config:
        schema_extra = {
            "example": {
                "parcel_id": "13097000B0012",
                "inventory_data": {
                    "items": [
                        {
                            "species": "quercus_ilex",
                            "diameter": 25.5,
                            "height": 12.0,
                            "health_status": "bon"
                        }
                    ],
                    "area": 1.5
                },
                "include_health_analysis": True
            }
        }

class ManagementPlanRequest(BaseModel):
    """Modèle pour la demande de plan de gestion."""
    parcel_id: str = Field(..., description="Identifiant de la parcelle")
    goals: List[str] = Field(..., description="Objectifs de gestion (production, biodiversité, resilience, etc.)")
    horizon_years: int = Field(10, description="Horizon temporel du plan en années")
    use_existing_diagnostic: bool = Field(False, description="Utiliser un diagnostic existant")
    
    class Config:
        schema_extra = {
            "example": {
                "parcel_id": "13097000B0012",
                "goals": ["production", "resilience"],
                "horizon_years": 15,
                "use_existing_diagnostic": True
            }
        }

class HealthAnalysisRequest(BaseModel):
    """Modèle pour la demande d'analyse sanitaire forestière."""
    inventory_data: InventoryData = Field(..., description="Données d'inventaire forestier")
    additional_symptoms: Optional[Dict[str, Any]] = Field(None, description="Observations supplémentaires de symptômes")
    climate_data: Optional[Dict[str, Any]] = Field(None, description="Données climatiques pour l'analyse de risques")
    parcel_id: Optional[str] = Field(None, description="Identifiant de parcelle pour enrichissement des données")
    
    class Config:
        schema_extra = {
            "example": {
                "inventory_data": {
                    "items": [
                        {
                            "species": "quercus_ilex",
                            "diameter": 25.5,
                            "height": 12.0,
                            "health_status": "moyen"
                        }
                    ],
                    "area": 1.5
                },
                "additional_symptoms": {
                    "leaf_discoloration": 0.35,
                    "observed_pests": ["bark_beetle"],
                    "crown_thinning": 0.25
                },
                "parcel_id": "13097000B0012"
            }
        }

class ReportRequest(BaseModel):
    """Modèle pour la demande de génération de rapport."""
    report_type: str = Field(..., description="Type de rapport (diagnostic, management_plan, health)")
    data_id: str = Field(..., description="Identifiant des données (parcelle, diagnostic, etc.)")
    format: str = Field("pdf", description="Format du rapport (pdf, html, txt)")
    health_detail_level: Optional[str] = Field("standard", description="Niveau de détail sanitaire (minimal, standard, complete)")
    
    class Config:
        schema_extra = {
            "example": {
                "report_type": "diagnostic",
                "data_id": "13097000B0012",
                "format": "pdf",
                "health_detail_level": "standard"
            }
        }
