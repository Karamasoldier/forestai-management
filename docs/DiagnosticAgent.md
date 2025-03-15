# Agent de diagnostic forestier (DiagnosticAgent)

L'agent de diagnostic forestier (DiagnosticAgent) est responsable de l'analyse des données terrain pour générer des diagnostics forestiers complets et des plans de gestion adaptés.

## Fonctionnalités principales

- Analyse des données d'inventaire forestier
- Génération de diagnostics forestiers
- Création de plans de gestion adaptés
- Production de rapports professionnels (HTML, PDF)
- Analyse de la structure du peuplement
- Calcul d'indices de diversité et d'estimation de volumes
- Recommandations d'espèces tenant compte du climat actuel et futur

## Architecture du DiagnosticAgent

Le DiagnosticAgent utilise une architecture modulaire avec plusieurs composants spécialisés :

```
forestai/agents/diagnostic_agent/
├── __init__.py                # Point d'entrée du module
├── diagnostic_agent.py       # Agent principal
├── inventory_analyzer.py     # Analyseur d'inventaire forestier
├── report_generator.py       # Générateur de rapports HTML/PDF
├── graph_generators/         # Générateurs de graphiques
│   ├── __init__.py
│   ├── diagnostic_graphs.py
│   └── management_plan_graphs.py
├── templates/                # Templates HTML
│   ├── __init__.py
│   ├── diagnostic_template.py
│   └── management_plan_template.py
└── data/                    # Données de référence
```

## Utilisation de base

### En ligne de commande

```bash
# Générer un diagnostic pour une parcelle
python run.py --agent diagnostic --action generate_diagnostic --params '{"parcel_id": "123456789"}'

# Générer un plan de gestion avec des objectifs spécifiques
python run.py --agent diagnostic --action generate_management_plan --params '{"parcel_id": "123456789", "goals": ["production", "resilience"], "horizon_years": 15}'

# Analyser un inventaire forestier
python run.py --agent diagnostic --action analyze_inventory --params '{"inventory_file": "path/to/inventory.csv"}'
```

### Via l'API REST

#### Endpoint de diagnostic

```http
POST /api/v1/diagnostic/generate
Content-Type: application/json

{
  "parcel_id": "123456789",
  "include_climate_data": true
}
```

#### Endpoint de plan de gestion

```http
POST /api/v1/diagnostic/management_plan
Content-Type: application/json

{
  "parcel_id": "123456789",
  "goals": ["production", "biodiversity", "resilience"],
  "horizon_years": 20
}
```

## Format d'entrée pour les données d'inventaire

L'agent accepte plusieurs formats d'entrée pour les données d'inventaire :

### Format CSV

Le format CSV doit contenir les colonnes suivantes :
- `species` : Nom de l'espèce (obligatoire)
- `diameter` : Diamètre en cm (recommandé)
- `height` : Hauteur en m (recommandé)
- `health_status` : État sanitaire (optionnel)
- `health_issue` : Problème sanitaire spécifique (optionnel)
- `x` et `y` : Coordonnées relatives ou GPS (optionnel)

### Format JSON

```json
{
  "area": 5.2,  // Surface en hectares
  "area_unit": "ha",  // Unité de surface (ha, m2)
  "items": [
    {
      "species": "Pinus sylvestris",
      "diameter": 25.4,
      "height": 15.2,
      "health_status": "healthy"
    },
    {
      "species": "Quercus robur",
      "diameter": 42.1,
      "height": 18.5,
      "health_status": "stressed",
      "health_issue": "drought"
    }
  ]
}
```

## Métriques calculées

L'analyseur d'inventaire calcule automatiquement les métriques suivantes :

### Métriques de base

- **Distribution des espèces** : Nombre et pourcentage d'arbres par espèce
- **Statistiques dimensionnelles** : Moyennes, médianes, écarts-types et quantiles des diamètres et hauteurs
- **Densité** : Nombre d'arbres par hectare

### Volumes

- **Volume total** : Estimation du volume de bois sur pied (m³)
- **Volume par espèce** : Ventilation du volume par espèce
- **Volume par classe de diamètre** : Distribution du volume par classes de diamètre

### Structure du peuplement

- **Distribution des diamètres** : Analyse de la normalité et classification du type de structure (régulière, irrégulière, bimodale)
- **Structure verticale** : Analyse par strates (régénération, sous-étage, étage intermédiaire, étage dominant)

### Biodiversité

- **Richesse spécifique** : Nombre d'espèces présentes
- **Indice de Shannon** : Mesure de la diversité spécifique
- **Indice de Simpson** : Mesure de la probabilité que deux arbres pris au hasard soient d'espèces différentes
- **Équitabilité de Pielou** : Mesure de l'égalité de la distribution des espèces

