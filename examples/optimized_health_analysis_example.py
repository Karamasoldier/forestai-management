#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation de l'analyseur sanitaire forestier optimisé.

Ce script démontre comment utiliser l'analyseur sanitaire optimisé
pour des analyses de santé forestière performantes sur des grands jeux
de données d'inventaire.

Usage:
    python optimized_health_analysis_example.py

Requirements:
    - forestai
    - matplotlib
    - pandas
"""

import time
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any
import random
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import des modules ForestAI
from forestai.agents.diagnostic_agent.health.health_analyzer import HealthAnalyzer
from forestai.agents.diagnostic_agent.health.optimized_analyzer import OptimizedHealthAnalyzer

# Dossier pour sauvegarder les résultats
OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_synthetic_inventory(num_trees: int = 1000, species_list: List[str] = None) -> Dict[str, Any]:
    """
    Génère un inventaire forestier synthétique pour les tests.
    
    Args:
        num_trees: Nombre d'arbres à générer
        species_list: Liste des espèces à utiliser
        
    Returns:
        Inventaire forestier au format attendu par l'analyseur sanitaire
    """
    if species_list is None:
        species_list = [
            "quercus_ilex", "quercus_pubescens", "pinus_halepensis", 
            "pinus_pinea", "cedrus_atlantica", "abies_alba"
        ]
    
    # Probabilités de statut sanitaire (biaisées pour être réalistes)
    health_status_probs = {
        "bon": 0.6,
        "moyen": 0.3,
        "mauvais": 0.1
    }
    
    # Générer les arbres
    trees = []
    for i in range(num_trees):
        # Sélectionner une espèce au hasard
        species = random.choice(species_list)
        
        # Déterminer le statut sanitaire selon les probabilités
        health_status = random.choices(
            list(health_status_probs.keys()),
            weights=list(health_status_probs.values())
        )[0]
        
        # Générer des diamètres et hauteurs réalistes selon l'espèce
        diameter_base = {
            "quercus_ilex": 30, "quercus_pubescens": 35,
            "pinus_halepensis": 28, "pinus_pinea": 45,
            "cedrus_atlantica": 50, "abies_alba": 40
        }.get(species, 30)
        
        height_base = {
            "quercus_ilex": 12, "quercus_pubescens": 15,
            "pinus_halepensis": 18, "pinus_pinea": 20,
            "cedrus_atlantica": 25, "abies_alba": 30
        }.get(species, 15)
        
        # Ajouter une variation aléatoire
        diameter = diameter_base + random.uniform(-10, 10)
        height = height_base + random.uniform(-5, 5)
        
        # Créer l'arbre
        tree = {
            "species": species,
            "diameter": diameter,
            "height": height,
            "health_status": health_status
        }
        
        # Ajouter des notes pour certains arbres
        if random.random() < 0.2:
            notes = random.choice([
                "Présence de taches foliaires",
                "Écorce endommagée",
                "Branches mortes",
                "Champignons au pied",
                "Attaque d'insectes visible"
            ])
            tree["notes"] = notes
        
        trees.append(tree)
    
    # Créer l'inventaire complet
    inventory = {
        "items": trees,
        "area": num_trees / 200,  # Approximation d'une densité moyenne
        "date": "2025-03-15",
        "method": "placettes"
    }
    
    return inventory


def compare_analyzers(tree_counts: List[int]):
    """
    Compare les performances entre l'analyseur standard et l'analyseur optimisé.
    
    Args:
        tree_counts: Liste des nombres d'arbres à tester
    """
    # Initialiser les analyseurs
    standard_analyzer = HealthAnalyzer()
    optimized_analyzer = OptimizedHealthAnalyzer()
    
    # Définir les symptômes additionnels
    additional_symptoms = {
        "leaf_discoloration": 0.35,
        "observed_pests": ["bark_beetle"],
        "crown_thinning": 0.25
    }
    
    # Stocker les résultats
    results = {
        "tree_counts": tree_counts,
        "standard_times": [],
        "optimized_times": [],
        "optimized_forced_times": [],
        "standard_health_scores": [],
        "optimized_health_scores": []
    }
    
    # Exécuter les tests pour chaque nombre d'arbres
    for num_trees in tree_counts:
        print(f"\nTest avec {num_trees} arbres:")
        
        # Générer un inventaire synthétique
        inventory = generate_synthetic_inventory(num_trees)
        
        # 1. Tester l'analyseur standard
        start_time = time.time()
        standard_result = standard_analyzer.analyze_health(inventory, additional_symptoms)
        standard_time = time.time() - start_time
        standard_score = standard_result.get("overall_health_score", 0)
        
        print(f"  Analyseur standard: {standard_time:.2f} secondes, score: {standard_score:.2f}/10")
        results["standard_times"].append(standard_time)
        results["standard_health_scores"].append(standard_score)
        
        # 2. Tester l'analyseur optimisé avec sélection automatique
        start_time = time.time()
        optimized_result = optimized_analyzer.analyze_health(inventory, additional_symptoms)
        optimized_time = time.time() - start_time
        optimized_score = optimized_result.get("overall_health_score", 0)
        
        used_optimizer = optimized_result.get("metadata", {}).get("optimized_analyzer", {}).get("used_optimizer", False)
        print(f"  Analyseur optimisé: {optimized_time:.2f} secondes, score: {optimized_score:.2f}/10 (optimisation {'activée' if used_optimizer else 'désactivée'})")
        results["optimized_times"].append(optimized_time)
        results["optimized_health_scores"].append(optimized_score)
        
        # 3. Tester l'analyseur optimisé avec optimisation forcée
        start_time = time.time()
        forced_result = optimized_analyzer.force_optimized_analysis(inventory, additional_symptoms)
        optimized_forced_time = time.time() - start_time
        
        print(f"  Analyseur optimisé forcé: {optimized_forced_time:.2f} secondes")
        results["optimized_forced_times"].append(optimized_forced_time)
    
    return results


def plot_performance_comparison(results: Dict[str, List]):
    """
    Génère un graphique comparatif des performances.
    
    Args:
        results: Résultats des tests de performance
    """
    tree_counts = results["tree_counts"]
    standard_times = results["standard_times"]
    optimized_times = results["optimized_times"]
    optimized_forced_times = results["optimized_forced_times"]
    
    # Créer un graphique de performance
    plt.figure(figsize=(10, 6))
    plt.plot(tree_counts, standard_times, 'b-o', label='Analyseur standard')
    plt.plot(tree_counts, optimized_times, 'g-o', label='Analyseur optimisé (auto)')
    plt.plot(tree_counts, optimized_forced_times, 'r-o', label='Analyseur optimisé (forcé)')
    
    plt.xlabel('Nombre d\'arbres')
    plt.ylabel('Temps d\'exécution (secondes)')
    plt.title('Comparaison des performances entre analyseurs sanitaires')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Sauvegarder le graphique
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'performance_comparison.png', dpi=300)
    plt.close()
    
    # Créer un tableau des résultats
    df = pd.DataFrame({
        'Nombre d\'arbres': tree_counts,
        'Temps standard (s)': standard_times,
        'Temps optimisé (s)': optimized_times,
        'Temps optimisé forcé (s)': optimized_forced_times,
        'Gain (%)': [(s - o) / s * 100 for s, o in zip(standard_times, optimized_times)],
        'Score standard': results["standard_health_scores"],
        'Score optimisé': results["optimized_health_scores"]
    })
    
    # Sauvegarder les résultats en CSV
    df.to_csv(OUTPUT_DIR / 'performance_results.csv', index=False)
    
    # Afficher le tableau
    print("\nRésultats de performance:")
    print(df.to_string(index=False))


def run_detailed_analysis(num_trees: int = 5000):
    """
    Exécute une analyse détaillée avec l'analyseur optimisé sur un grand jeu de données.
    
    Args:
        num_trees: Nombre d'arbres à analyser
    """
    print(f"\nAnalyse détaillée avec {num_trees} arbres:")
    
    # Générer un inventaire synthétique
    inventory = generate_synthetic_inventory(num_trees)
    
    # Définir les symptômes additionnels et données climatiques
    additional_symptoms = {
        "leaf_discoloration": 0.35,
        "observed_pests": ["bark_beetle", "processionary_caterpillar"],
        "crown_thinning": 0.25,
        "bark_damage": 0.15
    }
    
    climate_data = {
        "annual_temp": 14.2,
        "annual_precip": 650,
        "drought_index": 0.4,
        "temperature_anomaly": 1.2
    }
    
    # Initialiser l'analyseur optimisé avec configuration
    config = {
        "optimization": {
            "parallel_enabled": True,
            "max_processes": 4,
            "batch_size": 100,
            "tree_threshold": 100
        }
    }
    optimized_analyzer = OptimizedHealthAnalyzer(config)
    
    # Exécuter l'analyse
    start_time = time.time()
    result = optimized_analyzer.analyze_health(inventory, additional_symptoms, climate_data)
    execution_time = time.time() - start_time
    
    # Afficher les résultats principaux
    print(f"  Analyse terminée en {execution_time:.2f} secondes")
    print(f"  Score sanitaire global: {result.get('overall_health_score', 0):.2f}/10")
    print(f"  État sanitaire: {result.get('health_status', '')}")
    print(f"  Problèmes détectés: {len(result.get('detected_issues', []))}")
    
    # Sauvegarder les résultats
    with open(OUTPUT_DIR / f'detailed_analysis_{num_trees}_trees.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def main():
    """Fonction principale exécutant les exemples d'utilisation."""
    print("🌲 Exemple d'utilisation de l'analyseur sanitaire forestier optimisé 🌲")
    
    # Test de performance avec différentes tailles d'inventaire
    tree_counts = [10, 100, 500, 1000, 5000, 10000]
    results = compare_analyzers(tree_counts)
    
    # Générer et sauvegarder les graphiques de performance
    plot_performance_comparison(results)
    
    # Exécuter une analyse détaillée sur un grand jeu de données
    run_detailed_analysis(5000)
    
    print(f"\n✅ Démonstration terminée. Les résultats sont disponibles dans le dossier: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
