#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation du DocumentAgent pour générer des documents forestiers.

Ce script démontre comment utiliser le DocumentAgent pour générer différents types
de documents administratifs liés à la gestion forestière.

Usage:
    python document_agent_example.py
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import des modules ForestAI
from forestai.agents.document_agent import DocumentAgent
from forestai.agents.document_agent.models.document_models import DocumentType, DocumentFormat

# Dossier pour sauvegarder les résultats
OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_contract_example():
    """Exemple de génération d'un contrat de vente de bois."""
    print("\n🌲 Génération d'un contrat de vente de bois...")
    
    # Initialiser le DocumentAgent
    agent = DocumentAgent()
    
    # Données du contrat
    contract_data = {
        "contract_type": "vente de bois",
        "reference": f"VENTE-BOIS-{datetime.now().strftime('%Y%m%d%H%M')}",
        "title": "Contrat de Vente de Bois",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "duration": "6 mois",
        "location": "Forêt communale de Saint-Martin-de-Crau",
        "parties": [
            {
                "name": "Commune de Saint-Martin-de-Crau",
                "address": "Place du Dr Général Blanc, 13310 Saint-Martin-de-Crau",
                "representative": "M. Jean Dupont",
                "function": "Maire",
                "type": "vendor"
            },
            {
                "name": "Scierie Provençale SARL",
                "address": "ZI Les Pins, Route de Marseille, 13310 Saint-Martin-de-Crau",
                "representative": "Mme. Marie Durand",
                "function": "Directrice",
                "siret": "12345678900012",
                "type": "buyer"
            }
        ],
        "parcels": [
            {
                "id": "13097000B0012",
                "section": "B",
                "numero": "0012",
                "commune": "Saint-Martin-de-Crau",
                "area_ha": 15.5,
                "volume_estimated_m3": 450
            }
        ],
        "amount": "22 500",
        "price_per_m3": "50",
        "payment_terms": "30% à la signature, solde à l'enlèvement complet du bois",
        "special_conditions": "L'exploitation devra être réalisée en période sèche pour préserver les sols."
    }
    
    # Formats de sortie souhaités
    formats = ["pdf", "docx", "html"]
    
    # Générer le contrat
    result = agent.execute_action(
        "generate_contract",
        {
            "contract_data": contract_data,
            "formats": formats
        }
    )
    
    # Afficher le résultat
    if result.get("status") == "success":
        files = result.get("result", {}).get("files", {})
        print("✅ Contrat généré avec succès:")
        for fmt, file_path in files.items():
            print(f"  • Format {fmt.upper()}: {file_path}")
    else:
        print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")

def generate_specifications_example():
    """Exemple de génération d'un cahier des charges pour des travaux forestiers."""
    print("\n📝 Génération d'un cahier des charges pour travaux forestiers...")
    
    # Initialiser le DocumentAgent
    agent = DocumentAgent()
    
    # Données du cahier des charges
    spec_data = {
        "spec_type": "plantation forestière",
        "reference": f"CDC-PLT-{datetime.now().strftime('%Y%m%d%H%M')}",
        "title": "Cahier des Charges - Travaux de Plantation Forestière",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "client": {
            "name": "ONF - Direction Territoriale Méditerranée",
            "address": "46 Avenue Paul Cézanne, 13090 Aix-en-Provence",
            "contact": "M. Pierre Martin",
            "phone": "04 42 17 57 00",
            "email": "dt.mediterranee@onf.fr"
        },
        "work_types": ["préparation du sol", "plantation", "protection gibier"],
        "parcels": [
            {
                "id": "13097000B0012",
                "section": "B",
                "numero": "0012",
                "commune": "Saint-Martin-de-Crau",
                "area_ha": 8.3,
                "description": "Parcelle à reboiser suite à un incendie"
            },
            {
                "id": "13097000B0013",
                "section": "B",
                "numero": "0013",
                "commune": "Saint-Martin-de-Crau",
                "area_ha": 5.7,
                "description": "Extension de boisement sur friche agricole"
            }
        ],
        "species": [
            {
                "name": "Pinus halepensis",
                "french_name": "Pin d'Alep",
                "density": 1100,
                "percentage": 60
            },
            {
                "name": "Quercus ilex",
                "french_name": "Chêne vert",
                "density": 800,
                "percentage": 30
            },
            {
                "name": "Quercus pubescens",
                "french_name": "Chêne pubescent",
                "density": 400,
                "percentage": 10
            }
        ],
        "start_date": "2025-10-15",
        "end_date": "2026-03-30",
        "budget_estimate": "45 000 €"
    }
    
    # Formats de sortie souhaités
    formats = ["pdf", "docx"]
    
    # Générer le cahier des charges
    result = agent.execute_action(
        "generate_specifications",
        {
            "spec_data": spec_data,
            "formats": formats
        }
    )
    
    # Afficher le résultat
    if result.get("status") == "success":
        files = result.get("result", {}).get("files", {})
        print("✅ Cahier des charges généré avec succès:")
        for fmt, file_path in files.items():
            print(f"  • Format {fmt.upper()}: {file_path}")
    else:
        print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")

