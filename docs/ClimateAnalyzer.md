# Module d'analyse climatique (ClimateAnalyzer)

Le module ClimateAnalyzer intègre les données climatiques Climessences de l'ONF pour proposer des recommandations d'essences forestières adaptées au changement climatique.

## Fonctionnalités

- Identification des zones climatiques pour une parcelle donnée
- Recommandation d'espèces adaptées au climat actuel
- Anticipation de l'évolution de la compatibilité avec différents scénarios climatiques
- Intégration avec les modules de géotraitement pour des recommandations enrichies

## Architecture

Le module suit une architecture modulaire avec plusieurs composants spécialisés :

```
┌───────────────────────┐
│    ClimateAnalyzer    │
└─────────┬─────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│                                                        │
│  ┌─────────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │ClimateDataLoader│  │ClimateZone    │  │Species   │  │
│  │                 │  │Analyzer       │  │Recommender│  │
│  └─────────────────┘  └───────────────┘  └──────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Composants

- **ClimateAnalyzer** : Point d'entrée principal qui orchestre l'analyse climatique
- **ClimateDataLoader** : Gère le chargement des données climatiques (zones, compatibilité des espèces)
- **ClimateZoneAnalyzer** : Identifie les zones climatiques correspondant à une géométrie
- **SpeciesRecommender** : Calcule les scores et recommande les espèces adaptées

## Installation et prérequis

### Dépendances

- Python 3.8 ou supérieur
- geopandas
- shapely
- pandas
- matplotlib (pour les visualisations)

### Configuration

Le module utilise des données climatiques qui sont automatiquement générées si les fichiers n'existent pas :

```
data/climate/
├── climate_zones.geojson     # Zones climatiques avec leurs caractéristiques
├── species_compatibility.json # Compatibilité des espèces par zone et scénario
└── climate_scenarios.json    # Définition des scénarios climatiques
```

## Utilisation

### Initialisation

```python
from forestai.core.domain.services import ClimateAnalyzer

# Initialisation avec le répertoire de données par défaut
analyzer = ClimateAnalyzer()

# Ou avec un répertoire personnalisé
analyzer = ClimateAnalyzer(data_dir="chemin/vers/donnees")
```

### Analyse d'une parcelle

```python
from shapely.geometry import Polygon

# Créer une géométrie (exemple : rectangle en coordonnées Lambert 93)
geometry = Polygon([
    (650000, 6800000), (750000, 6800000), 
    (750000, 6700000), (650000, 6700000), 
    (650000, 6800000)
])

# Obtenir la zone climatique
climate_zone = analyzer.get_climate_zone(geometry)
print(f"Zone climatique: {climate_zone['name']}")
print(f"Température annuelle: {climate_zone['annual_temp']}°C")
print(f"Précipitations: {climate_zone['annual_precip']} mm")
```

### Recommandation d'espèces

```python
# Recommandation pour le climat actuel
current_recommendations = analyzer.recommend_species(
    geometry, 
    scenario="current",
    min_compatibility="suitable"
)

# Afficher les recommandations
for i, rec in enumerate(current_recommendations[:3], 1):
    print(f"{i}. {rec['species_name']} ({rec['common_name']})")
    print(f"   Score: {rec['global_score']}")
```

### Scénarios climatiques

```python
# Recommandation pour un scénario futur
future_recommendations = analyzer.recommend_species(
    geometry, 
    scenario="2050_rcp45",  # Scénario RCP 4.5 à l'horizon 2050
    min_compatibility="suitable"
)

# Comparaison entre scénarios
comparison = analyzer.compare_scenarios(
    geometry, 
    scenarios=["current", "2050_rcp45", "2050_rcp85"]
)
```

### Filtrage par risques

```python
# Filtrer les recommandations pour éviter certains risques
filtered_recommendations = analyzer.filter_recommendations_by_risks(
    current_recommendations,
    excluded_risks=["drought", "fire"]  # Éviter les espèces sensibles à la sécheresse et au feu
)
```

## Intégration avec le GeoAgent

Le ClimateAnalyzer est conçu pour s'intégrer avec le GeoAgent, permettant d'enrichir les analyses de terrain avec des recommandations climatiques :

```python
from forestai.agents.geo_agent.data_loaders.bdtopo import BDTopoLoader
from forestai.core.domain.services import ClimateAnalyzer

# Initialiser les deux modules
loader = BDTopoLoader()
analyzer = ClimateAnalyzer()

# Analyser une parcelle
terrain_analysis = loader.analyze_parcel(geometry)
climate_recommendations = analyzer.recommend_species(geometry, scenario="2050_rcp45")

# Filtrer les recommandations en fonction des contraintes de terrain
constraints = terrain_analysis.get("forestry_potential", {}).get("constraints", [])

if "pente_forte" in constraints:
    # Filtrer les espèces adaptées aux pentes fortes
    climate_recommendations = [r for r in climate_recommendations 
                               if r["species_name"] in ["Cedrus atlantica", "Pinus pinaster"]]

# Enrichir l'analyse de terrain avec les données climatiques
terrain_analysis["climate"] = {
    "zone": analyzer.get_climate_zone(geometry),
    "recommended_species": climate_recommendations[:3]
}
```

## Personnalisation des données

### Ajout de nouvelles zones climatiques

Pour ajouter des zones climatiques supplémentaires, modifiez le fichier `climate_zones.geojson` :

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "NOUVELLE_ZONE",
        "name": "Nouvelle Zone Climatique",
        "climate_type": "type_climat",
        "annual_temp": 12.5,
        "annual_precip": 900,
        "summer_drought_days": 20,
        "frost_days": 30
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [coordX1, coordY1],
            [coordX2, coordY2],
            [coordX3, coordY3],
            [coordX1, coordY1]
          ]
        ]
      }
    }
  ]
}
```

### Ajout de nouvelles espèces

Pour ajouter de nouvelles espèces, modifiez le fichier `species_compatibility.json` :

```json
{
  "Nouvelle Espece": {
    "common_name": "Nom commun",
    "climate_compatibility": {
      "ZONE1": {
        "current": "optimal",
        "2050_rcp45": "suitable",
        "2050_rcp85": "marginal"
      }
    },
    "risks": {
      "drought": "low",
      "frost": "medium",
      "pests": ["parasites connus"],
      "fire": "medium"
    },
    "growth_rate": "medium",
    "economic_value": "high",
    "ecological_value": "medium"
  }
}
```

## Exemple complet

Un exemple complet d'utilisation est disponible dans le fichier `examples/climate_analyzer_example.py`.

```bash
# Exécuter l'exemple
python examples/climate_analyzer_example.py
```

## Futures améliorations

- Intégration de données climatiques plus précises (mailles de 8km)
- Ajout de scénarios climatiques complémentaires (horizon 2070)
- Interface de visualisation des zones climatiques
- Calcul d'indicateurs de risque climatique par parcelle
- Export des recommandations au format PDF
