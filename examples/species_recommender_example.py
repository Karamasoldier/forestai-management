#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation du système de recommandation d'espèces.

Ce script démontre l'utilisation du système de recommandation d'espèces forestières
pour une parcelle hypothétique.
"""

import os
import sys
import json
from pprint import pprint
from datetime import datetime

# Ajouter le répertoire parent au chemin pour permettre l'importation depuis la racine du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forestai.domain.services.species_recommender.recommender import SpeciesRecommender
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

def run_example():
    """Exécute un exemple d'utilisation du système de recommandation d'espèces."""
    
    print_section("Initialisation du système de recommandation d'espèces")
    
    # Initialiser le recommandeur
    recommender = SpeciesRecommender()
    
    print("Système de recommandation d'espèces initialisé avec succès.")
    
    # Ajouter quelques espèces de test si aucune n'existe
    existing_species = recommender.get_species_data()
    
    if not existing_species:
        print_section("Ajout d'espèces de test")
        
        # Chêne sessile
        chene_sessile = {
            "id": "sp-001",
            "latin_name": "Quercus petraea",
            "common_name": "Chêne sessile",
            "family": "Fagaceae",
            "growth_form": "Arbre",
            "native": True,
            "description": "Arbre forestier de grande taille, pouvant atteindre 40m de hauteur, au feuillage caduc.",
            "min_temperature": -25.0,
            "max_temperature": 40.0,
            "optimal_temperature_range": {"min": 8.0, "max": 18.0},
            "annual_rainfall_range": {"min": 600, "max": 1500},
            "altitude_range": {"min": 0, "max": 1500},
            "suitable_soil_types": ["argileux", "limoneux", "sableux"],
            "suitable_moisture_regimes": ["sec", "moyen", "humide"],
            "drought_resistance": "élevée",
            "frost_resistance": "élevée",
            "shade_tolerance": 3,
            "wind_resistance": 8,
            "fire_resistance": 5,
            "growth_rate": "lent",
            "max_height": 40.0,
            "max_dbh": 200.0,
            "longevity": 800,
            "root_system_type": "pivot profond",
            "economic_value": "très élevée",
            "rotation_age": 180,
            "wood_density": 700.0,
            "wood_uses": ["construction", "ameublement", "placage"],
            "ecological_value": "élevée",
            "carbon_sequestration_rate": 4.2,
            "wildlife_value": 9,
            "erosion_control": 7,
            "pest_vulnerability": {"chenille processionnaire": 2, "oïdium": 5},
            "disease_vulnerability": {"phytophthora": 3},
            "tags": ["feuillus", "bois d'oeuvre", "zone tempérée", "longévité élevée"],
            "data_source": "ONF",
            "last_updated": "2024-03-01T00:00:00"
        }
        
        # Pin sylvestre
        pin_sylvestre = {
            "id": "sp-002",
            "latin_name": "Pinus sylvestris",
            "common_name": "Pin sylvestre",
            "family": "Pinaceae",
            "growth_form": "Arbre",
            "native": True,
            "description": "Conifère rustique à écorce orangée caractéristique.",
            "min_temperature": -40.0,
            "max_temperature": 35.0,
            "optimal_temperature_range": {"min": 5.0, "max": 15.0},
            "annual_rainfall_range": {"min": 400, "max": 1200},
            "altitude_range": {"min": 0, "max": 2000},
            "suitable_soil_types": ["sableux", "limoneux", "rocailleux"],
            "suitable_moisture_regimes": ["très sec", "sec", "moyen"],
            "drought_resistance": "très élevée",
            "frost_resistance": "très élevée",
            "shade_tolerance": 2,
            "wind_resistance": 7,
            "fire_resistance": 3,
            "growth_rate": "moyen",
            "max_height": 35.0,
            "max_dbh": 100.0,
            "longevity": 300,
            "root_system_type": "pivot profond et racines latérales",
            "economic_value": "élevée",
            "rotation_age": 80,
            "wood_density": 520.0,
            "wood_uses": ["construction", "pâte à papier", "énergie/chauffage"],
            "ecological_value": "moyenne",
            "carbon_sequestration_rate": 3.8,
            "wildlife_value": 6,
            "erosion_control": 8,
            "pest_vulnerability": {"scolyte": 7, "chenille processionnaire": 8},
            "disease_vulnerability": {"rouille courbeuse": 6},
            "tags": ["conifères", "résineux", "pionnier", "zone boréale", "zone tempérée"],
            "data_source": "ONF",
            "last_updated": "2024-03-01T00:00:00"
        }
        
        # Érable sycomore
        erable_sycomore = {
            "id": "sp-003",
            "latin_name": "Acer pseudoplatanus",
            "common_name": "Érable sycomore",
            "family": "Sapindaceae",
            "growth_form": "Arbre",
            "native": True,
            "description": "Arbre feuillu à croissance rapide avec une large canopée.",
            "min_temperature": -30.0,
            "max_temperature": 35.0,
            "optimal_temperature_range": {"min": 7.0, "max": 16.0},
            "annual_rainfall_range": {"min": 700, "max": 1800},
            "altitude_range": {"min": 0, "max": 1600},
            "suitable_soil_types": ["limoneux", "argileux", "calcaire"],
            "suitable_moisture_regimes": ["moyen", "humide"],
            "drought_resistance": "moyenne",
            "frost_resistance": "élevée",
            "shade_tolerance": 4,
            "wind_resistance": 5,
            "fire_resistance": 4,
            "growth_rate": "rapide",
            "max_height": 35.0,
            "max_dbh": 150.0,
            "longevity": 400,
            "root_system_type": "racines latérales étendues",
            "economic_value": "élevée",
            "rotation_age": 80,
            "wood_density": 630.0,
            "wood_uses": ["ameublement", "placage", "artisanat"],
            "ecological_value": "élevée",
            "carbon_sequestration_rate": 5.1,
            "wildlife_value": 7,
            "erosion_control": 6,
            "pest_vulnerability": {"puceron laineux": 4},
            "disease_vulnerability": {"verticilliose": 5},
            "tags": ["feuillus", "tolérant à la pollution", "zone tempérée"],
            "data_source": "ONF",
            "last_updated": "2024-03-01T00:00:00"
        }
        
        # Douglas
        douglas = {
            "id": "sp-004",
            "latin_name": "Pseudotsuga menziesii",
            "common_name": "Douglas",
            "family": "Pinaceae",
            "growth_form": "Arbre",
            "native": False,
            "description": "Grand conifère originaire d'Amérique du Nord, à croissance rapide et forte production.",
            "min_temperature": -30.0,
            "max_temperature": 35.0,
            "optimal_temperature_range": {"min": 7.0, "max": 18.0},
            "annual_rainfall_range": {"min": 800, "max": 2000},
            "altitude_range": {"min": 0, "max": 1800},
            "suitable_soil_types": ["limoneux", "sableux", "acide"],
            "suitable_moisture_regimes": ["moyen", "humide"],
            "drought_resistance": "moyenne",
            "frost_resistance": "élevée",
            "shade_tolerance": 5,
            "wind_resistance": 6,
            "fire_resistance": 4,
            "growth_rate": "très rapide",
            "max_height": 60.0,
            "max_dbh": 250.0,
            "longevity": 600,
            "root_system_type": "pivot profond et racines latérales",
            "economic_value": "très élevée",
            "rotation_age": 60,
            "wood_density": 530.0,
            "wood_uses": ["construction", "pâte à papier", "ameublement"],
            "ecological_value": "moyenne",
            "carbon_sequestration_rate": 6.2,
            "wildlife_value": 5,
            "erosion_control": 7,
            "pest_vulnerability": {"scolyte": 6, "puceron": 5},
            "disease_vulnerability": {"phaeocryptopus": 7, "rouille suisse": 8},
            "tags": ["conifères", "résineux", "production intensive", "exotique"],
            "data_source": "ONF",
            "last_updated": "2024-03-01T00:00:00"
        }
        
        # Ajouter les espèces
        recommender.add_or_update_species(chene_sessile)
        recommender.add_or_update_species(pin_sylvestre)
        recommender.add_or_update_species(erable_sycomore)
        recommender.add_or_update_species(douglas)
        
        print("Espèces de test ajoutées avec succès.")
    else:
        print(f"{len(existing_species)} espèces déjà présentes dans la base de données.")
    
    # Définir les données de parcelle pour la recommandation
    print_section("Définition des données pour la recommandation")
    
    # Données climatiques
    climate_data = {
        "mean_annual_temperature": 11.5,  # °C
        "min_temperature": -12.0,  # °C
        "max_temperature": 35.0,  # °C
        "annual_precipitation": 850,  # mm
        "drought_index": 5  # Échelle de 0 à 10
    }
    
    # Données pédologiques
    soil_data = {
        "soil_type": "limoneux",  # Type de sol
        "moisture_regime": "moyen",  # Régime d'humidité
        "pH": 6.5,  # pH du sol
        "depth": 120  # Profondeur du sol en cm
    }
    
    # Contexte de la recommandation
    context = {
        "objective": "production_rapide",  # Objectif principal
        "wood_use": "construction",  # Utilisation prévue du bois
        "climate_change_scenario": "moderate",  # Scénario de changement climatique
        "plantation_density": 1600,  # Densité de plantation (arbres/ha)
        "target_rotation": 60  # Durée de rotation cible (années)
    }
    
    print("Données climatiques:")
    pprint(climate_data)
    print("\nDonnées pédologiques:")
    pprint(soil_data)
    print("\nContexte:")
    pprint(context)
    
    # Lancer la recommandation
    print_section("Recommandation d'espèces")
    
    parcel_id = "P1234"  # ID de parcelle fictif
    recommendation = recommender.recommend_species(parcel_id, climate_data, soil_data, context)
    
    print(f"Recommandation générée avec l'ID: {recommendation.id}")
    print(f"Date de génération: {recommendation.metadata['generated_at']}")
    print(f"\nRecommandations pour la parcelle {parcel_id} (objectif: {context['objective']}):")
    
    # Afficher les recommandations
    for rec in recommendation.recommendations:
        print(f"\n{rec['rank']}. {rec['common_name']} ({rec['latin_name']})")
        print(f"   Score global: {rec['scores']['overall_score']:.3f}")
        print(f"   Score climatique: {rec['scores']['climate_score']:.3f}")
        print(f"   Score pédologique: {rec['scores']['soil_score']:.3f}")
        print(f"   Score économique: {rec['scores']['economic_score']:.3f}")
        print(f"   Score écologique: {rec['scores']['ecological_score']:.3f}")
        print(f"   Score de risque: {rec['scores']['risk_score']:.3f}")
    
    # Récupérer la recommandation sauvegardée
    print_section("Récupération de la recommandation sauvegardée")
    
    saved_recommendation = recommender.get_recommendation(recommendation.id)
    
    if saved_recommendation:
        print(f"Recommandation récupérée avec succès (ID: {saved_recommendation.id})")
        print(f"Nombre d'espèces recommandées: {len(saved_recommendation.recommendations)}")
    else:
        print("Échec de la récupération de la recommandation.")
    
    print_section("Fin de l'exemple")

if __name__ == "__main__":
    run_example()
