"""
Correctifs spécifiques pour Pydantic v1.x.

Ce module contient des correctifs pour résoudre les problèmes de récursion infinie
dans les modèles Pydantic v1.x, notamment pour les références circulaires.
"""

import sys
import logging
import inspect
from typing import Dict, List, Set, Any, Type, Optional, Callable, Union

logger = logging.getLogger("forestai.patches.pydantic_v1")

# Liste des modèles à patcher (sera remplie lors de l'appel à patch_pydantic_models)
MODELS_TO_PATCH = []

def is_pydantic_v1_installed() -> bool:
    """
    Vérifie si Pydantic v1.x est installé.
    
    Returns:
        bool: True si Pydantic v1.x est installé, False sinon.
    """
    try:
        import pydantic
        return pydantic.__version__.startswith("1.")
    except (ImportError, AttributeError):
        return False

def patch_pydantic_repr_args():
    """
    Patch la méthode __repr_args__ de BaseModel pour éviter les références circulaires.
    
    Returns:
        bool: True si le patch a été appliqué avec succès, False sinon.
    """
    try:
        # Importer pydantic
        from pydantic import BaseModel
        from pydantic.utils import sequence_like
        
        # Sauvegarder la méthode originale
        original_repr_args = BaseModel.__repr_args__
        
        # Garder une trace des objets déjà visités pour éviter les récursions infinies
        visited_objects = set()
        
        # Nouvelle implémentation sécurisée
        def safe_repr_args(self):
            """Version sécurisée de __repr_args__ pour éviter les récursions infinies."""
            # Détecter les références circulaires
            obj_id = id(self)
            if obj_id in visited_objects:
                # On a déjà visité cet objet, retourner une représentation simplifiée
                yield "(recursion)", f"<{self.__class__.__name__}>"
                return
            
            # Ajouter l'objet à la liste des objets visités
            visited_objects.add(obj_id)
            
            try:
                # Logique standard pour les représentations
                for k, v in self.__dict__.items():
                    if k == '__fields_set__' or k.startswith('_'):
                        continue
                    
                    # Traitement spécial pour les modèles Pydantic imbriqués
                    if isinstance(v, BaseModel):
                        yield k, f"<{v.__class__.__name__}>"
                        continue
                    
                    # Traitement spécial pour les listes de modèles Pydantic
                    if sequence_like(v) and v and all(isinstance(i, BaseModel) for i in v):
                        yield k, f"[<{v[0].__class__.__name__}>, ...]"
                        continue
                    
                    # Valeur normale
                    yield k, v
            finally:
                # Nettoyer après l'appel pour éviter les fuites mémoire
                visited_objects.remove(obj_id)
        
        # Remplacer la méthode
        BaseModel.__repr_args__ = safe_repr_args
        
        logger.info("Méthode __repr_args__ de BaseModel patchée avec succès")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors du patch de BaseModel.__repr_args__: {e}")
        return False

def patch_display_as_type():
    """
    Patch la fonction display_as_type pour éviter les récursions infinies.
    
    Returns:
        bool: True si le patch a été appliqué avec succès, False sinon.
    """
    try:
        # Importer le module interne de Pydantic
        from pydantic.typing import display_as_type
        
        # Sauvegarder la fonction originale
        original_display_as_type = display_as_type
        
        # Créer un dictionnaire pour mémoriser les types déjà rencontrés
        seen_types = {}
        
        # Nouvelle implémentation sécurisée
        def safe_display_as_type(t):
            """Version sécurisée de display_as_type pour éviter les récursions infinies."""
            # Si le type a déjà été rencontré dans cette chaîne d'appels, retourner une représentation simple
            type_id = id(t)
            if type_id in seen_types:
                return f"<{getattr(t, '__name__', str(t))}>"
            
            # Ajouter ce type à la liste des types visités
            seen_types[type_id] = True
            
            try:
                # Appeler la fonction originale
                result = original_display_as_type(t)
                return result
            except RecursionError:
                # En cas de récursion, retourner une forme simplifiée
                return f"<{getattr(t, '__name__', str(t))}>"
            except Exception:
                # En cas d'erreur, retourner une forme simplifiée
                return f"<{getattr(t, '__name__', str(t))}>"
            finally:
                # Nettoyer après l'appel
                if type_id in seen_types:
                    del seen_types[type_id]
        
        # Remplacer la fonction dans le module
        import pydantic.typing
        pydantic.typing.display_as_type = safe_display_as_type
        
        # Mettre à jour également les références dans d'autres modules
        for name, module in sys.modules.items():
            if name.startswith('pydantic.') and hasattr(module, 'display_as_type'):
                setattr(module, 'display_as_type', safe_display_as_type)
        
        logger.info("Fonction display_as_type patchée avec succès")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors du patch de display_as_type: {e}")
        return False

