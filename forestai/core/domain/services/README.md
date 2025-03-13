# Services de domaine pour ForestAI

Ce répertoire contient les services de domaine qui implémentent la logique métier centrale de ForestAI, indépendamment des agents qui les utilisent.

## Module d'analyse climatique

Le module d'analyse climatique (`ClimateAnalyzer`) permet d'analyser les données climatiques et de recommander des espèces forestières adaptées au climat actuel et futur. Il suit une architecture modulaire avec les composants suivants :

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

### ClimateAnalyzer

Le `ClimateAnalyzer` est le point d'entrée principal qui orchestre l'analyse climatique. Il fournit une interface simplifiée pour :
- Obtenir la zone climatique pour une géométrie donnée
- Recommander des espèces adaptées à différents scénarios climatiques
- Comparer les recommandations entre plusieurs scénarios
- Filtrer les recommandations en fonction des risques

```python
from forestai.core.domain.services import ClimateAnalyzer

# Initialisation
analyzer = ClimateAnalyzer()

# Analyse d'une parcelle
climate_zone = analyzer.get_climate_zone(geometry)
recommendations = analyzer.recommend_species(geometry, scenario="2050_rcp45")
```

### ClimateDataLoader

Le `ClimateDataLoader` est responsable du chargement des données climatiques depuis les fichiers (ou de leur création si nécessaire). Il gère :
- Les zones climatiques (climate_zones.geojson)
- La compatibilité des espèces (species_compatibility.json)
- Les scénarios climatiques (climate_scenarios.json)

```python
from forestai.core.domain.services import ClimateDataLoader

# Initialisation avec répertoire personnalisé
loader = ClimateDataLoader(data_dir="path/to/climate/data")

# Chargement des données
data = loader.load_or_create_data()
```

### ClimateZoneAnalyzer

Le `ClimateZoneAnalyzer` identifie les zones climatiques correspondant à une géométrie donnée. Il permet de :
- Trouver la zone climatique qui contient une géométrie
- Obtenir des informations sur les caractéristiques climatiques d'une zone
- Rechercher des zones par identifiant ou par région

```python
from forestai.core.domain.services import ClimateZoneAnalyzer

# Initialisation avec des zones climatiques
zone_analyzer = ClimateZoneAnalyzer(climate_zones_gdf)

# Identification d'une zone climatique
zone = zone_analyzer.get_climate_zone(geometry)
```

### SpeciesRecommender

Le `SpeciesRecommender` calcule des recommandations d'espèces forestières adaptées à différentes zones climatiques et scénarios. Il fournit des fonctionnalités pour :
- Filtrer les espèces compatibles avec une zone et un scénario
- Calculer des scores basés sur plusieurs critères (climatique, économique, écologique, risques)
- Classer les espèces selon leur tolérance à différents risques
- Filtrer les recommandations selon des contraintes spécifiques

```python
from forestai.core.domain.services import SpeciesRecommender

# Initialisation
recommender = SpeciesRecommender(species_compatibility_data)

# Recommandation d'espèces
compatible_species = recommender.get_compatible_species("ZONE_ID", "current")
recommendations = recommender.recommend_species("ZONE_ID", "2050_rcp45")
```

## Données climatiques

Le module utilise trois types de données climatiques qui sont automatiquement générées si les fichiers n'existent pas :

### 1. Zones climatiques (climate_zones.geojson)

Définit les zones climatiques avec leurs caractéristiques :
- Identifiant et nom de la zone
- Type de climat (continental, océanique, méditerranéen, etc.)
- Température annuelle moyenne (°C)
- Précipitations annuelles (mm)
- Jours de sécheresse estivale
- Jours de gel
- Géométrie de la zone (polygone)

### 2. Compatibilité des espèces (species_compatibility.json)

Définit la compatibilité des espèces forestières avec les différentes zones climatiques et scénarios :
- Nom botanique et nom commun de l'espèce
- Compatibilité par zone et par scénario (optimal, suitable, marginal, unsuitable)
- Risques (sécheresse, gel, incendie, parasites)
- Valeur économique et écologique
- Vitesse de croissance

### 3. Scénarios climatiques (climate_scenarios.json)

Définit les scénarios climatiques utilisés pour les recommandations :
- Climat actuel (période de référence)
- Scénarios futurs avec différents RCP et horizons temporels
- Description détaillée de chaque scénario

## Intégration avec d'autres modules

Le module d'analyse climatique est conçu pour s'intégrer avec d'autres modules de ForestAI, notamment :

### Intégration avec le GeoAgent

```python
from forestai.agents.geo_agent.data_loaders.bdtopo import BDTopoLoader
from forestai.core.domain.services import ClimateAnalyzer

# Initialiser les deux modules
loader = BDTopoLoader()
analyzer = ClimateAnalyzer()

# Analyser une parcelle
terrain_analysis = loader.analyze_parcel(geometry)
climate_recommendations = analyzer.recommend_species(geometry)

# Filtrer les recommandations en fonction des contraintes de terrain
constraints = terrain_analysis.get("constraints", [])
if "pente_forte" in constraints:
    # Filtrer pour les espèces adaptées aux pentes fortes
    climate_recommendations = analyzer.filter_recommendations_by_risks(
        climate_recommendations, ["erosion"]
    )
```

Pour plus de détails sur l'intégration avec le GeoAgent, consultez [ForestAI_Climate_Integration.md](../../../../docs/ForestAI_Climate_Integration.md).

## Exemples d'utilisation

Des exemples d'utilisation sont disponibles dans le répertoire `examples/` :

- `climate_analyzer_example.py` : Utilisation basique du module d'analyse climatique
- `climate_geo_integration_example.py` : Intégration avec le GeoAgent et génération de rapports combinés

## Futures améliorations

Les améliorations prévues pour ce module incluent :

1. Intégration de données climatiques à plus haute résolution spatiale
2. Ajout de scénarios climatiques plus précis (horizon 2070/2100)
3. Calcul d'indicateurs de risque climatique spécifiques aux parcelles
4. Interface de visualisation des zones climatiques
5. Intégration avec des API météo pour des données en temps réel
