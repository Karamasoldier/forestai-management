#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation du module sanitaire et de génération de rapports sanitaires.

Cet exemple montre comment:
1. Utiliser l'analyseur sanitaire (HealthAnalyzer) pour évaluer l'état sanitaire
2. Générer un rapport sanitaire complet avec différents formats de sortie
"""

import os
import sys
from pathlib import Path
import logging
import datetime

# Ajouter le répertoire parent au path pour importer les modules du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forestai.agents.diagnostic_agent.health import HealthAnalyzer
from forestai.agents.diagnostic_agent.report_generator.report_manager import ReportManager, ReportFormat, ReportType

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Fonction principale démontrant l'utilisation du module sanitaire
    et la génération de rapports d'analyse sanitaire.
    """
    # Chemin de sortie pour les rapports
    output_dir = Path("./output/examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Créer un exemple de données d'inventaire
    inventory_data = {
        "items": [
            {
                "id": "1",
                "species": "Pinus sylvestris",
                "common_name": "Pin sylvestre",
                "diameter": 25.0,
                "height": 15.0,
                "health_status": "Moyen",
                "foliage_loss": 0.25,
                "discoloration": 0.15,
                "symptoms": ["défoliation", "jaunissement"]
            },
            {
                "id": "2",
                "species": "Pinus sylvestris",
                "common_name": "Pin sylvestre",
                "diameter": 32.0,
                "height": 18.0,
                "health_status": "Bon",
                "foliage_loss": 0.05,
                "discoloration": 0.0,
                "symptoms": []
            },
            {
                "id": "3",
                "species": "Quercus robur",
                "common_name": "Chêne pédonculé",
                "diameter": 45.0,
                "height": 22.0,
                "health_status": "Mauvais",
                "foliage_loss": 0.40,
                "discoloration": 0.30,
                "symptoms": ["défoliation", "taches_foliaires", "galles"]
            }
        ]
    }
    
    # 2. Observation de symptômes supplémentaires
    additional_symptoms = {
        "presence_insectes": True,
        "types_insectes": ["scolytes", "chenilles processionnaires"],
        "presence_champignons": True,
        "types_champignons": ["oïdium"],
        "observations_generales": "Signes d'attaque de scolytes sur plusieurs pins. Présence d'oïdium sur les chênes."
    }
    
    # 3. Données climatiques de contexte
    climate_data = {
        "current_climate": {
            "temperature_avg": 12.5,
            "precipitation_annual": 750,
            "drought_index": 0.65
        },
        "projections_2050": {
            "temperature_avg": 14.2,
            "precipitation_annual": 680,
            "drought_index": 0.85
        }
    }
    
    # 4. Informations sur la parcelle
    parcel_data = {
        "parcel_id": "B123456",
        "parcel_area": 12.5,
        "parcel_commune": "Saint-Martin-de-Crau",
        "parcel_owner": "Jean Forestier",
        "forest_type": "Mixte - pins et chênes",
        "parcel_exposition": "Sud-Ouest"
    }
    
    # 5. Initialiser l'analyseur de santé
    logger.info("Initialisation de l'analyseur sanitaire...")
    analyzer = HealthAnalyzer()
    
    # 6. Exécuter l'analyse sanitaire
    logger.info("Analyse sanitaire en cours...")
    health_analysis = analyzer.analyze_health(
        inventory_data,
        additional_symptoms,
        climate_data
    )
    
    # 7. Afficher les résultats principaux
    logger.info(f"Analyse sanitaire terminée. Score de santé global: {health_analysis['overall_health_score']:.1f}/10")
    logger.info(f"État sanitaire: {health_analysis['health_status']}")
    logger.info(f"Résumé: {health_analysis['summary']}")
    
    # 8. Initialiser le gestionnaire de rapports
    logger.info("Initialisation du gestionnaire de rapports...")
    report_manager = ReportManager({
        "output_dir": output_dir,
        "company_info": {
            "name": "ForestAI Services",
            "contact": "contact@forestai.com",
            "website": "www.forestai.fr"
        }
    })
    
    # 9. Générer un rapport sanitaire spécifique
    logger.info("Génération du rapport sanitaire spécifique...")
    
    # Formats à générer
    formats = [ReportFormat.PDF, ReportFormat.HTML, ReportFormat.TXT, ReportFormat.JSON]
    
    # Génération du rapport sanitaire
    health_report_files = report_manager.generate_health_report(
        health_analysis,
        formats,
        parcel_data,
        output_dir,
        f"sante_forestiere_{parcel_data['parcel_id']}"
    )
    
    # 10. Générer un rapport de diagnostic incluant les données sanitaires
    logger.info("Génération du rapport de diagnostic complet avec section sanitaire...")
    
    # Création d'un diagnostic complet incluant les données sanitaires
    diagnostic_data = {
        "title": f"Diagnostic forestier - Parcelle {parcel_data['parcel_id']}",
        "subtitle": "État des lieux et recommandations",
        "date": datetime.datetime.now().strftime("%d/%m/%Y"),
        "summary": "Ce diagnostic présente l'état global de la parcelle forestière, incluant les aspects dendrométriques, climatiques et sanitaires.",
        "parcel_id": parcel_data["parcel_id"],
        "parcel_area": parcel_data["parcel_area"],
        "parcel_commune": parcel_data["parcel_commune"],
        "parcel_owner": parcel_data["parcel_owner"],
        "forest_type": parcel_data["forest_type"],
        "parcel_exposition": parcel_data["parcel_exposition"],
        
        # Inclure les données d'analyse sanitaire
        "health_analysis": health_analysis,
        
        # Ajouter un résumé pour l'inventaire
        "inventory_analysis": {
            "summary": {
                "total_trees": len(inventory_data["items"]),
                "unique_species": len(set(item["species"] for item in inventory_data["items"]))
            },
            "species_analysis": {
                "Pinus sylvestris": {
                    "count": 2,
                    "percentage": 66.7,
                    "diameter": {"mean": 28.5, "min": 25.0, "max": 32.0},
                    "height": {"mean": 16.5, "min": 15.0, "max": 18.0}
                },
                "Quercus robur": {
                    "count": 1,
                    "percentage": 33.3,
                    "diameter": {"mean": 45.0, "min": 45.0, "max": 45.0},
                    "height": {"mean": 22.0, "min": 22.0, "max": 22.0}
                }
            }
        },
        
        # Ajouter l'analyse climatique
        "climate_analysis": {
            "current": climate_data["current_climate"],
            "future": climate_data["projections_2050"]
        },
        
        # Recommandations (incluant automatiquement celles de l'analyse sanitaire)
        "recommendations": {
            "species": [
                {
                    "name": "Quercus pubescens",
                    "climate_score": 5,
                    "productivity_score": 3,
                    "comments": "Bien adapté aux conditions locales et futures"
                },
                {
                    "name": "Pinus pinea",
                    "climate_score": 4,
                    "productivity_score": 4,
                    "comments": "Résistant à la sécheresse, remplace avantageusement le pin sylvestre"
                }
            ],
            "operations": [
                {
                    "name": "Éclaircie sanitaire",
                    "priority": "Élevée",
                    "timeframe": "Automne 2025",
                    "description": "Retirer les arbres présentant des signes d'infestation par les scolytes"
                },
                {
                    "name": "Plantation diversifiée",
                    "priority": "Moyenne",
                    "timeframe": "Hiver 2025-2026",
                    "description": "Introduire de nouvelles espèces plus résistantes au changement climatique"
                }
            ]
        }
    }
    
    # Générer le rapport de diagnostic complet
    diagnostic_report_files = report_manager.generate_diagnostic_report(
        diagnostic_data,
        [ReportFormat.PDF, ReportFormat.HTML],
        None,  # Pas besoin de données parcellaires additionnelles car déjà incluses
        output_dir,
        f"diagnostic_complet_{parcel_data['parcel_id']}",
        "complet"  # Niveau de détail maximal pour les sections sanitaires
    )
    
    # 11. Afficher les chemins des rapports générés
    logger.info("Rapports générés avec succès:")
    for fmt, file_path in health_report_files.items():
        logger.info(f"- Rapport sanitaire ({fmt.value}): {file_path}")
    
    for fmt, file_path in diagnostic_report_files.items():
        logger.info(f"- Diagnostic complet ({fmt.value}): {file_path}")
    
    logger.info("Exemple terminé.")

if __name__ == "__main__":
    main()
