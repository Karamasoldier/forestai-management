# Journal des modifications (Changelog)

Ce document répertorie les modifications importantes apportées au projet ForestAI.

## [Non publié]

### Ajouté
- Documentation complète de l'installation (INSTALLATION.md)
- Documentation des exemples d'utilisation (EXAMPLES.md) 
- Feuille de route du projet (ROADMAP.md)
- Documentation détaillée du SubsidyAgent
- Guide d'intégration des agents (INTEGRATION.md)

### Implémenté
- Architecture modulaire en couches avec interfaces standardisées
- Infrastructure de base du système multi-agents
  - Système de configuration centralisé
  - Infrastructure de journalisation
  - Bus de messages asynchrone
- Agent de géotraitement (GeoAgent) 
  - Recherche de parcelles cadastrales
  - Analyse du potentiel forestier
  - Détection des zones prioritaires
- Agent de subventions (SubsidyAgent)
  - Module principal avec recherche et analyse d'éligibilité
  - Scrapers de subventions (BaseSubsidyScraper, FranceRelanceScraper)
  - Moteur d'analyse d'éligibilité avec règles avancées
  - Générateurs de documents (PDF, HTML, DOCX)
- Système de cache pour les données de subventions
- Intégration complète entre GeoAgent et SubsidyAgent
  - Enrichissement des données de projet avec analyses géospatiales
  - Utilisation des zones prioritaires pour la recherche de subventions
  - Exemple pratique d'intégration

### Amélioré
- Interface en ligne de commande pour exécuter les agents
- Documentation du système mise à jour

## [0.3.0] - 14/03/2025

### Ajouté
- Module d'analyse climatique (ClimateAnalyzer)
- Intégration entre GeoAgent et ClimateAnalyzer
- Documentation d'intégration climatique

### Optimisé
- Architecture modulaire pour GeoAgent
- Performance des analyses spatiales

## [0.2.0] - 01/03/2025

### Ajouté
- Agent de réglementation forestière (ReglementationAgent)
- Base de données réglementaires
- Module de vérification de conformité

### Amélioré
- Interface de ligne de commande
- Journalisation et gestion des erreurs

## [0.1.0] - 15/02/2025

### Ajouté
- Structure initiale du projet
- Agent de géotraitement (GeoAgent) avec analyses de base
- Intégration des données BD TOPO et cadastrales
- Documentation de base
