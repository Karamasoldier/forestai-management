# examples/logging_example.py

import time
import random
import datetime
from pathlib import Path
import sys
import os

# Ajout du répertoire parent au path pour l'importation des modules locaux
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forestai.core.utils.logging import get_logger
from forestai.core.utils.logging_config import (
    LoggingConfig, 
    LoggingMetrics, 
    setup_agent_logging,
    log_function
)

# Configuration personnalisée du système de logging
config = LoggingConfig.get_instance()
config.init({
    "level": "DEBUG",
    "log_dir": "logs/examples",
    "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    "collect_metrics": True
})

# Obtenir le collecteur de métriques
metrics = LoggingMetrics.get_instance()

# Exemple d'utilisation basique avec un logger simple
def basic_logging_example():
    print("\n=== Exemple de logging basique ===")
    
    # Créer un logger simple
    logger = get_logger("example.basic")
    
    # Exemples de logs à différents niveaux
    logger.debug("Ceci est un message DEBUG")
    logger.info("Ceci est un message INFO")
    logger.warning("Ceci est un message WARNING")
    logger.error("Ceci est un message ERROR", exc_info=False)
    
    # Logging avec contexte
    logger.update_context({"action": "test", "module": "basic"})
    logger.info("Message avec contexte")
    
    # Simuler une exception
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception(f"Une erreur s'est produite: {e}")

# Exemple d'utilisation avec les agents
def agent_logging_example():
    print("\n=== Exemple de logging d'agent ===")
    
    # Configurer un logger d'agent
    logger = setup_agent_logging("TestAgent", level="INFO", context={
        "version": "1.0.0",
        "mode": "test"
    })
    
    # Simuler des logs d'opérations d'agent
    logger.info("Agent démarré")
    
    # Simuler un appel API
    logger.log_api_call(
        api_name="Cadastre API",
        endpoint="/parcels/search",
        params={"commune": "Saint-Martin-de-Crau", "section": "B"},
        success=True,
        response_time=0.325
    )
    
    # Simuler une tâche
    task_id = f"task_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.log_task(
        task_id=task_id,
        task_type="analyze_parcel",
        agent_name="TestAgent",
        status="started",
        details={"params": {"parcel_id": "123456"}}
    )
    
    # Simuler du travail
    time.sleep(0.5)
    
    # Simuler la fin de la tâche
    logger.log_task(
        task_id=task_id,
        task_type="analyze_parcel",
        agent_name="TestAgent",
        status="completed",
        details={"result": {"potential_score": 0.85}}
    )
    
    # Simuler un appel API qui échoue
    logger.log_api_call(
        api_name="GeoService API",
        endpoint="/terrain/elevation",
        params={"coordinates": [43.6, 4.8]},
        success=False,
        response_time=1.23,
        error=Exception("Service indisponible")
    )

# Exemple d'utilisation du décorateur de logging
@log_function(logger="example.function", level="INFO")
def calculate_forest_potential(parcel_id, area_size, slope=None, soil_type=None):
    """Fonction de démonstration pour le calcul de potentiel forestier."""
    print(f"Traitement de la parcelle {parcel_id}...")
    
    # Simuler un traitement
    time.sleep(0.2)
    
    # Générer un score aléatoire
    basic_score = random.uniform(0.3, 0.9)
    
    # Ajustements basés sur les paramètres
    if slope and slope > 15:
        basic_score *= 0.8  # Pénalité pour pente forte
    
    if soil_type == "rocky":
        basic_score *= 0.7  # Pénalité pour sol rocheux
    elif soil_type == "clay":
        basic_score *= 1.2  # Bonus pour sol argileux
    
    # Simuler une erreur aléatoire
    if random.random() < 0.2:  # 20% de chance d'erreur
        raise ValueError(f"Données de terrain invalides pour la parcelle {parcel_id}")
    
    return {
        "parcel_id": parcel_id,
        "area_size": area_size,
        "potential_score": round(basic_score, 2),
        "recommended_species": ["pine", "oak"] if basic_score > 0.6 else ["birch"]
    }

# Exemple d'utilisation des métriques
def metrics_example():
    print("\n=== Exemple de métriques de logging ===")
    
    # Simuler des opérations qui génèrent des métriques
    for i in range(5):
        # Incrémenter des compteurs
        metrics.increment("operations")
        
        # Simuler des appels API avec succès/échec aléatoire
        success = random.random() > 0.3  # 70% de chance de succès
        response_time = random.uniform(0.1, 2.0)
        metrics.record_api_call(success, response_time)
        
        # Simuler des tâches avec succès/échec aléatoire
        status = "completed" if random.random() > 0.2 else "failed"
        metrics.record_task(status)
    
    # Afficher les métriques actuelles
    current_metrics = metrics.log_current_metrics()
    print(f"Métriques collectées: {len(current_metrics)} indicateurs")
    print(f"Taux de succès des appels API: {(1 - current_metrics['api_error_rate']) * 100:.1f}%")
    print(f"Taux de succès des tâches: {current_metrics['task_success_rate'] * 100:.1f}%")
    print(f"Temps de réponse moyen: {current_metrics['avg_response_time']:.3f}s")

# Exemple d'intégration avec les exceptions système
def exception_handling_example():
    print("\n=== Exemple de gestion d'exceptions système ===")
    
    logger = get_logger("example.exceptions")
    logger.info("Test de gestion d'exceptions non gérées")
    
    # Simuler une exception non gérée (commenté pour éviter l'arrêt du script)
    # raise RuntimeError("Exception non gérée de démonstration")
    
    # Alternative: déclencher une exception dans une fonction qui sera capturée
    @log_function(logger=logger, level="INFO")
    def buggy_function():
        bad_list = [1, 2, 3]
        return bad_list[10]  # Index hors limites
    
    try:
        buggy_function()
    except Exception as e:
        print(f"Exception capturée: {e}")
        logger.info("L'exception a été correctement interceptée et loggée")

# Exécuter les exemples
if __name__ == "__main__":
    print("Démonstration de l'infrastructure de logging ForestAI")
    
    # Exécuter chaque exemple
    basic_logging_example()
    agent_logging_example()
    
    # Tester le décorateur de fonction
    print("\n=== Exemple de décorateur de logging ===")
    for i in range(3):
        try:
            parcel_id = f"P{i+1000}"
            result = calculate_forest_potential(
                parcel_id=parcel_id,
                area_size=random.randint(5000, 20000),
                slope=random.randint(0, 30),
                soil_type=random.choice(["clay", "rocky", "sandy"])
            )
            print(f"Résultat pour {parcel_id}: {result['potential_score']}")
        except Exception as e:
            print(f"Erreur traitée: {e}")
    
    # Tester les métriques
    metrics_example()
    
    # Tester la gestion d'exceptions
    exception_handling_example()
    
    print("\nLes logs ont été générés dans le dossier:", Path("logs/examples").resolve())
