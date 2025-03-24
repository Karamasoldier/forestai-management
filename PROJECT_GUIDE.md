# Guide de développement pour ForestAI

## Aperçu du projet

ForestAI est un système multi-agents pour l'automatisation et l'optimisation de la gestion forestière. Il vise à créer un écosystème d'agents spécialisés qui travaillent ensemble pour faciliter la gestion forestière, identifier des opportunités, assurer la conformité réglementaire, et automatiser les processus administratifs.

## Structure des agents

### Agents principaux et leurs fonctions

1. **GeoAgent**
   - Analyse géospatiale des parcelles et propriétés
   - Identification des terrains à potentiel forestier
   - Cartographie et traitement des données cadastrales
   - Sous-composants principaux:
     - `cadastre.py`: Interaction avec les données cadastrales
     - `parcel_analyzer.py`: Analyse des parcelles pour potentiel forestier

2. **ReglementationAgent**
   - Expert du Code Forestier et des réglementations environnementales
   - Vérification de conformité des projets forestiers
   - Alerte sur les contraintes réglementaires
   - Intégration continue des mises à jour législatives

3. **SubventionAgent**
   - Surveillance des aides financières disponibles
   - Analyse d'éligibilité des projets aux subventions
   - Génération de dossiers de demande d'aide
   - Sous-composants:
     - `scrapers/`: Extraction de données depuis les sites officiels
     - `eligibility.py`: Règles et logique d'éligibilité aux aides

4. **DiagnosticAgent**
   - Analyse des données terrain pour évaluation forestière
   - Reconnaissance d'espèces et état sanitaire
   - Recommandations de gestion adaptées
   - Sous-composants:
     - `species.py`: Identification des espèces végétales
     - `health.py`: Détection de problèmes sanitaires

5. **DocumentAgent**
   - Génération automatique de documents administratifs
   - Création de cahiers des charges et contrats
   - Formalisation des plans de gestion
   - Sous-composants:
     - `templates/`: Modèles de documents
     - `regulations.py`: Intégration des contraintes légales

6. **ExploitantAgent**
   - Base de données des opérateurs forestiers
   - Mise en relation propriétaires-exploitants
   - Évaluation des performances des prestataires

## Architecture technique

```
forestai/
├── agents/                    # Agents spécialisés
│   ├── base_agent.py          # Classe parent pour tous les agents
│   ├── geo_agent/             
│   ├── reglementation_agent/
│   ├── subsidy_agent/
│   ├── diagnostic_agent/
│   ├── document_agent/
│   └── exploitant_agent/
├── core/                     # Fonctionnalités partagées
│   ├── communication/        # Échange entre agents
│   ├── domain/               # Modèles de domaine
│   ├── infrastructure/       # Services techniques
│   └── utils/                # Utilitaires communs
├── data/                     # Données et ressources
├── gui/                      # Interface graphique PyQt6
│   ├── components.py         # Composants d'interface
│   ├── agent_api.py          # API pour interagir avec les agents
│   └── main_window.py        # Interface principale
├── web/                      # Interface web (Vite.js)
└── webui/                    # Interface web alternative (Vue CLI)
```

## Logique de workflow

1. **Acquisition de données**
   - GeoAgent collecte et analyse les données géospatiales
   - Import/scraping de données externes (cadastre, réglementations)

2. **Analyse et diagnostic**
   - DiagnosticAgent évalue l'état des parcelles
   - ReglementationAgent détermine les contraintes légales
   - SubventionAgent identifie les aides disponibles

3. **Génération de recommandations**
   - Croisement des analyses pour recommander des actions
   - Optimisation selon critères économiques et écologiques

4. **Production de documents**
   - DocumentAgent génère les documents administratifs
   - Plans de gestion, demandes de subvention, contrats

5. **Mise en relation**
   - ExploitantAgent propose des prestataires adaptés
   - Suivi de l'exécution des travaux

## Directives pour le développement

### Interface graphique

**Une interface graphique est essentielle pour ce projet.** Les raisons principales:
- Visualisation des données géospatiales et forestières
- Interaction intuitive avec les agents spécialisés
- Suivi des processus et workflows
- Accessibilité pour les utilisateurs non-techniques

L'interface existante en PyQt6 permet déjà:
- La surveillance des agents actifs
- L'exécution d'actions sur les agents
- La visualisation des tâches et résultats

Cette interface devrait être étendue pour intégrer:
- Visualisation cartographique des parcelles
- Tableaux de bord pour les diagnostics forestiers
- Formulaires interactifs pour les demandes de subvention
- Prévisualisation et édition des documents générés

### Conseils d'implémentation

1. **Communication inter-agents**
   - Utiliser le pattern Observer/Observable pour les notifications
   - Maintenir une cohérence des modèles de données entre agents

2. **Persistance des données**
   - Privilégier SQLAlchemy pour l'ORM
   - Implémenter un cache multiniveau pour optimiser les performances

3. **Test et validation**
   - Créer des tests unitaires pour chaque agent
   - Établir des scénarios de test end-to-end

4. **Architecture modulaire**
   - Respecter les principes SOLID
   - Injection de dépendances pour faciliter les tests et la maintenance

## Priorités de développement

1. Stabilisation du système d'agents
2. Amélioration de l'interface graphique PyQt6
3. Intégration du système de cache multiniveau
4. Enrichissement des fonctionnalités de diagnostic
5. Développement des intégrations avec les API externes (cadastre, subventions)
