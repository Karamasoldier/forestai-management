#!/usr/bin/env python3
"""
Module de filtrage et de recommandation d'espèces adaptées aux contraintes terrain et climatiques.

Ce module contient les fonctions pour:
1. Filtrer les recommandations d'espèces en fonction des contraintes terrain
2. Ajuster les scores des espèces selon divers critères
3. Prioriser les espèces les plus adaptées au contexte spécifique
"""

import os
import sys
import logging
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from forestai.core.utils.logging_config import LoggingConfig

def setup_logging():
    """Configure le système de logging."""
    config = LoggingConfig.get_instance()
    config.init({
        "level": "INFO",
        "log_dir": "logs/advanced_example",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    return config.get_logger("examples.climate_geo_advanced.recommendations")

def filter_recommendations_with_constraints(recommendations, constraints, terrain_data):
    """
    Filtre intelligemment les recommandations d'espèces en fonction des contraintes de terrain.
    
    Args:
        recommendations: Liste des recommandations d'espèces du ClimateAnalyzer
        constraints: Liste des contraintes de terrain identifiées
        terrain_data: Données de terrain issues de l'analyse géospatiale
        
    Returns:
        Liste filtrée des recommandations d'espèces adaptées aux contraintes
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Filtrage des recommandations selon {len(constraints)} contraintes terrain")
    
    # Copier les recommandations pour éviter de modifier l'original
    filtered_recs = recommendations.copy()
    
    # Règles de filtrage en fonction des contraintes terrain
    if "pente_forte" in constraints:
        # Garder les espèces avec un système racinaire profond pour stabiliser les pentes
        filtered_recs = [r for r in filtered_recs if r["species_name"] not in ["Fagus sylvatica"]]
        logger.info("  - Filtrage pour pentes fortes appliqué")
    
    if "sécheresse_estivale" in constraints or "sol_sec" in constraints:
        # Filtrer pour garder uniquement les espèces résistantes à la sécheresse
        filtered_recs = [r for r in filtered_recs if r["risks"].get("drought") != "high"]
        logger.info("  - Filtrage pour résistance à la sécheresse appliqué")
    
    if "risque_incendie_élevé" in constraints:
        # Préférer les espèces moins inflammables
        filtered_recs = [r for r in filtered_recs if r["risks"].get("fire") != "high"]
        logger.info("  - Filtrage pour résistance au feu appliqué")
    
    if "gel_tardif" in constraints:
        # Préférer les espèces résistantes au gel
        filtered_recs = [r for r in filtered_recs if r["risks"].get("frost") != "high"]
        logger.info("  - Filtrage pour résistance au gel appliqué")
    
    # Vérifier si la pente est trop forte pour certaines espèces
    if terrain_data and "terrain_analysis" in terrain_data:
        slope_mean = terrain_data["terrain_analysis"]["slope"]["mean"]
        if slope_mean > 15:
            filtered_recs = [r for r in filtered_recs if r["species_name"] not in ["Quercus robur"]]
            logger.info(f"  - Filtrage pour forte pente moyenne ({slope_mean}°) appliqué")
    
    # Tenir compte de l'exposition pour certaines espèces
    if terrain_data and "terrain_analysis" in terrain_data:
        aspect = terrain_data["terrain_analysis"]["aspect"]
        if aspect in ["South", "Southeast", "Southwest"]:
            # Exposition sud: favoriser les espèces thermophiles
            for rec in filtered_recs:
                if rec["species_name"] in ["Quercus pubescens", "Cedrus atlantica", "Pinus pinaster"]:
                    rec["global_score"] *= 1.1  # Bonus de 10%
            logger.info("  - Bonus pour exposition sud appliqué")
    
    # Recalculer les rangs en fonction des scores modifiés
    filtered_recs = sorted(filtered_recs, key=lambda x: x["global_score"], reverse=True)
    
    logger.info(f"Recommandations après filtrage: {len(filtered_recs)}")
    
    return filtered_recs

def adjust_recommendations_for_economics(recommendations, economic_priority=1.0):
    """
    Ajuste les scores des recommandations en fonction de la priorité économique.
    
    Args:
        recommendations: Liste des recommandations d'espèces
        economic_priority: Coefficient de priorité économique (1.0 = normal, >1 = favoriser l'économique)
        
    Returns:
        Liste des recommandations avec scores ajustés
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Ajustement des scores avec priorité économique: {economic_priority}")
    
    # Copier les recommandations pour éviter de modifier l'original
    adjusted_recs = recommendations.copy()
    
    # Valeurs de conversion pour les scores qualitatifs
    economic_values = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.9,
        "very high": 1.0
    }
    
    # Ajuster les scores
    for rec in adjusted_recs:
        economic_value = economic_values.get(rec.get("economic_value", "medium"), 0.6)
        
        # Ajuster le score global en fonction de la valeur économique
        original_score = rec["global_score"]
        economic_factor = economic_value * economic_priority
        
        # Formule d'ajustement: moyenne pondérée entre score d'origine et facteur économique
        rec["global_score"] = (original_score * 0.7) + (economic_factor * 0.3)
        rec["score_adjustment"] = {
            "original_score": original_score,
            "economic_factor": economic_factor,
            "reason": "economic_priority"
        }
    
    # Recalculer les rangs en fonction des scores modifiés
    adjusted_recs = sorted(adjusted_recs, key=lambda x: x["global_score"], reverse=True)
    
    return adjusted_recs

def adjust_recommendations_for_ecological(recommendations, ecological_priority=1.0):
    """
    Ajuste les scores des recommandations en fonction de la priorité écologique.
    
    Args:
        recommendations: Liste des recommandations d'espèces
        ecological_priority: Coefficient de priorité écologique (1.0 = normal, >1 = favoriser l'écologie)
        
    Returns:
        Liste des recommandations avec scores ajustés
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Ajustement des scores avec priorité écologique: {ecological_priority}")
    
    # Copier les recommandations pour éviter de modifier l'original
    adjusted_recs = recommendations.copy()
    
    # Valeurs de conversion pour les scores qualitatifs
    ecological_values = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.9,
        "very high": 1.0
    }
    
    # Ajuster les scores
    for rec in adjusted_recs:
        ecological_value = ecological_values.get(rec.get("ecological_value", "medium"), 0.6)
        
        # Ajuster le score global en fonction de la valeur écologique
        original_score = rec["global_score"]
        ecological_factor = ecological_value * ecological_priority
        
        # Formule d'ajustement: moyenne pondérée entre score d'origine et facteur écologique
        rec["global_score"] = (original_score * 0.7) + (ecological_factor * 0.3)
        rec["score_adjustment"] = {
            "original_score": original_score,
            "ecological_factor": ecological_factor,
            "reason": "ecological_priority"
        }
    
    # Recalculer les rangs en fonction des scores modifiés
    adjusted_recs = sorted(adjusted_recs, key=lambda x: x["global_score"], reverse=True)
    
    return adjusted_recs

def adjust_recommendations_for_diversity(recommendations, current_forest_species=[]):
    """
    Ajuste les scores des recommandations pour favoriser la diversité des espèces.
    
    Args:
        recommendations: Liste des recommandations d'espèces
        current_forest_species: Liste des espèces déjà présentes dans la forêt
        
    Returns:
        Liste des recommandations avec scores ajustés
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Ajustement des scores pour la diversité forestière")
    
    # Copier les recommandations pour éviter de modifier l'original
    adjusted_recs = recommendations.copy()
    
    if not current_forest_species:
        return adjusted_recs
    
    # Extraire les genres déjà présents
    current_genera = set()
    for species in current_forest_species:
        parts = species.split()
        if parts:
            current_genera.add(parts[0])
    
    logger.info(f"Genres déjà présents: {', '.join(current_genera)}")
    
    # Ajuster les scores
    for rec in adjusted_recs:
        species_name = rec["species_name"]
        genus = species_name.split()[0] if species_name else ""
        
        original_score = rec["global_score"]
        
        # Pénaliser les espèces du même genre que celles déjà présentes
        if genus in current_genera:
            rec["global_score"] *= 0.9  # Pénalité de 10%
            rec["score_adjustment"] = {
                "original_score": original_score,
                "reason": "genre_déjà_présent"
            }
        else:
            # Bonus pour les espèces qui apportent de la diversité
            rec["global_score"] *= 1.1  # Bonus de 10%
            rec["score_adjustment"] = {
                "original_score": original_score,
                "reason": "diversification"
            }
    
    # Recalculer les rangs en fonction des scores modifiés
    adjusted_recs = sorted(adjusted_recs, key=lambda x: x["global_score"], reverse=True)
    
    return adjusted_recs

def combine_recommendations_for_climate_change(current_recs, future_recs, adaptation_weight=0.3):
    """
    Combine les recommandations pour le climat actuel et futur pour une gestion adaptative.
    
    Args:
        current_recs: Recommandations pour le climat actuel
        future_recs: Recommandations pour le climat futur
        adaptation_weight: Poids donné aux recommandations futures (0-1)
        
    Returns:
        Liste combinée des recommandations avec scores ajustés pour l'adaptation
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Combinaison des recommandations avec poids adaptation: {adaptation_weight}")
    
    # Créer un dictionnaire des recommandations actuelles pour un accès facile
    current_dict = {rec["species_name"]: rec for rec in current_recs}
    future_dict = {rec["species_name"]: rec for rec in future_recs}
    
    # Liste pour les recommandations combinées
    combined_recs = []
    
    # Traiter toutes les espèces des recommandations actuelles
    for species_name, current_rec in current_dict.items():
        combined_rec = current_rec.copy()
        
        # Si l'espèce existe aussi dans les recommandations futures, ajuster le score
        if species_name in future_dict:
            future_rec = future_dict[species_name]
            
            # Calculer le score combiné
            current_score = current_rec["global_score"]
            future_score = future_rec["global_score"]
            combined_score = (current_score * (1 - adaptation_weight)) + (future_score * adaptation_weight)
            
            combined_rec["global_score"] = combined_score
            combined_rec["score_components"] = {
                "current_score": current_score,
                "future_score": future_score,
                "adaptation_weight": adaptation_weight
            }
            combined_rec["climate_change_resilience"] = "good"
        else:
            # L'espèce n'est pas recommandée pour le climat futur
            combined_rec["global_score"] *= 0.8  # Pénalité
            combined_rec["climate_change_resilience"] = "poor"
        
        combined_recs.append(combined_rec)
    
    # Ajouter les espèces qui sont uniquement dans les recommandations futures
    for species_name, future_rec in future_dict.items():
        if species_name not in current_dict:
            new_rec = future_rec.copy()
            new_rec["global_score"] *= adaptation_weight  # Réduire l'importance car pas adapté au climat actuel
            new_rec["climate_change_resilience"] = "future_only"
            combined_recs.append(new_rec)
    
    # Recalculer les rangs en fonction des scores modifiés
    combined_recs = sorted(combined_recs, key=lambda x: x["global_score"], reverse=True)
    
    logger.info(f"Nombre total de recommandations combinées: {len(combined_recs)}")
    
    return combined_recs

def process_parcel_recommendations(terrain_analysis, climate_recommendations, priorities=None):
    """
    Traite et filtre les recommandations d'espèces pour une parcelle spécifique.
    
    Args:
        terrain_analysis: Résultats de l'analyse terrain
        climate_recommendations: Recommandations climatiques par scénario
        priorities: Dictionnaire des priorités (economics, ecology, adaptation)
        
    Returns:
        Dictionnaire avec les recommandations filtrées et combinées
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Traitement des recommandations pour la parcelle {terrain_analysis.get('id', 'inconnue')}")
    
    # Définir les priorités par défaut
    if priorities is None:
        priorities = {
            "economic": 1.0,
            "ecological": 1.0,
            "adaptation": 0.3
        }
    
    # Extraire les contraintes terrain
    constraints = terrain_analysis.get("forestry_potential", {}).get("constraints", [])
    
    # Obtenir les recommandations climatiques par scénario
    current_recs = climate_recommendations.get("current", [])
    future_recs = climate_recommendations.get("2050_rcp45", [])
    
    # 1. Filtrer selon les contraintes terrain
    logger.info("Étape 1: Filtrage selon les contraintes terrain")
    filtered_current = filter_recommendations_with_constraints(current_recs, constraints, terrain_analysis)
    filtered_future = filter_recommendations_with_constraints(future_recs, constraints, terrain_analysis)
    
    # 2. Ajuster selon les priorités économiques
    logger.info("Étape 2: Ajustement selon les priorités économiques")
    economic_adjusted_current = adjust_recommendations_for_economics(
        filtered_current, 
        economic_priority=priorities["economic"]
    )
    economic_adjusted_future = adjust_recommendations_for_economics(
        filtered_future, 
        economic_priority=priorities["economic"]
    )
    
    # 3. Ajuster selon les priorités écologiques
    logger.info("Étape 3: Ajustement selon les priorités écologiques")
    eco_adjusted_current = adjust_recommendations_for_ecological(
        economic_adjusted_current, 
        ecological_priority=priorities["ecological"]
    )
    eco_adjusted_future = adjust_recommendations_for_ecological(
        economic_adjusted_future, 
        ecological_priority=priorities["ecological"]
    )
    
    # 4. Combiner les recommandations actuelles et futures
    logger.info("Étape 4: Combinaison des recommandations actuelles et futures")
    combined_recs = combine_recommendations_for_climate_change(
        eco_adjusted_current,
        eco_adjusted_future,
        adaptation_weight=priorities["adaptation"]
    )
    
    # 5. Ajuster pour la diversité si des espèces existantes sont spécifiées
    current_species = terrain_analysis.get("existing_species", [])
    if current_species:
        logger.info("Étape 5: Ajustement pour la diversité")
        final_recs = adjust_recommendations_for_diversity(combined_recs, current_species)
    else:
        final_recs = combined_recs
    
    # Créer le résultat final
    result = {
        "filtered": {
            "current": filtered_current,
            "future": filtered_future
        },
        "combined": combined_recs,
        "final": final_recs[:10]  # Les 10 meilleures recommandations
    }
    
    logger.info(f"Traitement terminé. Recommandations finales: {len(result['final'])}")
    
    return result

if __name__ == "__main__":
    # Test du module
    logger = setup_logging()
    logger.info("Test du module de recommandation d'espèces")
    
    # Importer les modules nécessaires pour le test
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_preparation import create_real_world_parcels
    from climate_analysis import init_climate_analyzer, get_species_recommendations
    from geo_analysis import simulate_detailed_geo_analysis
    
    # Créer des parcelles
    parcels = create_real_world_parcels()
    parcel = parcels.iloc[2]  # Utiliser la parcelle de Provence pour cet exemple
    print(f"Parcelle sélectionnée: {parcel['name']} ({parcel['region']})")
    
    # Obtenir l'analyse de terrain
    terrain_data = simulate_detailed_geo_analysis(parcel)
    print(f"Contraintes identifiées: {terrain_data['forestry_potential']['constraints']}")
    
    # Obtenir des recommandations climatiques
    analyzer = init_climate_analyzer()
    recommendations = get_species_recommendations(analyzer, parcel["geometry"])
    
    print(f"Recommandations climatiques obtenues: {len(recommendations['current'])} pour le climat actuel")
    
    # Test de filtrage avec contraintes terrain
    filtered_recs = filter_recommendations_with_constraints(
        recommendations["current"],
        terrain_data["forestry_potential"]["constraints"],
        terrain_data
    )
    print(f"Recommandations après filtrage: {len(filtered_recs)}")
    
    # Test de traitement complet
    priorities = {
        "economic": 1.2,  # Priorité économique un peu plus forte
        "ecological": 1.0, # Priorité écologique normale
        "adaptation": 0.4  # Adaptation au changement climatique moyenne-haute
    }
    
    result = process_parcel_recommendations(terrain_data, recommendations, priorities)
    
    print("\nTop 5 recommandations finales:")
    for i, rec in enumerate(result["final"][:5], 1):
        print(f"{i}. {rec['species_name']} ({rec['common_name']}) - Score: {rec['global_score']:.2f}")
        if "climate_change_resilience" in rec:
            print(f"   Résilience au changement climatique: {rec['climate_change_resilience']}")