def generate_management_plan_example():
    """Exemple de génération d'un plan simple de gestion forestière."""
    print("\n📊 Génération d'un plan simple de gestion forestière...")
    
    # Initialiser le DocumentAgent
    agent = DocumentAgent()
    
    # Données du plan de gestion
    plan_data = {
        "plan_type": "plan_simple_gestion",
        "reference": f"PSG-{datetime.now().strftime('%Y%m%d%H%M')}",
        "title": "Plan Simple de Gestion - Domaine des Chênes",
        "property_name": "Domaine des Chênes",
        "owner": {
            "name": "SCI Forestière du Sud",
            "address": "145 Chemin des Pins, 13100 Aix-en-Provence",
            "contact": "M. Robert Dubois",
            "phone": "04 42 12 34 56",
            "email": "contact@sci-foret-sud.fr"
        },
        "start_date": "2025-01-01",
        "duration_years": 15,
        "parcels": [
            {
                "id": "13001000A0001",
                "section": "A",
                "numero": "0001",
                "commune": "Aix-en-Provence",
                "area_ha": 12.8,
                "cadastral_reference": "A0001"
            },
            {
                "id": "13001000A0002",
                "section": "A",
                "numero": "0002",
                "commune": "Aix-en-Provence",
                "area_ha": 7.3,
                "cadastral_reference": "A0002"
            },
            {
                "id": "13001000A0003",
                "section": "A",
                "numero": "0003",
                "commune": "Aix-en-Provence",
                "area_ha": 5.5,
                "cadastral_reference": "A0003"
            }
        ],
        "stands": [
            {
                "id": "S01",
                "type": "Futaie de chênes",
                "area_ha": 10.5,
                "main_species": "Quercus pubescens",
                "age": 65,
                "volume_per_ha": 120,
                "objective": "Production de bois d'œuvre"
            },
            {
                "id": "S02",
                "type": "Mélange pin-chêne",
                "area_ha": 8.2,
                "main_species": "Pinus halepensis / Quercus ilex",
                "age": 40,
                "volume_per_ha": 90,
                "objective": "Production et protection incendie"
            },
            {
                "id": "S03",
                "type": "Jeune plantation",
                "area_ha": 6.9,
                "main_species": "Quercus pubescens",
                "age": 12,
                "volume_per_ha": 15,
                "objective": "Reconstitution après incendie"
            }
        ],
        "scheduled_operations": [
            {
                "year": 2025,
                "stand_id": "S01",
                "operation": "Éclaircie",
                "details": "Prélèvement de 25% du volume",
                "expected_volume_m3": 315
            },
            {
                "year": 2027,
                "stand_id": "S02",
                "operation": "Éclaircie sanitaire pins",
                "details": "Retrait pins dépérissants",
                "expected_volume_m3": 120
            },
            {
                "year": 2030,
                "stand_id": "S03",
                "operation": "Dépressage",
                "details": "Sélection des tiges d'avenir",
                "expected_volume_m3": 0
            }
        ],
        "environmental_features": [
            {
                "type": "Zone humide",
                "location": "Parcelle A0001, partie sud",
                "area_ha": 0.8,
                "protection_measures": "Interdiction de passage d'engins"
            },
            {
                "type": "Habitat remarquable",
                "location": "Parcelle A0003, crête",
                "area_ha": 1.2,
                "protection_measures": "Conservation d'arbres morts et sénescents"
            }
        ]
    }
    
    # Formats de sortie souhaités
    formats = ["pdf", "docx"]
    
    # Générer le plan de gestion
    result = agent.execute_action(
        "generate_management_plan_doc",
        {
            "plan_data": plan_data,
            "formats": formats
        }
    )
    
    # Afficher le résultat
    if result.get("status") == "success":
        files = result.get("result", {}).get("files", {})
        print("✅ Plan de gestion généré avec succès:")
        for fmt, file_path in files.items():
            print(f"  • Format {fmt.upper()}: {file_path}")
    else:
        print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")

