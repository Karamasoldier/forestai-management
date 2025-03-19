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
- [Système de cache](docs/CACHE.md) - Documentation du système de cache pour l'optimisation des performances
- [Guide de l'interface web](README_UPDATE.md) - Guide d'utilisation des interfaces web

## Installation et démarrage rapide

### Installation automatisée

```bash
# Cloner le projet
git clone https://github.com/Karamasoldier/forestai-management.git
cd forestai-management

# Créer l'environnement virtuel Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate    # Windows

# Installation automatisée complète
python setup.py
```

### Démarrage avec scripts unifiés

**Linux/macOS**:
```bash
# Rendre le script exécutable
chmod +x run_web.sh

# Démarrer l'interface web avec l'API
./run_web.sh
```

**Windows**:
```bash
# Démarrer l'interface web avec l'API
run_web.bat
```

### Mode ligne de commande classique

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

### Interface Web

Le projet dispose de deux interfaces web :

1. **Interface Vite.js** (répertoire `web/`):
```bash
cd web
npm install
npm run dev
```

2. **Interface Vue CLI** (répertoire `webui/`):
```bash
cd webui
npm install
npm run serve
```

Pour plus de détails, consultez le [guide complet de l'interface web](README_UPDATE.md).

## Documentation des agents spécifiques

- [Agent de géotraitement (GeoAgent)](docs/GeoAgent.md)
- [Agent de réglementation forestière (ReglementationAgent)](docs/ReglementationAgent.md)
- [Module d'analyse climatique (ClimateAnalyzer)](docs/ClimateAnalyzer.md)
- [Agent de subventions (SubsidyAgent)](docs/SubsidyAgent.md)

## Optimisation des performances

Le projet intègre un système de cache multiniveau pour optimiser les performances :

```python
# Exemple d'utilisation du cache avec les agents
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

@cached(data_type=CacheType.GEODATA, policy=CachePolicy.WEEKLY)
def expensive_function(param):
    # Opération coûteuse...
    return result
```

Pour une démonstration complète, voir [l'exemple d'utilisation du cache](examples/cache_usage_example.py).

## Authentification et utilisateurs de test

L'interface web et l'API utilisent l'authentification JWT. Utilisateurs disponibles pour les tests :

1. **Administrateur** : `admin / adminpassword`
2. **Utilisateur** : `user / userpassword`
3. **Diagnostic** : `diagnostic / diagnosticpassword`

## Licence

Ce projet est sous licence MIT.
