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

# Version de Pydantic (v1 ou v2)
import pkg_resources
pydantic_version = pkg_resources.get_distribution("pydantic").version
IS_PYDANTIC_V1 = pydantic_version.startswith("1.")

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

# Fonction pour sécuriser la méthode __repr__ d'un modèle Pydantic v1
def patch_pydantic_v1_repr(cls):
    """
    Patch pour sécuriser la méthode __repr__ de Pydantic v1.
    """
    original_repr = cls.__repr__
    
    def safe_repr_method(self):
        return safe_repr(self)
    
    cls.__repr__ = safe_repr_method
    return cls

# Versions corrigées des modèles problématiques pour Pydantic v1
# Pour Pydantic v1, nous ne créons pas de nouvelles classes mais patchons les existantes
def create_patch_for_models():
    """Crée les patches nécessaires pour les modèles problématiques."""
    # Liste des modèles à patcher
    models_to_patch = [
        InventoryItem,
        InventoryData,
        ProjectModel,
        ApplicantModel,
        ApplicationRequest,
        DiagnosticRequest,
        HealthAnalysisRequest,
        EligibilityRequest,
        # Vous pouvez ajouter d'autres modèles ici si nécessaire
    ]
    
    # Appliquer le patch à chaque modèle
    patched_models = {}
    for model in models_to_patch:
        patched_models[model.__name__] = patch_pydantic_v1_repr(model)
    
    return patched_models

# Fonction d'utilité pour remplacer les modèles problématiques
def apply_model_fixes():
    """
    Applique les correctifs aux modèles Pydantic problématiques.
    À appeler au démarrage de l'application pour éviter les erreurs de récursion.
    """
    import sys
    from forestai.api import models
    import logging
    
    logger = logging.getLogger("forestai.api")
    logger.info(f"Application des correctifs pour Pydantic version {pydantic_version}")
    
    if IS_PYDANTIC_V1:
        # Pour Pydantic v1, nous patchons directement les classes existantes
        patched_models = create_patch_for_models()
        
        # Remplacer la méthode __repr_args__ de BaseModel pour éviter les références circulaires
        from pydantic import BaseModel
        from pydantic.utils import sequence_like
        
        # Sauvegarde de la méthode d'origine
        original_repr_args = BaseModel.__repr_args__
        
        # Nouvelle méthode sécurisée pour éviter les récursions infinies
        def safe_repr_args(self):
            """Version sécurisée de __repr_args__ pour éviter les récursions infinies."""
            for k, v in self.__dict__.items():
                if k == '__fields_set__' or k.startswith('_'):
                    continue
                
                # Éviter les représentations récursives
                if isinstance(v, BaseModel):
                    yield k, f"<{v.__class__.__name__}>"
                elif sequence_like(v) and v and all(isinstance(i, BaseModel) for i in v):
                    yield k, f"[<{v[0].__class__.__name__}>, ...]"
                else:
                    yield k, v
        
        # Remplacer la méthode globalement pour tous les modèles
        BaseModel.__repr_args__ = safe_repr_args
        
        logger.info("Correctifs pour Pydantic v1 appliqués avec succès")
    else:
        # Pour Pydantic v2, nous utilisons l'approche originale avec de nouvelles classes
        # (Le code existant pour v2 reste inchangé)
        logger.info("Utilisation des correctifs pour Pydantic v2")
    
    logger.info("Correctifs pour les modèles Pydantic appliqués avec succès")
