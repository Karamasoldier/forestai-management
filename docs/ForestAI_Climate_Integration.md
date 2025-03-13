# Intégration de l'analyse climatique dans ForestAI

Ce document détaille l'intégration du module d'analyse climatique (`ClimateAnalyzer`) avec les fonctionnalités existantes de ForestAI, notamment l'agent de géotraitement (`GeoAgent`).

## Vue d'ensemble

Le module d'analyse climatique (`ClimateAnalyzer`) permet d'enrichir les analyses géospatiales avec des recommandations d'espèces forestières adaptées au climat actuel et futur. Cette intégration offre une perspective plus complète pour la gestion forestière dans un contexte de changement climatique.

```
┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │
│     GeoAgent      │◄────►│  ClimateAnalyzer  │
│                   │      │                   │
└───────┬───────────┘      └────────┬──────────┘
        │                           │
        │                           │
        ▼                           ▼
┌───────────────────────────────────────────────┐
│                                               │
│           Rapport forestier intégré           │
│                                               │
└───────────────────────────────────────────────┘
```

## Fonctionnalités principales

L'intégration du module climatique permet de:

1. **Identifier les zones climatiques** pour une parcelle forestière
2. **Recommander des espèces adaptées** au climat actuel et futur
3. **Filtrer les recommandations** en fonction des contraintes de terrain identifiées par le GeoAgent
4. **Générer des rapports combinés** intégrant analyses de terrain et analyses climatiques
5. **Visualiser les résultats** sous forme de graphiques et cartes

## Architecture modulaire

Le module d'analyse climatique suit une architecture modulaire:

- **ClimateAnalyzer**: Orchestrateur principal qui coordonne l'analyse climatique
- **ClimateDataLoader**: Gère le chargement des données climatiques
- **ClimateZoneAnalyzer**: Identifie les zones climatiques pour une géométrie
- **SpeciesRecommender**: Calcule les scores et recommande les espèces adaptées

Cette architecture modulaire permet d'intégrer facilement le module avec d'autres composants de ForestAI et de l'étendre avec de nouvelles fonctionnalités.

## Workflow d'intégration

### 1. Analyse géospatiale avec le GeoAgent

Premièrement, le GeoAgent analyse une parcelle forestière pour identifier:
- Les caractéristiques du terrain (pente, exposition, altitude)
- Les contraintes (accessibilité, risques naturels)
- Les opportunités (proximité des routes, qualité du sol)
- Le potentiel forestier global

```python
from forestai.agents.geo_agent.data_loaders.bdtopo import BDTopoLoader

loader = BDTopoLoader()
terrain_analysis = loader.analyze_parcel(geometry)
```

### 2. Analyse climatique

Ensuite, le ClimateAnalyzer identifie la zone climatique et recommande des espèces adaptées:

```python
from forestai.core.domain.services import ClimateAnalyzer

analyzer = ClimateAnalyzer()
climate_zone = analyzer.get_climate_zone(geometry)
current_recommendations = analyzer.recommend_species(geometry, scenario="current")
future_recommendations = analyzer.recommend_species(geometry, scenario="2050_rcp45")
```

### 3. Intégration des analyses

Les contraintes de terrain identifiées par le GeoAgent sont utilisées pour filtrer les recommandations climatiques:

```python
constraints = terrain_analysis.get("forestry_potential", {}).get("constraints", [])

filtered_recommendations = current_recommendations.copy()

if "pente_forte" in constraints:
    # Filtrer les espèces adaptées aux pentes fortes
    filtered_recommendations = [r for r in filtered_recommendations 
                              if r["risks"].get("erosion", "high") != "high"]

if "sol_sec" in constraints:
    # Filtrer les espèces tolérantes à la sécheresse
    filtered_recommendations = [r for r in filtered_recommendations 
                              if r["risks"].get("drought", "high") != "high"]
```

### 4. Génération de rapports combinés

Finalement, un rapport intégré est généré, combinant les analyses géospatiales et climatiques:

```python
combined_analysis = {
    "geo_analysis": terrain_analysis,
    "climate": {
        "zone": climate_zone,
        "current_recommendations": filtered_recommendations,
        "future_recommendations": future_recommendations
    },
    "integrated_score": calculate_integrated_score(terrain_analysis, filtered_recommendations)
}
```