def find_pydantic_models():
    """
    Détecte automatiquement les modèles Pydantic dans le projet.
    
    Returns:
        List[Type]: Liste des classes Pydantic BaseModel trouvées.
    """
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
        except (ImportError, AttributeError, Exception) as e:
            # Ignorer les erreurs pour continuer le scan
            pass
    
    logger.info(f"Détection automatique: {len(result)} modèles Pydantic trouvés")
    return result

def patch_model_repr(model_class):
    """
    Patch la méthode __repr__ d'un modèle Pydantic spécifique.
    
    Args:
        model_class (Type): Classe de modèle Pydantic à patcher.
    
    Returns:
        bool: True si le patch a été appliqué avec succès, False sinon.
    """
    try:
        original_repr = model_class.__repr__
        
        def safe_repr(self):
            """Version sécurisée de __repr__ pour éviter les récursions infinies."""
            # Créer une représentation simplifiée
            attrs = []
            for k, v in self.__dict__.items():
                if k.startswith("_"):
                    continue
                
                # Traiter différemment selon le type
                from pydantic import BaseModel
                if isinstance(v, BaseModel):
                    attrs.append(f"{k}=<{v.__class__.__name__}>")
                elif isinstance(v, list) and v and isinstance(v[0], BaseModel):
                    attrs.append(f"{k}=[<{v[0].__class__.__name__}>, ...]")
                else:
                    attrs.append(f"{k}={repr(v)}")
            
            return f"{self.__class__.__name__}({', '.join(attrs)})"
        
        # Remplacer la méthode
        model_class.__repr__ = safe_repr
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors du patch de {model_class.__name__}.__repr__: {e}")
        return False

def patch_pydantic_models():
    """
    Applique tous les correctifs nécessaires aux modèles Pydantic v1.
    
    Cette fonction combine les différents correctifs pour résoudre les problèmes
    de récursion dans les modèles Pydantic.
    
    Returns:
        bool: True si tous les correctifs ont été appliqués avec succès, False sinon.
    """
    if not is_pydantic_v1_installed():
        logger.info("Pydantic v1.x n'est pas installé, les correctifs ne sont pas nécessaires")
        return False
    
    success = True
    
    # 1. Patcher la méthode __repr_args__ de BaseModel
    if not patch_pydantic_repr_args():
        success = False
    
    # 2. Patcher la fonction display_as_type
    if not patch_display_as_type():
        success = False
    
    # 3. Détecter et patcher les modèles problématiques
    global MODELS_TO_PATCH
    
    # Si la liste n'est pas fournie, la détecter automatiquement
    if not MODELS_TO_PATCH:
        MODELS_TO_PATCH = find_pydantic_models()
    
    # Patcher chaque modèle
    for model_class in MODELS_TO_PATCH:
        patched = patch_model_repr(model_class)
        if not patched:
            logger.warning(f"Échec du patch pour le modèle {model_class.__name__}")
            success = False
    
    return success
