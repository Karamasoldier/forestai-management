"""
Module de correctifs centralisé pour ForestAI.

Ce module contient tous les correctifs appliqués au système pour résoudre divers problèmes,
notamment les erreurs de récursion dans les modèles Pydantic et autres problèmes d'infrastructure.

Usage typique:
    ```python
    from forestai.core.patches import apply_all_patches
    
    # Appliquer tous les correctifs nécessaires au démarrage
    apply_all_patches()
    
    # Ou appliquer un correctif spécifique
    from forestai.core.patches import apply_pydantic_patches
    apply_pydantic_patches()
    ```
"""

import logging
import importlib
import sys
from typing import List, Dict, Optional, Any, Union

logger = logging.getLogger("forestai.patches")

# Vérification de la version de Pydantic
def get_pydantic_version() -> str:
    """
    Détermine la version de Pydantic installée.
    
    Returns:
        str: Version de Pydantic (ex: "1.10.8" ou "2.0.3")
    """
    try:
        import pkg_resources
        return pkg_resources.get_distribution("pydantic").version
    except (ImportError, pkg_resources.DistributionNotFound):
        try:
            import pydantic
            return pydantic.__version__
        except (ImportError, AttributeError):
            return "unknown"

# Fonction pour appliquer tous les correctifs
def apply_all_patches(verbose: bool = True) -> Dict[str, bool]:
    """
    Applique tous les correctifs disponibles.
    
    Args:
        verbose (bool): Si True, affiche des informations détaillées sur les correctifs appliqués.
    
    Returns:
        Dict[str, bool]: Dictionnaire des correctifs appliqués et leur statut (succès ou échec)
    """
    if verbose:
        logger.setLevel(logging.INFO)
    
    pydantic_version = get_pydantic_version()
    results = {}
    
    # Appliquer les correctifs Pydantic
    pydantic_success = apply_pydantic_patches(pydantic_version=pydantic_version)
    results["pydantic"] = pydantic_success
    
    # Peut être étendu avec d'autres correctifs au besoin
    
    if verbose:
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Correctifs appliqués avec succès: {success_count}/{len(results)}")
    
    return results

# Importation et application des correctifs Pydantic
def apply_pydantic_patches(pydantic_version: Optional[str] = None) -> bool:
    """
    Applique les correctifs spécifiques à Pydantic pour résoudre les problèmes de récursion.
    
    Args:
        pydantic_version (Optional[str]): Version de Pydantic. Si None, sera détectée automatiquement.
    
    Returns:
        bool: True si les correctifs ont été appliqués avec succès, False sinon.
    """
    if pydantic_version is None:
        pydantic_version = get_pydantic_version()
    
    logger.info(f"Application des correctifs pour Pydantic version {pydantic_version}")
    
    try:
        # Importer le module de correctifs approprié selon la version
        if pydantic_version.startswith("1."):
            from .pydantic_v1_fixes import patch_pydantic_models
        else:
            from .pydantic_v2_fixes import patch_pydantic_models
        
        # Appliquer les correctifs
        patch_pydantic_models()
        logger.info("Correctifs Pydantic appliqués avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'application des correctifs Pydantic: {e}")
        return False

__all__ = [
    "apply_all_patches",
    "apply_pydantic_patches",
    "get_pydantic_version"
]