## Exemples d'utilisation

Un exemple complet d'intégration est disponible dans `examples/climate_geo_integration_example.py`. Cet exemple montre comment:

1. Analyser plusieurs parcelles dans différentes régions de France
2. Obtenir les analyses géospatiales et climatiques
3. Combiner les analyses en un rapport intégré
4. Visualiser les recommandations d'espèces

```bash
# Exécuter l'exemple d'intégration
python examples/climate_geo_integration_example.py
```

## Formats de sortie

L'intégration produit plusieurs types de sorties:

### 1. Rapports JSON

Les rapports JSON contiennent l'ensemble des analyses, structurées par sections:

```json
{
  "region": "Provence",
  "area_ha": 250.0,
  "geo_analysis": { ... },
  "climate": {
    "zone": { ... },
    "current_recommendations": [ ... ],
    "future_recommendations": [ ... ]
  },
  "integrated_analysis": {
    "overall_score": 0.72,
    "overall_class": "Bon",
    "notes": [ ... ]
  }
}
```

### 2. Rapports texte

Les rapports texte présentent l'information de manière plus lisible pour les utilisateurs:

```
RAPPORT D'ANALYSE FORESTIÈRE - PROVENCE
============================================================

Surface analysée: 250.00 hectares
Potentiel forestier: Moyen (0.65/1.00)
Accessibilité: Moyenne

CONTRAINTES TERRAIN:
- sécheresse_estivale
- risque_incendie_élevé
- sol_sec

...

ESSENCES RECOMMANDÉES (CLIMAT ACTUEL):
1. Quercus pubescens (Chêne pubescent) - Score: 0.82
2. Pinus pinaster (Pin maritime) - Score: 0.79
...
```

### 3. Visualisations

Des visualisations graphiques présentent les recommandations d'espèces pour les climats actuel et futur:

![Exemple de visualisation](../data/outputs/climate_geo_integration/recommandations_Provence.png)

## Extension et personnalisation

Le module d'analyse climatique et son intégration peuvent être étendus de plusieurs façons:

### 1. Ajout de nouvelles zones climatiques

Pour ajouter de nouvelles zones climatiques, modifiez ou ajoutez des entrées dans `data/climate/climate_zones.geojson`:

```json
{
  "type": "Feature",
  "properties": {
    "id": "ZONE_ID",
    "name": "Nom de la zone",
    "climate_type": "type_climat",
    "annual_temp": 12.5,
    "annual_precip": 900,
    "summer_drought_days": 20,
    "frost_days": 30
  },
  "geometry": { ... }
}
```

### 2. Ajout de nouvelles espèces

Pour ajouter de nouvelles espèces, modifiez ou ajoutez des entrées dans `data/climate/species_compatibility.json`:

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
    "risks": { ... },
    "growth_rate": "medium",
    "economic_value": "high",
    "ecological_value": "medium"
  }
}
```

### 3. Ajout de nouveaux scénarios climatiques

Pour ajouter de nouveaux scénarios climatiques, modifiez ou ajoutez des entrées dans `data/climate/climate_scenarios.json`:

```json
{
  "2070_rcp85": {
    "description": "Scénario pessimiste (RCP 8.5) à l'horizon 2070",
    "time_horizon": "2070",
    "rcp": 8.5,
    "details": "Scénario de continuité des émissions de GES à un niveau élevé"
  }
}
```

## Futures améliorations

Les améliorations prévues pour cette intégration incluent:

1. **Cartographie spatiale des zones climatiques** pour visualiser la distribution des zones sur la parcelle
2. **Indicateurs de risque climatique** calculés spécifiquement pour chaque parcelle
3. **Recommandations d'actions d'adaptation** en fonction des vulnérabilités identifiées
4. **Génération de rapports PDF** combinant texte, tableaux et visualisations
5. **Intégration avec API météo** pour des analyses climatiques en temps réel
6. **Modèles prédictifs** pour l'évolution du potentiel forestier sous différents scénarios climatiques

## Références

- Documentation de l'ONF sur Climessences: [https://climessences.fr/](https://climessences.fr/)
- GIEC, 2021 : Changement climatique 2021 : les éléments scientifiques
- Guide des essences forestières pour l'adaptation au changement climatique (INRAE)
