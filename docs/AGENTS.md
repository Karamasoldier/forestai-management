# Agents ForestAI

ForestAI est basé sur une architecture multi-agents où chaque agent est spécialisé dans un domaine d'expertise spécifique. Cette page présente les agents disponibles et leurs fonctionnalités.

## GeoAgent

L'agent de géotraitement (GeoAgent) est responsable de l'analyse géospatiale des parcelles forestières.

### Fonctionnalités principales

- Recherche et identification de parcelles via données cadastrales
- Analyse du terrain (élévation, pente, hydrologie, risques naturels)
- Évaluation du potentiel forestier des parcelles
- Génération de cartes et visualisations
- Analyse de l'occupation des sols

### Versions disponibles

- **GeoAgent v1** : Version initiale avec analyses de base
- **GeoAgent v2** : Version améliorée avec intégration du message bus
- **GeoAgent v3** : Version actuelle avec architecture modulaire et services de terrain

Pour plus de détails, consultez la [documentation complète du GeoAgent](GeoAgent.md).

## ReglementationAgent

L'agent de réglementation forestière (ReglementationAgent) est expert du Code Forestier et des réglementations applicables.

### Fonctionnalités principales

- Vérification de conformité réglementaire des projets forestiers
- Identification des autorisations nécessaires pour différents types de projets
- Génération de rapports détaillés aux formats JSON, TXT et HTML
- Recommandations de mise en conformité avec actions concrètes
- Recherche de réglementations par mots-clés
- Vérification des zones protégées (zones humides, Natura 2000, etc.)

### Architecture

L'agent utilise une architecture modulaire avec des services de domaine spécifiques :
- `RegulatoryFrameworkService` : Gestion du cadre réglementaire
- `ComplianceCheckerService` : Vérification de conformité des projets

Pour plus de détails, consultez la [documentation complète du ReglementationAgent](ReglementationAgent.md).

## SubventionAgent (NOUVEAU)

L'agent de subventions (SubsidyAgent) est responsable de la veille sur les aides disponibles et de l'analyse d'éligibilité des projets.

### Fonctionnalités principales

- Veille sur les aides disponibles via différents scrapers spécialisés
- Analyse d'éligibilité des projets aux différentes subventions
- Génération automatique de dossiers de demande aux formats PDF, DOCX et HTML
- Recommandation de subventions adaptées aux parcelles et projets
- Stockage et mise à jour des informations sur les subventions disponibles
- Intégration avec le GeoAgent pour analyser le potentiel des parcelles

### Architecture

```
forestai/agents/subsidy_agent/
├── __init__.py                    # Point d'entrée du package
├── subsidy_agent.py               # Implémentation principale de l'agent
├── eligibility.py                 # Système d'analyse d'éligibilité
├── scrapers/                      # Scrapers de subventions
│   ├── base_scraper.py            # Classe de base pour tous les scrapers
│   ├── france_relance_scraper.py  # Scraper pour les aides France Relance
│   └── ...                        # Autres scrapers spécialisés
└── document_generation/           # Génération de documents
    ├── document_generator.py      # Coordinateur des générateurs
    ├── pdf_generator.py           # Génération de PDF
    ├── html_generator.py          # Génération de HTML
    └── docx_generator.py          # Génération de DOCX
```

Pour plus de détails, consultez la [documentation complète du SubsidyAgent](SubsidyAgent.md).

## Module d'analyse climatique (ClimateAnalyzer)

Le module d'analyse climatique (ClimateAnalyzer) est intégré dans le projet ForestAI pour prendre en compte les conditions climatiques actuelles et futures.

### Fonctionnalités principales

- Identification des zones climatiques pour une géométrie donnée
- Recommandation d'espèces adaptées au climat actuel et futur
- Évaluation des risques climatiques (sécheresse, gel, feux)
- Comparaison entre scénarios climatiques (horizons 2050, 2100)
- Intégration avec les analyses de terrain pour des recommandations complètes

### Architecture

```
domain/services/
├── climate_analyzer.py           # Orchestrateur principal
├── climate_data_loader.py        # Chargement des données climatiques
├── climate_zone_analyzer.py      # Analyse des zones climatiques
└── species_recommender.py        # Recommandation d'espèces adaptées
```

Pour plus de détails, consultez la [documentation complète du ClimateAnalyzer](ClimateAnalyzer.md).

## Agents en développement

### DiagnosticAgent

L'agent de diagnostic forestier (DiagnosticAgent) est en cours de développement. Il sera responsable de l'analyse des données terrain pour générer des diagnostics forestiers et des plans de gestion.

### DocumentAgent

L'agent de génération de documents (DocumentAgent) est en cours de développement. Il sera responsable de la création automatique de documents administratifs comme des cahiers des charges, des contrats, etc.

### ExploitantAgent

L'agent de gestion des exploitants forestiers (ExploitantAgent) est en cours de développement. Il sera responsable de la centralisation des données concernant les opérateurs forestiers.

## Intégration des agents

Les agents sont conçus pour fonctionner de manière autonome mais peuvent également collaborer pour fournir des analyses plus complètes. Des exemples d'intégration sont disponibles dans le répertoire `examples/` :

- Intégration GeoAgent ↔ ClimateAnalyzer : `examples/climate_geo_integration_example.py`
- Intégration GeoAgent ↔ SubventionAgent : `examples/subsidy_geo_integration_example.py`
