#!/usr/bin/env python3
"""
Exemple d'utilisation de l'agent de réglementation forestière (ReglementationAgent).

Cet exemple montre comment:
1. Initialiser l'agent de réglementation
2. Vérifier la conformité d'un projet forestier
3. Obtenir les autorisations nécessaires
4. Générer un rapport de conformité
"""

import os
import json
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forestai.agents.reglementation_agent import ReglementationAgent
from forestai.core.utils.logging_config import LoggingConfig

# Charger les variables d'environnement
load_dotenv()

def main():
    """Fonction principale pour démontrer l'utilisation de l'agent de réglementation."""
    
    # Configurer le logging
    logging_config = LoggingConfig.get_instance()
    logging_config.init({
        "level": "INFO",
        "log_dir": "logs",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })
    
    logger = logging_config.get_logger("examples.reglementation")
    logger.info("Démarrage de l'exemple ReglementationAgent")
    
    # Configuration de base
    config = {
        "data_path": "./data",
        "output_path": "./data/outputs"
    }
    
    # Créer l'agent de réglementation
    agent = ReglementationAgent(config, use_messaging=False)
    logger.info(f"Agent initialisé avec {len(agent.regulations)} réglementations")
    
    # Exemple 1: Vérifier la conformité d'un projet de défrichement
    logger.info("Exemple 1: Vérification de conformité pour un projet de défrichement")
    defrichement_result = agent.check_compliance(
        parcels=["123456789", "987654321"],
        project_type="defrichement",
        params={}
    )
    
    # Afficher les résultats
    logger.info(f"Conformité globale: {defrichement_result['overall_compliant']}")
    logger.info(f"Réglementations analysées: {defrichement_result['compliance_summary']['total_regulations']}")
    logger.info(f"Non conformes: {defrichement_result['compliance_summary']['non_compliant']}")
    
    # Sauvegarder le rapport au format HTML
    html_report = agent.generate_compliance_report(defrichement_result, "html")
    os.makedirs("./data/outputs", exist_ok=True)
    with open("./data/outputs/defrichement_report.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    logger.info("Rapport HTML sauvegardé dans ./data/outputs/defrichement_report.html")
    
    # Exemple 2: Vérifier les autorisations nécessaires pour un projet de boisement
    logger.info("Exemple 2: Autorisations pour un projet de boisement de 30 ha")
    authorizations = agent.get_required_authorizations(
        project_type="boisement",
        area=30.0
    )
    
    # Afficher les autorisations
    logger.info(f"Autorisations nécessaires: {len(authorizations)}")
    for auth in authorizations:
        logger.info(f"- {auth['description']} ({auth['authority']})")
    
    # Exemple 3: Rechercher des réglementations par mot-clé
    logger.info("Exemple 3: Recherche de réglementations sur les zones humides")
    regulations = agent.search_regulation("zone humide")
    
    # Afficher les réglementations trouvées
    logger.info(f"Réglementations trouvées: {len(regulations)}")
    for reg in regulations:
        logger.info(f"- {reg['id']}: {reg['name']}")
    
    # Exemple 4: Vérifier la conformité d'un projet en zone protégée
    logger.info("Exemple 4: Vérification de conformité pour un projet en zone Natura 2000")
    natura_result = agent.check_compliance(
        parcels=["123456789"],
        project_type="boisement",
        params={"natura_2000": True}
    )
    
    # Afficher les recommandations
    logger.info(f"Recommandations: {len(natura_result['recommendations'])}")
    for rec in natura_result['recommendations']:
        logger.info(f"- {rec['issue']}: {rec['action']}")
    
    # Exemple 5: Vérifier la protection des eaux pour des parcelles
    logger.info("Exemple 5: Vérification de la protection des eaux")
    water_protection = agent.check_parcels_water_protection(["123456789", "987654321"])
    
    # Afficher les résultats de protection des eaux
    logger.info(f"Parcelles protégées: {water_protection['protected_parcels']}/{water_protection['total_parcels']}")
    
    logger.info("Exemple terminé avec succès")

if __name__ == "__main__":
    main()
