#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation de l'API REST ForestAI pour l'analyse sanitaire forestière.

Ce script démontre comment :
1. Vérifier le statut de l'API
2. Effectuer une analyse sanitaire forestière
3. Générer un diagnostic forestier complet incluant l'analyse sanitaire
4. Générer un plan de gestion forestière
5. Produire différents types de rapports (PDF, HTML, TXT)

Usage:
    python api_health_analysis_example.py

Requirements:
    - requests
    - json
    - datetime
    - os
"""

import os
import json
import requests
import datetime
from pathlib import Path
import time

# Configuration de l'API
API_URL = "http://localhost:8000"  # Remplacer par l'URL de production si nécessaire
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Dossier pour sauvegarder les rapports générés
OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def check_api_status():
    """Vérifier que l'API est opérationnelle."""
    try:
        response = requests.get(f"{API_URL}/status", headers=HEADERS)
        if response.status_code == 200:
            status_data = response.json()
            if status_data.get("status") == "operational":
                print(f"✅ API opérationnelle (version: {status_data.get('api_version')})")
                print(f"   Agents disponibles: {', '.join(k for k, v in status_data.get('agents', {}).items() if v == 'available')}")
                return True
        print(f"❌ API non opérationnelle. Code: {response.status_code}")
        return False
    except requests.ConnectionError:
        print(f"❌ Impossible de se connecter à l'API à {API_URL}")
        return False


