#!/usr/bin/env python3
"""
Exemple d'intégration du module d'analyse climatique avec le GeoAgent.

Cet exemple montre comment:
1. Utiliser le module ClimateAnalyzer pour obtenir des recommandations climatiques
2. Intégrer ces recommandations avec les analyses géospatiales du GeoAgent
3. Générer un rapport combiné contenant les deux types d'analyses
"""

import os
import sys
import json
import logging
from pathlib import Path
from shapely.geometry import box
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules nécessaires
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
    
    return config.get_logger("examples.climate_geo")

def create_test_geometries():
    """Crée quelques géométries de test pour différentes régions de France."""
    # Coordonnées Lambert 93 pour différentes régions de France
    regions = {
        "Bretagne": box(200000, 6800000, 250000, 6850000),
        "Alsace": box(1000000, 6800000, 1050000, 6850000),
        "Provence": box(850000, 6250000, 900000, 6300000),
        "Alpes": box(950000, 6400000, 1000000, 6450000),
        "Centre": box(600000, 6650000, 650000, 6700000)
    }
    
    # Créer un GeoDataFrame
    gdf = gpd.GeoDataFrame(
        {"region": list(regions.keys())},
        geometry=list(regions.values()),
        crs="EPSG:2154"
    )
    
    print(f"Créé {len(gdf)} géométries de test représentant différentes régions de France")
    
    return gdf

def simulate_geo_agent_analysis(geometry, region_name):
    """
    Simule une analyse de terrain avec le GeoAgent.
    
    Dans un cas réel, cela utiliserait les modules du GeoAgent pour analyser
    les contraintes de terrain, l'accessibilité, etc.
    """
    # Simulation de l'analyse du GeoAgent
    geo_analysis = {
        "region": region_name,
        "area_ha": geometry.area / 10000,
        "forestry_potential": {}
    }
    
    # Simuler différentes contraintes et opportunités selon la région
    if region_name == "Bretagne":
        geo_analysis["forestry_potential"] = {
            "potential_score": 0.78,
            "potential_class": "Bon",
            "constraints": ["exposition_aux_vents", "humidité_élevée"],
            "opportunities": ["bonne_pluviométrie", "sols_fertiles"],
            "accessibility": "Bonne"
        }
    elif region_name == "Alsace":
        geo_analysis["forestry_potential"] = {
            "potential_score": 0.82,
            "potential_class": "Très bon",
            "constraints": ["proximité_agricole"],
            "opportunities": ["relief_plat", "réseau_routier_dense"],
            "accessibility": "Excellente"
        }
    elif region_name == "Provence":
        geo_analysis["forestry_potential"] = {
            "potential_score": 0.65,
            "potential_class": "Moyen",
            "constraints": ["sécheresse_estivale", "risque_incendie_élevé", "sol_sec"],
            "opportunities": ["exposition_sud", "climat_doux"],
            "accessibility": "Moyenne"
        }
    elif region_name == "Alpes":
        geo_analysis["forestry_potential"] = {
            "potential_score": 0.71,
            "potential_class": "Bon",
            "constraints": ["pente_forte", "enneigement_hivernal", "risque_avalanche"],
            "opportunities": ["protection_contre_érosion", "tourisme"],
            "accessibility": "Difficile"
        }
    else:  # Centre
        geo_analysis["forestry_potential"] = {
            "potential_score": 0.85,
            "potential_class": "Excellent",
            "constraints": ["urbanisation_proche"],
            "opportunities": ["bonne_desserte", "sols_profonds", "climat_tempéré"],
            "accessibility": "Très bonne"
        }
    
    return geo_analysis

