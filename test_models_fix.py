#!/usr/bin/env python
"""
Script de test pour les correctifs des modèles Pydantic.

Ce script permet de tester si les correctifs des modèles Pydantic
fonctionnent correctement en essayant de sérialiser/représenter les modèles problématiques.

Usage:
    python test_models_fix.py

Si le script s'exécute sans erreur, cela signifie que les correctifs ont résolu
les problèmes de récursion infinie.
"""

import sys
import logging
import json
from pydantic import BaseModel

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_models_fix")

def test_model_repr(model_class, name):
    """
    Teste la représentation d'un modèle pour détecter les erreurs de récursion.
    
    Args:
        model_class: Classe du modèle à tester
        name: Nom du modèle pour l'affichage
        
    Returns:
        bool: True si le test réussit, False sinon
    """
    try:
        instance = model_class()
        repr_str = repr(instance)
        logger.info(f"✓ Le modèle {name} se représente correctement: {repr_str[:50]}...")
        return True
    except RecursionError as e:
        logger.error(f"✗ Le modèle {name} cause une RecursionError: {str(e)}")
        return False
    except Exception as e:
        logger.warning(f"? Le modèle {name} a généré une erreur (non-récursion): {str(e)}")
        return False

def test_model_json(model_class, name):
    """
    Teste la sérialisation JSON d'un modèle pour détecter les erreurs de récursion.
    
    Args:
        model_class: Classe du modèle à tester
        name: Nom du modèle pour l'affichage
        
    Returns:
        bool: True si le test réussit, False sinon
    """
    try:
        instance = model_class()
        json_str = instance.model_dump_json()
        logger.info(f"✓ Le modèle {name} se sérialise correctement en JSON: {json_str[:50]}...")
        return True
    except RecursionError as e:
        logger.error(f"✗ Le modèle {name} cause une RecursionError lors de la sérialisation JSON: {str(e)}")
        return False
    except Exception as e:
        logger.warning(f"? Le modèle {name} a généré une erreur lors de la sérialisation JSON (non-récursion): {str(e)}")
        return False

def test_fixed_models():
    """
    Teste les modèles corrigés pour vérifier qu'ils fonctionnent correctement.
    """
    logger.info("Chargement des correctifs de modèles...")
    
    # Appliquer les correctifs
    try:
        from forestai.api.models_fix import apply_model_fixes
        apply_model_fixes()
        logger.info("✓ Correctifs appliqués avec succès.")
    except Exception as e:
        logger.error(f"✗ Erreur lors de l'application des correctifs: {str(e)}")
        return False
    
    # Tester les modèles problématiques connus
    from forestai.api import models
    
    # Modèles à tester (ceux qui causaient des problèmes)
    test_models = [
        (models.InventoryItem, "InventoryItem"),
        (models.InventoryData, "InventoryData"),
        (models.ProjectModel, "ProjectModel"),
        (models.ApplicantModel, "ApplicantModel"),
        (models.ApplicationRequest, "ApplicationRequest"),
        (models.DiagnosticRequest, "DiagnosticRequest"),
        (models.HealthAnalysisRequest, "HealthAnalysisRequest"),
        (models.EligibilityRequest, "EligibilityRequest")
    ]
    
    # Exécuter les tests
    repr_success = all(test_model_repr(model, name) for model, name in test_models)
    json_success = all(test_model_json(model, name) for model, name in test_models)
    
    # Résumé des résultats
    if repr_success and json_success:
        logger.info("✅ Tous les tests ont réussi ! Les correctifs fonctionnent correctement.")
        return True
    else:
        if not repr_success:
            logger.error("❌ Des erreurs de représentation sont encore présentes.")
        if not json_success:
            logger.error("❌ Des erreurs de sérialisation JSON sont encore présentes.")
        return False