### État sanitaire (si disponible)

- **Distribution sanitaire** : Proportion d'arbres par état sanitaire
- **Score sanitaire global** : Note sur 100% de l'état sanitaire du peuplement
- **Problèmes majeurs** : Identification des problèmes sanitaires principaux

## Plans de gestion

Les plans de gestion générés contiennent les éléments suivants :

- **Résumé du plan** : Présentation des objectifs et du contexte
- **Horizon temporel** : Définition de la période couverte par le plan
- **Phases d'intervention** : Chronologie des actions à mener
- **Espèces recommandées** : Recommandations adaptées au climat et aux objectifs
- **Coûts estimés** : Évaluation économique par phase
- **Plan de suivi** : Indicateurs à surveiller et fréquence
- **Considérations climatiques** : Prise en compte du changement climatique

### Types d'objectifs disponibles

- **production** : Optimisation de la production de bois
- **resilience** : Adaptation au changement climatique
- **biodiversity** : Préservation et amélioration de la biodiversité
- **restoration** : Restauration d'écosystèmes dégradés
- **carbon** : Séquestration carbone
- **recreation** : Usages récréatifs et paysagers

## Formats de rapports

Le DiagnosticAgent peut générer des rapports dans différents formats :

- **HTML** : Rapports interactifs avec graphiques
- **PDF** : Documents formels pour impression
- **JSON** : Données structurées pour intégration API

## Intégration avec d'autres agents

Le DiagnosticAgent s'intègre nativement avec :

- **GeoAgent** : Pour récupérer les données géospatiales des parcelles
- **ClimateAnalyzer** : Pour les recommandations d'espèces adaptées au climat
- **SubsidyAgent** : Pour identifier les subventions disponibles selon le diagnostic

### Exemple d'intégration avec GeoAgent et ClimateAnalyzer

```python
from forestai.agents.diagnostic_agent import DiagnosticAgent
from forestai.agents.geo_agent import GeoAgent
from forestai.core.domain.services import ClimateAnalyzer

# Initialisation des agents
geo_agent = GeoAgent()
diagnostic_agent = DiagnosticAgent()
climate_analyzer = ClimateAnalyzer()

# Récupération des données géospatiales
parcel_data = geo_agent.get_parcel_info("123456789")

# Analyse climatique
climate_data = climate_analyzer.analyze_climate(parcel_data["geometry"])

# Intégration dans le diagnostic
diagnostic = diagnostic_agent.generate_diagnostic(
    parcel_id="123456789",
    parcel_data=parcel_data,
    climate_data=climate_data
)

# Génération d'un plan de gestion adapté au climat
management_plan = diagnostic_agent.generate_management_plan(
    parcel_id="123456789", 
    diagnostic=diagnostic,
    goals=["production", "resilience"],
    horizon_years=15
)

# Export du plan en PDF
pdf_bytes = diagnostic_agent.report_generator.generate_management_plan_report_pdf(management_plan, diagnostic)
with open("plan_gestion.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## Configuration

Le DiagnosticAgent accepte les options de configuration suivantes :

```python
config = {
    "data_dir": "./data/diagnostic",           # Répertoire des données
    "templates_dir": "./templates/diagnostic", # Répertoire des modèles de rapports
    "output_dir": "./output/diagnostic",       # Répertoire des sorties
    "use_cache": True,                        # Utilisation du cache
    "climate_scenarios": ["current", "2050_rcp45", "2050_rcp85"], # Scénarios climatiques
    "form_factors": {                         # Facteurs de forme par espèce pour calcul volume
        "Pinus sylvestris": 0.48,
        "Quercus robur": 0.55
    }
}

diagnostic_agent = DiagnosticAgent(config)
```

## Dépendances

- Python 3.8+
- pandas, numpy, matplotlib, seaborn
- jinja2, weasyprint (ou pdfkit), reportlab
- scikit-learn (pour l'analyse de structure)
- geopandas (intégration avec GeoAgent)

## Limitations actuelles

- La qualité du diagnostic dépend des données d'inventaire fournies
- L'estimation des volumes utilise des formules génériques qui peuvent être améliorées
- Les modèles de documents sont basés sur des exemples génériques et peuvent nécessiter une adaptation

## Développements futurs

- Intégration d'un système de recommandation d'espèces basé sur le ML
- Module d'analyse d'images pour diagnostics à partir de photos
- Outils d'aide à la décision pour les interventions sylvicoles
- Visualisation 3D des peuplements
- Export vers des formats SIG