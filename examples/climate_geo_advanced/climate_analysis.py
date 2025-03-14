#!/usr/bin/env python3
"""
Module d'analyse climatique pour les parcelles forestières.

Ce module contient les fonctions pour:
1. Analyser les caractéristiques climatiques des parcelles
2. Recommander des espèces adaptées au climat actuel et futur
3. Comparer différents scénarios climatiques
"""

import os
import sys
import logging
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from forestai.core.utils.logging_config import LoggingConfig
from forestai.core.domain.services import ClimateAnalyzer

def setup_logging():
    """Configure le système de logging."""
    config = LoggingConfig.get_instance()
    config.init({
        "level": "INFO",
        "log_dir": "logs/advanced_example",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    return config.get_logger("examples.climate_geo_advanced.climate")

def init_climate_analyzer():
    """
    Initialise l'analyseur climatique.
    
    Returns:
        Instance de ClimateAnalyzer
    """
    logger = logging.getLogger(__name__)
    logger.info("Initialisation de l'analyseur climatique")
    
    analyzer = ClimateAnalyzer()
    
    return analyzer

def get_climate_zone_for_parcel(analyzer, geometry):
    """
    Obtient les informations de zone climatique pour une géométrie.
    
    Args:
        analyzer: Instance de ClimateAnalyzer
        geometry: Géométrie de la parcelle
        
    Returns:
        Dictionnaire contenant les informations de la zone climatique
    """
    logger = logging.getLogger(__name__)
    logger.info("Identification de la zone climatique")
    
    try:
        climate_zone = analyzer.get_climate_zone(geometry)
        logger.info(f"Zone climatique identifiée: {climate_zone.get('name', 'Inconnue')}")
        return climate_zone
    except Exception as e:
        logger.error(f"Erreur lors de l'identification de la zone climatique: {e}")
        return {
            "id": "unknown",
            "name": "Zone inconnue",
            "climate_type": "Inconnu",
            "annual_temp": 0,
            "annual_precip": 0,
            "summer_drought_days": 0,
            "frost_days": 0
        }

def get_species_recommendations(analyzer, geometry, scenarios=None):
    """
    Obtient des recommandations d'espèces pour différents scénarios climatiques.
    
    Args:
        analyzer: Instance de ClimateAnalyzer
        geometry: Géométrie de la parcelle
        scenarios: Liste des scénarios à analyser (par défaut: ["current", "2050_rcp45"])
        
    Returns:
        Dictionnaire contenant les recommandations par scénario
    """
    logger = logging.getLogger(__name__)
    
    if scenarios is None:
        scenarios = ["current", "2050_rcp45"]
    
    recommendations = {}
    
    for scenario in scenarios:
        logger.info(f"Recommandations pour le scénario {scenario}")
        try:
            # Obtenir les recommandations pour ce scénario
            scenario_recs = analyzer.recommend_species(
                geometry, 
                scenario=scenario,
                min_compatibility="suitable"
            )
            
            # Stocker les recommandations
            recommendations[scenario] = scenario_recs
            
            logger.info(f"Obtenu {len(scenario_recs)} recommandations")
            
            # Afficher les 3 premières recommandations
            for i, rec in enumerate(scenario_recs[:3], 1):
                logger.info(f"{i}. {rec['species_name']} ({rec['common_name']}) - Score: {rec['global_score']:.2f}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la recommandation pour le scénario {scenario}: {e}")
            recommendations[scenario] = []
    
    return recommendations

def analyze_climate_risks(analyzer, recommendations):
    """
    Analyse les risques climatiques des espèces recommandées.
    
    Args:
        analyzer: Instance de ClimateAnalyzer
        recommendations: Dictionnaire de recommandations par scénario
        
    Returns:
        Dictionnaire de risques analysés par scénario
    """
    logger = logging.getLogger(__name__)
    logger.info("Analyse des risques climatiques")
    
    risks_analysis = {}
    
    for scenario, recs in recommendations.items():
        # Compter les types de risques
        drought_risks = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
        frost_risks = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
        fire_risks = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
        
        for rec in recs:
            risks = rec.get("risks", {})
            
            # Risque de sécheresse
            drought_risk = risks.get("drought", "unknown")
            drought_risks[drought_risk] = drought_risks.get(drought_risk, 0) + 1
            
            # Risque de gel
            frost_risk = risks.get("frost", "unknown")
            frost_risks[frost_risk] = frost_risks.get(frost_risk, 0) + 1
            
            # Risque d'incendie
            fire_risk = risks.get("fire", "unknown")
            fire_risks[fire_risk] = fire_risks.get(fire_risk, 0) + 1
        
        # Stocker les analyses de risques pour ce scénario
        risks_analysis[scenario] = {
            "drought_risks": drought_risks,
            "frost_risks": frost_risks,
            "fire_risks": fire_risks,
            "dominant_risks": {
                "drought": max(drought_risks.items(), key=lambda x: x[1])[0],
                "frost": max(frost_risks.items(), key=lambda x: x[1])[0],
                "fire": max(fire_risks.items(), key=lambda x: x[1])[0]
            }
        }
        
        logger.info(f"Risques dominants pour {scenario}: "
                  f"Sécheresse: {risks_analysis[scenario]['dominant_risks']['drought']}, "
                  f"Gel: {risks_analysis[scenario]['dominant_risks']['frost']}, "
                  f"Feu: {risks_analysis[scenario]['dominant_risks']['fire']}")
    
    return risks_analysis

def compare_climate_scenarios(recommendations):
    """
    Compare les recommandations entre différents scénarios climatiques.
    
    Args:
        recommendations: Dictionnaire contenant les recommandations par scénario
        
    Returns:
        Dictionnaire avec les résultats de la comparaison
    """
    logger = logging.getLogger(__name__)
    logger.info("Comparaison des scénarios climatiques")
    
    # S'assurer qu'il y a au moins deux scénarios à comparer
    if len(recommendations) < 2:
        logger.warning("Pas assez de scénarios pour effectuer une comparaison")
        return {}
    
    comparison = {
        "scenarios": list(recommendations.keys()),
        "species_overlap": {},
        "changes": {},
        "robust_species": []
    }
    
    # Extraire les espèces pour chaque scénario
    species_by_scenario = {}
    for scenario, recs in recommendations.items():
        species_by_scenario[scenario] = {rec["species_name"]: rec for rec in recs}
    
    # Identifier les espèces présentes dans tous les scénarios (robustes)
    if len(species_by_scenario) >= 2:
        # Commencer avec toutes les espèces du premier scénario
        first_scenario = list(species_by_scenario.keys())[0]
        robust = set(species_by_scenario[first_scenario].keys())
        
        # Intersectionner avec les espèces des autres scénarios
        for scenario in list(species_by_scenario.keys())[1:]:
            robust = robust.intersection(set(species_by_scenario[scenario].keys()))
        
        comparison["robust_species"] = list(robust)
        
        logger.info(f"Espèces robustes (présentes dans tous les scénarios): {len(comparison['robust_species'])}")
    
    # Analyser les changements entre les scénarios
    for i, scenario1 in enumerate(comparison["scenarios"]):
        for scenario2 in comparison["scenarios"][i+1:]:
            # Calculer l'intersection des espèces
            species1 = set(species_by_scenario[scenario1].keys())
            species2 = set(species_by_scenario[scenario2].keys())
            
            overlap = species1.intersection(species2)
            only_in_1 = species1 - species2
            only_in_2 = species2 - species1
            
            # Stocker les résultats
            key = f"{scenario1}_vs_{scenario2}"
            comparison["species_overlap"][key] = {
                "overlap_count": len(overlap),
                "overlap_percentage": len(overlap) / max(len(species1), len(species2)) * 100 if max(len(species1), len(species2)) > 0 else 0,
                "only_in_first": list(only_in_1),
                "only_in_second": list(only_in_2)
            }
            
            # Analyser les changements de score pour les espèces communes
            score_changes = []
            for species in overlap:
                score1 = species_by_scenario[scenario1][species]["global_score"]
                score2 = species_by_scenario[scenario2][species]["global_score"]
                change = {
                    "species": species,
                    "score_change": score2 - score1,
                    "percentage_change": (score2 - score1) / score1 * 100 if score1 > 0 else 0
                }
                score_changes.append(change)
            
            # Trier par changement absolu
            score_changes.sort(key=lambda x: abs(x["score_change"]), reverse=True)
            
            comparison["changes"][key] = {
                "score_changes": score_changes[:10],  # Top 10 des changements
                "average_change": sum(c["score_change"] for c in score_changes) / len(score_changes) if score_changes else 0
            }
            
            logger.info(f"Comparaison {scenario1} vs {scenario2}: "
                      f"{comparison['species_overlap'][key]['overlap_percentage']:.1f}% de chevauchement, "
                      f"changement moyen: {comparison['changes'][key]['average_change']:.2f}")
    
    return comparison

def batch_analyze_climate(parcels, analyzer=None):
    """
    Effectue une analyse climatique pour un ensemble de parcelles.
    
    Args:
        parcels: GeoDataFrame contenant les parcelles à analyser
        analyzer: Instance de ClimateAnalyzer (si None, en crée une nouvelle)
        
    Returns:
        Dictionnaire avec les résultats d'analyse par parcelle
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Analyse climatique groupée pour {len(parcels)} parcelles")
    
    # Créer l'analyseur s'il n'est pas fourni
    if analyzer is None:
        analyzer = init_climate_analyzer()
    
    results = {}
    
    for i, parcel in parcels.iterrows():
        parcel_id = parcel["id"]
        logger.info(f"Analyse climatique pour la parcelle {parcel_id} ({parcel['name']})")
        
        # Obtenir la zone climatique
        climate_zone = get_climate_zone_for_parcel(analyzer, parcel["geometry"])
        
        # Obtenir les recommandations d'espèces
        recommendations = get_species_recommendations(analyzer, parcel["geometry"])
        
        # Analyser les risques
        risks = analyze_climate_risks(analyzer, recommendations)
        
        # Stocker les résultats
        results[parcel_id] = {
            "climate_zone": climate_zone,
            "recommendations": recommendations,
            "risks": risks
        }
    
    return results

if __name__ == "__main__":
    # Test du module
    logger = setup_logging()
    logger.info("Test du module d'analyse climatique")
    
    # Importer le module de préparation des données
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_preparation import create_real_world_parcels
    
    # Créer des parcelles
    parcels = create_real_world_parcels()
    print(f"Parcelles créées: {len(parcels)}")
    
    # Initialiser l'analyseur climatique
    analyzer = init_climate_analyzer()
    
    # Effectuer une analyse groupée
    results = batch_analyze_climate(parcels, analyzer)
    print(f"Analyses effectuées: {len(results)}")
    
    # Afficher quelques résultats
    for parcel_id, result in results.items():
        print(f"\nParcelle: {parcel_id}")
        print(f"Zone climatique: {result['climate_zone']['name']}")
        print(f"Température moyenne: {result['climate_zone']['annual_temp']}°C")
        print(f"Espèces recommandées (climat actuel): "
              f"{', '.join([r['species_name'] for r in result['recommendations']['current'][:3]])}")
