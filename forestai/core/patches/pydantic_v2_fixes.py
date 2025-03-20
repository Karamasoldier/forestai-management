"""
Correctifs spécifiques pour Pydantic v2.x.

Ce module contient des correctifs pour résoudre les problèmes potentiels
dans les modèles Pydantic v2.x.

Note: Pydantic v2 gère généralement mieux les références circulaires par défaut,
mais ce module fournit des correctifs au besoin.
"""

import sys
import logging
import inspect
from typing import Dict, List, Set, Any, Type, Optional, Callable, Union

logger = logging.getLogger("forestai.patches.pydantic_v2")

def is_pydantic_v2_installed() -> bool:
    """
    Vérifie si Pydantic v2.x est installé.
    
    Returns:
        bool: True si Pydantic v2.x est installé, False sinon.
    """
    try:
        import pydantic
        version = pydantic.__version__
        return version.startswith("2.")
    except (ImportError, AttributeError):
        return False

def find_pydantic_models():
    """
    Détecte automatiquement les modèles Pydantic dans le projet.
    
    Returns:
        List[Type]: Liste des classes Pydantic BaseModel trouvées.
    """
    try:
        from pydantic import BaseModel
        
        result = []
        
        # Parcourir tous les modules chargés
        for module_name, module in list(sys.modules.items()):
            # Ne considérer que les modules du projet
            if not module_name.startswith('forestai.'):
                continue
            
            try:
                # Inspecter tous les objets du module
                for name, obj in inspect.getmembers(module):
                    # Vérifier si c'est une classe qui hérite de BaseModel
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseModel) and 
                        obj != BaseModel):
                        result.append(obj)
            except (ImportError, AttributeError, Exception):
                # Ignorer les erreurs pour continuer le scan
                pass
        
        logger.info(f"Détection automatique: {len(result)} modèles Pydantic trouvés")
        return result
    except ImportError:
        logger.warning("Pydantic n'est pas installé")
        return []

def ensure_model_config(model_class):
    """
    S'assure que les modèles ont une configuration correcte pour gérer les références circulaires.
    
    Args:
        model_class (Type): Classe de modèle Pydantic à vérifier/modifier.
    
    Returns:
        bool: True si la configuration a été vérifiée/modifiée avec succès, False sinon.
    """
    try:
        # Vérifier si le modèle a besoin d'une configuration spéciale
        if not hasattr(model_class, "model_config"):
            # Pour Pydantic v2, définir model_config avec les paramètres recommandés
            model_class.model_config = {
                "arbitrary_types_allowed": True,
                "extra": "allow",
                "validate_assignment": True,
                "protected_namespaces": ()
            }
            return True
        
        # Si model_config existe déjà, vérifier/mettre à jour les paramètres importants
        config = model_class.model_config
        if isinstance(config, dict):
            config.setdefault("arbitrary_types_allowed", True)
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de {model_class.__name__}: {e}")
        return False

def add_safe_json_serialization(model_class):
    """
    Ajoute une méthode de sérialisation JSON sécurisée au modèle.
    
    Args:
        model_class (Type): Classe de modèle Pydantic à modifier.
    
    Returns:
        bool: True si la méthode a été ajoutée avec succès, False sinon.
    """
    try:
        from pydantic import BaseModel
        
        def safe_dict(self, exclude_none=True, by_alias=False, exclude_unset=False, 
                     exclude_defaults=False, exclude=None, include=None, 
                     max_recursion=10, **kwargs):
            """
            Méthode model_dump modifiée pour limiter la récursion.
            """
            if max_recursion <= 0:
                # Limiter la profondeur de récursion
                if isinstance(self, BaseModel):
                    return f"<{self.__class__.__name__}>"
                return str(self)
            
            # Appeler la méthode originale avec récursion limitée
            if hasattr(self, "model_dump"):
                # Pydantic v2
                dump_kwargs = {
                    "exclude_none": exclude_none,
                    "by_alias": by_alias,
                    "exclude_unset": exclude_unset,
                    "exclude_defaults": exclude_defaults,
                    "exclude": exclude,
                    "include": include,
                    **kwargs
                }
                result = self.model_dump(**dump_kwargs)
            else:
                # Pydantic v1 (si par erreur ce correctif est appliqué à v1)
                dump_kwargs = {
                    "exclude_none": exclude_none,
                    "by_alias": by_alias,
                    "exclude_unset": exclude_unset,
                    "exclude_defaults": exclude_defaults,
                    "exclude": exclude,
                    "include": include,
                    **kwargs
                }
                if hasattr(self, "dict"):
                    result = self.dict(**dump_kwargs)
                else:
                    result = dict(self)
            
            # Traiter récursivement les valeurs qui sont des modèles Pydantic
            for key, value in list(result.items()):
                if isinstance(value, BaseModel):
                    result[key] = safe_dict(value, max_recursion=max_recursion-1, **dump_kwargs)
                elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
                    result[key] = [
                        safe_dict(item, max_recursion=max_recursion-1, **dump_kwargs) 
                        if isinstance(item, BaseModel) else item 
                        for item in value
                    ]
                elif isinstance(value, dict):
                    result[key] = {
                        k: safe_dict(v, max_recursion=max_recursion-1, **dump_kwargs) 
                        if isinstance(v, BaseModel) else v 
                        for k, v in value.items()
                    }
            
            return result
        
        # Ajouter la méthode au modèle
        model_class.safe_dict = safe_dict
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de safe_dict à {model_class.__name__}: {e}")
        return False

def patch_pydantic_models():
    """
    Applique tous les correctifs nécessaires aux modèles Pydantic v2.
    
    Cette fonction configure les modèles Pydantic v2 pour résoudre
    ou éviter les problèmes potentiels de récursion.
    
    Returns:
        bool: True si tous les correctifs ont été appliqués avec succès, False sinon.
    """
    if not is_pydantic_v2_installed():
        logger.info("Pydantic v2.x n'est pas installé, les correctifs ne sont pas appliqués")
        return False
    
    logger.info("Application des correctifs pour Pydantic v2.x")
    
    # 1. Trouver les modèles Pydantic dans le projet
    models = find_pydantic_models()
    
    if not models:
        logger.warning("Aucun modèle Pydantic trouvé dans le projet")
        return True  # Pas d'erreur, simplement rien à faire
    
    success = True
    
    # 2. Appliquer les correctifs à chaque modèle
    for model_class in models:
        # Assurer une configuration correcte
        if not ensure_model_config(model_class):
            success = False
        
        # Ajouter une méthode de sérialisation sécurisée
        if not add_safe_json_serialization(model_class):
            success = False
    
    if success:
        logger.info(f"Correctifs appliqués avec succès à {len(models)} modèles Pydantic v2")
    else:
        logger.warning("Certains correctifs n'ont pas pu être appliqués")
    
    return success
