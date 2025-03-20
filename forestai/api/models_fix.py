"""
Module pour résoudre les problèmes de références circulaires dans les modèles Pydantic.

Ce module contient des versions modifiées des modèles de données API qui causent
des erreurs de récursion infinie lors de la sérialisation ou représentation.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import date

# Importez les modèles existants que nous allons corriger
from forestai.api.models import *

# Ajoutez cette fonction pour éviter les références circulaires dans __repr__
def safe_repr(obj):
    """
    Crée une représentation sûre d'un objet, en évitant les références circulaires.
    Remplace la méthode __repr__ problématique de Pydantic pour certains modèles.
    """
    class_name = obj.__class__.__name__
    attrs = []
    for key, value in obj.__dict__.items():
        if key.startswith("_"):
            continue
        
        # Éviter les représentations récursives
        if isinstance(value, BaseModel):
            attrs.append(f"{key}=<{value.__class__.__name__}>")
        elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
            attrs.append(f"{key}=[<{value[0].__class__.__name__}>, ...]")
        else:
            attrs.append(f"{key}={repr(value)}")
            
    return f"{class_name}({', '.join(attrs)})"

# Versions corrigées des modèles problématiques

class InventoryItemFixed(BaseModel):
    """Version fixée de InventoryItem sans références circulaires."""
    species: str = Field(..., description="Espèce de l'arbre")
    diameter: float = Field(..., description="Diamètre de l'arbre (en cm)")
    height: float = Field(..., description="Hauteur de l'arbre (en m)")
    age: Optional[int] = Field(None, description="Âge estimé de l'arbre (en années)")
    health_status: Optional[str] = Field(None, description="État sanitaire (bon, moyen, mauvais)")
    x: Optional[float] = Field(None, description="Coordonnée X (optionnelle)")
    y: Optional[float] = Field(None, description="Coordonnée Y (optionnelle)")
    notes: Optional[str] = Field(None, description="Notes supplémentaires")
    
    def __repr__(self):
        return safe_repr(self)

class InventoryDataFixed(BaseModel):
    """Version fixée de InventoryData sans références circulaires."""
    items: List[InventoryItemFixed] = Field(..., description="Liste des arbres inventoriés")
    area: Optional[float] = Field(None, description="Surface inventoriée (ha)")
    date: Optional[date] = Field(None, description="Date de l'inventaire")
    method: Optional[str] = Field(None, description="Méthode d'inventaire")
    
    def __repr__(self):
        return safe_repr(self)

class ProjectModelFixed(BaseModel):
    """Version fixée de ProjectModel sans références circulaires."""
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
    
    def __repr__(self):
        return safe_repr(self)

class ApplicantModelFixed(BaseModel):
    """Version fixée de ApplicantModel sans références circulaires."""
    name: str = Field(..., description="Nom du demandeur")
    address: str = Field(..., description="Adresse")
    contact: str = Field(..., description="Email de contact")
    siret: Optional[str] = Field(None, description="Numéro SIRET")
    contact_name: Optional[str] = Field(None, description="Nom du contact")
    contact_phone: Optional[str] = Field(None, description="Téléphone de contact")
    owner_since: Optional[date] = Field(None, description="Date d'acquisition de la propriété")
    
    def __repr__(self):
        return safe_repr(self)

class ApplicationRequestFixed(BaseModel):
    """Version fixée de ApplicationRequest sans références circulaires."""
    project: ProjectModelFixed = Field(..., description="Données du projet forestier")
    subsidy_id: str = Field(..., description="Identifiant de la subvention")
    applicant: ApplicantModelFixed = Field(..., description="Données du demandeur")
    output_formats: List[str] = Field(["pdf"], description="Formats de sortie souhaités")
    
    def __repr__(self):
        return safe_repr(self)

class DiagnosticRequestFixed(BaseModel):
    """Version fixée de DiagnosticRequest sans références circulaires."""
    parcel_id: str = Field(..., description="Identifiant de la parcelle")
    inventory_data: Optional[InventoryDataFixed] = Field(None, description="Données d'inventaire forestier (optionnel)")
    include_health_analysis: bool = Field(True, description="Inclure l'analyse sanitaire")
    
    def __repr__(self):
        return safe_repr(self)

class HealthAnalysisRequestFixed(BaseModel):
    """Version fixée de HealthAnalysisRequest sans références circulaires."""
    inventory_data: InventoryDataFixed = Field(..., description="Données d'inventaire forestier")
    additional_symptoms: Optional[Dict[str, Any]] = Field(None, description="Observations supplémentaires de symptômes")
    climate_data: Optional[Dict[str, Any]] = Field(None, description="Données climatiques pour l'analyse de risques")
    parcel_id: Optional[str] = Field(None, description="Identifiant de parcelle pour enrichissement des données")
    
    def __repr__(self):
        return safe_repr(self)

class EligibilityRequestFixed(BaseModel):
    """Version fixée de EligibilityRequest sans références circulaires."""
    project: ProjectModelFixed = Field(..., description="Données du projet forestier")
    subsidy_id: str = Field(..., description="Identifiant de la subvention à analyser")
    
    def __repr__(self):
        return safe_repr(self)

# Fonction d'utilité pour remplacer les modèles problématiques
def apply_model_fixes():
    """
    Applique les correctifs aux modèles Pydantic problématiques.
    À appeler au démarrage de l'application pour éviter les erreurs de récursion.
    """
    import sys
    from forestai.api import models
    
    # Remplacer les modèles problématiques
    models.InventoryItem = InventoryItemFixed
    models.InventoryData = InventoryDataFixed
    models.ProjectModel = ProjectModelFixed
    models.ApplicantModel = ApplicantModelFixed
    models.ApplicationRequest = ApplicationRequestFixed
    models.DiagnosticRequest = DiagnosticRequestFixed
    models.HealthAnalysisRequest = HealthAnalysisRequestFixed
    models.EligibilityRequest = EligibilityRequestFixed
    
    # Mise à jour systémique pour trouver d'autres modèles potentiellement problématiques
    for name in dir(models):
        item = getattr(models, name)
        if isinstance(item, type) and issubclass(item, BaseModel) and item not in [
            InventoryItemFixed, InventoryDataFixed, ProjectModelFixed, 
            ApplicantModelFixed, ApplicationRequestFixed, DiagnosticRequestFixed,
            HealthAnalysisRequestFixed, EligibilityRequestFixed
        ]:
            # Pour tous les autres modèles BaseModel qui n'ont pas déjà été remplacés
            original_repr = item.__repr__
            
            # Créer une méthode de remplacement pour __repr__
            def safe_repr_wrapper(self):
                return safe_repr(self)
            
            # Remplacer la méthode __repr__
            item.__repr__ = safe_repr_wrapper
    
    # Note de log pour confirmer l'application des correctifs
    import logging
    logger = logging.getLogger("forestai.api")
    logger.info("Correctifs pour les modèles Pydantic appliqués avec succès")
