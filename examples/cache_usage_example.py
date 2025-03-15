#!/usr/bin/env python3
"""
Exemple d'utilisation du système de cache avec les agents ForestAI.

Cet exemple montre comment utiliser les décorations de cache pour optimiser
les performances des agents en mettant en cache les données fréquemment utilisées.
"""

import time
import logging
from typing import Dict, Any, List

from forestai.agents.geo_agent import GeoAgent
from forestai.agents.reglementation_agent import ReglementationAgent
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy, CacheLevel
from forestai.core.infrastructure.cache.cache_utils import (
    cached, CachedProperty, preload_cache, get_cache_stats, 
    invalidate_cache, clear_cache_type
)

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger("cache_example")

# Chargement de la configuration
from forestai.core.utils.config import Config
config = Config.get_instance()
config.load_config(".env")


def performance_test(func, *args, **kwargs):
    """
    Mesure les performances d'exécution d'une fonction.
    
    Args:
        func: Fonction à exécuter
        *args: Arguments de la fonction
        **kwargs: Arguments nommés de la fonction
        
    Returns:
        Résultat de la fonction et temps d'exécution
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    return result, execution_time


class CachedGeoAgent(GeoAgent):
    """Version optimisée de GeoAgent avec utilisation du cache."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'agent géographique avec cache.
        
        Args:
            config: Configuration de l'agent
        """
        super().__init__(config)
        
        # Précharger les données communes
        self._preload_common_data()
    
    @cached(
        data_type=CacheType.GEODATA,
        identifier_key="parcel_id",
        policy=CachePolicy.WEEKLY,
        key_prefix="analyze_parcel"
    )
    def analyze_parcel(self, parcel_id: str, analyses: List[str] = None) -> Dict[str, Any]:
        """
        Analyse une parcelle avec mise en cache des résultats.
        
        Args:
            parcel_id: Identifiant de la parcelle
            analyses: Types d'analyses à effectuer
            
        Returns:
            Résultats de l'analyse
        """
        logger.info(f"Exécution de l'analyse de parcelle: {parcel_id}")
        # Simuler un temps de traitement
        time.sleep(1)
        return super().analyze_parcel(parcel_id, analyses)
    
    @CachedProperty(CacheType.GEODATA, CachePolicy.DAILY)
    def supported_analyses(self):
        """Liste des analyses supportées par l'agent."""
        logger.info("Récupération des analyses supportées")
        # Simuler un temps de traitement
        time.sleep(0.5)
        return [
            "basic", "terrain", "forest_potential", 
            "climate", "risks", "complete"
        ]
    
    def _preload_common_data(self):
        """Précharge les données communes pour améliorer les performances."""
        try:
            # Précharger les communes fréquemment recherchées
            def load_common_communes():
                logger.info("Préchargement des communes communes")
                # Simuler le chargement de données
                time.sleep(0.5)
                return {
                    "13001": {"name": "Marseille", "population": 870731},
                    "13097": {"name": "Saint-Martin-de-Crau", "population": 12795},
                    "13054": {"name": "Lambesc", "population": 10013},
                    # Autres communes...
                }
            
            count = preload_cache(
                data_type=CacheType.GEODATA,
                data_loader=load_common_communes,
                policy=CachePolicy.MONTHLY
            )
            
            logger.info(f"Préchargé {count} communes fréquemment utilisées")
        except Exception as e:
            logger.error(f"Erreur lors du préchargement des données: {e}")


class CachedReglementationAgent(ReglementationAgent):
    """Version optimisée de ReglementationAgent avec utilisation du cache."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'agent de réglementation avec cache.
        
        Args:
            config: Configuration de l'agent
        """
        super().__init__(config)
    
    @cached(
        data_type=CacheType.REGULATION,
        identifier_key="project_type",
        policy=CachePolicy.MONTHLY,
        key_prefix="get_regulations"
    )
    def get_regulations(self, project_type: str) -> Dict[str, Any]:
        """
        Récupère les réglementations pour un type de projet.
        
        Args:
            project_type: Type de projet (boisement, reboisement, etc.)
            
        Returns:
            Réglementations applicables
        """
        logger.info(f"Récupération des réglementations pour: {project_type}")
        # Simuler un temps de traitement
        time.sleep(1.5)
        return super().get_regulations(project_type)
    
    @cached(
        data_type=CacheType.REGULATION,
        policy=CachePolicy.MONTHLY,
        key_prefix="check_compliance"
    )
    def check_compliance(self, parcels: List[str], project_type: str) -> Dict[str, Any]:
        """
        Vérifie la conformité d'un projet sur des parcelles.
        
        Args:
            parcels: Liste d'identifiants de parcelles
            project_type: Type de projet
            
        Returns:
            Résultat de la vérification de conformité
        """
        logger.info(f"Vérification de conformité pour {len(parcels)} parcelles")
        # Simuler un temps de traitement
        time.sleep(2)
        return super().check_compliance(parcels, project_type)