def generate_combined_report(geo_analysis, climate_recommendations, climate_zone, output_dir):
    """
    Génère un rapport combiné intégrant les analyses géospatiales et climatiques.
    
    Args:
        geo_analysis: Résultats de l'analyse géospatiale
        climate_recommendations: Recommandations d'espèces adaptées au climat
        climate_zone: Informations sur la zone climatique
        output_dir: Répertoire de sortie pour le rapport
    """
    # Créer le répertoire de sortie
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Combiner les analyses
    combined_analysis = {
        "region": geo_analysis["region"],
        "area_ha": geo_analysis["area_ha"],
        "geo_analysis": geo_analysis,
        "climate": {
            "zone": climate_zone,
            "current_recommendations": climate_recommendations["current"][:5],
            "future_recommendations": climate_recommendations["2050_rcp45"][:5]
        },
        "integrated_analysis": {
            "overall_score": (geo_analysis["forestry_potential"]["potential_score"] + 
                             0.7 * climate_recommendations["current"][0]["global_score"] + 
                             0.3 * climate_recommendations["2050_rcp45"][0]["global_score"]) / 2,
            "notes": []
        }
    }
    
    # Ajouter des notes d'analyse intégrée
    constraints = geo_analysis["forestry_potential"]["constraints"]
    
    if "pente_forte" in constraints:
        combined_analysis["integrated_analysis"]["notes"].append(
            "Choisir des essences adaptées aux pentes fortes pour limiter l'érosion"
        )
    if "sécheresse_estivale" in constraints or "sol_sec" in constraints:
        combined_analysis["integrated_analysis"]["notes"].append(
            "Privilégier les essences résistantes à la sécheresse pour anticiper le changement climatique"
        )
    if "risque_incendie_élevé" in constraints:
        combined_analysis["integrated_analysis"]["notes"].append(
            "Éviter les essences hautement inflammables et prévoir des coupures de combustible"
        )
    
    # Classifier le résultat global
    overall_score = combined_analysis["integrated_analysis"]["overall_score"]
    if overall_score >= 0.8:
        combined_analysis["integrated_analysis"]["overall_class"] = "Excellent"
    elif overall_score >= 0.7:
        combined_analysis["integrated_analysis"]["overall_class"] = "Très bon"
    elif overall_score >= 0.6:
        combined_analysis["integrated_analysis"]["overall_class"] = "Bon"
    elif overall_score >= 0.5:
        combined_analysis["integrated_analysis"]["overall_class"] = "Moyen"
    else:
        combined_analysis["integrated_analysis"]["overall_class"] = "Faible"
    
    # Sauvegarder au format JSON
    json_path = output_dir / f"rapport_{geo_analysis['region']}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"Rapport JSON généré: {json_path}")
    
    # Générer un rapport texte formaté
    txt_path = output_dir / f"rapport_{geo_analysis['region']}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"RAPPORT D'ANALYSE FORESTIÈRE - {geo_analysis['region']}\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Surface analysée: {geo_analysis['area_ha']:.2f} hectares\n")
        f.write(f"Potentiel forestier: {geo_analysis['forestry_potential']['potential_class']} ({geo_analysis['forestry_potential']['potential_score']:.2f}/1.00)\n")
        f.write(f"Accessibilité: {geo_analysis['forestry_potential']['accessibility']}\n\n")
        
        f.write("CONTRAINTES TERRAIN:\n")
        for constraint in geo_analysis['forestry_potential']['constraints']:
            f.write(f"- {constraint}\n")
        f.write("\n")
        
        f.write("OPPORTUNITÉS TERRAIN:\n")
        for opportunity in geo_analysis['forestry_potential']['opportunities']:
            f.write(f"- {opportunity}\n")
        f.write("\n")
        
        f.write("CLIMAT:\n")
        f.write(f"Zone climatique: {climate_zone['name']} ({climate_zone['climate_type']})\n")
        f.write(f"Température annuelle: {climate_zone['annual_temp']}°C\n")
        f.write(f"Précipitations: {climate_zone['annual_precip']} mm\n")
        f.write(f"Jours de sécheresse estivale: {climate_zone['summer_drought_days']}\n")
        f.write(f"Jours de gel: {climate_zone['frost_days']}\n\n")
        
        f.write("ESSENCES RECOMMANDÉES (CLIMAT ACTUEL):\n")
        for i, rec in enumerate(climate_recommendations["current"][:5], 1):
            f.write(f"{i}. {rec['species_name']} ({rec['common_name']}) - Score: {rec['global_score']:.2f}\n")
        f.write("\n")
        
        f.write("ESSENCES RECOMMANDÉES (CLIMAT 2050):\n")
        for i, rec in enumerate(climate_recommendations["2050_rcp45"][:5], 1):
            f.write(f"{i}. {rec['species_name']} ({rec['common_name']}) - Score: {rec['global_score']:.2f}\n")
        f.write("\n")
        
        f.write("ANALYSE INTÉGRÉE:\n")
        f.write(f"Score global: {combined_analysis['integrated_analysis']['overall_score']:.2f} - {combined_analysis['integrated_analysis']['overall_class']}\n\n")
        
        f.write("RECOMMANDATIONS:\n")
        for note in combined_analysis['integrated_analysis']['notes']:
            f.write(f"- {note}\n")
    
    print(f"Rapport texte généré: {txt_path}")
    
    return combined_analysis

