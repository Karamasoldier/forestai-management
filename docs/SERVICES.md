# Services et Modules ForestAI

ForestAI repose sur une architecture modulaire avec des services spécialisés et des coordinateurs qui orchestrent les différentes fonctionnalités. Cette page présente les principaux services et modules du système.

## Services de terrain

Les services d'analyse de terrain ont été décomposés en modules spécialisés pour optimiser les performances et la maintenance :

```
terrain_services/
├── base_terrain_service.py  # Classe de base avec fonctionnalités communes
├── elevation_service.py     # Analyse d'altitude (MNT)
├── slope_service.py         # Calcul de pente et exposition
├── hydrology_service.py     # Analyse des cours d'eau
├── risk_service.py          # Analyse des risques naturels
└── terrain_coordinator.py   # Orchestrateur d'analyses
```

### Avantages de cette approche

- **Modularité** : Chaque service se concentre sur un aspect précis
- **Performance** : Possibilité de paralléliser les analyses
- **Maintenance** : Code plus facile à maintenir et à tester
- **Réutilisabilité** : Les services peuvent être utilisés indépendamment

### Coordinateur de terrain

Le coordinateur de terrain (`terrain_coordinator.py`) est un orchestrateur qui :
- Centralise l'accès aux différents services d'analyse
- Parallélise les analyses indépendantes pour améliorer les performances
- Séquence les analyses dépendantes (ex: l'analyse de pente nécessite l'élévation)
- Agrège les résultats des différentes analyses en statistiques combinées
- Calcule un score de potentiel forestier basé sur l'ensemble des facteurs

Exemple d'utilisation du coordinateur :
```python
coordinator = TerrainCoordinator(data_dir="data/raw")
result = coordinator.analyze_terrain(
    geometry=parcel_geometry,
    analysis_types=["elevation", "slope", "hydrology", "risks"],
    params={
        "elevation_resolution": 10,
        "compute_aspect": True,
        "hydro_buffer": 100
    }
)
```

## Services de réglementation forestière

Pour la gestion des réglementations forestières, une architecture en services a été mise en place :

```
domain/services/
├── regulatory_framework_service.py   # Gestion du cadre réglementaire
└── compliance_checker_service.py     # Vérification de conformité
```

### Avantages de cette architecture

- **Séparation des responsabilités** : Chaque service a un rôle spécifique
- **Réutilisabilité** : Les services peuvent être utilisés par différents agents
- **Évolutivité** : Ajout facile de nouvelles réglementations
- **Maintenabilité** : Code organisé par domaine fonctionnel

## Services d'analyse climatique

Le module d'analyse climatique intègre les données Climessences de l'ONF :

```
domain/services/
├── climate_analyzer.py           # Orchestrateur principal
├── climate_data_loader.py        # Chargement des données climatiques
├── climate_zone_analyzer.py      # Analyse des zones climatiques
└── species_recommender.py        # Recommandation d'espèces adaptées
```

### Fonctionnalités

- **Identification des zones climatiques** pour une parcelle donnée
- **Recommandation d'espèces adaptées** au climat actuel
- **Anticipation des impacts** du changement climatique
- **Intégration avec l'analyse de terrain** pour des recommandations complètes

## Loaders de données géospatiales

Le projet inclut plusieurs chargeurs de données géospatiales optimisés pour différentes sources :

```
data_loaders/
├── cadastre_loader.py          # Données cadastrales (format local)
├── corine_land_cover_loader.py # Données d'occupation des sols (PostgreSQL)
├── bdtopo_loader.py            # Données topographiques (format local)
└── bdtopo/                     # Nouvelle version modulaire du BDTopoLoader
    ├── base_loader.py          # Classe de base pour le chargement des données
    ├── vegetation_analyzer.py  # Analyse de la végétation
    ├── road_analyzer.py        # Analyse du réseau routier
    ├── hydro_analyzer.py       # Analyse du réseau hydrographique
    ├── building_analyzer.py    # Analyse des bâtiments
    ├── potential_calculator.py # Calcul du potentiel forestier
    └── main_loader.py          # Point d'entrée principal pour les utilisateurs
```

