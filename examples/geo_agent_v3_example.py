# examples/geo_agent_v3_example.py

import os
import time
import sys
from pathlib import Path

# Ajout du répertoire parent au path pour l'importation des modules locaux
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forestai.agents.geo_agent.geo_agent_v3 import GeoAgentV3
from forestai.core.infrastructure.memory.agent_memory import AgentMemory
from forestai.core.infrastructure.messaging.message_bus import MessageBus
from forestai.core.utils.logging_config import LoggingConfig, LoggingMetrics

# Configuration du logging
config = LoggingConfig.get_instance()
config.init({
    "level": "DEBUG",  # Niveau de log plus verbeux pour le développement
    "log_dir": "logs/geo_agent_v3",
    "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "collect_metrics": True
})

# Initialiser les composants d'infrastructure
memory = AgentMemory()
message_bus = MessageBus()

# Écouter les événements du bus de messages
def message_handler(topic, message):
    print(f"## Event reçu: {topic}")
    print(f"## Message: {message}")

# S'abonner aux événements GeoAgent
message_bus.subscribe("PARCELS_FOUND", message_handler)
message_bus.subscribe("PARCEL_ANALYZED", message_handler)
message_bus.subscribe("FOREST_PARCELS_FOUND", message_handler)

# Créer l'agent
print("Initialisation du GeoAgent v3...")
agent = GeoAgentV3(
    data_dir="data/raw",
    memory=memory,
    message_bus=message_bus,
    log_level="DEBUG"
)
print("GeoAgent v3 initialisé")

def exemple_recherche_parcelles():
    """Exemple de recherche de parcelles."""
    print("\n==== Exemple de recherche de parcelles ====")
    
    # Paramètres de recherche
    commune = "Saint-Martin-de-Crau"
    section = "B"
    
    print(f"Recherche de parcelles à {commune}, section {section}...")
    result = agent.search_parcels(commune=commune, section=section)
    
    if result["success"]:
        print(f"Recherche réussie: {result['count']} parcelles trouvées")
        parcels = result["results"].get("parcels", [])
        if parcels:
            print("\nExemple de parcelles trouvées:")
            for i, parcel in enumerate(parcels[:3]):  # Afficher les 3 premières
                print(f"  {i+1}. ID: {parcel.get('id')}, Surface: {parcel.get('surface')} m²")
    else:
        print(f"Erreur de recherche: {result.get('error')}")

def exemple_analyse_parcelle():
    """Exemple d'analyse d'une parcelle."""
    print("\n==== Exemple d'analyse de parcelle ====")
    
    # Paramètres de recherche pour trouver une parcelle
    commune = "Saint-Martin-de-Crau"
    section = "B"
    
    # Rechercher des parcelles
    search_result = agent.search_parcels(commune=commune, section=section)
    
    if not search_result["success"] or search_result["count"] == 0:
        print("Aucune parcelle trouvée pour l'analyse.")
        return
    
    # Prendre la première parcelle
    parcels = search_result["results"].get("parcels", [])
    parcel_id = parcels[0].get("id")
    
    print(f"Analyse de la parcelle {parcel_id}...")
    start_time = time.time()
    result = agent.analyze_parcel(parcel_id)
    execution_time = time.time() - start_time
    
    if result["success"]:
        print(f"Analyse réussie en {execution_time:.2f}s")
        
        # Afficher les résultats d'analyse
        analysis = result.get("analysis", {})
        potential = result.get("potential", {})
        
        print("\nRésultats d'analyse:")
        print(f"  Altitude moyenne: {analysis.get('elevation_mean', 'N/A')} m")
        print(f"  Pente moyenne: {analysis.get('slope_mean', 'N/A')}°")
        print(f"  Occupation du sol: {analysis.get('land_cover_type', 'N/A')}")
        
        print("\nPotentiel forestier:")
        print(f"  Score: {potential.get('score', 'N/A')}")
        print(f"  Espèces recommandées: {', '.join(potential.get('recommended_species', ['N/A']))}")
    else:
        print(f"Erreur d'analyse: {result.get('error')}")

def exemple_recherche_parcelles_forestieres():
    """Exemple de recherche de parcelles à potentiel forestier."""
    print("\n==== Exemple de recherche de parcelles forestières ====")
    
    # Paramètres de recherche
    commune = "Saint-Martin-de-Crau"
    min_size = 10000  # Surface minimale 1 hectare
    min_potential = 0.7  # Score potentiel forestier minimum
    
    print(f"Recherche de parcelles forestières à {commune}...")
    print(f"Critères: surface >= {min_size} m², potentiel >= {min_potential}")
    
    start_time = time.time()
    result = agent.find_forest_parcels(
        commune=commune,
        min_size=min_size,
        min_potential=min_potential
    )
    execution_time = time.time() - start_time
    
    if result["success"]:
        print(f"Recherche réussie en {execution_time:.2f}s")
        print(f"{result['count']} parcelles forestières trouvées")
        
        if result['count'] > 0:
            print("\nExemple de parcelles forestières:")
            for i, parcel in enumerate(result['parcels'][:3]):  # Afficher les 3 premières
                print(f"  {i+1}. ID: {parcel.get('parcel_id')}")
                print(f"     Surface: {parcel.get('surface')} m²")
                print(f"     Score: {parcel.get('potential_score')}")
                print(f"     Espèces: {', '.join(parcel.get('recommended_species', []))}")
    else:
        print(f"Erreur de recherche: {result.get('error')}")

def exemple_metriques():
    """Exemple d'affichage des métriques de l'agent."""
    print("\n==== Métriques du GeoAgent ====")
    
    # Récupérer les métriques
    metrics = agent.get_metrics()
    
    print("Métriques:")
    print(f"  Appels API total: {metrics.get('api_calls', 0)}")
    print(f"  Erreurs API: {metrics.get('api_errors', 0)}")
    print(f"  Tâches total: {metrics.get('tasks', {}).get('total', 0)}")
    print(f"  Tâches réussies: {metrics.get('tasks', {}).get('completed', 0)}")
    print(f"  Tâches échouées: {metrics.get('tasks', {}).get('failed', 0)}")
    
    if metrics.get('api_calls', 0) > 0:
        print(f"  Taux d'erreur API: {metrics.get('api_error_rate', 0) * 100:.1f}%")
    
    print(f"  Temps de réponse moyen: {metrics.get('avg_response_time', 0):.3f}s")
    print(f"  Temps d'exécution: {metrics.get('uptime_seconds', 0):.1f}s")
    
    # Logger les métriques dans les fichiers de log
    agent.log_performance()

# Exécuter les exemples
if __name__ == "__main__":
    print("Démonstration du GeoAgent v3 avec infrastructure de logging")
    
    try:
        # Exemple de recherche de parcelles
        exemple_recherche_parcelles()
        
        # Exemple d'analyse de parcelle
        exemple_analyse_parcelle()
        
        # Exemple de recherche de parcelles forestières
        # Commenté car peut prendre beaucoup de temps
        # exemple_recherche_parcelles_forestieres()
        
        # Afficher les métriques
        exemple_metriques()
        
        print("\nDémonstration terminée")
        print(f"Les logs ont été générés dans le dossier: {Path('logs/geo_agent_v3').resolve()}")
        
    except KeyboardInterrupt:
        print("\nOpération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\nUne erreur s'est produite: {str(e)}")
    finally:
        # Réinitialiser les métriques
        agent.reset_metrics()
