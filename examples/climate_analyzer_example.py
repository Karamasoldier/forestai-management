#!/usr/bin/env python3
"""
Exemple d'utilisation du module d'analyse climatique (ClimateAnalyzer).

Cet exemple montre comment:
1. Initialiser l'analyseur climatique
2. Obtenir des informations sur une zone climatique
3. Recommander des espèces adaptées au climat actuel et futur
4. Comparer les recommandations entre différents scénarios climatiques
5. Intégrer l'analyse climatique avec le GeoAgent
"""

import os
import sys
import json
import logging
from pathlib import Path
from shapely.geometry import box
import geopandas as gpd

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer le module d'analyse climatique
from forestai.core.domain.services import ClimateAnalyzer
from forestai.core.utils.logging_config import LoggingConfig

def setup_logging():
    """Configure le système de logging."""
    config = LoggingConfig.get_instance()
    config.init({
        "level": "INFO",
        "log_dir": "logs/examples",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    return config.get_logger("examples.climate")

def create_test_geometry():
    """Crée une géométrie de test pour les exemples."""
    # Créer un simple rectangle en coordonnées Lambert 93
    minx, miny, maxx, maxy = 843000, 6278000, 844000, 6279000
    geometry = box(minx, miny, maxx, maxy)
    
    # Créer un GeoDataFrame
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geometry], crs="EPSG:2154")
    
    print(f"Géométrie de test créée: Rectangle de {geometry.area / 10000:.2f} hectares")
    
    return geometry

def example_basic_climate_analysis(analyzer, geometry):
    """Exemple d'analyse climatique de base pour une parcelle."""
    print("\n=== Exemple d'analyse climatique de base ===")
    
    # Obtenir la zone climatique
    climate_zone = analyzer.get_climate_zone(geometry)
    
    print(f"Zone climatique identifiée: {climate_zone['name']} (ID: {climate_zone['id']})")
    print(f"Type de climat: {climate_zone['climate_type']}")
    print(f"Température annuelle moyenne: {climate_zone['annual_temp']}°C")
    print(f"Précipitations annuelles: {climate_zone['annual_precip']} mm")
    print(f"Jours de sécheresse estivale: {climate_zone['summer_drought_days']}")
    print(f"Jours de gel: {climate_zone['frost_days']}")
    
    return climate_zone

def example_species_recommendations(analyzer, geometry):
    """Exemple de recommandation d'espèces adaptées."""
    print("\n=== Exemple de recommandation d'espèces adaptées ===")
    
    # Recommandation pour le climat actuel
    print("Recommandations pour le climat actuel:")
    current_recommendations = analyzer.recommend_species(geometry, scenario="current", min_compatibility="suitable")
    
    for i, rec in enumerate(current_recommendations[:3], 1):
        print(f"{i}. {rec['species_name']} ({rec['common_name']})")
        print(f"   - Score global: {rec['global_score']}")
        print(f"   - Compatibilité: {rec['compatibility']}")
        print(f"   - Valeur économique: {rec['economic_value']}")
        print(f"   - Valeur écologique: {rec['ecological_value']}")
        print(f"   - Vitesse de croissance: {rec['growth_rate']}")
    
    # Recommandation pour le climat futur (2050, RCP 4.5)
    print("\nRecommandations pour le climat futur (2050, scénario RCP 4.5):")
    future_recommendations = analyzer.recommend_species(geometry, scenario="2050_rcp45", min_compatibility="suitable")
    
    for i, rec in enumerate(future_recommendations[:3], 1):
        print(f"{i}. {rec['species_name']} ({rec['common_name']})")
        print(f"   - Score global: {rec['global_score']}")
        print(f"   - Compatibilité: {rec['compatibility']}")
    
    return current_recommendations, future_recommendations

def example_scenario_comparison(analyzer, geometry):
    """Exemple de comparaison entre différents scénarios climatiques."""
    print("\n=== Exemple de comparaison entre scénarios climatiques ===")
    
    # Comparer les scénarios
    scenarios = ["current", "2050_rcp45", "2050_rcp85"]
    comparison = analyzer.compare_scenarios(geometry, scenarios)
    
    # Afficher les différences de recommandations
    print("Comparaison des espèces recommandées par scénario:")
    
    for scenario in scenarios:
        print(f"\nScénario: {scenario}")
        if f"{scenario}_info" in comparison:
            info = comparison[f"{scenario}_info"]
            print(f"Description: {info.get('description', 'Inconnu')}")
        
        recommendations = comparison[scenario]
        for i, rec in enumerate(recommendations[:2], 1):
            print(f"{i}. {rec['species_name']} ({rec['common_name']}) - Score: {rec['global_score']}")
    
    # Identifier les espèces robustes au changement climatique
    print("\nEspèces robustes au changement climatique (recommandées dans tous les scénarios):")
    
    # Extraire les espèces de chaque scénario
    species_by_scenario = {
        scenario: [rec["species_name"] for rec in comparison[scenario]] 
        for scenario in scenarios
    }
    
    # Trouver les espèces présentes dans tous les scénarios
    robust_species = set(species_by_scenario[scenarios[0]])
    for scenario in scenarios[1:]:
        robust_species = robust_species.intersection(set(species_by_scenario[scenario]))
    
    for species in robust_species:
        print(f"- {species}")
    
    return comparison

