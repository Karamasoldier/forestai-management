#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API REST ForestAI.

Ce script démontre comment utiliser l'API REST ForestAI pour effectuer
différentes opérations comme la recherche de parcelles, l'analyse de parcelles,
la recherche de subventions et l'analyse d'éligibilité.

Usage:
    python api_usage_example.py

Note: Assurez-vous que le serveur API est en cours d'exécution (python api_server.py)
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path
from pprint import pprint

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# URL de base de l'API
API_BASE_URL = "http://localhost:8000"

def check_api_status():
    """Vérifier le statut de l'API."""
    logger.info("=== Vérification du statut de l'API ===")
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        response.raise_for_status()
        
        status = response.json()
        pprint(status)
        
        return status["status"] == "operational"
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut de l'API: {e}")
        return False

def search_parcels_example():
    """Exemple de recherche de parcelles."""
    logger.info("\n=== Exemple de recherche de parcelles ===")
    try:
        # Données de recherche
        search_data = {
            "commune": "Saint-Martin-de-Crau",
            "section": "B"
        }
        
        # Effectuer la requête
        response = requests.post(f"{API_BASE_URL}/geo/search", json=search_data)
        response.raise_for_status()
        
        # Traiter la réponse
        result = response.json()
        
        if result["status"] == "success":
            parcels = result["result"].get("parcels", [])
            
            logger.info(f"Nombre de parcelles trouvées: {len(parcels)}")
            
            # Afficher les premières parcelles
            for i, parcel in enumerate(parcels[:5], 1):
                print(f"\nParcelle {i}:")
                print(f"  ID: {parcel.get('id')}")
                print(f"  Surface: {parcel.get('area_m2')} m²")
                print(f"  Adresse: {parcel.get('address', 'Non disponible')}")
            
            # Retourner la première parcelle pour utilisation dans d'autres exemples
            return parcels[0]["id"] if parcels else None
        else:
            logger.error(f"Erreur: {result.get('error_message')}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de parcelles: {e}")
        return None

def analyze_parcel_example(parcel_id):
    """Exemple d'analyse de parcelle."""
    logger.info("\n=== Exemple d'analyse de parcelle ===")
    
    if not parcel_id:
        logger.error("Aucun ID de parcelle fourni pour l'analyse")
        return None
    
    try:
        # Données d'analyse
        analyze_data = {
            "parcel_id": parcel_id,
            "analyses": ["terrain", "forest_potential", "risks"]
        }
        
        # Effectuer la requête
        response = requests.post(f"{API_BASE_URL}/geo/analyze", json=analyze_data)
        response.raise_for_status()
        
        # Traiter la réponse
        result = response.json()
        
        if result["status"] == "success":
            analysis = result["result"]
            
            print("\nRésultat de l'analyse:")
            print(f"  Surface: {analysis.get('area_ha')} hectares")
            print(f"  Élévation moyenne: {analysis.get('average_elevation')} m")
            print(f"  Pente moyenne: {analysis.get('average_slope')}°")
            
            if "soil_type" in analysis:
                print(f"  Type de sol: {analysis.get('soil_type')}")
            
            if "forest_potential" in analysis:
                print(f"  Potentiel forestier: {analysis.get('forest_potential').get('score')}/100")
                print(f"  Espèces recommandées: {', '.join(analysis.get('forest_potential').get('recommended_species', []))}")
            
            if "risks" in analysis and analysis["risks"]:
                print("\n  Risques identifiés:")
                for risk in analysis["risks"]:
                    print(f"    - {risk.get('type')}: {risk.get('level')} ({risk.get('details', 'Pas de détails')})")
            
            return analysis
        else:
            logger.error(f"Erreur: {result.get('error_message')}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de parcelle: {e}")
        return None

def search_subsidies_example(parcel_id=None):
    """Exemple de recherche de subventions."""
    logger.info("\n=== Exemple de recherche de subventions ===")
    try:
        # Données de recherche
        search_data = {
            "project_type": "reboisement",
            "region": "Provence-Alpes-Côte d'Azur",
            "owner_type": "private"
        }
        
        # Ajouter l'ID de parcelle si fourni
        if parcel_id:
            search_data["parcel_id"] = parcel_id
            print(f"Recherche avec enrichissement des données de la parcelle: {parcel_id}")
        
        # Effectuer la requête
        response = requests.post(f"{API_BASE_URL}/subsidies/search", json=search_data)
        response.raise_for_status()
        
        # Traiter la réponse
        result = response.json()
        
        if result["status"] == "success":
            subsidies = result["result"]
            
            logger.info(f"Nombre de subventions trouvées: {len(subsidies)}")
            
            # Afficher les subventions
            for i, subsidy in enumerate(subsidies[:3], 1):
                print(f"\nSubvention {i}:")
                print(f"  ID: {subsidy.get('id')}")
                print(f"  Titre: {subsidy.get('title')}")
                print(f"  Organisme: {subsidy.get('organization')}")
                
                if subsidy.get("deadline"):
                    print(f"  Date limite: {subsidy.get('deadline')}")
                
                if subsidy.get("funding_rate"):
                    print(f"  Taux de financement: {subsidy.get('funding_rate')}%")
                
                if subsidy.get("amount_per_ha"):
                    print(f"  Montant par hectare: {subsidy.get('amount_per_ha')} €/ha")
            
            # Retourner le premier ID de subvention pour utilisation dans d'autres exemples
            return subsidies[0]["id"] if subsidies else None
        else:
            logger.error(f"Erreur: {result.get('error_message')}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de subventions: {e}")
        return None

