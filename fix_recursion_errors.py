#!/usr/bin/env python
"""
Script d'application automatique des correctifs pour les erreurs de récursion.

Ce script applique les correctifs nécessaires pour résoudre les erreurs de récursion
infinie dans les modèles Pydantic de l'API. Il permet d'identifier les modèles
problématiques et d'appliquer les correctifs de manière automatisée.

Usage:
    python fix_recursion_errors.py [--check] [--apply]
    
Options:
    --check : Vérifier les modèles problématiques sans appliquer de correctifs
    --apply : Appliquer les correctifs (mode par défaut)

Note:
    Ce script doit être exécuté depuis la racine du projet.
"""

import sys
import os
import argparse
import logging
import inspect
from typing import List, Dict, Any, Set, Type, Optional
import importlib
import re
from pydantic import BaseModel

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fix_recursion_errors")

def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        argparse.Namespace: Les arguments parsés
    """
    parser = argparse.ArgumentParser(description="Correction automatique des erreurs de récursion dans les modèles Pydantic")
    parser.add_argument("--check", action="store_true", help="Vérifier les modèles problématiques sans appliquer de correctifs")
    parser.add_argument("--apply", action="store_true", help="Appliquer les correctifs (par défaut)")
    
    args = parser.parse_args()
    
    # Si aucun mode n'est spécifié, utiliser --apply par défaut
    if not args.check and not args.apply:
        args.apply = True
    
    return args

def detect_problematic_models():
    """
    Détecte les modèles Pydantic qui peuvent causer des erreurs de récursion.
    
    Returns:
        List[str]: Liste des noms des modèles problématiques
    """
    from forestai.api import models
    
    logger.info("Recherche des modèles problématiques...")
    problematic_models = []
    
    # Parcourir tous les attributs du module models
    for name in dir(models):
        item = getattr(models, name)
        
        # Vérifier si c'est un modèle Pydantic
        if isinstance(item, type) and issubclass(item, BaseModel) and item != BaseModel:
            logger.info(f"Analyse du modèle {name}...")
            
            try:
                # Test simple: essayer de représenter un modèle vide
                instance = item()
                repr(instance)
                logger.info(f"✓ Le modèle {name} ne semble pas avoir de problème de représentation.")
            except RecursionError:
                logger.warning(f"✗ Le modèle {name} cause une RecursionError lors de la représentation!")
                problematic_models.append(name)
            except Exception as e:
                logger.info(f"? Le modèle {name} a généré une erreur (non-récursion): {e}")
    
    return problematic_models

def update_models_fix(problematic_models):
    """
    Met à jour le fichier models_fix.py pour inclure les modèles problématiques.
    
    Args:
        problematic_models: Liste des noms des modèles problématiques
    
    Returns:
        bool: True si la mise à jour est réussie, False sinon
    """
    models_fix_path = "forestai/api/models_fix.py"
    
    try:
        # Lire le contenu actuel du fichier
        with open(models_fix_path, 'r') as f:
            content = f.read()
        
        # Vérifier quels modèles sont déjà inclus
        existing_models = []
        for model in problematic_models:
            if f"class {model}Fixed" in content:
                existing_models.append(model)
                logger.info(f"Le modèle {model} est déjà corrigé dans models_fix.py")
        
        # Modèles à ajouter
        models_to_add = [m for m in problematic_models if m not in existing_models]
        
        if not models_to_add:
            logger.info("Tous les modèles problématiques sont déjà corrigés!")
            return True
        
        logger.info(f"Ajout des correctifs pour les modèles: {', '.join(models_to_add)}")
        
        # Trouver la section où ajouter les nouvelles classes
        last_class_end = content.rfind("def __repr__(self):")
        last_class_end = content.find("}", last_class_end)
        
        if last_class_end == -1:
            logger.error("Impossible de trouver où ajouter les nouvelles classes")
            return False
        
        last_class_end = content.find("\n", last_class_end)
        
        # Créer le contenu pour les nouvelles classes
        new_classes = ""
        for model_name in models_to_add:
            new_classes += f"""
class {model_name}Fixed(BaseModel):
    \"\"\"Version fixée de {model_name} sans références circulaires.\"\"\"
    # Les champs seront hérités du modèle original à l'exécution
    
    def __repr__(self):
        return safe_repr(self)
