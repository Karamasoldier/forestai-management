#!/usr/bin/env python3
"""
Exemple avancé d'intégration du module d'analyse climatique avec le GeoAgent.

Cet exemple montre comment:
1. Utiliser les deux modules ensemble pour une analyse complète
2. Filtrer intelligemment les recommandations d'espèces en fonction des contraintes terrain
3. Générer des visualisations et rapports combinés
4. Exporter les données pour une utilisation dans d'autres systèmes
"""

import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from shapely.geometry import box, Point, Polygon
import geopandas as gpd

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
        "log_dir": "logs/advanced_example",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    return config.get_logger("examples.climate_geo_advanced")

def create_real_world_parcels():
    """
    Crée un ensemble de parcelles forestières basées sur des cas réels.
    
    Returns:
        GeoDataFrame avec les parcelles et leurs informations
    """
    # Définir quelques parcelles forestières fictives mais réalistes
    parcels_data = [
        {
            "id": "F001",
            "name": "Forêt de Brocéliande",
            "region": "Bretagne",
            "area_ha": 75.4,
            "soil_type": "argileux",
            "elevation_mean": 145,
            "slope_mean": 3.2,
            "constraints": ["humidité_élevée", "zone_touristique"],
            "geometry": Polygon([
                (350000, 6780000), (351500, 6780000), 
                (351500, 6781500), (350000, 6781500),
                (350000, 6780000)
            ])
        },
        {
            "id": "F002",
            "name": "Parcelle des Vosges",
            "region": "Grand Est",
            "area_ha": 32.7,
            "soil_type": "acide",
            "elevation_mean": 820,
            "slope_mean": 15.6,
            "constraints": ["pente_forte", "enneigement_hivernal"],
            "geometry": Polygon([
                (985000, 6790000), (986200, 6790000),
                (986200, 6791200), (985000, 6791200),
                (985000, 6790000)
            ])
        },
        {
            "id": "F003",
            "name": "Garrigue Méditerranéenne",
            "region": "Provence",
            "area_ha": 48.2,
            "soil_type": "calcaire",
            "elevation_mean": 280,
            "slope_mean": 8.4,
            "constraints": ["sécheresse_estivale", "risque_incendie_élevé", "sol_sec"],
            "geometry": Polygon([
                (850000, 6250000), (851200, 6250000),
                (851200, 6251000), (850000, 6251000),
                (850000, 6250000)
            ])
        },
        {
            "id": "F004",
            "name": "Plateau Central",
            "region": "Auvergne",
            "area_ha": 64.1,
            "soil_type": "limoneux",
            "elevation_mean": 520,
            "slope_mean": 6.3,
            "constraints": ["gel_tardif", "précipitations_variables"],
            "geometry": Polygon([
                (650000, 6500000), (651000, 6500000),
                (651000, 6501500), (650000, 6501500),
                (650000, 6500000)
            ])
        },
        {
            "id": "F005",
            "name": "Landes Atlantiques",
            "region": "Nouvelle-Aquitaine",
            "area_ha": 110.5,
            "soil_type": "sableux",
            "elevation_mean": 60,
            "slope_mean": 1.2,
            "constraints": ["nappe_phréatique_haute", "sols_pauvres"],
            "geometry": Polygon([
                (380000, 6400000), (382000, 6400000),
                (382000, 6402000), (380000, 6402000),
                (380000, 6400000)
            ])
        }
    ]
    
    # Créer un GeoDataFrame
    gdf = gpd.GeoDataFrame(parcels_data, crs="EPSG:2154")
    
    print(f"Créé {len(gdf)} parcelles forestières pour l'analyse")
    
    return gdf