def analyze_eligibility_example(subsidy_id, parcel_id):
    """Exemple d'analyse d'éligibilité."""
    logger.info("\n=== Exemple d'analyse d'éligibilité ===")
    
    if not subsidy_id or not parcel_id:
        logger.error("Identifiants de subvention ou de parcelle manquants")
        return None
    
    try:
        # Données du projet
        project_data = {
            "project": {
                "type": "reboisement",
                "area_ha": 5.2,
                "species": ["pinus_pinea", "quercus_suber"],
                "region": "Provence-Alpes-Côte d'Azur",
                "location": parcel_id,
                "owner_type": "private",
                "planting_density": 1200,
                "has_management_document": True,
                "maintenance_commitment_years": 5,
                "certifications": ["PEFC"]
            },
            "subsidy_id": subsidy_id
        }
        
        # Effectuer la requête
        response = requests.post(f"{API_BASE_URL}/subsidies/eligibility", json=project_data)
        response.raise_for_status()
        
        # Traiter la réponse
        result = response.json()
        
        if result["status"] == "success":
            eligibility = result["result"]
            
            print("\nRésultat de l'analyse d'éligibilité:")
            print(f"  Subvention: {eligibility.get('subsidy_title')} ({eligibility.get('subsidy_id')})")
            print(f"  Éligible: {'Oui' if eligibility.get('eligible') else 'Non'}")
            
            print("\n  Conditions d'éligibilité:")
            for condition in eligibility.get('conditions', []):
                status = "✓" if condition["satisfied"] else "✗"
                print(f"    {status} {condition['condition']}: {condition['details']}")
            
            if eligibility.get('eligible') and eligibility.get('funding_details'):
                funding = eligibility['funding_details']
                print("\n  Détails de financement:")
                print(f"    Montant de base: {funding['base_amount']} €")
                print(f"    Bonus: {funding['bonus_amount']} €")
                print(f"    Montant total: {funding['total_amount']} €")
            
            return eligibility
        else:
            logger.error(f"Erreur: {result.get('error_message')}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse d'éligibilité: {e}")
        return None

def generate_application_example(subsidy_id, parcel_id):
    """Exemple de génération de demande de subvention."""
    logger.info("\n=== Exemple de génération de demande de subvention ===")
    
    if not subsidy_id or not parcel_id:
        logger.error("Identifiants de subvention ou de parcelle manquants")
        return None
    
    try:
        # Données de la demande
        application_data = {
            "project": {
                "type": "reboisement",
                "area_ha": 5.2,
                "species": ["pinus_pinea", "quercus_suber"],
                "region": "Provence-Alpes-Côte d'Azur",
                "location": parcel_id,
                "owner_type": "private",
                "planting_density": 1200
            },
            "subsidy_id": subsidy_id,
            "applicant": {
                "name": "Domaine Forestier du Sud",
                "address": "Route des Pins 13200 Arles",
                "contact": "contact@domaineforestier.fr",
                "siret": "12345678900012",
                "contact_name": "Jean Dupont",
                "contact_phone": "0612345678"
            },
            "output_formats": ["pdf", "html"]
        }
        
        # Effectuer la requête
        response = requests.post(f"{API_BASE_URL}/subsidies/application", json=application_data)
        response.raise_for_status()
        
        # Traiter la réponse
        result = response.json()
        
        if result["status"] == "success":
            documents = result["result"]
            
            print("\nDocuments générés:")
            for format_type, path in documents.items():
                print(f"  Format {format_type.upper()}: {path}")
            
            return documents
        else:
            logger.error(f"Erreur: {result.get('error_message')}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de la génération de documents: {e}")
        return None

def main():
    """Fonction principale."""
    logger.info("Démarrage de l'exemple d'utilisation de l'API ForestAI")
    
    # Vérifier le statut de l'API
    if not check_api_status():
        logger.error("L'API ForestAI n'est pas disponible. Assurez-vous que le serveur est en cours d'exécution.")
        return
    
    try:
        # Recherche de parcelles
        parcel_id = search_parcels_example()
        
        if not parcel_id:
            logger.error("Impossible de continuer sans ID de parcelle")
            return
        
        # Analyse de parcelle
        analyze_parcel_example(parcel_id)
        
        # Recherche de subventions avec enrichissement par parcelle
        subsidy_id = search_subsidies_example(parcel_id)
        
        if not subsidy_id:
            logger.error("Impossible de continuer sans ID de subvention")
            return
        
        # Analyse d'éligibilité
        analyze_eligibility_example(subsidy_id, parcel_id)
        
        # Génération de demande
        generate_application_example(subsidy_id, parcel_id)
        
    except Exception as e:
        logger.error(f"Une erreur s'est produite: {e}", exc_info=True)
    
    logger.info("Exemple terminé")

if __name__ == "__main__":
    main()
