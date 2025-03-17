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

## Phase 2: Expansion des capacités (✅ Complété)

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
- ✅ Intégration des alertes et notifications
- ✅ Authentification et sécurisation de l'API REST
- ✅ Tests d'intégration entre agents
- ✅ Documentation de l'utilisation combinée des agents
- ✅ Amélioration des métriques de potentiel forestier

## Phase 3: Agents avancés (🔄 En cours)

Cette phase se concentre sur le développement d'agents spécialisés plus avancés.

### Objectifs complétés

- ✅ Implémentation du générateur de rapports forestiers (multi-formats: PDF, HTML, DOCX, TXT, JSON)
- ✅ Développement du module d'analyse sanitaire forestière (HealthAnalyzer)
- ✅ Intégration des analyses sanitaires dans les rapports de diagnostic
- ✅ Finalisation du DiagnosticAgent pour l'analyse des données terrain
- ✅ Exposition du DiagnosticAgent et HealthAnalyzer via l'API REST
- ✅ Tests unitaires et d'intégration pour l'API REST du DiagnosticAgent
- ✅ Optimisation des performances de l'analyse sanitaire et des diagnostics
- ✅ Parallélisation et traitement par lots pour les grands volumes de données sanitaires
- ✅ Mise en œuvre des exemples d'utilisation des fonctionnalités optimisées
- ✅ Développement du DocumentAgent pour la génération de documents administratifs
- ✅ Implémentation des générateurs de documents pour les contrats et cahiers des charges
- ✅ Implémentation des générateurs pour les plans de gestion et documents administratifs
- ✅ Implémentation des tests de régression automatisés
- ✅ Implémentation complète de l'ExploitantAgent
    - ✅ Gestionnaire des opérateurs forestiers (OperatorsManager)
    - ✅ Gestionnaire des opérations forestières (OperationsManager)
    - ✅ Gestionnaire des performances (PerformanceManager)
    - ✅ Intégration des modèles de données
    - ✅ Exemples d'utilisation
- ✅ Système de recommandation d'espèces forestières (base)
    - ✅ Modèles de données pour les espèces forestières
    - ✅ Système de scoring et de recommandation
    - ✅ Calcul de compatibilité climatique et pédologique
    - ✅ Évaluation des risques et du potentiel économique/écologique
    - ✅ Exemples d'utilisation

### Objectifs en cours

- 🔄 Extension du système de recommandation d'espèces avec ML
- 🔄 Intégration des données de télédétection (satellite, LIDAR)

### Objectifs planifiés

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
| DiagnosticAgent | 90% | Structure implémentée, intégration complète avec HealthAnalyzer et API REST |
| ReportGenerator | 100% | Système de génération de rapports multiformat complet et modulaire |
| HealthAnalyzer | 100% | Module d'analyse sanitaire forestière avec détection de problèmes, recommandations et intégration aux rapports |
| OptimizedHealthAnalyzer | 100% | Version optimisée avec parallélisation et traitement par lots pour grands volumes de données |
| DocumentAgent | 100% | Module de génération de documents administratifs complet : contrats, cahiers des charges, plans de gestion, documents administratifs |
| ExploitantAgent | 100% | Implémentation complète comprenant : gestionnaire des opérateurs, gestionnaire des opérations, gestionnaire des performances + modèles de données |
| SpeciesRecommender | 65% | Base du système de recommandation implémentée, intégration ML en cours |
| API REST | 95% | Tous les endpoints implémentés, incluant DiagnosticAgent et HealthAnalyzer, documentation OpenAPI complète |
| Cache | 100% | Système de cache multiniveau implémenté, avec stratégies de fraîcheur adaptatives |
| Tests | 80% | Tests unitaires étendus, tests d'intégration de base pour tous les agents, tests de régression automatisés ajoutés |
| Documentation | 90% | Documentation utilisateur et développeur complétée, incluant nouveaux composants et API |
| Optimisation | 80% | Parallélisation des analyses sanitaires implémentée, autres analyses en cours d'optimisation |

## Calendrier prévisionnel

- **Q2 2025**: Finalisation Phase 3
  - Système de recommandation d'espèces avec ML
  - Intégration des données de télédétection

- **Q3 2025**: Suite Phase 3
  - Interface utilisateur web basique
  - Système complet de recommandation d'espèces

- **Q4 2025**: Suite Phase 3
  - Tableau de bord de suivi forestier
  - Prédiction de croissance forestière

- **Q1 2026**: Début Phase 4
  - Orchestration autonome des agents V1
  - Intégration IoT préliminaire

## Comment contribuer

Les contributions au projet sont les bienvenues ! Voici les priorités actuelles :

1. **Extension du système de recommandation d'espèces** - Intégration de modèles de ML pour améliorer les recommandations
2. **Interface utilisateur** - Développement d'une interface web basique utilisant l'API REST
3. **Intégration données de télédétection** - Support pour les données satellite et LIDAR
4. **Optimisation de performance** - Parallélisation des autres analyses (géospatiales, réglementaires)
5. **Documentation** - Amélioration des guides d'utilisation et exemples
6. **Visualisation** - Amélioration de la génération de cartes et rapports
7. **Multilinguisme** - Support de langues supplémentaires dans les rapports et l'interface

Pour contribuer, consultez le fichier [CONTRIBUTING.md](../CONTRIBUTING.md) pour les instructions et les bonnes pratiques.

## Stratégie d'évolution

Le projet évolue selon trois principes directeurs :

1. **Modularité** - Chaque composant doit être utilisable indépendamment
2. **APIs stables** - Les interfaces entre modules sont conçues pour minimiser les changements cassants
3. **Évolution incrémentale** - Nouvelles fonctionnalités livrées progressivement en restant utilisables

Ce document est mis à jour régulièrement pour refléter l'évolution du projet. Dernière mise à jour: 17 Mars 2025.
