#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation du système de recommandation d'espèces basé sur ML.

Ce script démontre l'utilisation du système avancé de recommandation d'espèces
forestières avec des modèles d'apprentissage automatique pour une parcelle
hypothétique, notamment pour des scénarios de changement climatique.
"""

import os
import sys
import json
import pandas as pd
from pprint import pprint
from datetime import datetime
import numpy as np

# Ajouter le répertoire parent au chemin pour permettre l'importation depuis la racine du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forestai.domain.services.species_recommender.recommender import SpeciesRecommender
from forestai.domain.services.species_recommender.ml_recommender import MLSpeciesRecommender
from forestai.domain.services.species_recommender.models import (
    SoilType, 
    MoistureRegime, 
    DroughtResistance,
    FrostResistance,
    GrowthRate,
    WoodUse,
    SpeciesData
)
from forestai.domain.services.species_recommender.ml_models.train_utils import generate_training_data


def print_section(title):
    """Imprime un titre de section formaté."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def run_example():
    """Exécute un exemple d'utilisation du système de recommandation d'espèces avec ML."""
    
    print_section("Initialisation du système de recommandation d'espèces")
    
    # Initialiser les recommandeurs
    basic_recommender = SpeciesRecommender()
    ml_recommender = MLSpeciesRecommender()
    
    print("Système de recommandation d'espèces initialisé avec succès.")
    
    # Ajouter quelques espèces de test si aucune n'existe
    existing_species = basic_recommender.get_species_data()
    
    if not existing_species:
        # Utiliser le code d'exemple existant pour ajouter les espèces d'exemple
        print("Aucune espèce trouvée. Veuillez exécuter species_recommender_example.py d'abord.")
        return
    
    print(f"Nombre d'espèces disponibles: {len(existing_species)}")
    
    print_section("Entraînement des modèles ML")
    
    # Générer des données d'entraînement synthétiques
    training_data = generate_training_data(existing_species, n_samples=500)
    
    print(f"Données d'entraînement générées: {len(training_data)} échantillons")
    print("Aperçu des données d'entraînement:")
    print(training_data[['species_id', 'climate_score', 'soil_score', 'economic_score', 'ecological_score', 'risk_score', 'overall_score']].head())
    
    print_section("Définition des données pour la recommandation")
    
    # Données climatiques (scénario de changement climatique)
    current_climate_data = {
        "mean_annual_temperature": 11.5,  # °C
        "min_temperature": -12.0,  # °C
        "max_temperature": 35.0,  # °C
        "annual_precipitation": 850,  # mm
        "drought_index": 5  # Échelle de 0 à 10
    }
    
    # Scénario de changement climatique modéré (horizon 2050)
    future_climate_data = {
        "mean_annual_temperature": 13.2,  # °C (+1.7°C)
        "min_temperature": -9.0,  # °C (+3°C)
        "max_temperature": 38.0,  # °C (+3°C)
        "annual_precipitation": 800,  # mm (-50mm)
        "drought_index": 7  # Échelle de 0 à 10 (+2)
    }
    
    # Données pédologiques
    soil_data = {
        "soil_type": "limoneux",  # Type de sol
        "moisture_regime": "moyen",  # Régime d'humidité
        "pH": 6.5,  # pH du sol
        "depth": 120  # Profondeur du sol en cm
    }
    
    # Contexte de la recommandation
    context_current = {
        "objective": "production_rapide",  # Objectif principal
        "wood_use": "construction",  # Utilisation prévue du bois
        "climate_change_scenario": "none",  # Pas de prise en compte du changement climatique
        "plantation_density": 1600,  # Densité de plantation (arbres/ha)
        "target_rotation": 60  # Durée de rotation cible (années)
    }
    
    context_future = {
        "objective": "production_rapide",  # Objectif principal
        "wood_use": "construction",  # Utilisation prévue du bois
        "climate_change_scenario": "moderate",  # Scénario de changement climatique modéré
        "plantation_density": 1600,  # Densité de plantation (arbres/ha)
        "target_rotation": 60  # Durée de rotation cible (années)
    }
    
    print("Données climatiques actuelles:")
    pprint(current_climate_data)
    print("\nDonnées climatiques futures (scénario 2050):")
    pprint(future_climate_data)
    print("\nDonnées pédologiques:")
    pprint(soil_data)
    print("\nContexte de recommandation actuel:")
    pprint(context_current)
    print("\nContexte de recommandation futur:")
    pprint(context_future)
    
    # Lancer la recommandation avec le scénario actuel
    print_section("Recommandation d'espèces - Scénario actuel")
    
    parcel_id = "P1234"  # ID de parcelle fictif
    recommendation_current = basic_recommender.recommend_species(
        parcel_id, current_climate_data, soil_data, context_current
    )
    
    print(f"Recommandation générée avec l'ID: {recommendation_current.id}")
    print(f"Date de génération: {recommendation_current.metadata['generated_at']}")
    print(f"\nRecommandations pour la parcelle {parcel_id} (scénario actuel):")
    
    # Afficher les recommandations
    for rec in recommendation_current.recommendations[:5]:  # Top 5
        print(f"\n{rec['rank']}. {rec['common_name']} ({rec['latin_name']})")
        print(f"   Score global: {rec['scores']['overall_score']:.3f}")
        print(f"   Score climatique: {rec['scores']['climate_score']:.3f}")
        print(f"   Score pédologique: {rec['scores']['soil_score']:.3f}")
        print(f"   Score économique: {rec['scores']['economic_score']:.3f}")
        print(f"   Score écologique: {rec['scores']['ecological_score']:.3f}")
        print(f"   Score de risque: {rec['scores']['risk_score']:.3f}")
    
    # Lancer la recommandation avec le scénario futur
    print_section("Recommandation d'espèces - Scénario climatique 2050")
    
    recommendation_future = basic_recommender.recommend_species(
        parcel_id, future_climate_data, soil_data, context_future
    )
    
    print(f"Recommandation générée avec l'ID: {recommendation_future.id}")
    print(f"Date de génération: {recommendation_future.metadata['generated_at']}")
    print(f"\nRecommandations pour la parcelle {parcel_id} (scénario 2050):")
    
    # Afficher les recommandations
    for rec in recommendation_future.recommendations[:5]:  # Top 5
        print(f"\n{rec['rank']}. {rec['common_name']} ({rec['latin_name']})")
        print(f"   Score global: {rec['scores']['overall_score']:.3f}")
        print(f"   Score climatique: {rec['scores']['climate_score']:.3f}")
        print(f"   Score pédologique: {rec['scores']['soil_score']:.3f}")
        print(f"   Score économique: {rec['scores']['economic_score']:.3f}")
        print(f"   Score écologique: {rec['scores']['ecological_score']:.3f}")
        print(f"   Score de risque: {rec['scores']['risk_score']:.3f}")
    
    # Comparer les différences de recommandation entre les scénarios
    print_section("Comparaison des recommandations entre les scénarios")
    
    # Extraire les espèces recommandées pour chaque scénario
    current_species = {rec['species_id']: (rec['rank'], rec['scores']['overall_score']) 
                      for rec in recommendation_current.recommendations}
    future_species = {rec['species_id']: (rec['rank'], rec['scores']['overall_score']) 
                     for rec in recommendation_future.recommendations}
    
    # Identifier les espèces qui changent de classement
    rank_changes = {}
    for species_id, (current_rank, current_score) in current_species.items():
        if species_id in future_species:
            future_rank, future_score = future_species[species_id]
            rank_diff = current_rank - future_rank
            score_diff = future_score - current_score
            
            if rank_diff != 0:
                species = existing_species[species_id]
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
    
    print("Changements majeurs dans les recommandations d'espèces avec le changement climatique:")
    for species_id, change in sorted_changes[:5]:  # Top 5 des changements
        direction = "amélioration" if change['rank_diff'] > 0 else "dégradation"
        print(f"\n{change['species']}:")
        print(f"   Rang actuel: {change['current_rank']} → Rang futur: {change['future_rank']}")
        print(f"   Évolution: {abs(change['rank_diff'])} places ({direction})")
        print(f"   Différence de score: {change['score_diff']:.3f}")
    
    # Identifier les espèces qui sont uniquement dans le top 10 actuel
    only_current_top10 = set(rec['species_id'] for rec in recommendation_current.recommendations[:10]) - \
                        set(rec['species_id'] for rec in recommendation_future.recommendations[:10])
    
    # Identifier les espèces qui sont uniquement dans le top 10 futur
    only_future_top10 = set(rec['species_id'] for rec in recommendation_future.recommendations[:10]) - \
                       set(rec['species_id'] for rec in recommendation_current.recommendations[:10])
    
    print("\nEspèces qui sortent du top 10 avec le changement climatique:")
    for species_id in only_current_top10:
        species = existing_species[species_id]
        current_rank = next(rec['rank'] for rec in recommendation_current.recommendations 
                           if rec['species_id'] == species_id)
        print(f"- {species.common_name} (Rang actuel: {current_rank})")
    
    print("\nEspèces qui entrent dans le top 10 avec le changement climatique:")
    for species_id in only_future_top10:
        species = existing_species[species_id]
        future_rank = next(rec['rank'] for rec in recommendation_future.recommendations 
                          if rec['species_id'] == species_id)
        print(f"- {species.common_name} (Rang futur: {future_rank})")
    
    # Analyse des caractéristiques des espèces favorisées par le changement climatique
    print_section("Analyse des adaptations au changement climatique")
    
    # Récupérer les espèces qui s'améliorent significativement (au moins 3 places)
    improving_species = [species_id for species_id, change in rank_changes.items() 
                        if change['rank_diff'] >= 3]
    
    # Analyser les caractéristiques de ces espèces
    if improving_species:
        drought_resistance_counts = {}
        frost_resistance_counts = {}
        
        for species_id in improving_species:
            species = existing_species[species_id]
            
            # Compter les résistances à la sécheresse
            if species.drought_resistance:
                resistance = species.drought_resistance.value
                drought_resistance_counts[resistance] = drought_resistance_counts.get(resistance, 0) + 1
            
            # Compter les résistances au gel
            if species.frost_resistance:
                resistance = species.frost_resistance.value
                frost_resistance_counts[resistance] = frost_resistance_counts.get(resistance, 0) + 1
        
        print("Caractéristiques des espèces favorisées par le changement climatique:")
        
        print("\nRésistance à la sécheresse:")
        for resistance, count in sorted(drought_resistance_counts.items(), 
                                      key=lambda x: DroughtResistance(x[0]).value):
            print(f"- {resistance}: {count} espèces")
        
        print("\nRésistance au gel:")
        for resistance, count in sorted(frost_resistance_counts.items(), 
                                      key=lambda x: FrostResistance(x[0]).value):
            print(f"- {resistance}: {count} espèces")
    
    print_section("Fin de l'exemple")


if __name__ == "__main__":
    run_example()