def example_risk_filtering(analyzer, recommendations):
    """Exemple de filtrage des recommandations par risques."""
    print("\n=== Exemple de filtrage par risques ===")
    
    # Filtrer les espèces sensibles à la sécheresse et au feu
    excluded_risks = ["drought", "fire"]
    print(f"Filtrage des espèces sensibles à: {', '.join(excluded_risks)}")
    
    filtered_recommendations = analyzer.filter_recommendations_by_risks(
        recommendations, excluded_risks
    )
    
    print(f"Espèces avant filtrage: {len(recommendations)}")
    print(f"Espèces après filtrage: {len(filtered_recommendations)}")
    
    for i, rec in enumerate(filtered_recommendations[:3], 1):
        print(f"{i}. {rec['species_name']} ({rec['common_name']})")
        print(f"   - Risques: {rec['risks']}")
    
    return filtered_recommendations

def example_integration_with_bdtopo_loader():
    """Exemple d'intégration avec le BDTopoLoader."""
    print("\n=== Exemple d'intégration avec le BDTopoLoader ===")
    
    try:
        from forestai.agents.geo_agent.data_loaders.bdtopo import BDTopoLoader
        
        # Initialiser le loader et l'analyseur climatique
        loader = BDTopoLoader()
        analyzer = ClimateAnalyzer()
        
        # Créer une géométrie de test
        geometry = create_test_geometry()
        
        # Obtenir les résultats d'analyse de terrain
        terrain_analysis = loader.analyze_parcel(geometry, buffer_distance=100)
        print(f"Analyse de terrain réalisée: {terrain_analysis['area_ha']:.2f} hectares")
        
        # Obtenir les recommandations climatiques
        recommendations = analyzer.recommend_species(geometry, scenario="2050_rcp45")
        print(f"Recommandations climatiques obtenues: {len(recommendations)} espèces")
        
        # Filtrer les recommandations par les contraintes de terrain
        constraints = terrain_analysis.get("forestry_potential", {}).get("constraints", [])
        print(f"Contraintes identifiées: {len(constraints)}")
        
        if "pente_forte" in constraints:
            print("Filtrage des espèces pour pente forte")
            # Filtrer les espèces adaptées aux pentes fortes
            recommendations = [r for r in recommendations if r["species_name"] in ["Cedrus atlantica", "Pinus pinaster"]]
        
        if "sol_sec" in constraints:
            print("Filtrage des espèces pour sol sec")
            # Filtrer les espèces tolérantes à la sécheresse
            recommendations = [r for r in recommendations if r["risks"].get("drought") in ["low", "medium"]]
        
        # Afficher les recommandations finales
        print("\nRecommandations finales combinant terrain et climat:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec['species_name']} ({rec['common_name']})")
            print(f"   - Score global: {rec['global_score']}")
            print(f"   - Compatibilité: {rec['compatibility']}")
        
        # Enrichir les résultats terrain avec les données climatiques
        terrain_analysis["climate"] = {
            "zone": analyzer.get_climate_zone(geometry),
            "recommended_species": recommendations[:3]
        }
        
        # Sauvegarder les résultats enrichis
        output_dir = Path("data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "terrain_climate_analysis.json", "w", encoding="utf-8") as f:
            # Conversion des objets non sérialisables
            result = {k: v for k, v in terrain_analysis.items() if k != "geometry"}
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("\nAnalyse combinée sauvegardée dans data/outputs/terrain_climate_analysis.json")
        
    except ImportError as e:
        print(f"Impossible d'importer les modules nécessaires: {e}")
        print("Le BDTopoLoader est peut-être absent ou incomplet.")

def main():
    """Fonction principale pour exécuter les exemples."""
    logger = setup_logging()
    logger.info("Démarrage des exemples d'analyse climatique")
    
    try:
        # Initialiser l'analyseur climatique
        analyzer = ClimateAnalyzer()
        print("Analyseur climatique initialisé")
        
        # Créer une géométrie de test
        geometry = create_test_geometry()
        
        # Exemple d'analyse climatique de base
        climate_zone = example_basic_climate_analysis(analyzer, geometry)
        
        # Exemple de recommandation d'espèces
        current_recommendations, future_recommendations = example_species_recommendations(analyzer, geometry)
        
        # Exemple de comparaison entre scénarios
        comparison = example_scenario_comparison(analyzer, geometry)
        
        # Exemple de filtrage par risques
        filtered_recommendations = example_risk_filtering(analyzer, current_recommendations)
        
        # Exemple d'intégration avec le BDTopoLoader
        example_integration_with_bdtopo_loader()
        
        logger.info("Exemples d'analyse climatique terminés avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution des exemples: {e}", exc_info=True)
        print(f"\nUne erreur s'est produite: {e}")
    
if __name__ == "__main__":
    main()
