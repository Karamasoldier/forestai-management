#!/usr/bin/env python3
"""
Programme principal pour l'analyse forestière avancée.

Ce programme orchestre l'ensemble du processus d'analyse:
1. Préparation des données
2. Analyse géospatiale
3. Analyse climatique
4. Recommandations d'espèces
5. Visualisations
6. Génération de rapports
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importer les modules locaux
from data_preparation import create_real_world_parcels, create_output_directories, setup_logging
from geo_analysis import batch_analyze_parcels
from climate_analysis import init_climate_analyzer, batch_analyze_climate
from recommendation_engine import process_parcel_recommendations
from visualization import generate_all_charts
from report_generator import batch_generate_reports

def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="Programme d'analyse forestière avancée")
    
    parser.add_argument("--output-dir", type=str, default="data/outputs/climate_geo_advanced",
                        help="Répertoire de sortie pour les résultats")
    
    parser.add_argument("--parcels", type=str, nargs="+", default=None,
                        help="IDs des parcelles à analyser (par défaut: toutes)")
    
    parser.add_argument("--no-charts", action="store_true",
                        help="Désactiver la génération de graphiques")
    
    parser.add_argument("--economic-priority", type=float, default=1.0,
                        help="Priorité économique pour les recommandations d'espèces (défaut: 1.0)")
    
    parser.add_argument("--ecological-priority", type=float, default=1.0,
                        help="Priorité écologique pour les recommandations d'espèces (défaut: 1.0)")
    
    parser.add_argument("--adaptation-weight", type=float, default=0.3,
                        help="Poids d'adaptation au changement climatique (défaut: 0.3)")
    
    parser.add_argument("--report-format", type=str, choices=["all", "json", "txt", "md", "csv"], default="all",
                        help="Format des rapports à générer (défaut: all)")
    
    parser.add_argument("--verbose", action="store_true", 
                        help="Activer les messages de débogage détaillés")
    
    return parser.parse_args()

def main():
    """Fonction principale."""
    # Analyser les arguments
    args = parse_arguments()
    
    # Configurer le logging
    logger = setup_logging()
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    logger.info("Démarrage de l'analyse forestière avancée")
    
    # Créer les répertoires de sortie
    output_dirs = create_output_directories(args.output_dir)
    logger.info(f"Répertoires de sortie créés sous {args.output_dir}")
    
    # 1. Créer ou charger les parcelles
    parcels = create_real_world_parcels()
    
    # Filtrer les parcelles si spécifié
    if args.parcels:
        parcels = parcels[parcels["id"].isin(args.parcels)]
        logger.info(f"Filtrage des parcelles: {len(parcels)} parcelles sélectionnées")
    
    logger.info(f"Nombre total de parcelles à analyser: {len(parcels)}")
    
    # 2. Exécuter l'analyse géospatiale
    logger.info("Démarrage de l'analyse géospatiale...")
    geo_analyses = {result["id"]: result for result in batch_analyze_parcels(parcels)}
    logger.info(f"Analyse géospatiale terminée pour {len(geo_analyses)} parcelles")
    
    # 3. Initialiser l'analyseur climatique
    logger.info("Initialisation de l'analyseur climatique...")
    climate_analyzer = init_climate_analyzer()
    
    # 4. Exécuter l'analyse climatique
    logger.info("Démarrage de l'analyse climatique...")
    climate_analyses = batch_analyze_climate(parcels, climate_analyzer)
    logger.info(f"Analyse climatique terminée pour {len(climate_analyses)} parcelles")
    
    # 5. Traiter les recommandations avec les priorités spécifiées
    logger.info("Traitement des recommandations d'espèces...")
    
    priorities = {
        "economic": args.economic_priority,
        "ecological": args.ecological_priority,
        "adaptation": args.adaptation_weight
    }
    
    combined_recommendations = {}
    for parcel_id, geo_analysis in geo_analyses.items():
        if parcel_id in climate_analyses:
            climate_data = climate_analyses[parcel_id]
            combined_recommendations[parcel_id] = process_parcel_recommendations(
                geo_analysis,
                climate_data["recommendations"],
                priorities
            )
    
    logger.info(f"Recommandations combinées générées pour {len(combined_recommendations)} parcelles")
    
    # 6. Générer les rapports
    logger.info("Génération des rapports...")
    reports = batch_generate_reports(
        geo_analyses,
        climate_analyses,
        combined_recommendations,
        output_dirs,
        not args.no_charts
    )
    logger.info(f"Rapports générés pour {len(reports)} parcelles")
    
    # 7. Afficher un résumé
    logger.info("\nRésumé des analyses:")
    for parcel_id, report_data in reports.items():
        logger.info(f"Parcelle {parcel_id} ({geo_analyses[parcel_id]['name']}):")
        logger.info(f"  - Score géospatial: {geo_analyses[parcel_id]['forestry_potential']['potential_score']:.2f}")
        logger.info(f"  - Score climatique: {climate_analyses[parcel_id]['recommendations']['current'][0]['global_score']:.2f}")
        logger.info(f"  - Score global: {report_data['combined_analysis']['integrated_analysis']['overall_score']:.2f} ({report_data['combined_analysis']['integrated_analysis']['overall_class']})")
    
    # 8. Indiquer où trouver les résultats
    logger.info(f"\nTous les résultats ont été enregistrés dans {args.output_dir}")
    logger.info(f"  - Rapports: {output_dirs['reports']}")
    if not args.no_charts:
        logger.info(f"  - Graphiques: {output_dirs['charts']}")
    logger.info(f"  - Données CSV: {output_dirs['csv']}")
    logger.info(f"  - Données JSON: {output_dirs['json']}")
    
    logger.info("Analyse forestière avancée terminée avec succès!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.getLogger(__name__).error(f"Erreur lors de l'exécution: {e}", exc_info=True)
        sys.exit(1)
