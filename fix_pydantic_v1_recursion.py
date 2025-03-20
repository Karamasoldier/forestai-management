#!/usr/bin/env python
"""
Script de correctif direct pour les problèmes de récursion dans Pydantic v1.

Ce script corrige directement le module Pydantic pour éviter les erreurs
de récursion infinie en modifiant la façon dont les représentations des
modèles sont générées.

Usage:
    python fix_pydantic_v1_recursion.py

Note:
    Ce script doit être exécuté avant d'importer tout code qui utilise Pydantic.
"""

import sys
import os
import logging
import importlib
import inspect

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fix_pydantic")

def patch_pydantic_repr():
    """
    Patch la méthode __repr_args__ de BaseModel pour éviter les références circulaires.
    """
    try:
        # Importer pydantic
        import pydantic
        from pydantic import BaseModel
        
        # Vérifier la version
        version = pydantic.__version__
        logger.info(f"Version de Pydantic détectée: {version}")
        
        if not version.startswith("1."):
            logger.info("Cette version de Pydantic n'a pas besoin de ce correctif spécifique.")
            return False
        
        # Sauvegarder la méthode originale
        original_repr_args = BaseModel.__repr_args__
        
        # Nouvelle implémentation sécurisée
        def safe_repr_args(self):
            """Version sécurisée de __repr_args__ pour éviter les récursions infinies."""
            from pydantic.utils import sequence_like
            
            visited = set()
            visited.add(id(self))
            
            for k, v in self.__dict__.items():
                if k == '__fields_set__' or k.startswith('_'):
                    continue
                
                # Éviter les références circulaires
                if hasattr(v, '__dict__') and id(v) in visited:
                    yield k, f"<{v.__class__.__name__}>"
                    continue
                
                # Traiter les modèles Pydantic
                if isinstance(v, BaseModel):
                    yield k, f"<{v.__class__.__name__}>"
                    continue
                
                # Traiter les séquences de modèles Pydantic
                if sequence_like(v) and v and all(isinstance(i, BaseModel) for i in v):
                    yield k, f"[<{v[0].__class__.__name__}>, ...]"
                    continue
                
                # Valeur normale
                yield k, v
        
        # Remplacer la méthode
        BaseModel.__repr_args__ = safe_repr_args
        
        # Tester le patch
        class TestModel(BaseModel):
            x: int = 1
        
        instance = TestModel()
        repr_str = repr(instance)
        logger.info(f"Test du patch réussi: {repr_str}")
        
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors du patch de Pydantic: {e}")
        return False

def patch_display_as_type():
    """
    Patch la fonction display_as_type pour éviter les récursions infinies.
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
                # Nettoyer après l'appel
                del seen_types[type_id]
                return result
            except RecursionError:
                # En cas de récursion, retourner une forme simplifiée
                if hasattr(t, '__name__'):
                    return f"<{t.__name__}>"
                return f"<{str(t)}>"
            except Exception:
                # Nettoyer en cas d'erreur
                if type_id in seen_types:
                    del seen_types[type_id]
                # Réessayer avec une approche plus simple
                return f"<{getattr(t, '__name__', str(t))}>"
        
        # Remplacer la fonction dans le module
        import pydantic.typing
        pydantic.typing.display_as_type = safe_display_as_type
        
        # Mettre à jour également les références dans d'autres modules
        for name, module in sys.modules.items():
            if name.startswith('pydantic.') and hasattr(module, 'display_as_type'):
                setattr(module, 'display_as_type', safe_display_as_type)
        
        logger.info("Patch de display_as_type appliqué avec succès")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors du patch de display_as_type: {e}")
        return False

def main():
    """
    Fonction principale.
    """
    logger.info("Application des correctifs pour Pydantic v1...")
    
    # Patch de la méthode __repr_args__ de BaseModel
    if patch_pydantic_repr():
        logger.info("✅ Patch de BaseModel.__repr_args__ appliqué avec succès")
    else:
        logger.error("❌ Échec du patch de BaseModel.__repr_args__")
    
    # Patch de la fonction display_as_type
    if patch_display_as_type():
        logger.info("✅ Patch de display_as_type appliqué avec succès")
    else:
        logger.error("❌ Échec du patch de display_as_type")
    
    logger.info("Terminé. Les modèles Pydantic devraient maintenant être protégés contre les erreurs de récursion.")

if __name__ == "__main__":
    main()
