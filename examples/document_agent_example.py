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
    
    print("\n✅ Démonstration terminée.")

if __name__ == "__main__":
    main()
