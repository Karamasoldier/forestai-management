# Feuille de route ForestAI

Ce document présente la feuille de route du projet ForestAI, détaillant les phases de développement planifiées et l'état d'avancement actuel.

## Vue d'ensemble

Le développement de ForestAI est organisé en plusieurs phases, avec une approche incrémentale permettant de livrer régulièrement des fonctionnalités utilisables tout en ajoutant progressivement des capacités plus avancées.

## Phase 1: Fondations (✅ Complété)

Cette phase a établi les bases de l'architecture et les fonctionnalités essentielles.

### Objectifs complétés

- ✅ Architecture multi-agents de base
- ✅ Base de code modulaire et extensible
- ✅ Implémentation du GeoAgent pour l'analyse géospatiale
- ✅ Intégration des données BD TOPO et cadastrales
- ✅ Mise en place de la structure de projet
- ✅ Système de logging et gestion des erreurs
- ✅ Documentation de base du système

## Phase 2: Expansion des capacités (🔄 En cours)

Cette phase enrichit le système avec des agents supplémentaires et améliore l'intégration entre composants.

### Objectifs complétés

- ✅ Implémentation du ReglementationAgent
- ✅ Intégration des données du Code Forestier
- ✅ Développement du ClimateAnalyzer
- ✅ Intégration GeoAgent ↔ ClimateAnalyzer
- ✅ Mise en place du système de bus de messages
- ✅ Implémentation du SubsidyAgent
- ✅ Développement des scrapers de subventions
- ✅ Génération automatique de documents (PDF, HTML, DOCX)
- ✅ Intégration SubsidyAgent ↔ GeoAgent
- ✅ Système de détection automatique des zones prioritaires pour subventions
- ✅ API REST pour l'accès externe aux fonctionnalités
- ✅ Documentation de l'API avec OpenAPI
- ✅ Finalisation du système de cache pour les données externes

### Objectifs en cours

- 🔄 Tests d'intégration entre agents
- 🔄 Documentation de l'utilisation combinée des agents
- 🔄 Amélioration des métriques de potentiel forestier
- 🔄 Tests unitaires et d'intégration pour l'API REST

### Objectifs planifiés

- ⏳ Intégration des alertes et notifications
- ⏳ Implémentation des tests de régression automatisés
- ⏳ Authentification et sécurisation de l'API REST

## Phase 3: Agents avancés (🔄 En cours)

Cette phase se concentre sur le développement d'agents spécialisés plus avancés.

### Objectifs complétés

- ✅ Implémentation du générateur de rapports forestiers (multi-formats: PDF, HTML, DOCX, TXT, JSON)
- ✅ Développement du module d'analyse sanitaire forestière (HealthAnalyzer)

### Objectifs en cours

- 🔄 Finalisation du DiagnosticAgent pour l'analyse des données terrain
- 🔄 Intégration des analyses sanitaires dans les rapports de diagnostic

### Objectifs planifiés

- ⏳ Développement du DocumentAgent pour la génération de documents administratifs
- ⏳ Création de l'ExploitantAgent pour la gestion des opérateurs forestiers
- ⏳ Système avancé de recommandation d'espèces basé sur ML
- ⏳ Intégration des données de télédétection (satellite, LIDAR)
- ⏳ Prédiction de croissance forestière avec série temporelle
- ⏳ Interface utilisateur web basique consommant l'API REST

## Phase 4: Intelligence collective et automatisation (🔮 Vision future)

Cette phase vise à développer les capacités d'intelligence collective du système et l'automatisation avancée.

### Objectifs envisagés

- 🔮 Orchestration autonome des agents avec prise de décision
- 🔮 Analyses prédictives du marché du bois et des tendances
- 🔮 Adaptation automatique aux changements réglementaires
- 🔮 Optimisation avancée des plans de gestion forestière
- 🔮 Intégration avec systèmes IoT forestiers (capteurs, drones)
- 🔮 Générateur de jumeaux numériques de parcelles forestières