def visualize_recommendations(region_name, climate_recommendations, output_dir):
    """
    Génère une visualisation des recommandations d'espèces.
    
    Args:
        region_name: Nom de la région
        climate_recommendations: Recommandations d'espèces par scénario
        output_dir: Répertoire de sortie pour la visualisation
    """
    try:
        # Créer le répertoire de sortie
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Préparer les données pour le graphique
        current_species = [rec["species_name"] for rec in climate_recommendations["current"][:5]]
        current_scores = [rec["global_score"] for rec in climate_recommendations["current"][:5]]
        
        future_species = [rec["species_name"] for rec in climate_recommendations["2050_rcp45"][:5]]
        future_scores = [rec["global_score"] for rec in climate_recommendations["2050_rcp45"][:5]]
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(current_species))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], current_scores, width, label='Climat actuel', color='#4285F4')
        
        # Ajouter les barres pour le scénario futur, en alignant les espèces identiques
        future_bars = []
        for species, score in zip(future_species, future_scores):
            if species in current_species:
                idx = current_species.index(species)
                future_bars.append((idx + width/2, score))
            else:
                # Ajouter à la fin si l'espèce n'est pas dans les recommandations actuelles
                future_bars.append((len(current_species) - 0.5 + len(future_bars) * 0.5, score))
        
        # Tracer les barres du scénario futur
        future_x = [i[0] for i in future_bars]
        future_y = [i[1] for i in future_bars]
        future_labels = [s if s not in current_species else "" for s in future_species]
        
        ax.bar(future_x, future_y, width, label='Climat 2050 (RCP 4.5)', color='#EA4335')
        
        # Ajouter les étiquettes, le titre et la légende
        ax.set_ylabel('Score global', fontsize=12)
        ax.set_title(f'Recommandations d\'espèces pour {region_name}', fontsize=14)
        ax.set_xticks(range(len(current_species)))
        ax.set_xticklabels(current_species, rotation=45, ha='right', fontsize=10)
        ax.legend()
        
        # Ajouter du texte pour les espèces futures qui ne sont pas dans les recommandations actuelles
        for x, y, label in zip(future_x, future_y, future_labels):
            if label:
                ax.text(x, y + 0.02, label, ha='center', va='bottom', rotation=45, fontsize=9, color='#EA4335')
        
        # Ajuster la mise en page
        fig.tight_layout()
        
        # Sauvegarder le graphique
        output_path = output_dir / f"recommandations_{region_name}.png"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print(f"Visualisation générée: {output_path}")
        
    except Exception as e:
        print(f"Erreur lors de la génération de la visualisation: {e}")

def main():
    """Fonction principale pour exécuter l'exemple d'intégration."""
    logger = setup_logging()
    logger.info("Démarrage de l'exemple d'intégration ClimateAnalyzer-GeoAgent")
    
    try:
        # Initialiser l'analyseur climatique
        analyzer = ClimateAnalyzer()
        print("Analyseur climatique initialisé")
        
        # Créer des géométries de test
        geometries = create_test_geometries()
        
        # Créer un répertoire pour les sorties
        output_dir = Path("data/outputs/climate_geo_integration")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analyser chaque région
        for idx, row in geometries.iterrows():
            region_name = row['region']
            geometry = row['geometry']
            
            print(f"\n=== Analyse de la région: {region_name} ===")
            
            # 1. Obtenir l'analyse géospatiale
            geo_analysis = simulate_geo_agent_analysis(geometry, region_name)
            print(f"Analyse géospatiale réalisée: Potentiel forestier {geo_analysis['forestry_potential']['potential_class']}")
            
            # 2. Obtenir l'analyse climatique
            climate_zone = analyzer.get_climate_zone(geometry)
            print(f"Zone climatique identifiée: {climate_zone.get('name', 'Inconnue')}")
            
            # 3. Obtenir les recommandations d'espèces pour différents scénarios
            climate_recommendations = {}
            
            # Climat actuel
            current_recommendations = analyzer.recommend_species(geometry, scenario="current")
            climate_recommendations["current"] = current_recommendations
            print(f"Recommandations pour le climat actuel: {len(current_recommendations)} espèces")
            
            # Climat futur (RCP 4.5, 2050)
            future_recommendations = analyzer.recommend_species(geometry, scenario="2050_rcp45")
            climate_recommendations["2050_rcp45"] = future_recommendations
            print(f"Recommandations pour le climat 2050 (RCP 4.5): {len(future_recommendations)} espèces")
            
            # 4. Générer un rapport combiné
            combined_report = generate_combined_report(
                geo_analysis, 
                climate_recommendations, 
                climate_zone, 
                output_dir
            )
            
            # 5. Visualiser les recommandations
            visualize_recommendations(region_name, climate_recommendations, output_dir)
            
        logger.info("Exemple d'intégration terminé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de l'exemple: {e}", exc_info=True)
        print(f"\nUne erreur s'est produite: {e}")

if __name__ == "__main__":
    main()
