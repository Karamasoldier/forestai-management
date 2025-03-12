# examples/terrain_services_example.py

import sys
import os
import time
from pathlib import Path
import json
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box, Point, Polygon

# Ajout du répertoire parent au path pour l'importation des modules locaux
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import des modules forestai
from forestai.core.utils.logging_config import LoggingConfig
from forestai.agents.geo_agent.terrain_services.elevation_service import ElevationService
from forestai.agents.geo_agent.terrain_services.slope_service import SlopeService
from forestai.agents.geo_agent.terrain_services.hydrology_service import HydrologyService
from forestai.agents.geo_agent.terrain_services.risk_service import RiskService
from forestai.agents.geo_agent.terrain_services.terrain_coordinator import TerrainCoordinator

# Configuration du logging
config = LoggingConfig.get_instance()
config.init({
    "level": "DEBUG",
    "log_dir": "logs/examples/terrain",
    "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
})

# Définir le répertoire des données
data_dir = os.environ.get("DATA_PATH", "data/raw")

def create_test_geometry():
    """Crée une géométrie de test pour les exemples."""
    # Option 1: Créer un simple polygone carré
    minx, miny, maxx, maxy = 843000, 6278000, 844000, 6279000  # Coordonnées Lambert 93
    geometry = box(minx, miny, maxx, maxy)
    
    # Option 2: Créer un polygone plus complexe
    # points = [
    #     (843000, 6278000),
    #     (844000, 6278000),
    #     (844200, 6278500),
    #     (843800, 6279000),
    #     (843000, 6278800),
    #     (843000, 6278000)
    # ]
    # geometry = Polygon(points)
    
    # Créer un GeoDataFrame
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geometry], crs="EPSG:2154")
    
    print(f"Géométrie de test créée: {geometry.wkt[:60]}...")
    
    return geometry

def example_elevation_service():
    """Exemple d'utilisation du service d'élévation."""
    print("\n=== Exemple du Service d'Élévation ===")
    
    # Créer le service
    elevation_service = ElevationService(data_dir, log_level="INFO")
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Analyser l'élévation
    print("Analyse de l'élévation...")
    start_time = time.time()
    elevation_result = elevation_service.analyze_elevation(geometry, resolution=10)
    duration = time.time() - start_time
    
    # Afficher les résultats
    print(f"Analyse terminée en {duration:.2f}s")
    
    if "elevation_mean" in elevation_result:
        print(f"Élévation moyenne: {elevation_result['elevation_mean']:.1f}m")
        print(f"Élévation min: {elevation_result['elevation_min']:.1f}m")
        print(f"Élévation max: {elevation_result['elevation_max']:.1f}m")
    else:
        print("Données d'élévation non disponibles ou erreur")
    
    return elevation_result

def example_slope_service(elevation_data=None):
    """Exemple d'utilisation du service de pente."""
    print("\n=== Exemple du Service de Pente ===")
    
    # Créer le service
    slope_service = SlopeService(data_dir, log_level="INFO")
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Analyser la pente
    print("Analyse de la pente...")
    start_time = time.time()
    
    if elevation_data and "elevation_array" in elevation_data:
        print("Utilisation des données d'élévation existantes")
        slope_result = slope_service.calculate_slope_from_elevation(
            elevation_data["elevation_array"],
            elevation_data.get("transform"),
            compute_aspect=True
        )
    else:
        slope_result = slope_service.analyze_slope(geometry, compute_aspect=True)
    
    duration = time.time() - start_time
    
    # Afficher les résultats
    print(f"Analyse terminée en {duration:.2f}s")
    
    if "slope_mean" in slope_result:
        print(f"Pente moyenne: {slope_result['slope_mean']:.1f}°")
        print(f"Pente max: {slope_result['slope_max']:.1f}°")
        
        if "aspect_mean" in slope_result:
            print(f"Orientation moyenne: {slope_result['aspect_mean']:.1f}°")
            print(f"Orientation dominante: {slope_result.get('aspect_class', 'N/A')}")
    else:
        print("Données de pente non disponibles ou erreur")
    
    return slope_result