def generate_administrative_doc_example():
    """Exemple de génération d'une autorisation de coupe."""
    print("\n📄 Génération d'une autorisation de coupe...")
    
    # Initialiser le DocumentAgent
    agent = DocumentAgent()
    
    # Données de l'autorisation de coupe
    admin_data = {
        "reference": f"AUT-COUPE-{datetime.now().strftime('%Y%m%d%H%M')}",
        "title": "Autorisation de Coupe - Propriété Forestière des Oliviers",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "authority": "Direction Départementale des Territoires et de la Mer des Bouches-du-Rhône",
        "owner": {
            "name": "M. Laurent Olivier",
            "address": "420 Chemin des Oliviers, 13080 Aix-en-Provence",
            "phone": "04 42 98 76 54",
            "email": "l.olivier@email.fr"
        },
        "parcels": [
            {
                "id": "13080000C0042",
                "section": "C",
                "numero": "0042",
                "commune": "Aix-en-Provence",
                "area_ha": 7.2,
                "cadastral_reference": "C0042"
            }
        ],
        "volume_m3": 320,
        "surface_ha": 7.2,
        "forest_type": "Futaie de pins d'Alep",
        "cut_type": "Coupe d'éclaircie",
        "validity_period": "2 ans",
        "validity_start": datetime.now().strftime("%Y-%m-%d"),
        "validity_end": datetime.now().replace(year=datetime.now().year + 2).strftime("%Y-%m-%d"),
        "legal_references": [
            "Article L. 124-5 du Code forestier",
            "Article R. 124-1 du Code forestier",
            "Arrêté préfectoral du 5 avril 2023 relatif aux coupes de bois"
        ],
        "conditions": [
            "Respect des bonnes pratiques sylvicoles",
            "Conservation d'un minimum de 25 arbres adultes par hectare",
            "Maintien des feuillus présents dans le peuplement",
            "Protection des sols contre l'érosion",
            "Remise en état des chemins après exploitation"
        ],
        "additional_requirements": "Une visite de contrôle sera effectuée à la fin des travaux."
    }
    
    # Formats de sortie souhaités
    formats = ["pdf", "docx"]
    
    # Générer l'autorisation de coupe
    result = agent.execute_action(
        "generate_administrative_doc",
        {
            "admin_data": admin_data,
            "doc_type": "autorisation_coupe",
            "formats": formats
        }
    )
    
    # Afficher le résultat
    if result.get("status") == "success":
        files = result.get("result", {}).get("files", {})
        print("✅ Autorisation de coupe générée avec succès:")
        for fmt, file_path in files.items():
            print(f"  • Format {fmt.upper()}: {file_path}")
    else:
        print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")