def main():
    """Fonction principale de démonstration."""
    logger.info("Démarrage de la démonstration du cache")
    
    # Charger la configuration
    config_dict = config.as_dict()
    
    # Instancier les agents avec cache
    geo_agent = CachedGeoAgent(config_dict)
    reg_agent = CachedReglementationAgent(config_dict)
    
    # Démonstration GeoAgent
    logger.info("\n--- Démonstration GeoAgent ---")
    
    # Premier appel (sans cache)
    logger.info("Premier appel à analyze_parcel:")
    result1, time1 = performance_test(
        geo_agent.analyze_parcel,
        "13097000B0012",
        ["terrain", "forest_potential"]
    )
    logger.info(f"Durée: {time1:.2f} secondes")
    
    # Deuxième appel (avec cache)
    logger.info("Deuxième appel à analyze_parcel (même parcelle):")
    result2, time2 = performance_test(
        geo_agent.analyze_parcel,
        "13097000B0012",
        ["terrain", "forest_potential"]
    )
    logger.info(f"Durée: {time2:.2f} secondes")
    logger.info(f"Accélération: {time1/time2:.1f}x")
    
    # Propriété mise en cache
    logger.info("\nPremier accès à la propriété supported_analyses:")
    _ = geo_agent.supported_analyses
    
    logger.info("Deuxième accès à la propriété supported_analyses:")
    analyses = geo_agent.supported_analyses
    logger.info(f"Analyses supportées: {analyses}")
    
    # Démonstration ReglementationAgent
    logger.info("\n--- Démonstration ReglementationAgent ---")
    
    # Premier appel (sans cache)
    logger.info("Premier appel à get_regulations:")
    result1, time1 = performance_test(
        reg_agent.get_regulations,
        "boisement"
    )
    logger.info(f"Durée: {time1:.2f} secondes")
    
    # Deuxième appel (avec cache)
    logger.info("Deuxième appel à get_regulations (même type de projet):")
    result2, time2 = performance_test(
        reg_agent.get_regulations,
        "boisement"
    )
    logger.info(f"Durée: {time2:.2f} secondes")
    logger.info(f"Accélération: {time1/time2:.1f}x")
    
    # Vérification de conformité
    logger.info("\nPremier appel à check_compliance:")
    result1, time1 = performance_test(
        reg_agent.check_compliance,
        ["13097000B0012", "13097000B0013"],
        "boisement"
    )
    logger.info(f"Durée: {time1:.2f} secondes")
    
    logger.info("Deuxième appel à check_compliance (mêmes parcelles):")
    result2, time2 = performance_test(
        reg_agent.check_compliance,
        ["13097000B0012", "13097000B0013"],
        "boisement"
    )
    logger.info(f"Durée: {time2:.2f} secondes")
    logger.info(f"Accélération: {time1/time2:.1f}x")
    
    # Invalidation manuelle du cache
    logger.info("\n--- Invalidation du cache ---")
    invalidate_cache(
        data_type=CacheType.GEODATA,
        identifier="analyze_parcel:13097000B0012"
    )
    logger.info("Cache invalidé pour la parcelle 13097000B0012")
    
    # Appel après invalidation
    logger.info("Appel après invalidation:")
    result3, time3 = performance_test(
        geo_agent.analyze_parcel,
        "13097000B0012",
        ["terrain", "forest_potential"]
    )
    logger.info(f"Durée: {time3:.2f} secondes")
    
    # Afficher les statistiques du cache
    logger.info("\n--- Statistiques du cache ---")
    stats = get_cache_stats()
    logger.info(f"Ratio de hits: {stats['hit_ratio']:.2f} ({stats['hits']} hits / {stats['misses']} misses)")
    logger.info(f"Hits en mémoire: {stats['memory_hits']}")
    logger.info(f"Hits sur disque: {stats['disk_hits']}")
    logger.info(f"Entrées sauvegardées: {stats['cache_saves']}")
    
    logger.info("\nDémonstration terminée")


if __name__ == "__main__":
    main()
