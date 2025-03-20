#!/usr/bin/env python
"""
Script de débogage pour identifier les modèles Pydantic problématiques
qui peuvent causer des erreurs de récursion infinie.

Ce script parcourt les modèles Pydantic définis dans forestai.api.models
et tente de détecter les références circulaires potentielles.

Usage:
    python scripts/debug_pydantic_models.py

Ce script est utile pour trouver les causes profondes des erreurs RecursionError.
"""

import sys
import inspect
from typing import Set, Dict, List, Any, Type, Optional
import logging
from pydantic import BaseModel

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("debug_pydantic")

def analyze_model_field(field_type, visited_models: Set[Type], depth: int, max_depth: int = 10) -> bool:
    """
    Analyse récursivement un type de champ pour détecter les références circulaires.
    
    Args:
        field_type: Type du champ à analyser
        visited_models: Ensemble des modèles déjà visités dans cette branche
        depth: Profondeur actuelle dans l'arbre de récursion
        max_depth: Profondeur maximale à explorer
        
    Returns:
        bool: True si une référence circulaire est détectée, False sinon
    """
    if depth > max_depth:
        logger.warning(f"Profondeur maximale atteinte ({max_depth}), arrêt de l'analyse pour éviter une boucle infinie")
        return False
    
    # Origin est généralement le type de base pour les types génériques (List, Dict, etc.)
    origin = getattr(field_type, "__origin__", None)
    args = getattr(field_type, "__args__", [])
    
    # Analyser les types génériques (List, Dict, etc.)
    if origin is not None:
        for arg in args:
            if inspect.isclass(arg) and issubclass(arg, BaseModel):
                if arg in visited_models:
                    return True
                new_visited = visited_models.copy()
                new_visited.add(arg)
                if analyze_model(arg, new_visited, depth + 1, max_depth):
                    return True
            elif hasattr(arg, "__origin__"):  # Type générique imbriqué
                if analyze_model_field(arg, visited_models, depth + 1, max_depth):
                    return True
                    
    # Analyser les types non génériques
    elif inspect.isclass(field_type) and issubclass(field_type, BaseModel):
        if field_type in visited_models:
            return True
        new_visited = visited_models.copy()
        new_visited.add(field_type)
        if analyze_model(field_type, new_visited, depth + 1, max_depth):
            return True
            
    return False

def analyze_model(model_class: Type[BaseModel], visited_models: Set[Type] = None, depth: int = 0, max_depth: int = 10) -> bool:
    """
    Analyse un modèle Pydantic pour détecter les références circulaires.
    
    Args:
        model_class: Classe du modèle à analyser
        visited_models: Ensemble des modèles déjà visités dans cette branche
        depth: Profondeur actuelle dans l'arbre de récursion
        max_depth: Profondeur maximale à explorer
    
    Returns:
        bool: True si une référence circulaire est détectée, False sinon
    """
    if visited_models is None:
        visited_models = {model_class}
    
    if depth > max_depth:
        logger.warning(f"Profondeur maximale atteinte ({max_depth}), arrêt de l'analyse pour éviter une boucle infinie")
        return False
    
    circular_refs = []
    
    try:
        # Inspecter les champs du modèle via les annotations de type
        for field_name, field_info in model_class.__annotations__.items():
            field_type = field_info
            
            # Détecter les références circulaires
            if analyze_model_field(field_type, visited_models, depth + 1, max_depth):
                circular_refs.append(field_name)
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du modèle {model_class.__name__}: {e}")
    
    return len(circular_refs) > 0

def find_circular_references():
    """
    Recherche les références circulaires dans tous les modèles Pydantic de l'API.
    """
    from forestai.api import models
    
    logger.info("Recherche des références circulaires dans les modèles Pydantic...")
    circular_models = []
    
    # Parcourir tous les attributs du module models
    for name in dir(models):
        item = getattr(models, name)
        
        # Vérifier si c'est un modèle Pydantic
        if isinstance(item, type) and issubclass(item, BaseModel) and item != BaseModel:
            logger.info(f"Analyse du modèle {name}...")
            
            try:
                # Test simple: essayer de représenter le modèle default vide
                instance = item()
                repr(instance)
                logger.info(f"✓ Le modèle {name} ne semble pas avoir de problème de représentation.")
            except RecursionError:
                logger.error(f"✗ Le modèle {name} cause une RecursionError lors de la représentation!")
                circular_models.append(name)
            except Exception as e:
                logger.warning(f"? Le modèle {name} a généré une erreur (non-récursion): {e}")
            
            # Analyse approfondie des relations
            visited = {item}
            if analyze_model(item, visited):
                logger.warning(f"! Le modèle {name} contient potentiellement des références circulaires.")
                if name not in circular_models:
                    circular_models.append(name)
    
    # Afficher un résumé
    if circular_models:
        logger.warning("Modèles avec références circulaires détectées:")
        for model in circular_models:
            logger.warning(f" - {model}")
        
        logger.info("\nAjoutez ces modèles à la liste des modèles à corriger dans forestai/api/models_fix.py")
    else:
        logger.info("Aucune référence circulaire détectée dans les modèles.")

def test_apply_model_fixes():
    """
    Teste l'application des correctifs aux modèles Pydantic.
    """
    logger.info("Test de l'application des correctifs...")
    
    try:
        from forestai.api.models_fix import apply_model_fixes
        apply_model_fixes()
        logger.info("✓ Correctifs appliqués avec succès.")
    except Exception as e:
        logger.error(f"✗ Erreur lors de l'application des correctifs: {e}")
        return False
    
    # Vérifier si les modèles corrigés fonctionnent correctement
    from forestai.api import models
    
    all_ok = True
    for name in dir(models):
        item = getattr(models, name)
        
        if isinstance(item, type) and issubclass(item, BaseModel) and item != BaseModel:
            try:
                # Test de représentation
                instance = item()
                repr(instance)
                logger.info(f"✓ Après correction, le modèle {name} fonctionne correctement.")
            except RecursionError:
                logger.error(f"✗ Après correction, le modèle {name} cause toujours une RecursionError!")
                all_ok = False
            except Exception as e:
                logger.warning(f"? Après correction, le modèle {name} a généré une erreur (non-récursion): {e}")
    
    return all_ok

if __name__ == "__main__":
    logger.info("Démarrage du débogage des modèles Pydantic...")
    
    # Rechercher les références circulaires
    find_circular_references()
    
    # Tester les correctifs
    if test_apply_model_fixes():
        logger.info("Tous les modèles semblent fonctionner correctement après correction.")
    else:
        logger.warning("Certains modèles présentent encore des problèmes après correction.")
        
    logger.info("Débogage terminé.")