## Phase 5: Expansion et écosystème (🔮 Vision future)

Cette phase vise à étendre l'utilisation et l'écosystème de ForestAI.

### Objectifs envisagés

- 🔮 Interface utilisateur web complète
- 🔮 Application mobile pour diagnostics sur le terrain
- 🔮 Marketplace d'extensions et modules spécialisés
- 🔮 Adaptation internationale (réglementations, espèces, climats)
- 🔮 Intégration avec plateformes de marché carbone
- 🔮 Tableau de bord de performance forestière en temps réel

## État d'avancement actuel

| Module | Progression | Détails |
|--------|-------------|---------|
| GeoAgent | 95% | Fonctionnalités principales + détection automatique zones prioritaires complètes |
| ReglementationAgent | 85% | Base réglementaire complète, mises à jour automatiques à finaliser |
| ClimateAnalyzer | 75% | Intégration de données climatiques complète, modèles prédictifs en développement |
| SubsidyAgent | 80% | Structure principale et génération de documents complètes, intégration avancée réalisée |
| DiagnosticAgent | 60% | Structure de base implémentée, générateur de rapports et analyseur sanitaire forestier développés |
| ReportGenerator | 100% | Système de génération de rapports multiformat complet et modulaire |
| HealthAnalyzer | 95% | Module d'analyse sanitaire forestière avec détection de problèmes et recommandations |
| DocumentAgent | 5% | Conception préliminaire, implémentation à venir |
| ExploitantAgent | 0% | Planifié pour phase ultérieure |
| API REST | 90% | Endpoints principaux implémentés, documentation OpenAPI complète, tests unitaires en place |
| Cache | 100% | Système de cache multiniveau implémenté, avec stratégies de fraîcheur adaptatives |
| Tests | 60% | Tests unitaires étendus, tests d'intégration en développement |
| Documentation | 85% | Documentation utilisateur et développeur complétée, guides d'intégration et API documentée |

## Calendrier prévisionnel

- **Q2 2025**: Finalisation Phase 2
  - Tests d'intégration complets
  - Authentification et sécurisation de l'API REST
  - Documentation inter-agents

- **Q3 2025**: Suite Phase 3
  - Finalisation du DiagnosticAgent V1
  - Intégration des données de télédétection
  - Premiers modules du DocumentAgent
  - Interface utilisateur web basique

- **Q4 2025**: Suite Phase 3
  - Implémentation de l'ExploitantAgent
  - Système avancé de recommandation d'espèces
  - Tableau de bord de suivi forestier

- **Q1 2026**: Début Phase 4
  - Prédiction de croissance forestière
  - Orchestration autonome des agents V1
  - Intégration IoT préliminaire

## Comment contribuer

Les contributions au projet sont les bienvenues ! Voici les priorités actuelles :

1. **Tests d'intégration** - Développement de tests pour valider les intégrations entre agents
2. **Interface utilisateur** - Développement d'une interface web basique utilisant l'API REST
3. **Optimisation de performance** - Parallélisation des analyses spatiales
4. **Documentation** - Amélioration des guides d'utilisation et exemples
5. **Visualisation** - Amélioration de la génération de cartes et rapports

Pour contribuer, consultez le fichier [CONTRIBUTING.md](../CONTRIBUTING.md) pour les instructions et les bonnes pratiques.

## Stratégie d'évolution

Le projet évolue selon trois principes directeurs :

1. **Modularité** - Chaque composant doit être utilisable indépendamment
2. **APIs stables** - Les interfaces entre modules sont conçues pour minimiser les changements cassants
3. **Évolution incrémentale** - Nouvelles fonctionnalités livrées progressivement en restant utilisables

Ce document est mis à jour régulièrement pour refléter l'évolution du projet. Dernière mise à jour: 15 Mars 2025.