def generate_certification_doc_example():
    """Exemple de génération d'un document de certification forestière."""
    print("\n🏆 Génération d'un document de certification forestière...")
    
    # Initialiser le DocumentAgent
    agent = DocumentAgent()
    
    # Données du document de certification
    admin_data = {
        "reference": f"CERT-FOR-{datetime.now().strftime('%Y%m%d%H%M')}",
        "title": "Certificat de Gestion Forestière Durable",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "certification_type": "PEFC",
        "certificate_holder": {
            "name": "Groupement Forestier du Luberon",
            "address": "18 Avenue des Cèdres, 84240 Cabrières-d'Aigues",
            "siret": "79123456700013",
            "contact": "Mme. Sophie Vernier",
            "phone": "04 90 77 88 99",
            "email": "contact@gf-luberon.fr"
        },
        "certification_body": {
            "name": "ECOCERT Forestry",
            "address": "BP 47, 32600 L'Isle-Jourdain",
            "logo_url": "https://example.com/logos/ecocert.png"
        },
        "certified_area_ha": 1245.8,
        "forest_locations": [
            "Cabrières-d'Aigues",
            "Cucuron",
            "Vaugines"
        ],
        "issue_date": datetime.now().strftime("%Y-%m-%d"),
        "validity_years": 5,
        "certification_criteria": [
            "Gestion forestière durable conforme aux standards PEFC",
            "Maintien et amélioration des ressources forestières",
            "Préservation de la diversité biologique des écosystèmes forestiers",
            "Respect des fonctions socio-économiques de la forêt",
            "Planification de la gestion forestière",
            "Traçabilité des produits forestiers"
        ],
        "audit_schedule": "Audit de surveillance annuel et audit de renouvellement tous les 5 ans",
        "conclusion": "Le Groupement Forestier du Luberon répond aux exigences du référentiel PEFC pour une gestion forestière durable."
    }
    
    # Formats de sortie souhaités
    formats = ["pdf"]
    
    # Générer le document de certification
    result = agent.execute_action(
        "generate_administrative_doc",
        {
            "admin_data": admin_data,
            "doc_type": "certification",
            "formats": formats
        }
    )
    
    # Afficher le résultat
    if result.get("status") == "success":
        files = result.get("result", {}).get("files", {})
        print("✅ Document de certification généré avec succès:")
        for fmt, file_path in files.items():
            print(f"  • Format {fmt.upper()}: {file_path}")
    else:
        print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")

def get_document_types_example():
    """Exemple de récupération des types de documents disponibles."""
    print("\n📋 Récupération des types de documents disponibles...")
    
    # Initialiser le DocumentAgent
    agent = DocumentAgent()
    
    # Récupérer les types de documents
    result = agent.execute_action("get_document_types", {})
    
    # Afficher le résultat
    if result.get("status") == "success":
        document_types = result.get("result", {})
        print("✅ Types de documents disponibles:")
        
        for category, types in document_types.items():
            print(f"\n📂 {category}:")
            for type_id, type_name in types.items():
                print(f"  • {type_id}: {type_name}")
    else:
        print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")

def main():
    """Fonction principale exécutant les exemples d'utilisation."""
    print("🌳 Exemple d'utilisation du DocumentAgent pour la gestion forestière 🌳")
    
    # Récupérer les types de documents disponibles
    get_document_types_example()
    
    # Générer un contrat
    generate_contract_example()
    
    # Générer un cahier des charges
    generate_specifications_example()
    
    # Générer un plan de gestion
    generate_management_plan_example()
    
    # Générer une autorisation de coupe
    generate_administrative_doc_example()
    
    # Générer un document de certification forestière
    generate_certification_doc_example()
    
    print("\n✅ Démonstration terminée.")

if __name__ == "__main__":
    main()
