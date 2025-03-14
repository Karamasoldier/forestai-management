# SubsidyAgent - Documentation

L'agent de subventions (SubsidyAgent) est un composant clé du système ForestAI qui se concentre sur la recherche, l'analyse et la génération de documents pour les subventions forestières.

## Vue d'ensemble

Le SubsidyAgent permet d'identifier les opportunités de financement adaptées aux projets forestiers, d'analyser l'éligibilité des projets selon les critères des subventions et de générer automatiquement les dossiers de demande.

```
┌───────────────────────────────────────────────────────────┐
│                      SubsidyAgent                          │
└─────────────────┬─────────────────────────┬───────────────┘
                  │                         │
    ┌─────────────▼─────────────┐ ┌─────────▼─────────────┐
    │      Scrapers Module      │ │ Document Generation   │
    │                           │ │                       │
    │ • FranceRelanceScraper    │ │ • PDFGenerator        │
    │ • BaseSubsidyScraper      │ │ • HTMLGenerator       │
    └───────────────────────────┘ └───────────────────────┘
                  │                         │
                  │                         │
    ┌─────────────▼─────────────┐           │
    │    Eligibility Module     │           │
    │                           │           │
    │ • EligibilityAnalyzer     │◄──────────┘
    │ • EligibilityRuleEngine   │
    └───────────────────────────┘
```

## Fonctionnalités principales

### 1. Recherche de subventions

Le SubsidyAgent permet de rechercher des subventions adaptées à un projet forestier selon divers critères:

- Type de projet (reboisement, boisement, etc.)
- Région administrative
- Type de propriétaire (privé, public, etc.)
- Superficie du projet
- Espèces à planter

Exemple d'utilisation:
```python
subsidies = subsidy_agent.search_subsidies(
    project_type="reboisement",
    region="Occitanie",
    owner_type="private"
)
```

### 2. Analyse d'éligibilité

L'agent peut analyser l'éligibilité d'un projet spécifique à une ou plusieurs subventions en tenant compte de critères complexes:

- Type de projet et localisation
- Superficie et caractéristiques du terrain
- Espèces prévues et densité de plantation
- Date limite de la subvention
- Critères spécifiques selon le type de subvention

Le système utilise un moteur de règles avancé permettant d'appliquer des logiques d'éligibilité différentes selon le type de subvention (France Relance, FEADER, subventions régionales).

Exemple d'utilisation:
```python
eligibility = subsidy_agent.analyze_eligibility(
    project={
        "type": "reboisement",
        "area_ha": 5.2,
        "species": ["pinus_pinea", "quercus_suber"],
        "region": "Provence-Alpes-Côte d'Azur"
    },
    subsidy_id="FR-2023-12"
)
```

### 3. Génération de documents

L'agent peut générer automatiquement les documents nécessaires pour les demandes de subvention:

- Formulaires de demande personnalisés
- Documents d'accompagnement
- Annexes techniques
- Récapitulatifs financiers

Les documents peuvent être générés dans plusieurs formats:
- PDF (pour l'impression et l'envoi officiel)
- HTML (pour la visualisation web)
- DOCX (pour édition ultérieure)

Exemple d'utilisation:
```python
document_paths = subsidy_agent.generate_application_documents(
    project=project_data,
    subsidy_id="FR-2023-12",
    applicant=applicant_data,
    output_formats=["pdf", "html"]
)
```

## Architecture

### Scrapers

Le module de scrapers est responsable de la collecte des informations sur les subventions disponibles à partir de différentes sources:

- **BaseSubsidyScraper**: Classe abstraite définissant l'interface commune pour tous les scrapers
- **FranceRelanceScraper**: Implémentation pour les subventions du programme France Relance

Chaque scraper implémente une méthode `fetch_subsidies()` qui retourne une liste standardisée de subventions.

### Module d'éligibilité

Le module d'éligibilité fournit les outils pour analyser la compatibilité entre un projet et une subvention:

- **EligibilityAnalyzer**: Analyse les critères de base communs à toutes les subventions
- **EligibilityRuleEngine**: Applique des règles spécifiques selon le type de subvention

Le système est conçu pour être facilement extensible avec de nouvelles règles d'éligibilité.

### Génération de documents

Le module de génération de documents permet de créer les fichiers nécessaires aux demandes de subvention:

- **SubsidyDocumentGenerator**: Coordonne la génération dans différents formats
- **PDFGenerator**: Génère des documents PDF à partir des templates
- **HTMLGenerator**: Génère des documents HTML interactifs

Les documents générés utilisent des templates Jinja2 personnalisables qui peuvent être adaptés à chaque type de subvention.

## Système de cache

Pour optimiser les performances, le SubsidyAgent intègre un système de cache:

- Les données des subventions sont stockées localement
- Le cache a une durée de validité configurable
- Possibilité de forcer le rafraîchissement du cache

## Intégration avec les autres agents

Le SubsidyAgent est conçu pour fonctionner en synergie avec les autres agents:

- **GeoAgent**: Fournit les données géospatiales utilisées pour l'analyse d'éligibilité
- **ReglementationAgent**: Vérifie la conformité réglementaire des projets
- **ClimateAnalyzer**: Permet de valider la pertinence climatique des espèces

## Utilisation avancée

### API REST

Le SubsidyAgent peut être exposé via l'API REST de ForestAI:

```
GET /api/subsidies/search?project_type=reboisement&region=Occitanie
POST /api/subsidies/analyze_eligibility
POST /api/subsidies/generate_documents
```

### Ligne de commande

L'agent peut être utilisé directement via la ligne de commande:

```bash
python run.py --agent subsidy --action search_subsidies --params '{
  "project_type": "reboisement", 
  "region": "Occitanie"
}'
```

### Exemple complet

Un exemple complet d'utilisation est disponible dans le fichier `examples/subsidy_agent_example.py`.

## Configuration

La configuration du SubsidyAgent se fait via le fichier `.env`:

```
# Configuration du SubsidyAgent
SUBSIDY_CACHE_DURATION=7              # Durée de validité du cache en jours
SUBSIDY_TEMPLATES_DIR=data/templates  # Répertoire des templates de documents
SUBSIDY_OUTPUT_DIR=outputs/subsidies  # Répertoire de sortie des documents
```

## Développements futurs

- Ajout de scrapers pour d'autres programmes de subventions
- Implémentation d'un système d'alerte pour les dates limites approchantes
- Intégration avec un service d'envoi automatique de demandes
- Suivi de l'état d'avancement des demandes de subvention