def example_hydrology_service():
    """Exemple d'utilisation du service hydrologique."""
    print("\n=== Exemple du Service Hydrologique ===")
    
    # Créer le service
    hydrology_service = HydrologyService(data_dir, log_level="INFO")
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Analyser l'hydrologie
    print("Analyse hydrologique...")
    start_time = time.time()
    hydro_result = hydrology_service.analyze_hydrology(
        geometry, 
        buffer_distance=100,
        include_water_bodies=True
    )
    duration = time.time() - start_time
    
    # Afficher les résultats
    print(f"Analyse terminée en {duration:.2f}s")
    
    if "has_water_access" in hydro_result:
        print(f"Accès à l'eau: {hydro_result['has_water_access']}")
        print(f"Distance au cours d'eau le plus proche: {hydro_result.get('nearest_river_distance', 'N/A')}m")
        
        water_bodies = hydro_result.get("water_bodies", [])
        if water_bodies:
            print(f"Masses d'eau à proximité: {len(water_bodies)}")
            for i, wb in enumerate(water_bodies[:2]):  # Afficher seulement les 2 premiers
                print(f"  {i+1}. Type: {wb.get('type')}, Surface: {wb.get('area', 0):.1f}m²")
    else:
        print("Données hydrologiques non disponibles ou erreur")
    
    return hydro_result

def example_risk_service():
    """Exemple d'utilisation du service de risque."""
    print("\n=== Exemple du Service d'Analyse des Risques ===")
    
    # Créer le service
    risk_service = RiskService(data_dir, log_level="INFO")
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Analyser tous les risques
    print("Analyse complète des risques...")
    start_time = time.time()
    risk_result = risk_service.analyze_all_risks(geometry, {"season": "summer"})
    duration = time.time() - start_time
    
    # Afficher les résultats
    print(f"Analyse terminée en {duration:.2f}s")
    
    if "global_risk_level" in risk_result:
        print(f"Niveau de risque global: {risk_result['global_risk_level']}")
        print(f"Score de risque global: {risk_result.get('global_risk_score', 'N/A')}")
        
        # Afficher les risques individuels
        risk_types = ["flood_risk", "fire_risk", "erosion_risk", "landslide_risk"]
        for risk_type in risk_types:
            if risk_type in risk_result:
                risk_info = risk_result[risk_type]
                level = risk_info.get(f"{risk_type}_level", "N/A")
                score = risk_info.get(f"{risk_type}_score", "N/A")
                print(f"  {risk_type}: niveau={level}, score={score}")
        
        # Afficher les recommandations
        recommendations = risk_result.get("recommendations", [])
        if recommendations:
            print("\nRecommandations:")
            for i, rec in enumerate(recommendations):
                print(f"  {i+1}. {rec}")
    else:
        print("Données de risque non disponibles ou erreur")
    
    return risk_result

def example_terrain_coordinator():
    """Exemple d'utilisation du coordinateur de terrain."""
    print("\n=== Exemple du Coordinateur de Terrain ===")
    
    # Créer le coordinateur
    coordinator = TerrainCoordinator(data_dir, log_level="INFO", use_parallel=True)
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Paramètres d'analyse
    params = {
        "elevation_resolution": 10,
        "compute_aspect": True,
        "hydro_buffer": 100,
        "season": "summer",
        "include_water_bodies": True
    }
    
    # 1. Exécuter toutes les analyses
    print("Exécution de toutes les analyses de terrain...")
    start_time = time.time()
    result_all = coordinator.analyze_terrain(geometry, analysis_types=None, params=params)
    duration = time.time() - start_time
    
    print(f"Analyses complètes terminées en {duration:.2f}s")
    print(f"Succès: {result_all['success']}")
    
    if "results" in result_all and "combined_stats" in result_all["results"]:
        combined_stats = result_all["results"]["combined_stats"]
        print(f"Score de potentiel forestier: {combined_stats.get('forestry_potential_score', 'N/A')}")
        print(f"Classe de potentiel: {combined_stats.get('forestry_potential_class', 'N/A')}")
        
        # Afficher les contraintes
        constraints = combined_stats.get("constraints", [])
        if constraints:
            print("\nContraintes identifiées:")
            for constraint in constraints:
                print(f"  - {constraint}")
        
        # Afficher les opportunités
        opportunities = combined_stats.get("opportunities", [])
        if opportunities:
            print("\nOpportunités identifiées:")
            for opportunity in opportunities:
                print(f"  - {opportunity}")
        
        # Afficher les espèces recommandées
        species = combined_stats.get("recommended_species", [])
        if species:
            print("\nEspèces recommandées:")
            for sp in species:
                print(f"  - {sp}")
    
    # 2. Exécuter seulement certaines analyses
    print("\nExécution d'analyses spécifiques (élévation et risques)...")
    start_time = time.time()
    result_partial = coordinator.analyze_terrain(
        geometry, 
        analysis_types=["elevation", "risks"],
        params=params
    )
    duration = time.time() - start_time
    
    print(f"Analyses partielles terminées en {duration:.2f}s")
    print(f"Types d'analyses effectuées: {', '.join(result_partial.get('results', {}).keys())}")
    
    return result_all