### Loader BD TOPO

Le `BDTopoLoader` est un loader modulaire pour les données BD TOPO de l'IGN. Il permet d'analyser :

- La végétation (couverture, types dominants)
- Le réseau routier (densité, accessibilité)
- Le réseau hydrographique (cours d'eau, plans d'eau)
- Les bâtiments (densité, types)

Il calcule également un score de potentiel forestier basé sur l'ensemble de ces critères et génère des recommandations d'espèces adaptées au terrain.

Exemple d'utilisation :
```python
from forestai.agents.geo_agent.data_loaders.bdtopo import BDTopoLoader

# Initialiser le loader
loader = BDTopoLoader(data_dir="data/raw/bdtopo")

# Créer une géométrie (exemple avec un rectangle)
from shapely.geometry import box
geometry = box(843000, 6278000, 844000, 6279000)  # coordonnées Lambert 93

# Analyser le potentiel forestier d'une parcelle
potential = loader.calculate_forestry_potential(geometry, buffer_distance=100)

print(f"Potentiel forestier: {potential['potential_score']} ({potential['potential_class']})")
print(f"Contraintes: {potential['constraints']}")
print(f"Opportunités: {potential['opportunities']}")
print(f"Espèces recommandées: {potential['recommended_species']}")
```

### Loader Corine Land Cover SQL

Le `CorineLandCoverLoader` permet d'accéder aux données d'occupation des sols stockées dans une base de données PostgreSQL avec extension PostGIS. Ce loader :

- Détermine automatiquement les noms de tables et de colonnes
- Effectue des requêtes spatiales optimisées pour extraire uniquement les données nécessaires
- Calcule les statistiques d'occupation des sols (dominante, pourcentages)
- Évalue le potentiel forestier basé sur l'occupation des sols
- Recommande des espèces adaptées selon le type de sol

## Module de génération de documents

Le module de génération de documents du SubsidyAgent permet de créer automatiquement des dossiers de demande de subvention sous différents formats :

```
document_generation/
├── document_generator.py      # Coordinateur des générateurs
├── pdf_generator.py           # Génération de PDF
├── html_generator.py          # Génération de HTML
└── docx_generator.py          # Génération de DOCX
```

### Fonctionnalités

- Génération de documents structurés à partir de templates
- Support de multiples formats (PDF, DOCX, HTML)
- Fallback automatique entre les formats en cas d'erreur
- Intégration d'éléments dynamiques (tableaux, graphiques)
- Personnalisation selon les besoins des utilisateurs

## Autres services

### Bus de messages

Le bus de messages permet la communication entre agents de manière asynchrone :

```python
# Publication d'un message
message_bus.publish("PARCEL_ANALYZED", {
    "parcel_id": "123456789",
    "potential_score": 0.85,
    "suitable_species": ["pine", "oak"]
})

# Souscription à un sujet
@message_bus.subscribe("PARCEL_ANALYZED")
def handle_parcel_analysis(message):
    parcel_id = message["parcel_id"]
    potential_score = message["potential_score"]
    # Traitement du message
```

### Agent Memory

Le système de mémoire partagée permet aux agents de stocker et de récupérer des informations :

```python
# Stockage d'une information
agent_memory.store("analysis:123456789", analysis_result)

# Récupération d'une information
result = agent_memory.retrieve("analysis:123456789")
```

### Infrastructure de Logging

L'infrastructure de logging permet de tracer les opérations des agents et de gérer les erreurs :

```python
from forestai.core.utils.logging_config import LoggingConfig

logger = LoggingConfig.get_instance().get_logger("MyComponent")
logger.info("Une information")
logger.warning("Un avertissement")
logger.error("Une erreur", exc_info=True)
```
