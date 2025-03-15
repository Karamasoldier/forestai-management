# -*- coding: utf-8 -*-
"""
Module d'analyse sanitaire forestière optimisé.

Ce module intègre le HealthAnalyzer standard avec les optimisations de performances
pour fournir une analyse sanitaire forestière performante et efficace, particulièrement
pour les grands volumes de données.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from forestai.agents.diagnostic_agent.health.health_analyzer import HealthAnalyzer
from forestai.agents.diagnostic_agent.health.performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)

class OptimizedHealthAnalyzer(HealthAnalyzer):
    """
    Version optimisée de l'analyseur sanitaire forestier qui utilise
    la parallélisation et le traitement par lots pour améliorer les performances.
    
    Cette classe hérite du HealthAnalyzer standard mais remplace certaines méthodes
    par des versions optimisées pour de meilleures performances avec de grands jeux de données.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise l'analyseur sanitaire optimisé.
        
        Args:
            config: Configuration contenant les options standard du HealthAnalyzer
                   ainsi que des options d'optimisation:
                   - optimization: Configuration spécifique à l'optimisation
                     - parallel_enabled: Activer la parallélisation (défaut: True)
                     - max_processes: Nombre maximum de processus (défaut: basé sur CPU)
                     - batch_size: Taille de lot pour l'analyse par lot (défaut: 50)
                     - auto_select: Sélection automatique du mode d'analyse (défaut: True)
                     - tree_threshold: Seuil d'arbres pour l'optimisation (défaut: 100)
        """
        # Initialisation du HealthAnalyzer standard
        super().__init__(config)
        
        # Options d'optimisation
        opt_config = self.config.get("optimization", {})
        self.optimizer = PerformanceOptimizer(opt_config)
        
        # Configuration pour la sélection automatique d'analyse standard ou optimisée
        self.auto_select = opt_config.get("auto_select", True)
        self.tree_threshold = opt_config.get("tree_threshold", 100)
        
        logger.info(f"OptimizedHealthAnalyzer initialisé (auto_select={self.auto_select}, tree_threshold={self.tree_threshold})")
    
    def analyze_health(self, inventory_data: Dict[str, Any], 
                      additional_symptoms: Optional[Dict[str, Any]] = None,
                      climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyse l'état sanitaire d'une forêt, en choisissant automatiquement
        entre l'analyse standard et l'analyse optimisée selon la taille des données.
        
        Args:
            inventory_data: Données d'inventaire forestier
            additional_symptoms: Observations supplémentaires de symptômes
            climate_data: Données climatiques pour l'analyse de risques
            
        Returns:
            Analyse sanitaire complète
        """
        # Déterminer le nombre d'arbres
        tree_count = 0
        if "items" in inventory_data:
            tree_count = len(inventory_data["items"])
        elif isinstance(inventory_data, list):
            tree_count = len(inventory_data)
        
        start_time = time.time()
        
        # Sélection automatique du mode d'analyse
        if self.auto_select and tree_count >= self.tree_threshold:
            logger.info(f"Utilisation de l'analyse optimisée pour {tree_count} arbres")
            result = self.optimizer.optimized_health_analysis(
                inventory_data, additional_symptoms, climate_data
            )
            
            # Adapter le format du résultat optimisé pour qu'il soit compatible avec le format standard
            # si nécessaire
            result = self._adapt_optimized_result(result)
        else:
            logger.info(f"Utilisation de l'analyse standard pour {tree_count} arbres")
            result = super().analyze_health(inventory_data, additional_symptoms, climate_data)
        
        # Ajouter des métadonnées d'optimisation
        if "metadata" not in result:
            result["metadata"] = {}
        
        result["metadata"]["optimized_analyzer"] = {
            "used_optimizer": tree_count >= self.tree_threshold and self.auto_select,
            "execution_time": time.time() - start_time,
            "tree_count": tree_count
        }
        
        return result
    
    def _adapt_optimized_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapte le résultat de l'analyse optimisée pour qu'il soit compatible
        avec le format de l'analyse standard.
        
        Args:
            result: Résultat de l'analyse optimisée
            
        Returns:
            Résultat adapté au format standard
        """
        # Cette méthode est nécessaire pour assurer que les résultats optimisés
        # ont la même structure que les résultats standard, pour garantir la
        # compatibilité avec le reste du système
        
        # Pour la plupart des cas, le résultat optimisé devrait déjà être compatible
        # mais cette méthode peut être étendue si nécessaire pour des adaptations spécifiques
        
        # Vérifier si des champs requis sont manquants
        required_fields = [
            "summary", "overall_health_score", "health_status", 
            "detected_issues", "species_health", "health_indicators", 
            "recommendations"
        ]
        
        for field in required_fields:
            if field not in result and field not in result.get("summary", {}):
                if field == "recommendations" and "summary" in result:
                    # Générer des recommandations de base si manquantes
                    result["recommendations"] = {
                        "summary": f"Recommandations basées sur un score de santé de {result.get('overall_health_score', 0)}/10",
                        "priority_actions": []
                    }
                elif field == "species_health" and "species_details" in result:
                    # Adapter le format des détails par espèce
                    result["species_health"] = {}
                    for species, details in result.get("species_details", {}).items():
                        result["species_health"][species] = {
                            "health_score": details.get("health_score", 0),
                            "main_issues": [issue.get("id") for issue in details.get("detected_issues", [])]
                        }
        
        return result
    
    def force_optimized_analysis(self, inventory_data: Dict[str, Any],
                               additional_symptoms: Optional[Dict[str, Any]] = None,
                               climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Force l'utilisation de l'analyse optimisée, quel que soit le nombre d'arbres.
        
        Cette méthode est utile pour les tests ou lorsque l'utilisateur sait
        que l'analyse optimisée sera plus performante.
        
        Args:
            inventory_data: Données d'inventaire forestier
            additional_symptoms: Observations supplémentaires de symptômes
            climate_data: Données climatiques pour l'analyse de risques
            
        Returns:
            Analyse sanitaire complète avec optimisation forcée
        """
        logger.info("Utilisation forcée de l'analyse optimisée")
        
        result = self.optimizer.optimized_health_analysis(
            inventory_data, additional_symptoms, climate_data
        )
        
        # Adapter le format du résultat optimisé
        result = self._adapt_optimized_result(result)
        
        # Ajouter des métadonnées d'optimisation
        if "metadata" not in result:
            result["metadata"] = {}
        
        result["metadata"]["optimized_analyzer"] = {
            "used_optimizer": True,
            "forced": True
        }
        
        return result
    
    def force_standard_analysis(self, inventory_data: Dict[str, Any],
                              additional_symptoms: Optional[Dict[str, Any]] = None,
                              climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Force l'utilisation de l'analyse standard, quel que soit le nombre d'arbres.
        
        Cette méthode est utile lorsque l'analyse optimisée cause des problèmes
        ou lorsque l'utilisateur préfère les résultats exacts de l'analyse standard.
        
        Args:
            inventory_data: Données d'inventaire forestier
            additional_symptoms: Observations supplémentaires de symptômes
            climate_data: Données climatiques pour l'analyse de risques
            
        Returns:
            Analyse sanitaire complète avec analyse standard forcée
        """
        logger.info("Utilisation forcée de l'analyse standard")
        
        result = super().analyze_health(inventory_data, additional_symptoms, climate_data)
        
        # Ajouter des métadonnées d'optimisation
        if "metadata" not in result:
            result["metadata"] = {}
        
        result["metadata"]["optimized_analyzer"] = {
            "used_optimizer": False,
            "forced": True
        }
        
        return result
