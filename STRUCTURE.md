# Structure du projet ForestAI

```
forestai/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Classe de base pour tous les agents
│   ├── geo_agent/              # Agent de géotraitement
│   │   ├── __init__.py
│   │   ├── geo_agent.py        # Implémentation principale
│   │   ├── cadastre.py         # Fonctions d'interaction avec le cadastre
│   │   └── parcel_analyzer.py  # Analyse des parcelles
│   ├── subsidy_agent/          # Agent de subventions
│   │   ├── __init__.py
│   │   ├── subsidy_agent.py    # Implémentation principale
│   │   ├── scrapers/           # Extracteurs web pour subventions
│   │   └── eligibility.py      # Règles d'éligibilité
│   ├── diagnostic_agent/       # Agent de diagnostic
│   │   ├── __init__.py
│   │   ├── diagnostic_agent.py # Implémentation principale
│   │   ├── species.py          # Reconnaissance d'espèces
│   │   └── health.py           # Analyse de santé forestière
│   ├── document_agent/         # Agent de documents
│   │   ├── __init__.py
│   │   ├── document_agent.py   # Implémentation principale
│   │   ├── templates/          # Templates de documents
│   │   └── regulations.py      # Règles et contraintes légales
│   └── operator_agent/         # Agent exploitants
│       ├── __init__.py
│       ├── operator_agent.py   # Implémentation principale
│       └── company_db.py       # Base de données entreprises
├── core/
│   ├── __init__.py
│   ├── config.py               # Configuration du système
│   ├── db/                     # Couche base de données
│   │   ├── __init__.py
│   │   ├── models.py           # Modèles de données
│   │   └── db_manager.py       # Gestionnaire de BDD
│   ├── api/                    # API REST
│   │   ├── __init__.py
│   │   ├── routes.py           # Points d'entrée API
│   │   └── auth.py             # Authentification
│   └── utils/                  # Utilitaires communs
│       ├── __init__.py
│       ├── logging.py          # Journalisation
│       ├── file_utils.py       # Manipulation de fichiers
│       └── geo_utils.py        # Fonctions géospatiales
├── data/
│   ├── raw/                    # Données brutes
│   ├── processed/              # Données traitées
│   └── cache/                  # Cache temporaire
├── gui/                        # Interface desktop (PyQt6)
│   ├── __init__.py
│   ├── main_window.py          # Fenêtre principale
│   ├── components.py           # Composants d'interface
│   ├── models.py               # Modèles de données
│   └── agent_api.py            # API pour interagir avec les agents
├── web/                        # Interface web Vite.js
│   ├── src/
│   ├── public/
│   └── package.json
├── webui/                      # Interface web Vue CLI
│   ├── src/
│   ├── public/
│   └── package.json
├── ui/
│   ├── templates/              # Templates web
│   ├── static/                 # Fichiers statiques
│   └── app.py                  # Application web
├── scripts/
│   ├── setup.py                # Script d'installation
│   └── maintenance.py          # Tâches de maintenance
├── tests/
│   ├── __init__.py
│   ├── test_geo_agent.py
│   ├── test_subsidy_agent.py
│   └── ...
├── .env.example                # Exemple de variables d'environnement
├── requirements.txt            # Dépendances Python
├── requirements-gui.txt        # Dépendances de l'interface PyQt6
├── run.py                      # Point d'entrée principal
├── run_gui.py                  # Démarrage de l'interface desktop
├── run_gui.bat                 # Script Windows pour l'interface desktop
├── run_gui.sh                  # Script Linux/Mac pour l'interface desktop
├── README.md                   # Documentation principale
├── README_GUI.md               # Documentation de l'interface desktop
└── README_UPDATE.md            # Documentation des interfaces web
```

## Composants principaux

### Agents
Chaque agent est un module autonome avec une responsabilité spécifique. La classe `BaseAgent` définit l'interface commune à tous les agents.

### Core
Contient les fonctionnalités partagées comme la configuration, la base de données et les utilitaires.

### Data
Structure de dossiers pour les différents types de données manipulées par le système.

### Interfaces
Le système propose plusieurs interfaces pour interagir avec les agents :

#### GUI - Interface desktop (PyQt6)
Interface graphique desktop utilisant PyQt6 pour tester et surveiller les agents. Cette interface peut fonctionner en mode direct ou en communiquant avec l'API REST.

#### Web - Interface web Vite.js
Interface web moderne basée sur Vite.js et Vue.js pour une utilisation en production.

#### WebUI - Interface web Vue CLI
Interface web alternative basée sur Vue CLI pour les développeurs préférant cet écosystème.

#### UI - Interface web traditionnelle
Interface web traditionnelle utilisant des templates HTML pour une compatibilité maximale.

### Tests
Tests unitaires et d'intégration pour chaque composant du système.
