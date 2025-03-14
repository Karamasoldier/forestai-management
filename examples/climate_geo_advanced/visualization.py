#!/usr/bin/env python3
"""
Module de visualisation pour les analyses forestières avancées.

Ce module contient les fonctions pour:
1. Créer des graphiques de comparaison d'espèces
2. Visualiser les risques climatiques
3. Générer des cartes et représentations spatiales
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from matplotlib.colors import LinearSegmentedColormap
import geopandas as gpd
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
    
    return config.get_logger("examples.climate_geo_advanced.visualization")

def generate_species_comparison_chart(recommendations, base_filename, output_dir):
    """
    Génère un graphique comparant les espèces recommandées pour différents scénarios climatiques.
    
    Args:
        recommendations: Dictionnaire des recommandations par scénario
        base_filename: Nom de base pour le fichier de sortie
        output_dir: Répertoire de sortie
    """
    logger = logging.getLogger(__name__)
    logger.info("Génération du graphique de comparaison des espèces")
    
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
    
    logger.info(f"Graphique comparatif généré: {chart_path}")
    
    return chart_path

def generate_risk_analysis_chart(risk_analysis, base_filename, output_dir):
    """
    Génère un graphique d'analyse des risques climatiques.
    
    Args:
        risk_analysis: Dictionnaire d'analyse des risques par scénario
        base_filename: Nom de base pour le fichier de sortie
        output_dir: Répertoire de sortie
    """
    logger = logging.getLogger(__name__)
    logger.info("Génération du graphique d'analyse des risques")
    
    # S'assurer qu'il y a des données pour au moins un scénario
    if not risk_analysis or not any(risk_analysis.values()):
        logger.warning("Pas de données d'analyse de risques disponibles")
        return None
    
    # Préparer les données
    scenarios = list(risk_analysis.keys())
    risk_types = ["drought", "frost", "fire"]
    risk_levels = ["low", "medium", "high", "unknown"]
    
    # Créer un DataFrame pour faciliter le tracé
    data = []
    
    for scenario in scenarios:
        scenario_risks = risk_analysis[scenario]
        
        for risk_type in risk_types:
            risk_key = f"{risk_type}_risks"
            if risk_key in scenario_risks:
                for level, count in scenario_risks[risk_key].items():
                    data.append({
                        "Scénario": scenario,
                        "Type de risque": risk_type.capitalize(),
                        "Niveau de risque": level.capitalize(),
                        "Nombre d'espèces": count
                    })
    
    df = pd.DataFrame(data)
    
    # Créer une figure pour chaque type de risque
    risk_names = {
        "drought": "Sécheresse",
        "frost": "Gel",
        "fire": "Incendie"
    }
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))
    
    for i, risk_type in enumerate(risk_types):
        risk_data = df[df["Type de risque"] == risk_type.capitalize()]
        if not risk_data.empty:
            # Créer un graphique empilé
            pivot_data = risk_data.pivot_table(
                index="Scénario",
                columns="Niveau de risque",
                values="Nombre d'espèces",
                aggfunc="sum"
            ).fillna(0)
            
            # Réordonner les colonnes pour avoir un ordre cohérent
            ordered_columns = [col for col in ["Low", "Medium", "High", "Unknown"] if col in pivot_data.columns]
            pivot_data = pivot_data[ordered_columns]
            
            # Tracer le graphique
            pivot_data.plot(
                kind="bar",
                stacked=True,
                ax=axes[i],
                colormap="RdYlGn_r"
            )
            
            axes[i].set_title(f"Risque de {risk_names[risk_type]}")
            axes[i].set_ylabel("Nombre d'espèces")
            axes[i].set_xlabel("")
            axes[i].grid(axis="y", linestyle="--", alpha=0.7)
    
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_path = output_dir / f"{base_filename}_risks.png"
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    logger.info(f"Graphique d'analyse des risques généré: {chart_path}")
    
    return chart_path

def generate_terrain_analysis_chart(terrain_data, base_filename, output_dir):
    """
    Génère un graphique d'analyse du terrain.
    
    Args:
        terrain_data: Dictionnaire avec les résultats d'analyse du terrain
        base_filename: Nom de base pour le fichier de sortie
        output_dir: Répertoire de sortie
    """
    logger = logging.getLogger(__name__)
    logger.info("Génération du graphique d'analyse du terrain")
    
    # Créer une figure avec plusieurs sous-graphiques
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # 1. Graphique d'élévation (haut gauche)
    if "terrain_analysis" in terrain_data and "elevation" in terrain_data["terrain_analysis"]:
        elevation = terrain_data["terrain_analysis"]["elevation"]
        axes[0, 0].bar(["Min", "Moyenne", "Max"], 
                      [elevation["min"], elevation["mean"], elevation["max"]],
                      color=["lightblue", "steelblue", "darkblue"])
        axes[0, 0].set_title("Élévation (m)")
        axes[0, 0].grid(axis="y", linestyle="--", alpha=0.7)
    else:
        axes[0, 0].text(0.5, 0.5, "Données d'élévation non disponibles", 
                       ha="center", va="center", fontsize=12)
    
    # 2. Graphique de pente (haut droite)
    if "terrain_analysis" in terrain_data and "slope" in terrain_data["terrain_analysis"]:
        slope = terrain_data["terrain_analysis"]["slope"]
        axes[0, 1].bar(["Min", "Moyenne", "Max"], 
                      [slope["min"], slope["mean"], slope["max"]],
                      color=["lightgreen", "forestgreen", "darkgreen"])
        axes[0, 1].set_title("Pente (°)")
        axes[0, 1].grid(axis="y", linestyle="--", alpha=0.7)
    else:
        axes[0, 1].text(0.5, 0.5, "Données de pente non disponibles", 
                       ha="center", va="center", fontsize=12)
    
    # 3. Graphique d'exposition (bas gauche)
    if "terrain_analysis" in terrain_data and "aspect" in terrain_data["terrain_analysis"]:
        aspect = terrain_data["terrain_analysis"]["aspect"]
        # Créer un diagramme polaire pour l'exposition
        axes[1, 0].remove()  # Supprimer l'axe actuel
        axes[1, 0] = fig.add_subplot(223, projection='polar')
        
        # Définir les angles pour chaque direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        angles = np.linspace(0, 2*np.pi, len(directions), endpoint=False)
        
        # Créer des valeurs basées sur l'exposition dominante
        values = np.ones(len(directions))
        try:
            idx = directions.index(aspect[:1] + aspect[1:].lower())
            values[idx] = 2  # Mettre en évidence l'exposition dominante
        except (ValueError, IndexError):
            pass
        
        # Tracé du diagramme polaire
        axes[1, 0].bar(angles, values, width=2*np.pi/len(directions), bottom=0.0, alpha=0.8)
        axes[1, 0].set_xticks(angles)
        axes[1, 0].set_xticklabels(directions)
        axes[1, 0].set_yticks([])
        axes[1, 0].set_title("Exposition dominante")
    else:
        axes[1, 0].text(0.5, 0.5, "Données d'exposition non disponibles", 
                       ha="center", va="center", fontsize=12)
    
    # 4. Graphique de couverture des sols (bas droite)
    if "land_cover" in terrain_data and "forest_percentage" in terrain_data["land_cover"]:
        # Créer un graphique en camembert pour la couverture forestière
        forest_pct = terrain_data["land_cover"]["forest_percentage"]
        other_pct = 100 - forest_pct
        
        axes[1, 1].pie([forest_pct, other_pct], 
                      labels=[f"Forêt ({forest_pct:.1f}%)", f"Autre ({other_pct:.1f}%)"],
                      colors=["forestgreen", "wheat"],
                      autopct="%1.1f%%",
                      startangle=90)
        axes[1, 1].set_title("Couverture des sols")
    else:
        axes[1, 1].text(0.5, 0.5, "Données de couverture des sols non disponibles", 
                       ha="center", va="center", fontsize=12)
    
    # Titre global
    plt.suptitle(f"Analyse du terrain - {terrain_data.get('name', 'Parcelle')}", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Ajuster pour le titre
    
    # Sauvegarder le graphique
    chart_path = output_dir / f"{base_filename}_terrain.png"
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    logger.info(f"Graphique d'analyse du terrain généré: {chart_path}")
    
    return chart_path

def generate_climate_analysis_chart(climate_zone, base_filename, output_dir):
    """
    Génère un graphique d'analyse climatique.
    
    Args:
        climate_zone: Dictionnaire avec les informations de zone climatique
        base_filename: Nom de base pour le fichier de sortie
        output_dir: Répertoire de sortie
    """
    logger = logging.getLogger(__name__)
    logger.info("Génération du graphique d'analyse climatique")
    
    # Vérifier si les données climatiques sont disponibles
    if not climate_zone or not all(key in climate_zone for key in ["annual_temp", "annual_precip", "summer_drought_days", "frost_days"]):
        logger.warning("Données climatiques insuffisantes pour générer un graphique")
        return None
    
    # Créer une figure avec plusieurs sous-graphiques
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Graphique de température (haut gauche)
    axes[0, 0].bar(["Température annuelle moyenne"], [climate_zone["annual_temp"]], color="orangered")
    axes[0, 0].set_title("Température (°C)")
    axes[0, 0].grid(axis="y", linestyle="--", alpha=0.7)
    axes[0, 0].set_ylim(0, max(30, climate_zone["annual_temp"] * 1.2))
    
    # 2. Graphique de précipitations (haut droite)
    axes[0, 1].bar(["Précipitations annuelles"], [climate_zone["annual_precip"]], color="royalblue")
    axes[0, 1].set_title("Précipitations (mm)")
    axes[0, 1].grid(axis="y", linestyle="--", alpha=0.7)
    axes[0, 1].set_ylim(0, max(1500, climate_zone["annual_precip"] * 1.2))
    
    # 3. Graphique de jours de sécheresse (bas gauche)
    axes[1, 0].bar(["Jours de sécheresse estivale"], [climate_zone["summer_drought_days"]], color="darkorange")
    axes[1, 0].set_title("Jours de sécheresse")
    axes[1, 0].grid(axis="y", linestyle="--", alpha=0.7)
    axes[1, 0].set_ylim(0, max(120, climate_zone["summer_drought_days"] * 1.2))
    
    # 4. Graphique de jours de gel (bas droite)
    axes[1, 1].bar(["Jours de gel"], [climate_zone["frost_days"]], color="lightblue")
    axes[1, 1].set_title("Jours de gel")
    axes[1, 1].grid(axis="y", linestyle="--", alpha=0.7)
    axes[1, 1].set_ylim(0, max(120, climate_zone["frost_days"] * 1.2))
    
    # Titre global
    plt.suptitle(f"Analyse climatique - {climate_zone.get('name', 'Zone climatique')}", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Ajuster pour le titre
    
    # Sauvegarder le graphique
    chart_path = output_dir / f"{base_filename}_climate.png"
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    logger.info(f"Graphique d'analyse climatique généré: {chart_path}")
    
    return chart_path

def generate_potential_gauge_chart(integrated_analysis, base_filename, output_dir):
    """
    Génère un graphique en jauge pour le potentiel global.
    
    Args:
        integrated_analysis: Dictionnaire contenant l'analyse intégrée
        base_filename: Nom de base pour le fichier de sortie
        output_dir: Répertoire de sortie
    """
    logger = logging.getLogger(__name__)
    logger.info("Génération du graphique en jauge pour le potentiel global")
    
    # Obtenir le score global et la classe
    score = integrated_analysis.get("overall_score", 0)
    score_class = integrated_analysis.get("overall_class", "Inconnu")
    
    # Créer une figure avec un subplot polaire
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, polar=True)
    
    # Paramètres pour la jauge
    N = 100  # Nombre de divisions
    theta = np.linspace(0, np.pi, N)  # Demi-cercle
    width = np.pi / N
    radii = np.ones_like(theta)
    
    # Palette de couleurs pour la jauge
    cmap = LinearSegmentedColormap.from_list("custom", ["tomato", "gold", "yellowgreen", "forestgreen"])
    
    # Tracé des segments colorés de la jauge
    bars = ax.bar(theta, radii, width=width, bottom=0.3, alpha=0.8)
    
    # Coloration des segments basée sur la position (rouge à gauche, vert à droite)
    for i, bar in enumerate(bars):
        bar.set_facecolor(cmap(i / N))
    
    # Limites des axes et ajustements des labels
    ax.set_rlim(0, 1.4)
    ax.set_rticks([])
    ax.set_xticks([0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi])
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1.0"])
    
    # Flèche indiquant le score
    arrow_angle = score * np.pi
    ax.annotate("",
                xy=(arrow_angle, 0.9),
                xytext=(arrow_angle, 0.4),
                arrowprops=dict(facecolor="black", width=2, headwidth=8),
                ha="center", va="center")
    
    # Texte avec le score et la classe
    plt.text(np.pi/2, 0.1, f"Score: {score:.2f}", ha="center", fontsize=14)
    plt.text(np.pi/2, 0, f"Classe: {score_class}", ha="center", fontsize=14, fontweight="bold")
    
    # Enlever les lignes et bordures inutiles
    ax.spines["polar"].set_visible(False)
    ax.set_theta_zero_location("W")
    ax.set_theta_direction(-1)  # Sens horaire
    
    # Ajouter un titre
    plt.title("Potentiel forestier global", fontsize=16, pad=20)
    
    # Sauvegarder le graphique
    chart_path = output_dir / f"{base_filename}_gauge.png"
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    logger.info(f"Graphique en jauge généré: {chart_path}")
    
    return chart_path

def generate_all_charts(terrain_data, climate_zone, recommendations, risk_analysis, integrated_analysis, base_filename, output_dir):
    """
    Génère tous les graphiques pour une parcelle.
    
    Args:
        terrain_data: Données d'analyse du terrain
        climate_zone: Informations sur la zone climatique
        recommendations: Recommandations d'espèces par scénario
        risk_analysis: Analyse des risques climatiques
        integrated_analysis: Analyse intégrée
        base_filename: Nom de base pour les fichiers de sortie
        output_dir: Répertoire de sortie
        
    Returns:
        Dictionnaire contenant les chemins vers les graphiques générés
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Génération de tous les graphiques pour {base_filename}")
    
    # S'assurer que le répertoire de sortie existe
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer les différents graphiques
    charts = {}
    
    # 1. Graphique de comparaison des espèces
    if recommendations:
        charts["species_comparison"] = generate_species_comparison_chart(
            recommendations, base_filename, output_dir
        )
    
    # 2. Graphique d'analyse des risques
    if risk_analysis:
        charts["risk_analysis"] = generate_risk_analysis_chart(
            risk_analysis, base_filename, output_dir
        )
    
    # 3. Graphique d'analyse du terrain
    if terrain_data:
        charts["terrain_analysis"] = generate_terrain_analysis_chart(
            terrain_data, base_filename, output_dir
        )
    
    # 4. Graphique d'analyse climatique
    if climate_zone:
        charts["climate_analysis"] = generate_climate_analysis_chart(
            climate_zone, base_filename, output_dir
        )
    
    # 5. Graphique en jauge pour le potentiel global
    if integrated_analysis:
        charts["potential_gauge"] = generate_potential_gauge_chart(
            integrated_analysis, base_filename, output_dir
        )
    
    logger.info(f"Génération terminée. {len(charts)} graphiques créés.")
    
    return charts