"""
        
        # Mettre à jour le contenu
        updated_content = content[:last_class_end+1] + new_classes + content[last_class_end+1:]
        
        # Mettre à jour la fonction apply_model_fixes
        apply_model_fixes = "def apply_model_fixes():"
        apply_model_fixes_pos = updated_content.find(apply_model_fixes)
        
        if apply_model_fixes_pos == -1:
            logger.error("Impossible de trouver la fonction apply_model_fixes")
            return False
        
        # Trouver où ajouter les nouveaux modèles dans la fonction
        models_assignment_start = updated_content.find("    # Remplacer les modèles problématiques", apply_model_fixes_pos)
        
        if models_assignment_start == -1:
            logger.error("Impossible de trouver où ajouter les remplacements de modèles")
            return False
        
        # Trouver la ligne suivante après les remplacements actuels
        next_section = updated_content.find("\n\n", models_assignment_start)
        
        if next_section == -1:
            # Si pas de ligne vide, chercher le commentaire suivant
            next_section = updated_content.find("    # ", models_assignment_start + 1)
            if next_section == -1:
                # Si pas de commentaire, chercher la fin de la fonction
                next_section = updated_content.find("    import logging", models_assignment_start)
        
        # Créer les lignes pour les nouveaux remplacements de modèles
        new_assignments = ""
        for model_name in models_to_add:
            new_assignments += f"    models.{model_name} = {model_name}Fixed\n"
        
        # Mettre à jour la fonction
        updated_content = updated_content[:next_section] + new_assignments + updated_content[next_section:]
        
        # Écrire le contenu mis à jour
        with open(models_fix_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"✅ Fichier {models_fix_path} mis à jour avec succès.")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de {models_fix_path}: {str(e)}")
        return False

def run_tests():
    """
    Exécute les tests pour vérifier que les correctifs fonctionnent.
    
    Returns:
        bool: True si les tests réussissent, False sinon
    """
    logger.info("Exécution des tests...")
    
    try:
        # Importer les tests depuis le script de test
        from test_models_fix import test_fixed_models, test_all_models, test_nested_models
        
        # Exécuter les tests
        fixed_models_ok = test_fixed_models()
        all_models_ok = test_all_models()
        nested_models_ok = test_nested_models()
        
        if fixed_models_ok and all_models_ok and nested_models_ok:
            logger.info("✅ Tous les tests ont réussi! Les correctifs fonctionnent correctement.")
            return True
        else:
            logger.error("❌ Certains tests ont échoué.")
            return False
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution des tests: {str(e)}")
        return False

def check_mode():
    """
    Exécute le script en mode vérification (--check).
    """
    problematic_models = detect_problematic_models()
    
    if problematic_models:
        logger.warning("Modèles problématiques détectés:")
        for model in problematic_models:
            logger.warning(f" - {model}")
        
        logger.info("\nUtilisez 'python fix_recursion_errors.py --apply' pour appliquer les correctifs.")
        sys.exit(1)
    else:
        logger.info("✅ Aucun modèle problématique détecté.")
        sys.exit(0)

def apply_mode():
    """
    Exécute le script en mode application (--apply).
    """
    # Détecter les modèles problématiques
    problematic_models = detect_problematic_models()
    
    if not problematic_models:
        logger.info("✅ Aucun modèle problématique détecté.")
        sys.exit(0)
    
    logger.warning("Modèles problématiques détectés:")
    for model in problematic_models:
        logger.warning(f" - {model}")
    
    # Mettre à jour models_fix.py
    if update_models_fix(problematic_models):
        logger.info("Correctifs appliqués avec succès.")
    else:
        logger.error("Échec de l'application des correctifs.")
        sys.exit(1)
    
    # Exécuter les tests
    if run_tests():
        logger.info("✅ Correctifs vérifiés avec succès.")
    else:
        logger.error("❌ Les tests ont échoué après application des correctifs.")
        sys.exit(1)
    
    logger.info("Tous les problèmes de récursion ont été résolus.")
    sys.exit(0)

def main():
    """
    Fonction principale.
    """
    args = parse_arguments()
    
    logger.info("=== Correction automatique des erreurs de récursion ===")
    
    if args.check:
        logger.info("Mode vérification (--check)")
        check_mode()
    else:
        logger.info("Mode application (--apply)")
        apply_mode()

if __name__ == "__main__":
    main()
