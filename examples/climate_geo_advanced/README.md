# Module d'analyse forestière avancée

Ce module est une version modulaire du script `climate_geo_advanced_example.py`, décomposé en plusieurs programmes spécialisés pour une meilleure maintenabilité et réutilisabilité.

## Architecture

Le module est organisé en plusieurs fichiers Python, chacun responsable d'une partie spécifique du processus d'analyse :

```
climate_geo_advanced/
├── __init__.py               # Définition du package
├── README.md                 # Ce fichier
├── data_preparation.py       # Préparation des données
├── geo_analysis.py           # Analyse géographique
├── climate_analysis.py       # Analyse climatique
├── recommendation_engine.py  # Recommandations d'espèces
├── visualization.py          # Génération de graphiques
├── report_generator.py       # Génération de rapports
└── main.py                   # Programme principal
```

## Fonctionnalités

### Préparation des données (`data_preparation.py`)
- Création de parcelles forestières de test
- Configuration du système de logging
- Création des répertoires de sortie

### Analyse géographique (`geo_analysis.py`)
- Analyse détaillée des caractéristiques du terrain
- Calcul du potentiel forestier
- Identification des contraintes et opportunités

### Analyse climatique (`climate_analysis.py`)
- Identification des zones climatiques
- Recommandation d'espèces adaptées au climat actuel et futur
- Analyse des risques climatiques (sécheresse, gel, incendie)

### Recommandations d'espèces (`recommendation_engine.py`)
- Filtrage des recommandations selon les contraintes terrain
- Ajustement des scores selon les priorités (économiques, écologiques)
- Combinaison des recommandations pour une gestion adaptative

### Visualisations (`visualization.py`)
- Graphiques de comparaison d'espèces recommandées
- Visualisations des risques climatiques
- Graphiques d'analyse du terrain
- Jauges de potentiel forestier

### Génération de rapports (`report_generator.py`)
- Rapports détaillés au format JSON, TXT et Markdown
- Rapports combinant analyses géospatiales et climatiques
- Export des données pour utilisation externe (CSV)

### Programme principal (`main.py`)
- Orchestration de l'ensemble du processus d'analyse
- Interface en ligne de commande configurable
- Gestion des priorités et préférences d'analyse

## Utilisation

### Exécution complète

Pour lancer une analyse complète avec les paramètres par défaut :

```bash
python main.py
```

### Options disponibles

Le programme accepte plusieurs options pour personnaliser l'analyse :

```bash
python main.py --output-dir data/mes_resultats --parcels F001 F003 --economic-priority 1.2 --ecological-priority 0.8
```

Options principales :
- `--output-dir` : Répertoire de sortie pour les résultats
- `--parcels` : IDs des parcelles à analyser (par défaut: toutes)
- `--no-charts` : Désactiver la génération de graphiques
- `--economic-priority` : Priorité économique (défaut: 1.0)
- `--ecological-priority` : Priorité écologique (défaut: 1.0)
- `--adaptation-weight` : Poids d'adaptation au changement climatique (défaut: 0.3)
- `--report-format` : Format des rapports à générer (défaut: all)
- `--verbose` : Activer les messages de débogage détaillés

## Utilisation des modules individuellement

Les modules peuvent également être utilisés individuellement pour des analyses spécifiques :

### Analyse géospatiale uniquement

```python
from data_preparation import create_real_world_parcels
from geo_analysis import batch_analyze_parcels

parcels = create_real_world_parcels()
geo_analyses = batch_analyze_parcels(parcels)

for analysis in geo_analyses:
    print(f"Parcelle {analysis['id']}: Potentiel {analysis['forestry_potential']['potential_score']:.2f}")
```

### Analyse climatique uniquement

```python
from data_preparation import create_real_world_parcels
from climate_analysis import init_climate_analyzer, batch_analyze_climate

parcels = create_real_world_parcels()
analyzer = init_climate_analyzer()
climate_analyses = batch_analyze_climate(parcels, analyzer)

for parcel_id, analysis in climate_analyses.items():
    zone = analysis["climate_zone"]
    print(f"Parcelle {parcel_id}: Zone {zone['name']}, Temp. {zone['annual_temp']}°C")
```

### Génération de graphiques

```python
from data_preparation import create_real_world_parcels, create_output_directories
from geo_analysis import simulate_detailed_geo_analysis
from climate_analysis import init_climate_analyzer, get_species_recommendations
from visualization import generate_species_comparison_chart

parcels = create_real_world_parcels()
output_dirs = create_output_directories("data/outputs/charts")
analyzer = init_climate_analyzer()

# Obtenir des recommandations
parcel = parcels.iloc[0]
recommendations = get_species_recommendations(analyzer, parcel["geometry"])

# Générer un graphique
generate_species_comparison_chart(
    recommendations,
    f"{parcel['id']}_{parcel['name']}",
    output_dirs["charts"]
)
```

## Extension du module

Pour étendre le module avec de nouvelles fonctionnalités :

1. **Nouveaux types d'analyses** : Créez un nouveau fichier Python pour votre analyse spécifique
2. **Nouveaux formats de rapports** : Étendez `report_generator.py` avec vos formats personnalisés
3. **Nouvelles visualisations** : Ajoutez vos graphiques dans `visualization.py`
4. **Support pour de nouvelles sources de données** : Modifiez `data_preparation.py`

## Dépendances

Ce module dépend des packages suivants :
- Packages internes de ForestAI : `forestai.core.domain.services`, `forestai.core.utils`
- Packages externes : `numpy`, `pandas`, `geopandas`, `matplotlib`, `seaborn`
