#!/usr/bin/env python3
"""
Exemple d'utilisation de l'agent de subventions (SubsidyAgent).

Ce script démontre comment utiliser le SubsidyAgent pour rechercher des subventions
forestières adaptées à un projet, analyser l'éligibilité et générer des documents.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Ajout du répertoire parent au path pour permettre l'import local
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forestai.agents.subsidy_agent import SubsidyAgent
from forestai.core.utils.config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def search_subsidies_example(agent, example_params):
    """
    Exemple de recherche de subventions.
    
    Args:
        agent: Instance du SubsidyAgent
        example_params: Paramètres d'exemple pour la recherche
    """
    logger.info("=== Exemple de recherche de subventions ===")
    
    # Récupérer les paramètres de l'exemple
    project_type = example_params.get("project_type", "reboisement")
    region = example_params.get("region", "Occitanie")
    owner_type = example_params.get("owner_type", "private")
    
    logger.info(f"Paramètres: type={project_type}, région={region}, propriétaire={owner_type}")
    
    # Effectuer la recherche
    subsidies = agent.search_subsidies(
        project_type=project_type,
        region=region,
        owner_type=owner_type
    )
    
    # Afficher les résultats
    logger.info(f"Nombre de subventions trouvées: {len(subsidies)}")
    for i, subsidy in enumerate(subsidies, 1):
        print(f"\n--- Subvention {i} ---")
        print(f"ID: {subsidy.get('id')}")
        print(f"Titre: {subsidy.get('title')}")
        print(f"Organisme: {subsidy.get('organization')}")
        
        if subsidy.get("deadline"):
            print(f"Date limite: {subsidy.get('deadline')}")
        
        if subsidy.get("funding_rate"):
            print(f"Taux de financement: {subsidy.get('funding_rate')}%")
        
        if subsidy.get("amount_per_ha"):
            print(f"Montant par hectare: {subsidy.get('amount_per_ha')} €/ha")
        
        if subsidy.get("max_funding"):
            print(f"Financement max: {subsidy.get('max_funding')} €")


def analyze_eligibility_example(agent, example_params):
    """
    Exemple d'analyse d'éligibilité.
    
    Args:
        agent: Instance du SubsidyAgent
        example_params: Paramètres d'exemple pour l'analyse
    """
    logger.info("\n=== Exemple d'analyse d'éligibilité ===")
    
    # Informations sur le projet
    project = {
        "type": "reboisement",
        "area_ha": 5.2,
        "species": ["pinus_pinea", "quercus_suber"],
        "region": "Provence-Alpes-Côte d'Azur",
        "location": "13097000B0012",
        "owner_type": "private",
        "planting_density": 1200,
        "slope": 15,
        "protected_areas": [],
        "has_management_document": True,
        "maintenance_commitment_years": 5,
        "priority_zones": ["france_relance"],
        "certifications": ["PEFC"]
    }
    
    # ID de la subvention à analyser
    subsidy_id = example_params.get("subsidy_id")
    
    # Si pas d'ID spécifié, rechercher une subvention
    if not subsidy_id:
        subsidies = agent.search_subsidies(
            project_type=project["type"],
            region=project["region"],
            owner_type=project["owner_type"]
        )
        
        if subsidies:
            subsidy_id = subsidies[0]["id"]
            logger.info(f"Subvention sélectionnée: {subsidy_id} - {subsidies[0]['title']}")
        else:
            logger.error("Aucune subvention trouvée pour l'analyse d'éligibilité")
            return
    
    # Analyser l'éligibilité
    eligibility = agent.analyze_eligibility(project, subsidy_id)
    
    # Afficher les résultats
    print("\n--- Résultat de l'analyse d'éligibilité ---")
    print(f"Subvention: {eligibility.get('subsidy_title')} ({eligibility.get('subsidy_id')})")
    print(f"Éligible: {'Oui' if eligibility.get('eligible') else 'Non'}")
    
    print("\nConditions d'éligibilité:")
    for condition in eligibility.get('conditions', []):
        status = "✓" if condition["satisfied"] else "✗"
        print(f"  {status} {condition['condition']}: {condition['details']}")
    
    if eligibility.get('eligible') and eligibility.get('funding_details'):
        funding = eligibility['funding_details']
        print("\nDétails de financement:")
        print(f"  Montant de base: {funding['base_amount']} €")
        print(f"  Bonus: {funding['bonus_amount']} €")
        print(f"  Montant total: {funding['total_amount']} €")
        
        if funding.get('details', {}).get('bonus_details'):
            print("\n  Détail des bonus:")
            for bonus in funding['details']['bonus_details']:
                print(f"    - {bonus['type']}: {bonus['amount']} € ({bonus['rate']})")


def generate_documents_example(agent, example_params):
    """
    Exemple de génération de documents.
    
    Args:
        agent: Instance du SubsidyAgent
        example_params: Paramètres d'exemple pour la génération
    """
    logger.info("\n=== Exemple de génération de documents ===")
    
    # Informations sur le projet
    project = {
        "type": "reboisement",
        "area_ha": 5.2,
        "species": ["pinus_pinea", "quercus_suber"],
        "region": "Provence-Alpes-Côte d'Azur",
        "location": "13097000B0012",
        "owner_type": "private",
        "planting_density": 1200,
        "slope": 15,
        "has_management_document": True,
        "maintenance_commitment_years": 5,
        "priority_zones": ["france_relance"],
        "certifications": ["PEFC"]
    }
    
    # Informations sur le demandeur
    applicant = {
        "name": "Domaine Forestier du Sud",
        "address": "Route des Pins 13200 Arles",
        "contact": "contact@domaineforestier.fr",
        "siret": "12345678900012",
        "contact_name": "Jean Dupont",
        "contact_phone": "0612345678",
        "owner_since": "2015-06-12"
    }
    
    # ID de la subvention à utiliser
    subsidy_id = example_params.get("subsidy_id")
    
    # Si pas d'ID spécifié, rechercher une subvention
    if not subsidy_id:
        subsidies = agent.search_subsidies(
            project_type=project["type"],
            region=project["region"],
            owner_type=project["owner_type"]
        )
        
        if subsidies:
            subsidy_id = subsidies[0]["id"]
            logger.info(f"Subvention sélectionnée: {subsidy_id} - {subsidies[0]['title']}")
        else:
            logger.error("Aucune subvention trouvée pour la génération de documents")
            return
    
    # Formats de sortie souhaités
    output_formats = example_params.get("output_formats", ["pdf", "html"])
    
    # Générer les documents
    document_paths = agent.generate_application_documents(
        project=project,
        subsidy_id=subsidy_id,
        applicant=applicant,
        output_formats=output_formats
    )
    
    # Afficher les résultats
    print("\n--- Documents générés ---")
    if document_paths:
        for format_type, path in document_paths.items():
            print(f"Format {format_type.upper()}: {path}")
    else:
        print("Aucun document n'a pu être généré")


def refresh_cache_example(agent):
    """
    Exemple de rafraîchissement du cache de subventions.
    
    Args:
        agent: Instance du SubsidyAgent
    """
    logger.info("\n=== Exemple de rafraîchissement du cache ===")
    
    # Forcer le rechargement des subventions
    agent._handle_refresh_cache()
    
    # Afficher le statut du cache
    status = agent.get_status_report()
    print("\n--- Statut du cache ---")
    print(f"Nombre de subventions en cache: {status.get('subsidies_count')}")
    print(f"État du cache: {status.get('cache_status')}")
    print(f"Scrapers disponibles: {', '.join(status.get('scrapers', []))}")


def main():
    """Fonction principale."""
    logger.info("Démarrage de l'exemple SubsidyAgent")
    
    # Charger la configuration
    config = Config().load_config()
    
    # Créer l'agent
    agent = SubsidyAgent(config)
    
    # Paramètres d'exemple
    example_params = {
        "project_type": "reboisement",
        "region": "Provence-Alpes-Côte d'Azur",
        "owner_type": "private",
        "output_formats": ["pdf", "html"]
    }
    
    # Exécuter les exemples
    try:
        # Recherche de subventions
        search_subsidies_example(agent, example_params)
        
        # Analyse d'éligibilité
        analyze_eligibility_example(agent, example_params)
        
        # Génération de documents
        generate_documents_example(agent, example_params)
        
        # Rafraîchissement du cache
        refresh_cache_example(agent)
        
    except Exception as e:
        logger.error(f"Une erreur s'est produite: {e}", exc_info=True)
    
    logger.info("Exemple terminé")


if __name__ == "__main__":
    main()