def simulate_detailed_geo_analysis(parcel):
    """
    Simule une analyse géospatiale détaillée d'une parcelle.
    
    Dans un cas réel, cela utiliserait les modules du GeoAgent pour analyser
    la parcelle (BDTopoLoader, TerrainCoordinator, etc.)
    
    Args:
        parcel: Une ligne du GeoDataFrame de parcelles
        
    Returns:
        Dictionnaire avec les résultats de l'analyse géospatiale
    """
    # Simuler l'analyse du GeoAgent avec des valeurs réalistes
    geo_analysis = {
        "id": parcel["id"],
        "name": parcel["name"],
        "region": parcel["region"],
        "area_ha": parcel["area_ha"],
        "geometry": parcel["geometry"],
        "soil_analysis": {
            "type": parcel["soil_type"],
            "ph": np.random.uniform(4.5, 7.5),
            "organic_matter": np.random.uniform(1.0, 5.0)
        },
        "terrain_analysis": {
            "elevation": {
                "min": parcel["elevation_mean"] - np.random.uniform(10, 50),
                "max": parcel["elevation_mean"] + np.random.uniform(10, 50),
                "mean": parcel["elevation_mean"]
            },
            "slope": {
                "min": max(0, parcel["slope_mean"] - np.random.uniform(1, 5)),
                "max": parcel["slope_mean"] + np.random.uniform(1, 10),
                "mean": parcel["slope_mean"]
            },
            "aspect": np.random.choice(["North", "South", "East", "West", "Northeast", "Southeast", "Southwest", "Northwest"])
        },
        "hydrology": {
            "water_bodies": int(np.random.poisson(1)),
            "streams_length_m": np.random.uniform(0, 500),
            "distance_to_nearest_water_m": np.random.uniform(50, 2000)
        },
        "land_cover": {
            "dominant": np.random.choice(["Forêt mixte", "Forêt de conifères", "Forêt de feuillus", "Végétation arbustive"]),
            "forest_percentage": np.random.uniform(60, 95)
        },
        "infrastructure": {
            "roads_length_m": np.random.uniform(0, 1000),
            "distance_to_nearest_road_m": np.random.uniform(20, 1000),
            "buildings_count": int(np.random.poisson(0.5))
        },
        "forestry_potential": {
            "potential_score": np.random.uniform(0.55, 0.90),
            "constraints": parcel["constraints"],
            "opportunities": [
                np.random.choice(["bonne_accessibilité", "présence_cours_eau", "exposition_favorable"]),
                np.random.choice(["sol_adapté", "climat_tempéré", "protection_vent"])
            ]
        }
    }
    
    # Déterminer la classe de potentiel en fonction du score
    score = geo_analysis["forestry_potential"]["potential_score"]
    if score >= 0.80:
        geo_analysis["forestry_potential"]["potential_class"] = "Excellent"
    elif score >= 0.70:
        geo_analysis["forestry_potential"]["potential_class"] = "Très bon"
    elif score >= 0.60:
        geo_analysis["forestry_potential"]["potential_class"] = "Bon"
    elif score >= 0.50:
        geo_analysis["forestry_potential"]["potential_class"] = "Moyen"
    else:
        geo_analysis["forestry_potential"]["potential_class"] = "Faible"
    
    return geo_analysis

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
    # Copier les recommandations pour éviter de modifier l'original
    filtered_recs = recommendations.copy()
    
    # Règles de filtrage en fonction des contraintes terrain
    if "pente_forte" in constraints:
        # Garder les espèces avec un système racinaire profond pour stabiliser les pentes
        filtered_recs = [r for r in filtered_recs if r["species_name"] not in ["Fagus sylvatica"]]
        print("  - Filtrage pour pentes fortes appliqué")
    
    if "sécheresse_estivale" in constraints or "sol_sec" in constraints:
        # Filtrer pour garder uniquement les espèces résistantes à la sécheresse
        filtered_recs = [r for r in filtered_recs if r["risks"].get("drought") != "high"]
        print("  - Filtrage pour résistance à la sécheresse appliqué")
    
    if "risque_incendie_élevé" in constraints:
        # Préférer les espèces moins inflammables
        filtered_recs = [r for r in filtered_recs if r["risks"].get("fire") != "high"]
        print("  - Filtrage pour résistance au feu appliqué")
    
    if "gel_tardif" in constraints:
        # Préférer les espèces résistantes au gel
        filtered_recs = [r for r in filtered_recs if r["risks"].get("frost") != "high"]
        print("  - Filtrage pour résistance au gel appliqué")
    
    # Tenir compte de la pente moyenne pour les espèces sensibles
    if terrain_data["terrain_analysis"]["slope"]["mean"] > 15:
        filtered_recs = [r for r in filtered_recs if r["species_name"] not in ["Quercus robur"]]
        print("  - Filtrage pour forte pente moyenne appliqué")
    
    # Tenir compte de l'exposition pour certaines espèces
    aspect = terrain_data["terrain_analysis"]["aspect"]
    if aspect in ["South", "Southeast", "Southwest"]:
        # Exposition sud: favoriser les espèces thermophiles
        for rec in filtered_recs:
            if rec["species_name"] in ["Quercus pubescens", "Cedrus atlantica", "Pinus pinaster"]:
                rec["global_score"] *= 1.1  # Bonus de 10%
        print("  - Bonus pour exposition sud appliqué")
    
    # Recalculer les rangs en fonction des scores modifiés
    filtered_recs = sorted(filtered_recs, key=lambda x: x["global_score"], reverse=True)
    
    return filtered_recs

