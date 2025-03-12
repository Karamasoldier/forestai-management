# examples/corine_land_cover_example.py

import os
import sys
import time
from pathlib import Path
import json
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box, Point, Polygon
from dotenv import load_dotenv

# Ajout du répertoire parent au path pour l'importation des modules locaux
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import des modules forestai
from forestai.core.utils.logging_config import LoggingConfig
from forestai.agents.geo_agent.data_loaders.corine_land_cover_loader import CorineLandCoverLoader
from forestai.agents.geo_agent.terrain_services.terrain_coordinator import TerrainCoordinator

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
config = LoggingConfig.get_instance()
config.init({
    "level": "DEBUG",
    "log_dir": "logs/examples/corine",
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

def example_basic_clc_loading():
    """Exemple de chargement basique des données Corine Land Cover."""
    print("\n=== Exemple de chargement des données Corine Land Cover ===")
    
    # Créer le loader
    clc_loader = CorineLandCoverLoader()
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Charger les données CLC pour la géométrie
    print("Chargement des données Corine Land Cover...")
    start_time = time.time()
    clc_data = clc_loader.load_landcover_for_geometry(geometry)
    duration = time.time() - start_time
    
    # Afficher les résultats
    print(f"Chargement terminé en {duration:.2f}s")
    
    if clc_data is not None:
        print(f"Données chargées: {len(clc_data)} polygones CLC")
        print("\nAperçu des données:")
        print(clc_data[['code', 'label', 'category', 'overlap_area']].head())
        
        # Afficher les différentes catégories trouvées
        categories = clc_data['category'].value_counts()
        print("\nRépartition par catégories:")
        for category, count in categories.items():
            print(f"  - {category}: {count} polygones")
    else:
        print("Erreur: Aucune donnée Corine Land Cover n'a pu être chargée")
    
    return clc_data

def example_dominant_landcover():
    """Exemple d'analyse de l'occupation des sols dominante."""
    print("\n=== Exemple d'analyse de l'occupation des sols dominante ===")
    
    # Créer le loader
    clc_loader = CorineLandCoverLoader()
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Analyse de l'occupation des sols dominante
    print("Analyse de l'occupation des sols...")
    start_time = time.time()
    landcover = clc_loader.get_dominant_landcover(geometry)
    duration = time.time() - start_time
    
    # Afficher les résultats
    print(f"Analyse terminée en {duration:.2f}s")
    
    print(f"\nOccupation dominante: {landcover['dominant_label']}")
    print(f"Code CLC: {landcover['dominant_code']}")
    print(f"Catégorie: {landcover['dominant_category']}")
    print(f"Couverture: {landcover['coverage_percentage']:.1f}%")
    
    print("\nDétail des occupations des sols:")
    coverage_details = landcover['coverage_details']
    for code, details in coverage_details.items():
        print(f"  - {code} ({details['label']}): {details['percentage']:.1f}%")
    
    print("\nDétail par catégories:")
    category_details = landcover['category_details']
    for category, details in category_details.items():
        print(f"  - {category}: {details['percentage']:.1f}%")
    
    return landcover

def example_forestry_potential():
    """Exemple d'évaluation du potentiel forestier basé sur l'occupation des sols."""
    print("\n=== Exemple d'évaluation du potentiel forestier ===")
    
    # Créer le loader
    clc_loader = CorineLandCoverLoader()
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Calculer le potentiel forestier
    print("Calcul du potentiel forestier...")
    start_time = time.time()
    potential = clc_loader.calculate_forestry_potential(geometry)
    duration = time.time() - start_time
    
    # Afficher les résultats
    print(f"Calcul terminé en {duration:.2f}s")
    
    print(f"\nScore de potentiel forestier: {potential['potential_score']:.2f}/1.00")
    
    # Afficher les opportunités
    print("\nOpportunités identifiées:")
    for opportunity in potential['opportunities']:
        print(f"  ✓ {opportunity}")
    
    # Afficher les contraintes
    print("\nContraintes identifiées:")
    for constraint in potential['constraints']:
        print(f"  ✗ {constraint}")
    
    # Afficher les espèces recommandées
    print("\nEspèces recommandées:")
    for species in potential['recommended_species']:
        print(f"  • {species}")
    
    return potential

def example_integration_with_terrain_coordinator():
    """Exemple d'intégration avec le coordinateur de terrain."""
    print("\n=== Exemple d'intégration avec le coordinateur de terrain ===")
    
    # Créer le loader CLC
    clc_loader = CorineLandCoverLoader()
    
    # Créer le coordinateur de terrain
    terrain_coordinator = TerrainCoordinator(data_dir=data_dir)
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # 1. Analyser le terrain avec le coordinateur
    print("Analyse du terrain...")
    terrain_result = terrain_coordinator.analyze_terrain(
        geometry, 
        analysis_types=["elevation", "slope"],
        params={"elevation_resolution": 10, "compute_aspect": True}
    )
    
    # 2. Analyser l'occupation des sols avec CLC
    print("Analyse de l'occupation des sols...")
    clc_result = clc_loader.calculate_forestry_potential(geometry)
    
    # 3. Combiner les résultats pour une évaluation globale
    print("Combinaison des résultats...")
    
    # Exemple de calcul d'un score combiné
    terrain_score = 0.5  # Score par défaut si pas de données de terrain
    if terrain_result["success"] and "combined_stats" in terrain_result["results"]:
        terrain_score = terrain_result["results"]["combined_stats"].get("forestry_potential_score", 0.5)
    
    clc_score = clc_result["potential_score"]
    
    # Pondération: 60% terrain, 40% occupation des sols
    combined_score = (terrain_score * 0.6) + (clc_score * 0.4)
    
    # Afficher les résultats
    print("\nRésultats de l'analyse combinée:")
    print(f"  Score basé sur le terrain: {terrain_score:.2f}/1.00")
    print(f"  Score basé sur l'occupation des sols: {clc_score:.2f}/1.00")
    print(f"  Score combiné: {combined_score:.2f}/1.00")
    
    # Combinaison des contraintes et opportunités
    combined_constraints = []
    combined_opportunities = []
    
    # Ajouter les contraintes et opportunités du terrain
    if terrain_result["success"] and "combined_stats" in terrain_result["results"]:
        terrain_constraints = terrain_result["results"]["combined_stats"].get("constraints", [])
        terrain_opportunities = terrain_result["results"]["combined_stats"].get("opportunities", [])
        
        combined_constraints.extend(terrain_constraints)
        combined_opportunities.extend(terrain_opportunities)
    
    # Ajouter les contraintes et opportunités de l'occupation des sols
    combined_constraints.extend(clc_result["constraints"])
    combined_opportunities.extend(clc_result["opportunities"])
    
    # Afficher les contraintes et opportunités combinées
    if combined_constraints:
        print("\nContraintes de la parcelle:")
        for constraint in combined_constraints:
            print(f"  ✗ {constraint}")
    
    if combined_opportunities:
        print("\nOpportunités de la parcelle:")
        for opportunity in combined_opportunities:
            print(f"  ✓ {opportunity}")
    
    # Combinaison des espèces recommandées
    combined_species = []
    
    # Ajouter les espèces recommandées du terrain
    if terrain_result["success"] and "combined_stats" in terrain_result["results"]:
        terrain_species = terrain_result["results"]["combined_stats"].get("recommended_species", [])
        combined_species.extend(terrain_species)
    
    # Ajouter les espèces recommandées de l'occupation des sols
    combined_species.extend(clc_result["recommended_species"])
    
    # Dédupliquer
    combined_species = list(set(combined_species))
    
    if combined_species:
        print("\nEspèces recommandées (terrain + occupation des sols):")
        for species in combined_species:
            print(f"  • {species}")
    
    return {
        "terrain_score": terrain_score,
        "clc_score": clc_score,
        "combined_score": combined_score,
        "constraints": combined_constraints,
        "opportunities": combined_opportunities,
        "recommended_species": combined_species
    }

def visualize_clc_data(clc_data):
    """Visualise les données Corine Land Cover."""
    if clc_data is None or len(clc_data) == 0:
        print("Pas de données à visualiser")
        return
    
    print("\n=== Visualisation des données Corine Land Cover ===")
    
    # Créer une palette de couleurs pour les catégories
    category_colors = {
        "urban": "#FF0000",         # Rouge
        "agriculture": "#FFFF00",    # Jaune
        "forest": "#008000",         # Vert foncé
        "shrub": "#90EE90",          # Vert clair
        "open_space": "#A0522D",     # Marron
        "wetland": "#0000FF",        # Bleu
        "water": "#ADD8E6",          # Bleu clair
        "unknown": "#808080"         # Gris
    }
    
    # Préparer la figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Tracer les polygones colorés par catégorie
    for category in clc_data['category'].unique():
        subset = clc_data[clc_data['category'] == category]
        color = category_colors.get(category, "#000000")
        subset.plot(ax=ax, color=color, edgecolor='black', linewidth=0.5, label=category)
    
    # Ajouter un titre et une légende
    ax.set_title('Occupation des sols (Corine Land Cover)')
    ax.legend(title="Catégories")
    
    # Ajouter une échelle et une flèche d'orientation
    ax.set_xlabel('Coordonnées X (Lambert 93)')
    ax.set_ylabel('Coordonnées Y (Lambert 93)')
    
    # Créer le dossier de sortie s'il n'existe pas
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder le graphique
    output_path = output_dir / "corine_land_cover.png"
    plt.savefig(output_path)
    print(f"Visualisation sauvegardée dans {output_path}")
    
    # Afficher le graphique
    plt.tight_layout()
    plt.show()

# Exécuter les exemples
if __name__ == "__main__":
    print("Démonstration du loader Corine Land Cover")
    
    try:
        # Choix des exemples à exécuter
        run_basic_loading = True
        run_dominant_analysis = True
        run_potential_analysis = True
        run_integration = True
        run_visualization = True
        
        clc_data = None
        
        if run_basic_loading:
            print("\n--- Test du chargement basique ---")
            clc_data = example_basic_clc_loading()
        
        if run_dominant_analysis:
            print("\n--- Test de l'analyse de l'occupation dominante ---")
            example_dominant_landcover()
        
        if run_potential_analysis:
            print("\n--- Test de l'analyse du potentiel forestier ---")
            example_forestry_potential()
        
        if run_integration:
            print("\n--- Test de l'intégration avec le coordinateur de terrain ---")
            example_integration_with_terrain_coordinator()
        
        if run_visualization and clc_data is not None:
            visualize_clc_data(clc_data)
        
        print("\nDémonstration terminée")
        print(f"Les logs ont été générés dans le dossier: {Path('logs/examples/corine').resolve()}")
        
    except KeyboardInterrupt:
        print("\nOpération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\nUne erreur s'est produite: {str(e)}")