def test_all_models():
    """
    Teste tous les modèles Pydantic du module models.
    """
    logger.info("Test de tous les modèles Pydantic après correction...")
    
    from forestai.api import models
    
    all_repr_success = True
    all_json_success = True
    
    # Parcourir tous les attributs du module models
    for name in dir(models):
        item = getattr(models, name)
        
        # Vérifier si c'est un modèle Pydantic
        if isinstance(item, type) and issubclass(item, BaseModel) and item != BaseModel:
            logger.info(f"Test du modèle {name}...")
            
            # Tester la représentation
            repr_ok = test_model_repr(item, name)
            if not repr_ok:
                all_repr_success = False
            
            # Tester la sérialisation JSON
            json_ok = test_model_json(item, name)
            if not json_ok:
                all_json_success = False
    
    # Résumé des résultats
    if all_repr_success and all_json_success:
        logger.info("✅ Tous les modèles ont passé les tests avec succès !")
        return True
    else:
        if not all_repr_success:
            logger.error("❌ Certains modèles présentent encore des erreurs de représentation.")
        if not all_json_success:
            logger.error("❌ Certains modèles présentent encore des erreurs de sérialisation JSON.")
        return False

def test_nested_models():
    """
    Teste spécifiquement les modèles imbriqués qui sont plus susceptibles
    d'avoir des problèmes de récursion.
    """
    logger.info("Test des modèles imbriqués...")
    
    from forestai.api import models
    
    # Construction d'exemples imbriqués
    try:
        # Construire un modèle InventoryData avec des InventoryItem
        items = [models.InventoryItem(
            species="quercus_ilex", 
            diameter=25.5, 
            height=12.0, 
            health_status="bon"
        )]
        inventory_data = models.InventoryData(items=items, area=1.5)
        
        # Construire un DiagnosticRequest avec InventoryData
        diagnostic_request = models.DiagnosticRequest(
            parcel_id="13097000B0012",
            inventory_data=inventory_data
        )
        
        # Tester la représentation et la sérialisation
        repr(diagnostic_request)
        diagnostic_request.model_dump_json()
        
        # Construire un HealthAnalysisRequest avec InventoryData
        health_request = models.HealthAnalysisRequest(
            inventory_data=inventory_data,
            parcel_id="13097000B0012"
        )
        
        # Tester la représentation et la sérialisation
        repr(health_request)
        health_request.model_dump_json()
        
        # Construire un ApplicationRequest avec ProjectModel et ApplicantModel
        project = models.ProjectModel(
            type="reboisement",
            area_ha=5.2,
            species=["pinus_pinea", "quercus_suber"],
            region="Provence-Alpes-Côte d'Azur",
            location="13097000B0012",
            owner_type="private"
        )
        
        applicant = models.ApplicantModel(
            name="Domaine Forestier du Sud",
            address="Route des Pins 13200 Arles",
            contact="contact@domaineforestier.fr"
        )
        
        application = models.ApplicationRequest(
            project=project,
            subsidy_id="fr_reforest_2025",
            applicant=applicant
        )
        
        # Tester la représentation et la sérialisation
        repr(application)
        application.model_dump_json()
        
        logger.info("✅ Test des modèles imbriqués réussi !")
        return True
    except RecursionError as e:
        logger.error(f"❌ Erreur de récursion avec des modèles imbriqués: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur lors du test des modèles imbriqués: {str(e)}")
        return False

def main():
    """
    Fonction principale.
    """
    logger.info("Démarrage des tests de correctifs pour les modèles Pydantic...")
    
    # Tester les modèles connus comme problématiques
    if not test_fixed_models():
        logger.error("Les correctifs n'ont pas résolu tous les problèmes avec les modèles connus.")
        sys.exit(1)
    
    # Tester tous les modèles
    if not test_all_models():
        logger.error("Des problèmes subsistent avec certains modèles.")
        sys.exit(1)
        
    # Tester les modèles imbriqués
    if not test_nested_models():
        logger.error("Des problèmes subsistent avec les modèles imbriqués.")
        sys.exit(1)
    
    logger.info("✅ Tous les tests ont réussi ! Les correctifs ont résolu les problèmes de récursion.")
    sys.exit(0)

if __name__ == "__main__":
    main()