def generate_species_comparison_chart(recommendations, base_filename, output_dir):
    """
    Génère un graphique comparant les espèces recommandées pour différents scénarios climatiques.
    
    Args:
        recommendations: Dictionnaire des recommandations par scénario
        base_filename: Nom de base pour le fichier de sortie
        output_dir: Répertoire de sortie
    """
    # Préparer les données
    current_species = [f"{rec['species_name']} ({rec['common_name']})" for rec in recommendations["current"][:5]]
    current_scores = [rec["global_score"] for rec in recommendations["current"][:5]]
    
    future_species = [f"{rec['species_name']} ({rec['common_name']})" for rec in recommendations["2050_rcp45"][:5]]
    future_scores = [rec["global_score"] for rec in recommendations["2050_rcp45"][:5]]
    
    # Créer un DataFrame pour faciliter le tracé
    data = []
    
    for species, score in zip(current_species, current_scores):
        data.append({"Espèce": species, "Score": score, "Scénario": "Climat actuel"})
    
    for species, score in zip(future_species, future_scores):
        data.append({"Espèce": species, "Score": score, "Scénario": "Climat 2050 (RCP 4.5)"})
    
    df = pd.DataFrame(data)
    
    # Créer la figure
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x="Espèce", y="Score", hue="Scénario", data=df)
    
    # Personnaliser le graphique
    plt.title("Comparaison des espèces recommandées par scénario climatique", fontsize=14)
    plt.xlabel("Espèce", fontsize=12)
    plt.ylabel("Score global", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_path = output_dir / f"{base_filename}_comparison.png"
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"Graphique comparatif généré: {chart_path}")

