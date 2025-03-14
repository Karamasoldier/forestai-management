#!/usr/bin/env python3
"""
Module de génération de rapports pour les analyses forestières avancées.

Ce module contient les fonctions pour:
1. Générer des rapports détaillés au format JSON, TXT et autres formats
2. Combiner les résultats des analyses géospatiales et climatiques
3. Exporter les données pour utilisation externe
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
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
    
    return config.get_logger("examples.climate_geo_advanced.reports")

def generate_advanced_report(geo_analysis, climate_zone, recommendations, output_dir):
    """
    Génère un rapport avancé combinant analyses géospatiales et climatiques.
    
    Args:
        geo_analysis: Résultats de l'analyse géospatiale
        climate_zone: Informations sur la zone climatique
        recommendations: Recommandations d'espèces par scénario
        output_dir: Répertoire de sortie pour le rapport
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Génération d'un rapport avancé pour {geo_analysis.get('id', 'inconnu')}")
    
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
    
    logger.info(f"Rapport JSON généré: {json_path}")
    
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
    
    logger.info(f"Rapport texte généré: {txt_path}")
    
    return combined_analysis

def export_combined_results_to_csv(results, output_dir):
    """
    Exporte les résultats combinés au format CSV pour utilisation externe.
    
    Args:
        results: Liste des résultats d'analyse combinée
        output_dir: Répertoire de sortie
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Exportation des résultats combinés au format CSV")
    
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
    
    logger.info(f"Export CSV généré: {csv_path}")
    
    return csv_path

def generate_markdown_report(combined_analysis, charts=None, output_dir=None):
    """
    Génère un rapport au format Markdown intégrant des liens vers les graphiques.
    
    Args:
        combined_analysis: Résultat d'analyse combinée
        charts: Dictionnaire des chemins vers les graphiques générés
        output_dir: Répertoire de sortie (si différent de celui des graphiques)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Génération d'un rapport au format Markdown")
    
    # Déterminer le répertoire de sortie
    if output_dir is None and charts:
        # Utiliser le répertoire du premier graphique
        chart_path = next(iter(charts.values()))
        output_dir = chart_path.parent
    
    output_dir = Path(output_dir) if output_dir else Path("data/outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Créer le contenu Markdown
    md_content = f"# Rapport d'analyse forestière - {combined_analysis['parcel']['name']}\n\n"
    
    # Informations de base
    md_content += f"**ID de la parcelle**: {combined_analysis['parcel']['id']}  \n"
    md_content += f"**Région**: {combined_analysis['parcel']['region']}  \n"
    md_content += f"**Surface**: {combined_analysis['parcel']['area_ha']:.2f} hectares  \n"
    md_content += f"**Date du rapport**: {combined_analysis['report_id'].split('-')[-1]}  \n\n"
    
    # Score global
    md_content += f"## Score global: {combined_analysis['integrated_analysis']['overall_score']:.2f}/1.00 ({combined_analysis['integrated_analysis']['overall_class']})\n\n"
    
    # Ajouter le graphique en jauge si disponible
    if charts and "potential_gauge" in charts:
        gauge_path = charts["potential_gauge"]
        md_content += f"![Potentiel forestier global]({gauge_path.name})\n\n"
    
    # Analyse du terrain
    md_content += "## Analyse géospatiale\n\n"
    
    if charts and "terrain_analysis" in charts:
        terrain_path = charts["terrain_analysis"]
        md_content += f"![Analyse du terrain]({terrain_path.name})\n\n"
    
    md_content += "### Caractéristiques du terrain\n\n"
    md_content += "| Paramètre | Valeur |\n"
    md_content += "| --- | --- |\n"
    md_content += f"| **Sol** | {combined_analysis['geo_analysis']['soil_analysis']['type']}, pH {combined_analysis['geo_analysis']['soil_analysis']['ph']:.1f} |\n"
    md_content += f"| **Élévation moyenne** | {combined_analysis['geo_analysis']['terrain_analysis']['elevation']['mean']:.1f} m |\n"
    md_content += f"| **Pente moyenne** | {combined_analysis['geo_analysis']['terrain_analysis']['slope']['mean']:.1f}° |\n"
    md_content += f"| **Exposition dominante** | {combined_analysis['geo_analysis']['terrain_analysis']['aspect']} |\n"
    md_content += f"| **Couvert forestier** | {combined_analysis['geo_analysis']['land_cover']['forest_percentage']:.1f}% ({combined_analysis['geo_analysis']['land_cover']['dominant']}) |\n\n"
    
    md_content += "### Contraintes et opportunités\n\n"
    
    md_content += "**Contraintes identifiées**:\n"
    for constraint in combined_analysis['geo_analysis']['forestry_potential']['constraints']:
        md_content += f"- {constraint}\n"
    md_content += "\n"
    
    md_content += "**Opportunités identifiées**:\n"
    for opportunity in combined_analysis['geo_analysis']['forestry_potential']['opportunities']:
        md_content += f"- {opportunity}\n"
    md_content += "\n"
    
    # Analyse climatique
    md_content += "## Analyse climatique\n\n"
    
    if charts and "climate_analysis" in charts:
        climate_path = charts["climate_analysis"]
        md_content += f"![Analyse climatique]({climate_path.name})\n\n"
    
    md_content += "### Caractéristiques climatiques\n\n"
    md_content += "| Paramètre | Valeur |\n"
    md_content += "| --- | --- |\n"
    md_content += f"| **Zone climatique** | {combined_analysis['climate']['zone']['name']} ({combined_analysis['climate']['zone']['climate_type']}) |\n"
    md_content += f"| **Température annuelle** | {combined_analysis['climate']['zone']['annual_temp']}°C |\n"
    md_content += f"| **Précipitations** | {combined_analysis['climate']['zone']['annual_precip']} mm/an |\n"
    md_content += f"| **Jours de sécheresse estivale** | {combined_analysis['climate']['zone']['summer_drought_days']} |\n"
    md_content += f"| **Jours de gel** | {combined_analysis['climate']['zone']['frost_days']} |\n\n"
    
    # Analyse des risques
    if charts and "risk_analysis" in charts:
        risk_path = charts["risk_analysis"]
        md_content += "### Analyse des risques climatiques\n\n"
        md_content += f"![Analyse des risques]({risk_path.name})\n\n"
    
    # Recommandations d'espèces
    md_content += "## Recommandations d'espèces\n\n"
    
    if charts and "species_comparison" in charts:
        species_path = charts["species_comparison"]
        md_content += f"![Comparaison des espèces]({species_path.name})\n\n"
    
    md_content += "### Climat actuel\n\n"
    md_content += "| Espèce | Score | Compatibilité | Risques |\n"
    md_content += "| --- | --- | --- | --- |\n"
    
    for rec in combined_analysis["climate"]["current_recommendations"]:
        risks = f"Sécheresse: {rec['risks'].get('drought', 'inconnu')}, "
        risks += f"Gel: {rec['risks'].get('frost', 'inconnu')}, "
        risks += f"Feu: {rec['risks'].get('fire', 'inconnu')}"
        
        md_content += f"| **{rec['species_name']}** ({rec['common_name']}) | {rec['global_score']:.2f} | {rec['compatibility']} | {risks} |\n"
    
    md_content += "\n### Climat 2050 (RCP 4.5)\n\n"
    md_content += "| Espèce | Score | Compatibilité |\n"
    md_content += "| --- | --- | --- |\n"
    
    for rec in combined_analysis["climate"]["future_recommendations"]:
        md_content += f"| **{rec['species_name']}** ({rec['common_name']}) | {rec['global_score']:.2f} | {rec['compatibility']} |\n"
    
    # Recommandations de gestion
    md_content += "\n## Recommandations de gestion\n\n"
    
    for rec in combined_analysis['integrated_analysis']['recommendations']:
        md_content += f"- {rec}\n"
    
    # Sauvegarder le fichier Markdown
    base_filename = f"{combined_analysis['report_id']}_{combined_analysis['parcel']['name'].replace(' ', '_')}"
    md_path = output_dir / f"{base_filename}.md"
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    logger.info(f"Rapport Markdown généré: {md_path}")
    
    return md_path

def batch_generate_reports(geo_analyses, climate_analyses, combined_recommendations, output_dirs, include_charts=True):
    """
    Génère des rapports pour plusieurs parcelles.
    
    Args:
        geo_analyses: Liste des analyses géospatiales par parcelle
        climate_analyses: Liste des analyses climatiques par parcelle
        combined_recommendations: Liste des recommandations combinées par parcelle
        output_dirs: Dictionnaire des répertoires de sortie
        include_charts: Booléen indiquant si des graphiques doivent être générés
        
    Returns:
        Dictionnaire des rapports générés par parcelle
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Génération en lots de rapports pour {len(geo_analyses)} parcelles")
    
    # Importer les modules uniquement si nécessaire
    if include_charts:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from visualization import generate_all_charts
    
    reports = {}
    combined_results = []
    
    for parcel_id, geo_analysis in geo_analyses.items():
        logger.info(f"Génération de rapport pour la parcelle {parcel_id}")
        
        # Récupérer les données climatiques correspondantes
        if parcel_id not in climate_analyses:
            logger.warning(f"Pas d'analyse climatique disponible pour la parcelle {parcel_id}")
            continue
        
        climate_data = climate_analyses[parcel_id]
        
        # Récupérer les recommandations combinées
        combined_recs = combined_recommendations.get(parcel_id, None)
        
        # Générer des graphiques si demandé
        charts = None
        if include_charts:
            # Préparer le nom de base du fichier
            base_filename = f"{parcel_id}_{geo_analysis['name'].replace(' ', '_')}"
            
            # Générer tous les graphiques
            integrated_analysis = {
                "overall_score": 0.0,  # Sera calculé dans generate_advanced_report
                "overall_class": ""
            }
            
            charts = generate_all_charts(
                geo_analysis,
                climate_data["climate_zone"],
                climate_data["recommendations"],
                climate_data.get("risks", {}),
                integrated_analysis,
                base_filename,
                output_dirs["charts"]
            )
        
        # Générer le rapport avancé
        combined_analysis = generate_advanced_report(
            geo_analysis,
            climate_data["climate_zone"],
            climate_data["recommendations"],
            output_dirs["reports"]
        )
        
        # Mettre à jour les graphiques avec le score calculé si nécessaire
        if include_charts and "potential_gauge" in charts:
            from visualization import generate_potential_gauge_chart
            generate_potential_gauge_chart(
                combined_analysis["integrated_analysis"],
                f"{parcel_id}_{geo_analysis['name'].replace(' ', '_')}",
                output_dirs["charts"]
            )
        
        # Générer le rapport Markdown
        generate_markdown_report(
            combined_analysis,
            charts,
            output_dirs["reports"]
        )
        
        # Stocker le résultat pour l'export CSV
        combined_results.append(combined_analysis)
        
        # Stocker le rapport par parcelle
        reports[parcel_id] = {
            "combined_analysis": combined_analysis,
            "charts": charts
        }
    
    # Exporter les résultats combinés au format CSV
    if combined_results:
        export_combined_results_to_csv(combined_results, output_dirs["csv"])
    
    logger.info(f"Génération de rapports terminée pour {len(reports)} parcelles")
    
    return reports

if __name__ == "__main__":
    # Test du module
    logger = setup_logging()
    logger.info("Test du module de génération de rapports")
    
    # Importer les modules nécessaires pour le test
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_preparation import create_real_world_parcels, create_output_directories
    from climate_analysis import init_climate_analyzer, batch_analyze_climate
    from geo_analysis import batch_analyze_parcels
    
    # Créer des parcelles et des répertoires de sortie
    parcels = create_real_world_parcels()
    output_dirs = create_output_directories("data/outputs/test_reports")
    
    print(f"Parcelles créées: {len(parcels)}")
    
    # Obtenir les analyses géospatiales et climatiques
    geo_analyses = {result["id"]: result for result in batch_analyze_parcels(parcels)}
    analyzer = init_climate_analyzer()
    climate_analyses = batch_analyze_climate(parcels, analyzer)
    
    # Générer des rapports pour toutes les parcelles
    reports = batch_generate_reports(
        geo_analyses,
        climate_analyses,
        {},  # Pas de recommandations combinées pour ce test
        output_dirs
    )
    
    print(f"Rapports générés: {len(reports)}")
    for parcel_id, report_data in reports.items():
        print(f"Parcelle {parcel_id}: Score global {report_data['combined_analysis']['integrated_analysis']['overall_score']:.2f} ({report_data['combined_analysis']['integrated_analysis']['overall_class']})")
