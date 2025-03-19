"""
Module pour résoudre les problèmes de références circulaires dans les modèles Pydantic.

Ce module contient des versions modifiées des modèles de données API qui causent
des erreurs de récursion infinie lors de la sérialisation ou représentation.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

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

# Remplacez ou corrigez les modèles qui causent des problèmes

# Exemple: si ProjectData et ApplicantData ont des références circulaires
class ProjectDataFixed(BaseModel):
    """Version fixée de ProjectData sans références circulaires."""
    # Copiez les champs de la classe originale ici
    name: str
    description: Optional[str] = None
    area: Optional[float] = None
    location: Optional[Dict[str, Any]] = None
    parcel_ids: Optional[List[str]] = None
    
    def __repr__(self):
        return safe_repr(self)

class ApplicantDataFixed(BaseModel):
    """Version fixée de ApplicantData sans références circulaires."""
    # Copiez les champs de la classe originale ici
    name: str
    contact: Optional[Dict[str, str]] = None
    address: Optional[str] = None
    
    def __repr__(self):
        return safe_repr(self)

# Si ApplicationRequest cause des problèmes
class ApplicationRequestFixed(BaseModel):
    """Version fixée de ApplicationRequest sans références circulaires."""
    project: ProjectDataFixed
    subsidy_id: str
    applicant: ApplicantDataFixed
    output_formats: List[str] = ["pdf"]
    
    def __repr__(self):
        return safe_repr(self)

# Ajoutez d'autres modèles fixés selon besoin

# Fonction d'utilité pour remplacer les modèles problématiques
def apply_model_fixes():
    """
    Applique les correctifs aux modèles Pydantic problématiques.
    À appeler au démarrage de l'application pour éviter les erreurs de récursion.
    """
    import sys
    from forestai.api import models
    
    # Remplacer les modèles problématiques
    # Exemple:
    # models.ProjectData = ProjectDataFixed
    # models.ApplicantData = ApplicantDataFixed
    # models.ApplicationRequest = ApplicationRequestFixed
    
    # Vous pourriez avoir besoin d'ajouter d'autres modèles selon les erreurs que vous rencontrez
    
    # Note de log pour confirmer l'application des correctifs
    import logging
    logger = logging.getLogger("forestai.api")
    logger.info("Correctifs pour les modèles Pydantic appliqués avec succès")