def visualize_results(results):
    """Visualise certains résultats d'analyse."""
    print("\n=== Visualisation des résultats ===")
    
    if not results or "results" not in results:
        print("Pas de résultats à visualiser")
        return
    
    # Vérifier si nous avons des données pour visualiser
    has_elevation = "elevation" in results["results"] and "elevation_array" in results["results"]["elevation"]
    has_slope = "slope" in results["results"] and "slope_array" in results["results"]["slope"]
    
    if not has_elevation and not has_slope:
        print("Pas de données d'élévation ou de pente pour la visualisation")
        return
    
    # Préparer le graphique
    fig, axes = plt.subplots(1, 3 if has_slope else 1, figsize=(15, 5))
    axes = [axes] if not has_slope else axes
    
    # Visualiser l'élévation
    if has_elevation:
        elevation_data = results["results"]["elevation"]
        elevation_array = elevation_data["elevation_array"]
        
        im = axes[0].imshow(elevation_array, cmap='terrain')
        axes[0].set_title("Modèle d'élévation")
        fig.colorbar(im, ax=axes[0], label='Altitude (m)')
    
    # Visualiser la pente
    if has_slope:
        slope_data = results["results"]["slope"]
        slope_array = slope_data["slope_array"]
        
        im = axes[1].imshow(slope_array, cmap='YlOrRd')
        axes[1].set_title('Carte des pentes')
        fig.colorbar(im, ax=axes[1], label='Pente (°)')
        
        # Visualiser l'orientation
        if "aspect_array" in slope_data:
            aspect_array = slope_data["aspect_array"]
            im = axes[2].imshow(aspect_array, cmap='hsv')
            axes[2].set_title('Carte des orientations')
            fig.colorbar(im, ax=axes[2], label='Orientation (°)')
    
    plt.tight_layout()
    
    # Créer le dossier de sortie s'il n'existe pas
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder le graphique
    output_path = output_dir / "terrain_analysis.png"
    plt.savefig(output_path)
    print(f"Visualisation sauvegardée dans {output_path}")
    
    # Afficher le graphique
    plt.show()

# Exécuter les exemples
if __name__ == "__main__":
    print("Démonstration des services d'analyse de terrain")
    
    try:
        # Choix des exemples à exécuter
        run_individual_services = False
        run_coordinator = True
        visualize = True
        
        results = None
        
        if run_individual_services:
            print("\n--- Tests des services individuels ---")
            elevation_data = example_elevation_service()
            slope_data = example_slope_service(elevation_data)
            hydro_data = example_hydrology_service()
            risk_data = example_risk_service()
        
        if run_coordinator:
            print("\n--- Test du coordinateur de terrain ---")
            results = example_terrain_coordinator()
        
        if visualize and results:
            visualize_results(results)
        
        print("\nDémonstration terminée")
        print(f"Les logs ont été générés dans le dossier: {Path('logs/examples/terrain').resolve()}")
        
    except KeyboardInterrupt:
        print("\nOpération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\nUne erreur s'est produite: {str(e)}")
