# examples/bdtopo_loader_example.py

import sys
import os
from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Polygon
import matplotlib.pyplot as plt

# Ajout du répertoire parent au path pour l'importation des modules locaux
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import des modules forestai
from forestai.core.utils.logging_config import LoggingConfig
from forestai.agents.geo_agent.data_loaders.bdtopo import BDTopoLoader

def setup_logging():
    """Configure le système de logging."""
    config = LoggingConfig.get_instance()
    config.init({
        "level": "INFO",
        "log_dir": "logs/examples/bdtopo",
        "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    })

def create_test_geometry():
    """Crée une géométrie de test pour les exemples."""
    # Créer un simple polygone carré en coordonnées Lambert 93
    minx, miny, maxx, maxy = 843000, 6278000, 844000, 6279000
    geometry = box(minx, miny, maxx, maxy)
    
    # Créer un GeoDataFrame
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geometry], crs="EPSG:2154")
    
    print(f"Géométrie de test créée: {geometry.wkt[:60]}...")
    print(f"Surface: {geometry.area / 10000:.2f} hectares")
    
    return geometry

def example_basic_loading():
    """Démontre le chargement de base des données BD TOPO."""
    print("\n=== Exemple de chargement de données BD TOPO ===")
    
    # Initialiser le chargeur
    loader = BDTopoLoader()
    
    # Afficher les thèmes disponibles
    themes = loader.get_available_themes()
    print(f"Thèmes disponibles: {', '.join(themes)}")
    
    # Obtenir un résumé des données
    summary = loader.get_summary()
    print(f"Résumé des données BD TOPO dans '{summary['data_dir']}':")
    print(f"  - {summary['themes_count']} thèmes")
    print(f"  - {summary['total_files_count']} fichiers au total")
    
    # Créer une géométrie de test
    geometry = create_test_geometry()
    
    # Charger les données pour un thème spécifique
    if "vegetation" in themes:
        print("\nChargement des données de végétation...")
        veg_data = loader.load_data_for_geometry("vegetation", geometry)
        if veg_data is not None:
            print(f"  - {len(veg_data)} entités de végétation trouvées")
            if not veg_data.empty:
                print(f"  - Colonnes disponibles: {', '.join(veg_data.columns)}")
    
    return loader, geometry

def example_vegetation_analysis(loader, geometry):
    """Démontre l'analyse de la végétation."""
    print("\n=== Exemple d'analyse de végétation ===")
    
    # Analyser la végétation
    print("Analyse de la végétation...")
    veg_result = loader.analyze_vegetation(geometry)
    
    # Afficher les résultats
    print(f"Végétation détectée: {veg_result['has_vegetation']}")
    print(f"Couverture végétale: {veg_result['vegetation_coverage']:.1f}%")
    
    if veg_result["dominant_vegetation"]:
        dom_veg = veg_result["dominant_vegetation"]
        print(f"Type de végétation dominant: {dom_veg['type']} ({dom_veg['category']})")
        print(f"  - Pourcentage: {dom_veg['percentage']:.1f}%")
        print(f"  - Surface: {dom_veg['area']/10000:.2f} hectares")
    
    return veg_result

def example_road_analysis(loader, geometry):
    """Démontre l'analyse du réseau routier."""
    print("\n=== Exemple d'analyse du réseau routier ===")
    
    # Analyser le réseau routier avec un buffer de 100m
    print("Analyse du réseau routier (buffer de 100m)...")
    road_result = loader.analyze_road_network(geometry, buffer_distance=100)
    
    # Afficher les résultats
    print(f"Accès routier: {road_result['has_road_access']}")
    if road_result["has_road_access"]:
        print(f"Distance à la route la plus proche: {road_result['nearest_road_distance']:.1f}m")
        print(f"Longueur totale du réseau routier: {road_result['road_network_length']:.1f}m")
        print(f"Densité du réseau routier: {road_result['road_density']:.1f}m/km²")
        
        # Afficher les types de routes si disponibles
        if road_result["road_types"]:
            print("Types de routes:")
            for road_type, count in road_result["road_types"].items():
                print(f"  - {road_type}: {count}")
    
    return road_result

def example_forestry_potential(loader, geometry):
    """Démontre le calcul du potentiel forestier."""
    print("\n=== Exemple de calcul du potentiel forestier ===")
    
    # Calculer le potentiel forestier
    print("Calcul du potentiel forestier...")
    potential_result = loader.calculate_forestry_potential(geometry, buffer_distance=100)
    
    # Afficher les résultats
    print(f"Potentiel forestier: {potential_result['potential_score']:.2f} ({potential_result['potential_class']})")
    
    # Afficher les contraintes
    if potential_result["constraints"]:
        print("Contraintes identifiées:")
        for constraint in potential_result["constraints"]:
            print(f"  - {constraint}")
    
    # Afficher les opportunités
    if potential_result["opportunities"]:
        print("Opportunités identifiées:")
        for opportunity in potential_result["opportunities"]:
            print(f"  - {opportunity}")
    
    # Afficher les espèces recommandées
    if potential_result["recommended_species"]:
        print("Espèces recommandées:")
        for species in potential_result["recommended_species"]:
            print(f"  - {species}")
    
    return potential_result

def example_complete_analysis(loader, geometry):
    """Démontre une analyse complète de parcelle."""
    print("\n=== Exemple d'analyse complète de parcelle ===")
    
    # Réaliser une analyse complète
    print("Analyse complète de la parcelle...")
    analysis = loader.analyze_parcel(geometry, buffer_distance=100)
    
    # Afficher les informations de base
    print(f"Surface: {analysis['area_ha']:.2f} hectares")
    print(f"Périmètre: {analysis['perimeter_m']:.1f} mètres")
    
    # Afficher le potentiel forestier
    potential = analysis["forestry_potential"]
    print(f"Potentiel forestier: {potential['potential_score']:.2f} ({potential['potential_class']})")
    
    # Enregistrer les résultats
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "parcel_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Conversion en dict sérialisable
        analysis_json = {}
        for k, v in analysis.items():
            if k != "geometry":  # Exclure la géométrie qui n'est pas sérialisable
                analysis_json[k] = v
        json.dump(analysis_json, f, ensure_ascii=False, indent=2)
    
    print(f"Résultats enregistrés dans {output_file}")
    
    return analysis

# Exécuter les exemples
if __name__ == "__main__":
    print("Démonstration du BDTopoLoader\n")
    setup_logging()
    
    try:
        # Configuration du chemin des données si nécessaire
        if len(sys.argv) > 1:
            os.environ["BDTOPO_DIR"] = sys.argv[1]
            print(f"Utilisation du répertoire de données: {sys.argv[1]}")
        
        # Charger les données de base
        loader, geometry = example_basic_loading()
        
        # Afficher le loader
        print(f"\nLoader: {loader}")
        
        # Analyses spécifiques
        veg_result = example_vegetation_analysis(loader, geometry)
        road_result = example_road_analysis(loader, geometry)
        potential_result = example_forestry_potential(loader, geometry)
        
        # Analyse complète
        analysis = example_complete_analysis(loader, geometry)
        
        print("\nDémonstration terminée!")
        
    except KeyboardInterrupt:
        print("\nOpération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\nUne erreur s'est produite: {str(e)}")