def generate_advanced_report(geo_analysis, climate_zone, recommendations, output_dir):
    """
    Génère un rapport avancé combinant analyses géospatiales et climatiques.
    
    Args:
        geo_analysis: Résultats de l'analyse géospatiale
        climate_zone: Informations sur la zone climatique
        recommendations: Recommandations d'espèces par scénario
        output_dir: Répertoire de sortie pour le rapport
    """
    # Créer le répertoire de sortie
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Formater la date pour le nom de fichier
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Nom de base du fichier
    base_filename = f"{date_str}_{geo_analysis['id']}_{geo_analysis['name'].replace(' ', '_')}"
    
    # Générer le rapport JSON
    combined_analysis = {
        "report_id": f"REP-{geo_analysis['id']}-{date_str}",
        "parcel": {
            "id": geo_analysis["id"],
            "name": geo_analysis["name"],
            "region": geo_analysis["region"],
            "area_ha": geo_analysis["area_ha"]
        },
        "geo_analysis": geo_analysis,
        "climate": {
            "zone": climate_zone,
            "current_recommendations": recommendations["current"][:5],
            "future_recommendations": recommendations["2050_rcp45"][:5]
        },
        "integrated_analysis": {
            "overall_score": round(
                (geo_analysis["forestry_potential"]["potential_score"] * 0.5 +
                recommendations["current"][0]["global_score"] * 0.3 +
                recommendations["2050_rcp45"][0]["global_score"] * 0.2),
                2
            )
        }
    }
    
    # Déterminer la classe globale
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
    
    # Ajouter des recommandations personnalisées
    combined_analysis["integrated_analysis"]["recommendations"] = []
    
    # Basé sur les contraintes et les opportunités
    constraints = geo_analysis["forestry_potential"]["constraints"]
    opportunities = geo_analysis["forestry_potential"]["opportunities"]
    
    for constraint in constraints:
        if constraint == "pente_forte":
            combined_analysis["integrated_analysis"]["recommendations"].append(
                "Utiliser des techniques de plantation adaptées aux fortes pentes"
            )
        elif constraint in ["sécheresse_estivale", "sol_sec"]:
            combined_analysis["integrated_analysis"]["recommendations"].append(
                "Prévoir un système d'irrigation pendant la phase d'établissement"
            )
        elif constraint == "risque_incendie_élevé":
            combined_analysis["integrated_analysis"]["recommendations"].append(
                "Créer des coupures de combustible et maintenir un débroussaillage régulier"
            )
    
    # Recommandations basées sur le climat futur
    if recommendations["current"][0]["species_name"] != recommendations["2050_rcp45"][0]["species_name"]:
        combined_analysis["integrated_analysis"]["recommendations"].append(
            "Privilégier les espèces recommandées pour le climat futur pour anticiper le changement climatique"
        )
    
    # Sauvegarder au format JSON
    json_path = output_dir / f"{base_filename}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"Rapport JSON généré: {json_path}")
    
    # Générer un rapport texte formaté
    txt_path = output_dir / f"{base_filename}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"RAPPORT D'ANALYSE FORESTIÈRE - {geo_analysis['name']}\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"ID: {geo_analysis['id']}\n")
        f.write(f"Région: {geo_analysis['region']}\n")
        f.write(f"Surface: {geo_analysis['area_ha']:.2f} hectares\n\n")
        
        f.write("ANALYSE GÉOSPATIALE\n")
        f.write("-"*80 + "\n")
        f.write(f"Potentiel forestier: {geo_analysis['forestry_potential']['potential_class']} ({geo_analysis['forestry_potential']['potential_score']:.2f}/1.00)\n")
        f.write(f"Sol: {geo_analysis['soil_analysis']['type']}, pH {geo_analysis['soil_analysis']['ph']:.1f}, matière organique {geo_analysis['soil_analysis']['organic_matter']:.1f}%\n")
        f.write(f"Élévation moyenne: {geo_analysis['terrain_analysis']['elevation']['mean']:.1f} m\n")
        f.write(f"Pente moyenne: {geo_analysis['terrain_analysis']['slope']['mean']:.1f}°\n")
        f.write(f"Exposition dominante: {geo_analysis['terrain_analysis']['aspect']}\n")
        f.write(f"Couvert forestier: {geo_analysis['land_cover']['forest_percentage']:.1f}% ({geo_analysis['land_cover']['dominant']})\n\n")
        
        f.write("Contraintes identifiées:\n")
        for constraint in geo_analysis['forestry_potential']['constraints']:
            f.write(f"- {constraint}\n")
        f.write("\n")
        
        f.write("Opportunités identifiées:\n")
        for opportunity in geo_analysis['forestry_potential']['opportunities']:
            f.write(f"- {opportunity}\n")
        f.write("\n")
        
        f.write("ANALYSE CLIMATIQUE\n")
        f.write("-"*80 + "\n")
        f.write(f"Zone climatique: {climate_zone['name']} ({climate_zone['climate_type']})\n")
        f.write(f"Température annuelle: {climate_zone['annual_temp']}°C\n")
        f.write(f"Précipitations: {climate_zone['annual_precip']} mm/an\n")
        f.write(f"Jours de sécheresse estivale: {climate_zone['summer_drought_days']}\n")
        f.write(f"Jours de gel: {climate_zone['frost_days']}\n\n")
        
        f.write("RECOMMANDATIONS D'ESPÈCES\n")
        f.write("-"*80 + "\n")
        
        f.write("Climat actuel:\n")
        for i, rec in enumerate(recommendations["current"][:5], 1):
            f.write(f"{i}. {rec['species_name']} ({rec['common_name']})\n")
            f.write(f"   Score: {rec['global_score']:.2f} | Compatibilité: {rec['compatibility']}\n")
            f.write(f"   Risques: Sécheresse - {rec['risks'].get('drought', 'inconnu')}, Gel - {rec['risks'].get('frost', 'inconnu')}, Feu - {rec['risks'].get('fire', 'inconnu')}\n")
            f.write(f"   Valeur économique: {rec['economic_value']} | Valeur écologique: {rec['ecological_value']} | Croissance: {rec['growth_rate']}\n\n")
        
        f.write("Climat 2050 (RCP 4.5):\n")
        for i, rec in enumerate(recommendations["2050_rcp45"][:5], 1):
            f.write(f"{i}. {rec['species_name']} ({rec['common_name']})\n")
            f.write(f"   Score: {rec['global_score']:.2f} | Compatibilité: {rec['compatibility']}\n\n")
        
        f.write("ANALYSE INTÉGRÉE\n")
        f.write("-"*80 + "\n")
        f.write(f"Score global: {combined_analysis['integrated_analysis']['overall_score']:.2f}/1.00 ({combined_analysis['integrated_analysis']['overall_class']})\n\n")
        
        f.write("Recommandations de gestion:\n")
        for rec in combined_analysis['integrated_analysis']['recommendations']:
            f.write(f"- {rec}\n")
    
    print(f"Rapport texte généré: {txt_path}")
    
    # Générer un graphique comparatif des espèces recommandées
    try:
        generate_species_comparison_chart(recommendations, base_filename, output_dir)
    except Exception as e:
        print(f"Erreur lors de la génération du graphique: {e}")
    
    return combined_analysis

