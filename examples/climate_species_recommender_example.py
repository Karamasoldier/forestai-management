#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemple avancé d'utilisation du système de recommandation d'espèces avec analyse climatique.

Ce script démontre l'utilisation du système de recommandation d'espèces intégré
avec l'analyseur de scénarios climatiques pour évaluer l'adaptation des espèces
forestières aux changements climatiques.
"""

import os
import sys
import json
import pandas as pd
from pprint import pprint
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Ajouter le répertoire parent au chemin pour permettre l'importation depuis la racine du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forestai.domain.services.species_recommender.recommender import SpeciesRecommender
from forestai.domain.services.species_recommender.ml_recommender import MLSpeciesRecommender
from forestai.domain.services.species_recommender.ml_models.climate_analyzer import ClimateScenarioAnalyzer
from forestai.domain.services.species_recommender.models import (
    SoilType, 
    MoistureRegime, 
    DroughtResistance,
    FrostResistance,
    GrowthRate,
    WoodUse,
    SpeciesData
)


def print_section(title):
    """Imprime un titre de section formaté."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def plot_adaptability_chart(comparison, scenario_id, output_dir=None):
    """
    Génère un graphique de comparaison d'adaptabilité des espèces pour un scénario donné.
    
    Args:
        comparison: Résultats de comparaison des espèces
        scenario_id: Identifiant du scénario à représenter
        output_dir: Répertoire de sortie pour sauvegarder le graphique (facultatif)
    """
    # Récupérer les 10 premières espèces par ordre d'adaptabilité
    top_species = sorted(
        [s for s in comparison["species_rankings"].values() if scenario_id in s["scenario_rankings"]],
        key=lambda x: x["scenario_rankings"][scenario_id]["score"],
        reverse=True
    )[:10]
    
    # Préparer les données pour le graphique
    species_names = [s["common_name"] for s in top_species]
    scores = [s["scenario_rankings"][scenario_id]["score"] for s in top_species]
    
    # Créer le graphique
    plt.figure(figsize=(12, 8))
    bars = plt.barh(species_names, scores, color='skyblue')
    
    # Ajouter les valeurs sur les barres
    for i, bar in enumerate(bars):
        plt.text(
            bar.get_width() + 0.01,
            bar.get_y() + bar.get_height()/2,
            f"{scores[i]:.2f}",
            va='center'
        )
    
    # Personnaliser le graphique
    scenario_name = next((s["name"] for s in comparison["scenarios"] if s["id"] == scenario_id), scenario_id)
    plt.title(f"Top 10 des espèces les plus adaptées - Scénario {scenario_name}")
    plt.xlabel("Score d'adaptabilité (0-1)")
    plt.ylabel("Espèces")
    plt.xlim(0, 1.0)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Sauvegarder ou afficher le graphique
    if output_dir:
        output_path = Path(output_dir) / f"adaptability_{scenario_id}.png"
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        print(f"Graphique sauvegardé: {output_path}")
    
    plt.tight_layout()
    plt.show()