if __name__ == "__main__":
    # Test du module
    logger = setup_logging()
    logger.info("Test du module de visualisation")
    
    # Importer les modules nécessaires pour le test
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_preparation import create_real_world_parcels, create_output_directories
    from climate_analysis import init_climate_analyzer, get_climate_zone_for_parcel, get_species_recommendations, analyze_climate_risks
    from geo_analysis import simulate_detailed_geo_analysis
    
    # Créer des parcelles et des répertoires de sortie
    parcels = create_real_world_parcels()
    parcel = parcels.iloc[0]  # Utiliser la première parcelle pour cet exemple
    output_dirs = create_output_directories("data/outputs/test_visualization")
    
    print(f"Parcelle sélectionnée: {parcel['name']} ({parcel['region']})")
    
    # Obtenir les analyses de terrain et climatiques
    analyzer = init_climate_analyzer()
    terrain_data = simulate_detailed_geo_analysis(parcel)
    climate_zone = get_climate_zone_for_parcel(analyzer, parcel["geometry"])
    recommendations = get_species_recommendations(analyzer, parcel["geometry"])
    risk_analysis = analyze_climate_risks(analyzer, recommendations)
    
    # Créer une analyse intégrée de test
    integrated_analysis = {
        "overall_score": 0.75,
        "overall_class": "Très bon",
        "recommendations": [
            "Privilégier les espèces adaptées à l'humidité",
            "Prévoir des coupures de combustible"
        ]
    }
    
    # Générer tous les graphiques
    base_filename = f"{parcel['id']}_{parcel['name'].replace(' ', '_')}"
    charts = generate_all_charts(
        terrain_data,
        climate_zone,
        recommendations,
        risk_analysis,
        integrated_analysis,
        base_filename,
        output_dirs["charts"]
    )
    
    # Afficher les graphiques générés
    for chart_type, chart_path in charts.items():
        print(f"Graphique {chart_type}: {chart_path}")
