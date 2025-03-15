#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation du DiagnosticAgent pour l'analyse d'inventaire forestier
et la génération de plans de gestion.

Cet exemple montre comment :
1. Charger des données d'inventaire
2. Générer un diagnostic
3. Créer un plan de gestion avec différents objectifs
4. Produire des rapports au format HTML et PDF
"""

import os
import json
import pandas as pd
from pathlib import Path

# Importer les composants ForestAI
from forestai.agents.diagnostic_agent import DiagnosticAgent
from forestai.agents.geo_agent import GeoAgent
from forestai.core.domain.services.climate_analyzer import ClimateAnalyzer

# Création des répertoires de sortie
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Configuration des agents
diagnostic_agent = DiagnosticAgent({
    "output_dir": str(output_dir),
    "data_dir": "data/diagnostic"
})

geo_agent = GeoAgent()
climate_analyzer = ClimateAnalyzer()

def main():
    """Exemple principal d'utilisation du DiagnosticAgent"""
    print("\n=== Exemple d'utilisation du DiagnosticAgent ===\n")
    
    # 1. Chargement d'un inventaire forestier d'exemple
    print("1. Chargement des données d'inventaire...")
    inventory_data = load_sample_inventory()
    print(f"   - Inventaire chargé avec {len(inventory_data['items'])} arbres sur {inventory_data['area']} hectares")
    
    # 2. Analyse de l'inventaire
    print("\n2. Analyse de l'inventaire forestier...")
    inventory_analysis = diagnostic_agent.inventory_analyzer.analyze(inventory_data)
    
    # Affichage des résultats
    print("   - Statistiques de base :")
    print(f"     - Nombre total d'arbres : {inventory_analysis['basic_metrics']['total_trees']}")
    print(f"     - Nombre d'espèces : {inventory_analysis['basic_metrics']['species_count']}")
    print(f"     - Densité : {inventory_analysis['basic_metrics']['density']['trees_per_ha']:.1f} arbres/ha")
    
    print("   - Distribution des espèces :")
    for species, data in inventory_analysis['basic_metrics']['species_distribution'].items():
        print(f"     - {species}: {data['count']} arbres ({data['percent']:.1f}%)")
        
    if 'diversity' in inventory_analysis:
        print("   - Indices de diversité :")
        print(f"     - Indice de Shannon : {inventory_analysis['diversity']['shannon_index']:.2f}")
        print(f"     - Indice de Simpson : {inventory_analysis['diversity']['simpson_index']:.2f}")
    
    if 'volumes' in inventory_analysis:
        print("   - Volumes :")
        print(f"     - Volume total : {inventory_analysis['volumes']['total_volume_m3']:.2f} m³")
        print("     - Volume par espèce :")
        for species, volume in inventory_analysis['volumes']['by_species'].items():
            print(f"       - {species}: {volume['total_m3']:.2f} m³ ({volume['percent_of_total']:.1f}%)")
    
    # 3. Génération d'un diagnostic complet (simulation avec ID de parcelle fictif)
    print("\n3. Génération d'un diagnostic forestier...")
    parcel_id = "123456789"
    
    # Simuler une requête à GeoAgent et ClimateAnalyzer (en situation réelle)
    # Ces données seraient obtenues des services réels
    parcel_data = {
        "parcel_id": parcel_id,
        "geometry": {"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]], "crs": "EPSG:2154"},
        "area": inventory_data["area"],
        "elevation": {"min": 350, "max": 425, "mean": 385},
        "slope": {"min": 0, "max": 15, "mean": 5},
        "soil": {"type": "brunisol", "ph": 5.8, "depth": "medium"}
    }
    
    climate_data = {
        "data": {
            "temperature": {
                "annual_mean": 10.5,
                "monthly": [2.1, 3.5, 7.2, 9.8, 14.2, 17.5, 19.6, 19.1, 15.8, 11.3, 6.4, 3.2]
            },
            "precipitation": {
                "annual_mean": 850,
                "monthly": [85, 68, 72, 78, 92, 65, 52, 62, 75, 95, 102, 89]
            }
        },
        "summary": {
            "climate_type": "Continental tempéré",
            "risk_level": "Modéré",
            "description": "Climat continental tempéré avec étés modérément chauds et hivers froids. Précipitations bien réparties sur l'année avec légère sécheresse estivale."
        }
    }
    
    # Génération du diagnostic
    diagnostic = {
        "parcel_id": parcel_id,
        "parcel_data": parcel_data,
        "climate": climate_data,
        "inventory": inventory_analysis,
        "species_recommendations": {
            "recommended_species": [
                {
                    "species_name": "Quercus petraea",
                    "overall_suitability": 0.85,
                    "suitability": {"climate": 0.90, "soil": 0.82, "production": 0.88, "resilience": 0.76},
                    "comments": "Très bonne adéquation aux conditions locales actuelles et futures"
                },
                {
                    "species_name": "Pinus sylvestris",
                    "overall_suitability": 0.78,
                    "suitability": {"climate": 0.75, "soil": 0.85, "production": 0.82, "resilience": 0.72},
                    "comments": "Bonne résistance à la sécheresse, adéquation au sol"
                },
                {
                    "species_name": "Fagus sylvatica",
                    "overall_suitability": 0.68,
                    "suitability": {"climate": 0.65, "soil": 0.75, "production": 0.64, "resilience": 0.50},
                    "comments": "Attention aux risques liés aux sécheresses estivales futures"
                }
            ]
        },
        "potential": {
            "overall_score": 0.72,
            "production_score": 0.78,
            "biodiversity_score": 0.65,
            "resilience_score": 0.68
        },
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    print("   - Diagnostic généré avec succès")
    
    # 4. Génération d'un plan de gestion
    print("\n4. Génération d'un plan de gestion...")
    management_plan = generate_sample_management_plan(parcel_id, diagnostic)
    print(f"   - Plan de gestion généré avec {len(management_plan['phases'])} phases sur {management_plan['horizon']['duration_years']} ans")
    
    # 5. Export des rapports
    print("\n5. Génération des rapports...")
    
    # Export du diagnostic en HTML
    diagnostic_html_path = output_dir / "diagnostic_report.html"
    with open(diagnostic_html_path, "w", encoding="utf-8") as f:
        f.write(diagnostic_agent.report_generator.generate_diagnostic_report_html(diagnostic, parcel_data))
    print(f"   - Rapport de diagnostic HTML exporté vers: {diagnostic_html_path}")
    
    # Export du plan de gestion en HTML
    plan_html_path = output_dir / "management_plan_report.html"
    with open(plan_html_path, "w", encoding="utf-8") as f:
        f.write(diagnostic_agent.report_generator.generate_management_plan_report_html(management_plan, diagnostic))
    print(f"   - Rapport de plan de gestion HTML exporté vers: {plan_html_path}")
    
    try:
        # Tentative d'export PDF (selon disponibilité de WeasyPrint ou pdfkit)
        plan_pdf_path = output_dir / "management_plan_report.pdf"
        with open(plan_pdf_path, "wb") as f:
            f.write(diagnostic_agent.report_generator.generate_management_plan_report_pdf(management_plan, diagnostic))
        print(f"   - Rapport de plan de gestion PDF exporté vers: {plan_pdf_path}")
    except Exception as e:
        print(f"   - Export PDF non disponible: {str(e)}")
    
    print("\nExécution terminée. Les rapports sont disponibles dans le répertoire: {}".format(output_dir))

def load_sample_inventory():
    """Charge un inventaire forestier d'exemple pour la démonstration."""
    return {
        "area": 5.2,  # Surface en hectares
        "area_unit": "ha",
        "inventory_date": "2025-02-15",
        "items": [
            # Pins sylvestres
            *[{"species": "Pinus sylvestris", "diameter": 32.5 + i*0.8, "height": 18.2 + i*0.1, "health_status": "healthy"} for i in range(20)],
            *[{"species": "Pinus sylvestris", "diameter": 24.8 + i*0.7, "height": 16.5 + i*0.1, "health_status": "healthy"} for i in range(15)],
            *[{"species": "Pinus sylvestris", "diameter": 18.2 + i*0.5, "height": 12.8 + i*0.1, "health_status": "stressed", "health_issue": "drought"} for i in range(10)],
            
            # Chênes rouvres
            *[{"species": "Quercus petraea", "diameter": 45.2 + i*1.1, "height": 22.5 + i*0.2, "health_status": "healthy"} for i in range(12)],
            *[{"species": "Quercus petraea", "diameter": 38.6 + i*0.9, "height": 20.1 + i*0.1, "health_status": "healthy"} for i in range(8)],
            *[{"species": "Quercus petraea", "diameter": 28.4 + i*0.8, "height": 17.4 + i*0.1, "health_status": "stressed"} for i in range(5)],
            
            # Hêtres
            *[{"species": "Fagus sylvatica", "diameter": 35.6 + i*0.7, "height": 19.8 + i*0.1, "health_status": "healthy"} for i in range(18)],
            *[{"species": "Fagus sylvatica", "diameter": 28.1 + i*0.6, "height": 16.2 + i*0.1, "health_status": "stressed", "health_issue": "drought"} for i in range(7)],
            *[{"species": "Fagus sylvatica", "diameter": 22.3 + i*0.5, "height": 14.3 + i*0.1, "health_status": "damaged", "health_issue": "bark beetle"} for i in range(3)],
            
            # Erables
            *[{"species": "Acer pseudoplatanus", "diameter": 28.4 + i*0.6, "height": 16.8 + i*0.1, "health_status": "healthy"} for i in range(10)],
            *[{"species": "Acer pseudoplatanus", "diameter": 22.7 + i*0.5, "height": 14.2 + i*0.1, "health_status": "healthy"} for i in range(8)],
            
            # Frênes
            *[{"species": "Fraxinus excelsior", "diameter": 32.1 + i*0.7, "height": 18.4 + i*0.1, "health_status": "damaged", "health_issue": "chalarose"} for i in range(5)],
            *[{"species": "Fraxinus excelsior", "diameter": 25.8 + i*0.6, "height": 15.7 + i*0.1, "health_status": "damaged", "health_issue": "chalarose"} for i in range(3)],
        ]
    }

def generate_sample_management_plan(parcel_id, diagnostic):
    """Génère un plan de gestion d'exemple pour la démonstration."""
    from datetime import datetime
    current_year = datetime.now().year
    
    return {
        "parcel_id": parcel_id,
        "created_at": pd.Timestamp.now().isoformat(),
        "horizon": {
            "start_year": current_year,
            "end_year": current_year + 15,
            "duration_years": 15
        },
        "goals": ["production", "resilience", "biodiversity"],
        "summary": f"Plan de gestion forestière sur 15 ans visant à optimiser la production tout en renforçant la résilience au changement climatique et la biodiversité",
        "phases": [
            {
                "name": "Diagnostic et préparation",
                "year": current_year,
                "actions": [
                    "Réalisation d'un inventaire complet",
                    "Cartographie des zones d'intervention",
                    "Planification des accès"
                ],
                "expected_outcomes": "Stratégie détaillée d'intervention"
            },
            {
                "name": "Restauration des zones dégradées",
                "year": current_year + 1,
                "actions": [
                    "Dépressage dans les zones denses", 
                    "Éclaircie sélective des pins stressés", 
                    "Ouverture de clairières"
                ],
                "expected_outcomes": "Amélioration de la vigueur et de la diversité structurelle"
            },
            {
                "name": "Enrichissement en chêne rouvre",
                "year": current_year + 2,
                "actions": [
                    "Plantation de chêne rouvre dans les clairières",
                    "Protection contre le gibier",
                    "Entretien des plants"
                ],
                "expected_outcomes": "Introduction d'une espèce résiliente et productive"
            },
            {
                "name": "Première éclaircie profitable",
                "year": current_year + 5,
                "actions": [
                    "Martelage des tiges à éclaircir",
                    "Exploitation des pins de moins bonne qualité",
                    "Préservation d'arbres habitats"
                ],
                "expected_outcomes": "Première récolte commercialisable, amélioration du peuplement"
            },
            {
                "name": "Dégagement des cultures",
                "year": current_year + 6,
                "actions": [
                    "Dégagement des jeunes plants de chêne",
                    "Lutte contre la végétation concurrente",
                    "Taille de formation"
                ],
                "expected_outcomes": "Bon développement des plants introduits"
            },
            {
                "name": "Suivi et évaluation",
                "year": current_year + 10,
                "actions": [
                    "Inventaire de contrôle",
                    "Évaluation de la croissance",
                    "Analyse de la santé du peuplement"
                ],
                "expected_outcomes": "Validation de la stratégie ou ajustements"
            },
            {
                "name": "Seconde éclaircie profitable",
                "year": current_year + 12,
                "actions": [
                    "Martelage des tiges à éclaircir",
                    "Exploitation sélective",
                    "Préservation de bois mort"
                ],
                "expected_outcomes": "Seconde récolte commercialisable, amélioration de la biodiversité"
            }
        ],
        "recommended_species": diagnostic["species_recommendations"]["recommended_species"],
        "climate_considerations": {
            "current": diagnostic["climate"]["summary"],
            "future": {
                "description": "Vers 2050, augmentation prévisible des températures de 1.5 à 2°C, accentuation des sécheresses estivales et hausse des risques sanitaires pour certaines espèces comme le hêtre."
            }
        },
        "monitoring_plan": {
            "frequency": "biannuel",
            "indicators": [
                "Croissance en hauteur et diamètre",
                "Taux de survie des plantations",
                "Indice de biodiversité",
                "Santé des arbres",
                "Capacité de régénération naturelle"
            ]
        },
        "estimated_costs": {
            "total": 32850,
            "per_hectare": 6317.31,
            "phase_breakdown": [
                {"phase": "Diagnostic et préparation", "cost": 3250, "details": "Inventaire et planification"},
                {"phase": "Restauration des zones dégradées", "cost": 5200, "details": "Travaux sylvicoles"}, 
                {"phase": "Enrichissement en chêne rouvre", "cost": 7800, "details": "Plantation et protection"},
                {"phase": "Première éclaircie profitable", "cost": 3600, "details": "Exploitation et vente de bois"},
                {"phase": "Dégagement des cultures", "cost": 4200, "details": "Travaux sylvicoles"},
                {"phase": "Suivi et évaluation", "cost": 2800, "details": "Inventaire et analyse"},
                {"phase": "Seconde éclaircie profitable", "cost": 6000, "details": "Exploitation et vente de bois"}
            ],
            "disclaimer": "Estimation indicative susceptible de varier selon les conditions du terrain et du marché"
        }
    }

if __name__ == "__main__":
    main()
