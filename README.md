# ForestAI - Gestion Forestière Intelligente

Système multi-agents pour l'automatisation et l'optimisation de la gestion forestière.

## Objectifs

- Identifier les parcelles à potentiel forestier via géotraitement
- Automatiser la prospection de subventions et compensations carbone
- Générer des diagnostics forestiers et plans de gestion
- Créer automatiquement des documents administratifs (cahiers des charges, contrats)
- Centraliser les données des exploitants forestiers
- Assurer la conformité réglementaire avec le Code Forestier

## Architecture des agents

- **GeoAgent** : Analyse géospatiale des parcelles et propriétés (utilise des données locales)
- **ReglementationAgent** : Expert du Code Forestier et des réglementations applicables
- **SubventionAgent** : Veille sur les aides disponibles et analyse d'éligibilité
- **DiagnosticAgent** : Analyse des données terrain
- **DocumentAgent** : Génération de documents administratifs
- **ExploitantAgent** : Base de données des opérateurs forestiers

## Documentation

Le projet est divisé en plusieurs documents pour faciliter la navigation :

- [Architecture du système](docs/ARCHITECTURE.md) - Détails de l'approche architecturale
- [Agents disponibles](docs/AGENTS.md) - Description détaillée des agents
- [Services et modules](docs/SERVICES.md) - Services modulaires et coordinateurs
- [Guide d'installation](docs/INSTALLATION.md) - Instructions d'installation et prérequis
- [Exemples d'utilisation](docs/EXAMPLES.md) - Guide pratique avec exemples de code
- [Plan d'exécution](docs/ROADMAP.md) - Roadmap, phases de développement et état d'avancement
- [API REST](docs/API.md) - Documentation de l'API REST

## Guide rapide d'installation

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos clés API et chemins de données
```

## Utilisation rapide

### Mode ligne de commande

```bash
# Lancer le système complet
python run.py

# Utiliser un agent spécifique
python run.py --agent geoagent

# Rechercher des parcelles dans une commune spécifique
python run.py --agent geoagent --action search_parcels --params '{"commune": "Saint-Martin-de-Crau", "section": "B"}'

# Vérifier la conformité réglementaire d'une parcelle
python run.py --agent reglementation --action check_compliance --params '{"parcels": ["123456789"], "project_type": "boisement"}'

# Rechercher des subventions pour un type de projet
python run.py --agent subsidy --action search_subsidies --params '{"project_type": "reboisement", "region": "Occitanie"}'
```

### Mode API REST

```bash
# Démarrer le serveur API
python api_server.py

# Accéder à la documentation interactive
# Ouvrir http://localhost:8000/docs dans un navigateur

# Exemples d'utilisation de l'API
python examples/api_usage_example.py
```

## Documentation des agents spécifiques

- [Agent de géotraitement (GeoAgent)](docs/GeoAgent.md)
- [Agent de réglementation forestière (ReglementationAgent)](docs/ReglementationAgent.md)
- [Module d'analyse climatique (ClimateAnalyzer)](docs/ClimateAnalyzer.md)
- [Agent de subventions (SubsidyAgent)](docs/SubsidyAgent.md)

## Licence

Ce projet est sous licence MIT.