def export_combined_results_to_csv(results, output_dir):
    """
    Exporte les résultats combinés au format CSV pour utilisation externe.
    
    Args:
        results: Liste des résultats d'analyse combinée
        output_dir: Répertoire de sortie
    """
    # Créer le répertoire de sortie
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Préparation des données pour l'export CSV
    data = []
    
    for result in results:
        # Informations de base sur la parcelle
        parcel_data = {
            "report_id": result["report_id"],
            "parcel_id": result["parcel"]["id"],
            "parcel_name": result["parcel"]["name"],
            "region": result["parcel"]["region"],
            "area_ha": result["parcel"]["area_ha"],
            
            # Analyse géospatiale
            "geo_potential_score": result["geo_analysis"]["forestry_potential"]["potential_score"],
            "geo_potential_class": result["geo_analysis"]["forestry_potential"]["potential_class"],
            "soil_type": result["geo_analysis"]["soil_analysis"]["type"],
            "soil_ph": result["geo_analysis"]["soil_analysis"]["ph"],
            "elevation_mean": result["geo_analysis"]["terrain_analysis"]["elevation"]["mean"],
            "slope_mean": result["geo_analysis"]["terrain_analysis"]["slope"]["mean"],
            "aspect": result["geo_analysis"]["terrain_analysis"]["aspect"],
            "forest_percentage": result["geo_analysis"]["land_cover"]["forest_percentage"],
            
            # Analyse climatique
            "climate_zone": result["climate"]["zone"]["name"],
            "climate_type": result["climate"]["zone"]["climate_type"],
            "annual_temp": result["climate"]["zone"]["annual_temp"],
            "annual_precip": result["climate"]["zone"]["annual_precip"],
            
            # Analyse intégrée
            "overall_score": result["integrated_analysis"]["overall_score"],
            "overall_class": result["integrated_analysis"]["overall_class"]
        }
        
        # Ajouter les contraintes et opportunités comme colonnes
        for i, constraint in enumerate(result["geo_analysis"]["forestry_potential"]["constraints"], 1):
            parcel_data[f"constraint_{i}"] = constraint
        
        for i, opportunity in enumerate(result["geo_analysis"]["forestry_potential"]["opportunities"], 1):
            parcel_data[f"opportunity_{i}"] = opportunity
        
        # Ajouter les recommandations comme colonnes
        for i, recommendation in enumerate(result["integrated_analysis"].get("recommendations", []), 1):
            parcel_data[f"recommendation_{i}"] = recommendation
        
        # Ajouter les espèces recommandées pour le climat actuel
        for i, rec in enumerate(result["climate"]["current_recommendations"], 1):
            parcel_data[f"current_species_{i}"] = rec["species_name"]
            parcel_data[f"current_species_{i}_score"] = rec["global_score"]
        
        # Ajouter les espèces recommandées pour le climat futur
        for i, rec in enumerate(result["climate"]["future_recommendations"], 1):
            parcel_data[f"future_species_{i}"] = rec["species_name"]
            parcel_data[f"future_species_{i}_score"] = rec["global_score"]
        
        data.append(parcel_data)
    
    # Créer un DataFrame
    df = pd.DataFrame(data)
    
    # Exporter au format CSV
    csv_path = output_dir / "parcelles_analyses_combinées.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    
    print(f"Export CSV généré: {csv_path}")