def run_example():
    """Exécute un exemple avancé d'utilisation du système de recommandation d'espèces avec analyse climatique."""
    
    print_section("Initialisation du système de recommandation d'espèces avec analyse climatique")
    
    # Initialiser les recommandeurs
    basic_recommender = SpeciesRecommender()
    ml_recommender = MLSpeciesRecommender()
    climate_analyzer = ClimateScenarioAnalyzer(ml_recommender)
    
    print("Système de recommandation d'espèces initialisé avec succès.")
    
    # Récupérer les espèces existantes
    species_data = basic_recommender.get_species_data()
    
    if not species_data:
        print("Aucune espèce trouvée. Veuillez exécuter species_recommender_example.py d'abord.")
        return
    
    print(f"Nombre d'espèces disponibles: {len(species_data)}")
    
    print_section("Définition des données climatiques et pédologiques pour l'analyse")
    
    # Données climatiques actuelles pour une parcelle hypothétique
    current_climate_data = {
        "mean_annual_temperature": 11.5,  # °C
        "min_temperature": -10.0,  # °C
        "max_temperature": 35.0,  # °C
        "annual_precipitation": 850,  # mm
        "drought_index": 4  # Échelle de 0 à 10
    }
    
    # Données pédologiques
    soil_data = {
        "soil_type": "limoneux",  # Type de sol
        "moisture_regime": "moyen",  # Régime d'humidité
        "pH": 6.8,  # pH du sol
        "depth": 120  # Profondeur du sol en cm
    }
    
    print("Données climatiques actuelles:")
    pprint(current_climate_data)
    print("\nDonnées pédologiques:")
    pprint(soil_data)
    
    print_section("Analyse des scénarios climatiques")
    
    # Scénarios climatiques à analyser
    scenarios_to_analyze = ["rcp26_2050", "rcp45_2050", "rcp85_2050"]
    
    print("Scénarios sélectionnés pour l'analyse:")
    for scenario_id in scenarios_to_analyze:
        scenario = climate_analyzer.get_predefined_scenario(scenario_id)
        print(f"- {scenario['name']}: {scenario['description']}")
        print(f"  Augmentation de température: +{scenario['temperature_increase']}°C")
        print(f"  Facteur de précipitations: {scenario['precipitation_change_factor']}")
        print(f"  Augmentation de l'indice de sécheresse: +{scenario['drought_index_increase']}")
    
    print("\nProjection des données climatiques pour les scénarios sélectionnés:")
    
    for scenario_id in scenarios_to_analyze:
        scenario = climate_analyzer.get_predefined_scenario(scenario_id)
        future_climate = climate_analyzer.project_climate_data(current_climate_data, scenario)
        
        print(f"\nScénario {scenario['name']}:")
        print(f"  Température moyenne: {current_climate_data['mean_annual_temperature']}°C → {future_climate['mean_annual_temperature']}°C")
        print(f"  Précipitations annuelles: {current_climate_data['annual_precipitation']} mm → {future_climate['annual_precipitation']} mm")
        print(f"  Indice de sécheresse: {current_climate_data['drought_index']} → {future_climate['drought_index']}")
    
    print_section("Comparaison d'adaptabilité des espèces aux scénarios climatiques")
    
    # Comparer l'adaptabilité des espèces à travers les scénarios
    comparison = climate_analyzer.compare_species_across_scenarios(
        species_data, current_climate_data, scenarios_to_analyze
    )
    
    print(f"Comparaison effectuée sur {len(comparison['species_rankings'])} espèces.")
    
    print("\nTop 5 des espèces les plus résilientes au changement climatique:")
    for i, species in enumerate(comparison["most_resilient_species"]):
        print(f"{i+1}. {species['common_name']} ({species['latin_name']}) - Score moyen: {species['average_adaptability']}")
    
    print("\nTop 5 des espèces les plus vulnérables au changement climatique:")
    for i, species in enumerate(comparison["most_vulnerable_species"]):
        print(f"{i+1}. {species['common_name']} ({species['latin_name']}) - Score moyen: {species['average_adaptability']}")
    
    print_section("Analyse détaillée d'espèces spécifiques")
    
    # Sélectionner deux espèces pour une analyse détaillée
    resilient_species_id = comparison["most_resilient_species"][0]["species_id"]
    vulnerable_species_id = comparison["most_vulnerable_species"][0]["species_id"]
    
    resilient_species = species_data[resilient_species_id]
    vulnerable_species = species_data[vulnerable_species_id]
    
    print(f"Analyse détaillée de deux espèces contrastées face au changement climatique:\n")
    
    print(f"1. Espèce résiliente: {resilient_species.common_name} ({resilient_species.latin_name})")
    print(f"   Famille: {resilient_species.family}")
    print(f"   Résistance à la sécheresse: {resilient_species.drought_resistance.value if resilient_species.drought_resistance else 'Non spécifiée'}")
    print(f"   Résistance au gel: {resilient_species.frost_resistance.value if resilient_species.frost_resistance else 'Non spécifiée'}")
    
    print(f"\n2. Espèce vulnérable: {vulnerable_species.common_name} ({vulnerable_species.latin_name})")
    print(f"   Famille: {vulnerable_species.family}")
    print(f"   Résistance à la sécheresse: {vulnerable_species.drought_resistance.value if vulnerable_species.drought_resistance else 'Non spécifiée'}")
    print(f"   Résistance au gel: {vulnerable_species.frost_resistance.value if vulnerable_species.frost_resistance else 'Non spécifiée'}")
    
    print("\nAdaptabilité par scénario:")
    
    for scenario_id in scenarios_to_analyze:
        scenario = climate_analyzer.get_predefined_scenario(scenario_id)
        future_climate = climate_analyzer.project_climate_data(current_climate_data, scenario)
        
        print(f"\nScénario {scenario['name']}:")
        
        # Analyser l'adaptabilité de l'espèce résiliente
        resilient_analysis = climate_analyzer.analyze_species_climate_adaptability(
            resilient_species, current_climate_data, future_climate
        )
        
        # Analyser l'adaptabilité de l'espèce vulnérable
        vulnerable_analysis = climate_analyzer.analyze_species_climate_adaptability(
            vulnerable_species, current_climate_data, future_climate
        )
        
        print(f"  {resilient_species.common_name}: Score d'adaptabilité {resilient_analysis['adaptability_score']} ({resilient_analysis['adaptability_level']})")
        print(f"  {vulnerable_species.common_name}: Score d'adaptabilité {vulnerable_analysis['adaptability_score']} ({vulnerable_analysis['adaptability_level']})")
        
        # Afficher les recommandations pour l'espèce vulnérable
        if vulnerable_analysis['recommendations']:
            print(f"\n  Recommandations pour {vulnerable_species.common_name}:")
            for rec in vulnerable_analysis['recommendations']:
                print(f"  - {rec}")
    
    print_section("Recommandation d'espèces pour la parcelle avec analyse climatique")
    
    # Contexte de recommandation
    context = {
        "objective": "balanced",
        "wood_use": "construction",
        "climate_change_scenario": "moderate",
        "plantation_density": 1600,
        "target_rotation": 60
    }
    
    # Scénario à utiliser pour la recommandation
    selected_scenario_id = "rcp45_2050"
    selected_scenario = climate_analyzer.get_predefined_scenario(selected_scenario_id)
    
    # Projeter le climat futur pour le scénario sélectionné
    future_climate = climate_analyzer.project_climate_data(current_climate_data, selected_scenario)
    
    print(f"Génération de recommandations pour le scénario {selected_scenario['name']}:")
    print("Contexte de plantation:")
    pprint(context)
    
    # Générer des recommandations pour le climat actuel
    print("\nRecommandations pour le climat actuel:")
    current_recommendation = basic_recommender.recommend_species(
        "parcel_example_current", current_climate_data, soil_data, context
    )
    
    # Afficher les 5 premières recommandations
    for i, rec in enumerate(current_recommendation.recommendations[:5]):
        print(f"{i+1}. {rec['common_name']} ({rec['latin_name']})")
        print(f"   Score global: {rec['scores']['overall_score']:.3f}")
        print(f"   Score climatique: {rec['scores']['climate_score']:.3f}")
        print(f"   Score de risque: {rec['scores']['risk_score']:.3f}")
    
    # Générer des recommandations pour le climat futur
    print("\nRecommandations pour le climat futur (scénario {})".format(selected_scenario['name']))
    future_recommendation = basic_recommender.recommend_species(
        "parcel_example_future", future_climate, soil_data, context
    )
    
    # Afficher les 5 premières recommandations
    for i, rec in enumerate(future_recommendation.recommendations[:5]):
        print(f"{i+1}. {rec['common_name']} ({rec['latin_name']})")
        print(f"   Score global: {rec['scores']['overall_score']:.3f}")
        print(f"   Score climatique: {rec['scores']['climate_score']:.3f}")
        print(f"   Score de risque: {rec['scores']['risk_score']:.3f}")
    
    print_section("Analyse des différences entre les recommandations")
    
    # Comparer les recommandations actuelles et futures
    current_species = {rec['species_id']: (rec['rank'], rec['scores']['overall_score']) 
                      for rec in current_recommendation.recommendations}
    future_species = {rec['species_id']: (rec['rank'], rec['scores']['overall_score']) 
                     for rec in future_recommendation.recommendations}
    
    # Identifier les espèces qui changent de classement
    rank_changes = {}
    for species_id, (current_rank, current_score) in current_species.items():
        if species_id in future_species:
            future_rank, future_score = future_species[species_id]
            rank_diff = current_rank - future_rank
            score_diff = future_score - current_score
            
            if abs(rank_diff) >= 2:  # Seuil de changement significatif
                species = species_data[species_id]
                rank_changes[species_id] = {
                    'species': f"{species.common_name} ({species.latin_name})",
                    'current_rank': current_rank,
                    'future_rank': future_rank,
                    'rank_diff': rank_diff,
                    'score_diff': score_diff
                }
    
    # Trier par ampleur du changement de rang
    sorted_changes = sorted(rank_changes.items(), 
                           key=lambda x: abs(x[1]['rank_diff']), 
                           reverse=True)
    
    print("Changements majeurs dans le classement des espèces recommandées:")
    for species_id, change in sorted_changes[:5]:  # Top 5 des changements
        direction = "amélioration" if change['rank_diff'] > 0 else "dégradation"
        print(f"\n{change['species']}:")
        print(f"   Rang actuel: {change['current_rank']} → Rang futur: {change['future_rank']}")
        print(f"   Évolution: {abs(change['rank_diff'])} places ({direction})")
        print(f"   Différence de score: {change['score_diff']:.3f}")
    
    # Identifier les espèces qui sont uniquement dans le top 10 actuel
    only_current_top10 = set(rec['species_id'] for rec in current_recommendation.recommendations[:10]) - \
                        set(rec['species_id'] for rec in future_recommendation.recommendations[:10])
    
    # Identifier les espèces qui sont uniquement dans le top 10 futur
    only_future_top10 = set(rec['species_id'] for rec in future_recommendation.recommendations[:10]) - \
                       set(rec['species_id'] for rec in current_recommendation.recommendations[:10])
    
    print("\nEspèces qui sortent du top 10 avec le changement climatique:")
    for species_id in only_current_top10:
        species = species_data[species_id]
        current_rank = next(rec['rank'] for rec in current_recommendation.recommendations 
                           if rec['species_id'] == species_id)
        print(f"- {species.common_name} (Rang actuel: {current_rank})")
    
    print("\nEspèces qui entrent dans le top 10 avec le changement climatique:")
    for species_id in only_future_top10:
        species = species_data[species_id]
        future_rank = next(rec['rank'] for rec in future_recommendation.recommendations 
                          if rec['species_id'] == species_id)
        print(f"- {species.common_name} (Rang futur: {future_rank})")
    
    print_section("Visualisation de l'adaptabilité des espèces")
    
    # Créer un répertoire pour les visualisations (facultatif)
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Générer des graphiques pour chaque scénario
    for scenario_id in scenarios_to_analyze:
        try:
            plot_adaptability_chart(comparison, scenario_id, output_dir)
        except Exception as e:
            print(f"Impossible de générer le graphique pour {scenario_id}: {str(e)}")
    
    print_section("Conclusion")
    
    print("Cet exemple a démontré l'utilisation du système de recommandation d'espèces")
    print("intégré avec l'analyse de scénarios climatiques pour évaluer et visualiser")
    print("l'adaptabilité des espèces forestières face au changement climatique.")
    
    print("\nLes fonctionnalités illustrées comprennent:")
    print("- Projection de données climatiques selon différents scénarios RCP")
    print("- Comparaison de l'adaptabilité des espèces à travers différents scénarios")
    print("- Analyse détaillée d'espèces spécifiques face au changement climatique")
    print("- Génération de recommandations adaptées aux climats actuels et futurs")
    print("- Visualisation graphique des résultats d'adaptabilité")
    
    print("\nCes outils permettent aux gestionnaires forestiers d'anticiper les effets")
    print("du changement climatique et de planifier des plantations adaptées aux")
    print("conditions futures, favorisant ainsi la résilience des forêts.")

if __name__ == "__main__":
    run_example()