def perform_health_analysis():
    """Effectuer une analyse sanitaire forestière."""
    # Données de test pour l'analyse sanitaire
    health_analysis_data = {
        "inventory_data": {
            "items": [
                {
                    "species": "quercus_ilex",
                    "diameter": 25.5,
                    "height": 12.0,
                    "health_status": "moyen",
                    "notes": "Présence de taches foliaires"
                },
                {
                    "species": "quercus_ilex",
                    "diameter": 28.2,
                    "height": 13.5,
                    "health_status": "moyen"
                },
                {
                    "species": "pinus_halepensis",
                    "diameter": 35.0,
                    "height": 18.5,
                    "health_status": "bon"
                }
            ],
            "area": 1.5,
            "date": "2025-03-01",
            "method": "placettes"
        },
        "additional_symptoms": {
            "leaf_discoloration": 0.35,
            "observed_pests": ["bark_beetle"],
            "crown_thinning": 0.25
        },
        "parcel_id": "13097000B0012"  # Optionnel, pour enrichir avec des données climatiques
    }

    print("\n📋 Analyse sanitaire forestière...")
    try:
        response = requests.post(
            f"{API_URL}/diagnostic/health-analysis",
            headers=HEADERS,
            json=health_analysis_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                health_data = result.get("result", {})
                
                print(f"✅ Analyse sanitaire réalisée avec succès")
                print(f"   Score sanitaire: {health_data.get('overall_health_score', 0):.1f}/10")
                print(f"   État sanitaire: {health_data.get('health_status', '')}")
                print(f"   Problèmes détectés: {len(health_data.get('detected_issues', []))}")
                
                # Sauvegarde des résultats
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = OUTPUT_DIR / f"health_analysis_{timestamp}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(health_data, f, indent=2, ensure_ascii=False)
                print(f"   Résultats sauvegardés dans {output_file}")
                
                return health_data
            else:
                print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return None


def generate_diagnostic():
    """Générer un diagnostic forestier complet incluant l'analyse sanitaire."""
    # Données de test pour le diagnostic
    diagnostic_data = {
        "parcel_id": "13097000B0012",
        "inventory_data": {
            "items": [
                {
                    "species": "quercus_ilex",
                    "diameter": 25.5,
                    "height": 12.0,
                    "health_status": "moyen"
                },
                {
                    "species": "pinus_halepensis",
                    "diameter": 35.0,
                    "height": 18.5,
                    "health_status": "bon"
                }
            ],
            "area": 1.5,
            "date": "2025-03-01",
            "method": "placettes"
        },
        "include_health_analysis": True
    }

    print("\n📋 Génération d'un diagnostic forestier complet...")
    try:
        response = requests.post(
            f"{API_URL}/diagnostic/generate",
            headers=HEADERS,
            json=diagnostic_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                diagnostic = result.get("result", {})
                
                print(f"✅ Diagnostic généré avec succès")
                print(f"   Parcelle: {diagnostic.get('parcel_id')}")
                print(f"   Score de potentiel: {diagnostic.get('potential', {}).get('score', 0)}")
                print(f"   Espèces recommandées: {', '.join(diagnostic.get('potential', {}).get('recommended_species', []))}")
                
                # Afficher les informations sanitaires si présentes
                if "health" in diagnostic:
                    health = diagnostic.get("health", {})
                    print(f"   Score sanitaire: {health.get('overall_health_score', 0):.1f}/10")
                    print(f"   État sanitaire: {health.get('health_status', '')}")
                
                # Sauvegarde des résultats
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = OUTPUT_DIR / f"diagnostic_{timestamp}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(diagnostic, f, indent=2, ensure_ascii=False)
                print(f"   Résultats sauvegardés dans {output_file}")
                
                return diagnostic
            else:
                print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return None


def generate_management_plan():
    """Générer un plan de gestion forestière."""
    # Données de test pour le plan de gestion
    management_plan_data = {
        "parcel_id": "13097000B0012",
        "goals": ["production", "resilience", "biodiversity"],
        "horizon_years": 15,
        "use_existing_diagnostic": True
    }

    print("\n📋 Génération d'un plan de gestion forestière...")
    try:
        response = requests.post(
            f"{API_URL}/diagnostic/management-plan",
            headers=HEADERS,
            json=management_plan_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                plan = result.get("result", {})
                
                print(f"✅ Plan de gestion généré avec succès")
                print(f"   Parcelle: {plan.get('parcel_id')}")
                print(f"   Horizon: {plan.get('horizon', {}).get('start_year')} à {plan.get('horizon', {}).get('end_year')}")
                print(f"   Objectifs: {', '.join(plan.get('goals', []))}")
                print(f"   Nombre de phases: {len(plan.get('phases', []))}")
                
                # Sauvegarde des résultats
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = OUTPUT_DIR / f"management_plan_{timestamp}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(plan, f, indent=2, ensure_ascii=False)
                print(f"   Résultats sauvegardés dans {output_file}")
                
                return plan
            else:
                print(f"❌ Erreur: {result.get('error_message', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return None


def generate_report(report_type, data_id, report_format="pdf", health_detail_level="standard"):
    """
    Générer un rapport forestier au format demandé.
    
    Args:
        report_type: Type de rapport ('diagnostic', 'management_plan', 'health')
        data_id: Identifiant des données (parcelle, diagnostic, etc.)
        report_format: Format du rapport ('pdf', 'html', 'txt')
        health_detail_level: Niveau de détail sanitaire ('minimal', 'standard', 'complete')
    """
    # Données pour la génération du rapport
    report_data = {
        "report_type": report_type,
        "data_id": data_id,
        "format": report_format,
        "health_detail_level": health_detail_level
    }

    print(f"\n📋 Génération d'un rapport {report_type} au format {report_format}...")
    try:
        response = requests.post(
            f"{API_URL}/diagnostic/report",
            headers=HEADERS,
            json=report_data,
            stream=True  # Important pour la récupération de fichiers binaires
        )
        
        if response.status_code == 200:
            # Déterminer l'extension du fichier
            extension = report_format.lower()
            
            # Nom du fichier de sortie
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = OUTPUT_DIR / f"{report_type}_{data_id}_{timestamp}.{extension}"
            
            # Sauvegarder le rapport
            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Rapport généré avec succès: {output_file}")
            return str(output_file)
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return None


def main():
    """Fonction principale exécutant les exemples d'utilisation de l'API."""
    print("🌲 Exemple d'utilisation de l'API ForestAI pour l'analyse sanitaire et les diagnostics 🌲")
    
    # Vérifier le statut de l'API
    if not check_api_status():
        print("Arrêt du script, l'API n'est pas disponible.")
        return
    
    # 1. Effectuer une analyse sanitaire
    health_analysis = perform_health_analysis()
    
    # 2. Générer un diagnostic complet
    diagnostic = generate_diagnostic()
    
    # 3. Générer un plan de gestion
    management_plan = generate_management_plan()
    
    # Pause pour laisser le temps au serveur de traiter les requêtes
    time.sleep(1)
    
    # 4. Générer différents rapports si les données ont été récupérées
    if diagnostic:
        parcel_id = diagnostic.get("parcel_id", "13097000B0012")
        
        # Rapport diagnostic au format PDF
        generate_report("diagnostic", parcel_id, "pdf", "standard")
        
        # Rapport diagnostic au format HTML avec détails sanitaires complets
        generate_report("diagnostic", parcel_id, "html", "complete")
    
    if management_plan:
        parcel_id = management_plan.get("parcel_id", "13097000B0012")
        
        # Rapport de plan de gestion au format PDF
        generate_report("management_plan", parcel_id, "pdf")
    
    print("\n✅ Démonstration terminée. Les résultats sont disponibles dans le dossier:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
