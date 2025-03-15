# -*- coding: utf-8 -*-
"""
Module d'optimisation des performances pour l'analyse sanitaire forestière.

Ce module permet d'améliorer les performances des analyses sanitaires en:
1. Utilisant un système de mise en cache intelligente pour les données fréquemment utilisées
2. Parallélisant certains traitements d'analyse coûteux
3. Utilisant des algorithmes optimisés pour les grands volumes de données
4. Permettant des analyses par lot pour les grands inventaires forestiers
"""

import logging
import time
import os
from functools import wraps
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing

from forestai.core.infrastructure.cache.cache_utils import cached
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy

logger = logging.getLogger(__name__)

# Nombre maximal de processus à utiliser pour la parallélisation
MAX_PROCESSES = min(os.cpu_count() or 4, 8)  # Limiter à 8 processus maximum

# Seuil pour basculer vers une analyse par lot
BATCH_THRESHOLD = 100  # Nombre d'arbres au-delà duquel l'analyse se fait par lot


def timing_decorator(func):
    """Décorateur pour mesurer le temps d'exécution d'une fonction."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Fonction {func.__name__} exécutée en {execution_time:.4f} secondes")
        return result
    return wrapper


class PerformanceOptimizer:
    """
    Optimiseur de performances pour l'analyse sanitaire forestière.
    
    Cette classe fournit des méthodes pour accélérer les analyses sanitaires
    en utilisant des techniques d'optimisation et de parallélisation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise l'optimiseur de performances.
        
        Args:
            config: Configuration optionnelle contenant:
                - parallel_enabled: Activer la parallélisation (défaut: True)
                - max_processes: Nombre maximum de processus (défaut: basé sur CPU)
                - batch_size: Taille de lot pour l'analyse par lot (défaut: 50)
        """
        self.config = config or {}
        self.parallel_enabled = self.config.get("parallel_enabled", True)
        self.max_processes = self.config.get("max_processes", MAX_PROCESSES)
        self.batch_size = self.config.get("batch_size", 50)
        
        logger.info(f"PerformanceOptimizer initialisé (parallel={self.parallel_enabled}, "
                   f"max_processes={self.max_processes}, batch_size={self.batch_size})")
    
    @timing_decorator
    def parallel_map(self, func: Callable, items: List[Any], use_threads: bool = False) -> List[Any]:
        """
        Exécute une fonction en parallèle sur une liste d'éléments.
        
        Args:
            func: Fonction à exécuter sur chaque élément
            items: Liste d'éléments à traiter
            use_threads: Utiliser des threads au lieu de processus
            
        Returns:
            Liste des résultats dans le même ordre que les éléments d'entrée
        """
        if not self.parallel_enabled or len(items) <= 1:
            return [func(item) for item in items]
        
        # Limiter le nombre de workers au nombre d'éléments
        workers = min(self.max_processes, len(items))
        
        # Choisir le type d'exécuteur (processus ou threads)
        executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
        
        results = []
        with executor_class(max_workers=workers) as executor:
            # Soumettre les tâches
            future_to_index = {executor.submit(func, item): i for i, item in enumerate(items)}
            
            # Collecter les résultats
            results = [None] * len(items)
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Erreur lors du traitement parallèle: {str(e)}")
                    results[index] = None
        
        return results
    
    @timing_decorator
    def process_in_batches(self, func: Callable, items: List[Any], batch_size: Optional[int] = None) -> List[Any]:
        """
        Traite une liste d'éléments par lots.
        
        Args:
            func: Fonction à exécuter sur chaque lot
            items: Liste d'éléments à traiter
            batch_size: Taille des lots (par défaut: self.batch_size)
            
        Returns:
            Liste agrégée des résultats de tous les lots
        """
        if not items:
            return []
        
        if batch_size is None:
            batch_size = self.batch_size
        
        if len(items) <= batch_size:
            return func(items)
        
        # Diviser les éléments en lots
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        logger.debug(f"Traitement en {len(batches)} lots de taille {batch_size}")
        
        # Traiter chaque lot (potentiellement en parallèle)
        if self.parallel_enabled and len(batches) > 1:
            batch_results = self.parallel_map(func, batches)
        else:
            batch_results = [func(batch) for batch in batches]
        
        # Agréger les résultats
        if all(isinstance(result, list) for result in batch_results):
            # Si chaque résultat est une liste, concaténer
            return [item for batch in batch_results for item in batch]
        else:
            # Sinon retourner les résultats des lots directement
            return batch_results
    
    @timing_decorator
    def adaptive_analysis(self, analyze_func: Callable, trees: List[Dict[str, Any]], 
                         params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue une analyse sanitaire adaptative selon la taille des données.
        
        Pour les petits jeux de données, effectue une analyse directe.
        Pour les grands jeux de données, utilise la parallélisation et le traitement par lots.
        
        Args:
            analyze_func: Fonction d'analyse à exécuter
            trees: Liste des arbres à analyser
            params: Paramètres supplémentaires pour l'analyse
            
        Returns:
            Résultats de l'analyse
        """
        num_trees = len(trees)
        
        if num_trees <= BATCH_THRESHOLD:
            # Pour les petits inventaires, analyse directe
            logger.debug(f"Analyse directe de {num_trees} arbres")
            return analyze_func(trees, **params)
        
        # Pour les grands inventaires, utiliser le traitement par lots et la parallélisation
        logger.info(f"Analyse adaptative pour {num_trees} arbres")
        
        # 1. Grouper les arbres par espèce pour optimiser l'analyse
        species_groups = {}
        for tree in trees:
            species = tree.get("species", "unknown")
            if species not in species_groups:
                species_groups[species] = []
            species_groups[species].append(tree)
        
        # 2. Analyser chaque groupe d'espèces (potentiellement en parallèle)
        def analyze_species_group(group_data):
            species, species_trees = group_data
            logger.debug(f"Analyse de {len(species_trees)} arbres de l'espèce {species}")
            return species, analyze_func(species_trees, **params)
        
        species_results = self.parallel_map(
            analyze_species_group, 
            list(species_groups.items())
        )
        
        # 3. Agréger les résultats
        all_results = {}
        for species, result in species_results:
            all_results[species] = result
        
        return self._merge_species_results(all_results)
    
    def _merge_species_results(self, species_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusionne les résultats d'analyse par espèce en un résultat global.
        
        Args:
            species_results: Dictionnaire des résultats par espèce
            
        Returns:
            Résultat global fusionné
        """
        # Cette méthode doit être adaptée selon la structure exacte des résultats
        # Voici un exemple générique de fusion:
        merged_result = {
            "species_details": species_results,
            "summary": {},
            "aggregated_data": {}
        }
        
        # Calculer des statistiques globales
        all_health_scores = []
        all_detected_issues = []
        all_health_indicators = {}
        health_status_counts = {
            "bon": 0,
            "moyen": 0,
            "mauvais": 0
        }
        
        for species, result in species_results.items():
            if "health_score" in result:
                all_health_scores.append(result["health_score"])
            
            if "detected_issues" in result:
                all_detected_issues.extend(result["detected_issues"])
            
            if "health_status" in result:
                status = result["health_status"].lower()
                if status in health_status_counts:
                    health_status_counts[status] += 1
            
            if "health_indicators" in result:
                for indicator, value in result["health_indicators"].items():
                    if indicator not in all_health_indicators:
                        all_health_indicators[indicator] = []
                    all_health_indicators[indicator].append(value)
        
        # Calculer les moyennes des indicateurs
        for indicator, values in all_health_indicators.items():
            if values:
                merged_result["aggregated_data"][indicator] = sum(values) / len(values)
        
        # Déterminer le statut sanitaire global
        if health_status_counts:
            max_status = max(health_status_counts, key=health_status_counts.get)
            merged_result["summary"]["health_status"] = max_status.capitalize()
        
        # Calculer le score de santé global
        if all_health_scores:
            merged_result["summary"]["overall_health_score"] = sum(all_health_scores) / len(all_health_scores)
        
        # Consolidation des problèmes détectés
        if all_detected_issues:
            # Regrouper par type de problème
            issue_types = {}
            for issue in all_detected_issues:
                issue_id = issue.get("id", "unknown")
                if issue_id not in issue_types:
                    issue_types[issue_id] = []
                issue_types[issue_id].append(issue)
            
            # Agréger les problèmes similaires
            merged_issues = []
            for issue_id, issues in issue_types.items():
                if len(issues) == 1:
                    merged_issues.append(issues[0])
                else:
                    # Fusionner des problèmes similaires
                    severities = [issue.get("severity", 0) for issue in issues]
                    avg_severity = sum(severities) / len(severities)
                    
                    merged_issue = issues[0].copy()
                    merged_issue["severity"] = avg_severity
                    merged_issue["affected_species"] = list(set(
                        species for issue in issues 
                        for species in issue.get("affected_species", [])
                    ))
                    merged_issues.append(merged_issue)
            
            merged_result["summary"]["detected_issues"] = merged_issues
        
        return merged_result

    @cached(data_type=CacheType.DIAGNOSTIC, policy=CachePolicy.DAILY)
    def optimized_health_analysis(self, inventory_data: Dict[str, Any], additional_symptoms: Optional[Dict[str, Any]] = None, 
                                climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Version optimisée de l'analyse sanitaire, avec mise en cache et parallélisation.
        
        Cette méthode est conçue pour être utilisée comme remplacement de la méthode
        analyze_health du HealthAnalyzer pour les grands volumes de données.
        
        Args:
            inventory_data: Données d'inventaire forestier
            additional_symptoms: Observations supplémentaires de symptômes
            climate_data: Données climatiques pour l'analyse de risques
            
        Returns:
            Analyse sanitaire complète
        """
        start_time = time.time()
        logger.info("Début de l'analyse sanitaire optimisée")
        
        # Extraction des données d'inventaire
        trees = []
        if "items" in inventory_data:
            trees = inventory_data["items"]
        elif isinstance(inventory_data, list):
            trees = inventory_data
        
        if not trees:
            logger.warning("Aucun arbre à analyser dans l'inventaire")
            return {
                "summary": "Aucune donnée d'inventaire valide pour l'analyse",
                "overall_health_score": 0,
                "health_status": "Indéterminé",
                "detected_issues": [],
                "metadata": {
                    "analysis_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "analysis_duration_seconds": time.time() - start_time,
                    "analyzer_version": "1.0.0-optimized"
                }
            }
        
        # Configuration de l'analyse
        params = {
            "additional_symptoms": additional_symptoms or {},
            "climate_data": climate_data or {}
        }
        
        # Fonction d'analyse qui sera appelée par l'optimiseur
        # Cette fonction doit être adaptée pour être compatible avec l'analyse par espèce
        def analyze_tree_group(tree_group):
            # Insérer ici la logique d'analyse spécifique
            # Ceci est un exemple simplifié
            return {
                "health_score": self._calculate_health_score(tree_group, params),
                "detected_issues": self._detect_issues(tree_group, params),
                "health_status": self._determine_health_status(tree_group, params),
                "health_indicators": self._calculate_indicators(tree_group, params)
            }
        
        # Effectuer l'analyse adaptative
        analysis_result = self.adaptive_analysis(analyze_tree_group, trees, params)
        
        # Compléter le résultat
        analysis_result["metadata"] = {
            "analysis_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "analysis_duration_seconds": time.time() - start_time,
            "analyzer_version": "1.0.0-optimized",
            "optimization": {
                "parallel_enabled": self.parallel_enabled,
                "batch_processing": len(trees) > BATCH_THRESHOLD,
                "trees_analyzed": len(trees)
            }
        }
        
        logger.info(f"Analyse sanitaire optimisée terminée en {time.time() - start_time:.2f} secondes")
        return analysis_result
    
    # Méthodes d'analyse simulées pour l'exemple
    # Dans une implémentation réelle, ces méthodes devraient être remplacées par des versions 
    # qui correspondent aux algorithmes spécifiques du HealthAnalyzer
    
    def _calculate_health_score(self, trees, params):
        """Calcule un score de santé pour un groupe d'arbres (méthode simulée)."""
        scores = []
        for tree in trees:
            # Score de base selon le statut sanitaire
            base_score = {"bon": 8.5, "moyen": 6.0, "mauvais": 3.0}.get(
                tree.get("health_status", "").lower(), 5.0)
            scores.append(base_score)
        
        return sum(scores) / len(scores) if scores else 5.0
    
    def _detect_issues(self, trees, params):
        """Détecte les problèmes sanitaires dans un groupe d'arbres (méthode simulée)."""
        issues = []
        
        # Exemple de détection basée sur les statuts sanitaires
        health_statuses = [tree.get("health_status", "").lower() for tree in trees]
        species = list(set(tree.get("species", "unknown") for tree in trees))
        
        # Problèmes basés sur les symptômes fournis
        additional_symptoms = params.get("additional_symptoms", {})
        
        if "leaf_discoloration" in additional_symptoms:
            issues.append({
                "id": "leaf_discoloration",
                "name": "Décoloration foliaire",
                "severity": additional_symptoms["leaf_discoloration"],
                "affected_species": species
            })
        
        if "crown_thinning" in additional_symptoms:
            issues.append({
                "id": "crown_thinning",
                "name": "Éclaircissement du houppier",
                "severity": additional_symptoms["crown_thinning"],
                "affected_species": species
            })
        
        # Problèmes basés sur les statuts sanitaires des arbres
        bad_health_ratio = health_statuses.count("mauvais") / len(health_statuses) if health_statuses else 0
        if bad_health_ratio >= 0.2:
            issues.append({
                "id": "general_decline",
                "name": "Dépérissement général",
                "severity": bad_health_ratio,
                "affected_species": species
            })
        
        return issues
    
    def _determine_health_status(self, trees, params):
        """Détermine le statut sanitaire global pour un groupe d'arbres (méthode simulée)."""
        health_statuses = [tree.get("health_status", "").lower() for tree in trees]
        status_counts = {
            status: health_statuses.count(status) 
            for status in ["bon", "moyen", "mauvais"] 
            if status in health_statuses
        }
        
        if not status_counts:
            return "Indéterminé"
        
        max_status = max(status_counts, key=status_counts.get)
        return max_status.capitalize()
    
    def _calculate_indicators(self, trees, params):
        """Calcule les indicateurs sanitaires pour un groupe d'arbres (méthode simulée)."""
        # Cet exemple simple utilise les données fournies dans additional_symptoms
        additional_symptoms = params.get("additional_symptoms", {})
        
        indicators = {
            "leaf_loss": additional_symptoms.get("leaf_loss", 0),
            "crown_transparency": additional_symptoms.get("crown_thinning", 0),
            "bark_damage": additional_symptoms.get("bark_damage", 0)
        }
        
        return indicators
