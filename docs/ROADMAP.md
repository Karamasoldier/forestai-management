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

### Objectifs en cours

- 🔄 Intégration SubsidyAgent ↔ GeoAgent
- 🔄 Système de détection automatique des zones prioritaires pour subventions
- 🔄 Tests d'intégration entre agents
- 🔄 Documentation de l'utilisation combinée des agents
- 🔄 API REST pour l'accès externe aux fonctionnalités
- 🔄 Amélioration des métriques de potentiel forestier

### Objectifs planifiés

- ⏳ Finalisation du système de cache pour les données externes
- ⏳ Intégration des alertes et notifications
- ⏳ Implémentation des tests de régression automatisés

## Phase 3: Agents avancés (🔜 Prochainement)

Cette phase se concentre sur le développement d'agents spécialisés plus avancés.

### Objectifs planifiés

- ⏳ Implémentation du DiagnosticAgent pour l'analyse des données terrain
- ⏳ Développement du DocumentAgent pour la génération de documents administratifs
- ⏳ Création de l'ExploitantAgent pour la gestion des opérateurs forestiers
- ⏳ Système avancé de recommandation d'espèces basé sur ML
- ⏳ Intégration des données de télédétection (satellite, LIDAR)
- ⏳ Prédiction de croissance forestière avec série temporelle

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
|--------|-------------|---------
| GeoAgent | 90% | Fonctionnalités principales implémentées, optimisations en cours |
| ReglementationAgent | 85% | Base réglementaire complète, mises à jour automatiques à finaliser |
| ClimateAnalyzer | 75% | Intégration de données climatiques complète, modèles prédictifs en développement |
| SubsidyAgent | 70% | Structure principale et génération de documents complètes, intégration avancée à finaliser |
| DiagnosticAgent | 5% | Conception préliminaire, implémentation à venir |
| DocumentAgent | 5% | Conception préliminaire, implémentation à venir |
| ExploitantAgent | 0% | Planifié pour phase ultérieure |
| API REST | 30% | Endpoints de base implémentés, documentation à compléter |
| Tests | 45% | Tests unitaires en place, tests d'intégration en développement |
| Documentation | 70% | Documentation utilisateur et développeur en cours de finalisation |

## Calendrier prévisionnel

- **Q2 2025**: Finalisation Phase 2
  - Intégration complète SubsidyAgent ↔ GeoAgent
  - API REST complète avec documentation OpenAPI
  - Système de cache optimisé
  - Documentation inter-agents

- **Q3 2025**: Début Phase 3
  - Implémentation du DiagnosticAgent V1
  - Intégration des données de télédétection
  - Premiers modules du DocumentAgent

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

1. **Intégration entre agents** - Développement de l'intégration SubsidyAgent ↔ GeoAgent
2. **Optimisation de performance** - Parallélisation des analyses spatiales et mise en cache intelligente
3. **Tests** - Développement de tests unitaires et d'intégration
4. **Documentation** - Amélioration des guides d'utilisation et exemples
5. **Visualisation** - Amélioration de la génération de cartes et rapports

Pour contribuer, consultez le fichier [CONTRIBUTING.md](../CONTRIBUTING.md) pour les instructions et les bonnes pratiques.

## Stratégie d'évolution

Le projet évolue selon trois principes directeurs :

1. **Modularité** - Chaque composant doit être utilisable indépendamment
2. **APIs stables** - Les interfaces entre modules sont conçues pour minimiser les changements cassants
3. **Évolution incrémentale** - Nouvelles fonctionnalités livrées progressivement en restant utilisables

Ce document est mis à jour régulièrement pour refléter l'évolution du projet. Dernière mise à jour: 14 Mars 2025.
