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
- [Guide de l'interface desktop (PyQt6)](README_GUI.md) - Guide d'utilisation de l'interface desktop
- [Correctifs pour erreurs de récursion](README_FIXES.md) - Documentation des correctifs pour les erreurs rencontrées avec l'interface web
- [Déploiement Docker](docs/DOCKER.md) - Guide de déploiement avec Docker

## Installation et démarrage rapide

### Option 1: Script de démarrage unifié (recommandé)

La méthode la plus simple pour démarrer ForestAI avec correctifs intégrés:

```bash
# Démarrer l'API et l'interface web
python run_forestai.py

# Démarrer uniquement l'API
python run_forestai.py --api-only

# Démarrer uniquement l'interface web
python run_forestai.py --web-only

# Spécifier le port ou l'hôte de l'API
python run_forestai.py --api-port 8080 --api-host 0.0.0.0
```

### Option 2: Déploiement avec Docker

```bash
# Windows
run_docker.bat

# Linux/macOS
docker-compose up -d
```

Voir [la documentation Docker](docs/DOCKER.md) pour plus de détails.

### Option 3: Installation automatisée classique

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

# Résoudre les erreurs de récursion
python fix_pydantic_v1_recursion.py
python run_api_with_fix.py
```

**Windows**:
```bash
# Démarrer l'interface web avec l'API
run_web.bat

# Résoudre les erreurs de récursion
python fix_pydantic_v1_recursion.py
python run_api_with_fix.py
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
# Démarrer le serveur API (avec correctif anti-récursion)
python run_api_with_fix.py

# Accéder à la documentation interactive
# Ouvrir http://localhost:8000/docs dans un navigateur

# Exemples d'utilisation de l'API
python examples/api_usage_example.py
```

### Interface Desktop (PyQt6)

Le projet inclut une interface graphique desktop basée sur PyQt6 pour tester et interagir avec les agents :

```bash
# Installation des dépendances de l'interface desktop
pip install -r requirements-gui.txt

# Démarrer l'interface desktop (mode API REST)
python run_gui.py

# Ou utiliser les scripts pratiques
# Windows:
run_gui.bat

# Linux/macOS:
chmod +x run_gui.sh
./run_gui.sh
```

L'interface desktop peut fonctionner en deux modes:
- **Mode API** : Communique avec les agents via l'API REST (nécessite que l'API soit démarrée)
- **Mode direct** : Interagit directement avec les agents en local

```bash
# Mode direct (sans API REST)
python run_gui.py --direct

# Spécifier une URL d'API personnalisée
python run_gui.py --api-url http://localhost:8080
```

Pour plus de détails, consultez le [guide complet de l'interface desktop](README_GUI.md).

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

En cas de problèmes avec l'interface web, consultez la [documentation des correctifs](README_FIXES.md).

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

## Résolution des problèmes

Si vous rencontrez des erreurs `RecursionError: maximum recursion depth exceeded` lors de l'utilisation de l'interface web ou de l'API, utilisez le script de démarrage unifié ou les correctifs spécifiques:

```bash
# Solution 1: Script de démarrage unifié
python run_forestai.py

# Solution 2: Correctif Pydantic v1
python fix_pydantic_v1_recursion.py
python run_api_with_fix.py
```

Pour plus d'informations, consultez la [documentation des correctifs](README_FIXES.md).

## Licence

Ce projet est sous licence MIT.
