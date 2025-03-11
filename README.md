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
- **SubventionAgent** : Veille sur les aides disponibles
- **DiagnosticAgent** : Analyse des données terrain
- **DocumentAgent** : Génération de documents administratifs
- **ExploitantAgent** : Base de données des opérateurs forestiers

## Données géographiques

Suite à l'arrêt de la génération de clés API Geoservices par l'IGN début 2024, ForestAI fonctionne avec des données géographiques téléchargées localement dans le dossier `data/raw/`. Pour plus d'informations, consultez la [documentation du GeoAgent](docs/GeoAgent.md).

## Installation

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

## Téléchargement des données

Les données géographiques doivent être téléchargées manuellement depuis les sources suivantes:

- [Données cadastrales](https://cadastre.data.gouv.fr/datasets/cadastre-etalab)
- [BD TOPO IGN](https://geoservices.ign.fr/bdtopo)
- [Occupation des sols (Corine Land Cover)](https://www.data.gouv.fr/fr/datasets/corine-land-cover-occupation-des-sols-en-france/)
- [Modèle Numérique de Terrain (MNT)](https://geoservices.ign.fr/rgealti)

Placez les données téléchargées dans les dossiers appropriés définis dans le fichier `.env`.

## Agents et documentation

- [Agent de géotraitement (GeoAgent)](docs/GeoAgent.md)
- [Agent de réglementation forestière](docs/ReglementationAgent.md)

## Utilisation

```bash
# Lancer le système complet
python run.py

# Utiliser un agent spécifique
python run.py --agent geoagent

# Rechercher des parcelles dans une commune spécifique
python run.py --agent geoagent --action search_parcels --params '{"commune": "Saint-Martin-de-Crau", "section": "B"}'

# Vérifier la conformité réglementaire d'une parcelle
python run.py --agent reglementation --action check_compliance --params '{"parcels": ["123456789"], "project_type": "boisement"}'
```

## Approche architecturale

Pour gérer efficacement la complexité croissante du système, la nouvelle architecture suit ces principes :

### 1. Architecture en couches

```
┌─────────────────────────────────────────────────────┐
│                     Agent Layer                      │
│  (GeoAgent, ReglementationAgent, SubventionAgent)   │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│                  Domain Layer                        │
│ (ForestryAnalytics, RegulatoryFramework, etc.)      │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│                Infrastructure Layer                  │
│ (GeoData Access, Database, API Integration)         │
└─────────────────────────────────────────────────────┘
```

### 2. Services de domaine

Encapsuler la logique métier complexe dans des services spécialisés utilisés par les agents :

```python
# Exemple : ForestPotentialService utilisé par le GeoAgent
forest_potential_service = ForestPotentialService(geo_data_repository, climate_repository)
potential_score = forest_potential_service.analyze_parcel_potential(parcel_id)
```

### 3. Interfaces de communication standardisées

Utiliser des structures de données fortement typées pour la communication entre agents :

```python
@dataclass
class ParcelAnalysisRequest:
    parcel_ids: List[str]
    analysis_type: str
    parameters: Dict[str, Any] = None
```

### 4. Bus de messages

Implémenter un système de messagerie asynchrone entre agents pour un couplage faible :

```python
message_bus.publish("PARCEL_ANALYZED", {
    "parcel_id": "123456789",
    "potential_score": 0.85,
    "suitable_species": ["pine", "oak"]
})
```

### 5. Configuration modulaire

Rendre les fonctionnalités des agents configurables pour faciliter les tests et le déploiement progressif.

### 6. Mémoire partagée entre agents

Système de stockage contextuel pour partager l'état entre les agents :

```python
agent_memory.store("analysis:123456789", analysis_result)
```

### 7. Journalisation et monitoring

Journalisation détaillée des opérations des agents pour faciliter le débogage et l'optimisation.

### 8. Framework de test

Tests automatisés pour valider le comportement des agents.

### 9. Déploiement par phases

Suivre la roadmap en implémentant progressivement les agents et leurs fonctionnalités.

### 10. Pattern de fédération

Pour les agents complexes, les diviser en sous-agents spécialisés avec un coordinateur :

```
┌───────────────────────────────────┐
│        GeoAgent Coordinator       │
└──┬────────────┬─────────────┬─────┘
   │            │             │
┌──▼───┐    ┌───▼──┐    ┌─────▼────┐
│Parcel│    │Terrain│    │Land Cover│
│Agent │    │Agent  │    │Agent     │
└──────┘    └───────┘    └──────────┘
```

## Intégration CrewAI (Optionnelle)

Le système peut être adapté pour utiliser le framework CrewAI qui offre une orchestration avancée des agents IA autonomes. L'approche consisterait à :

1. Convertir les agents actuels en agents CrewAI
2. Transformer les méthodes d'agents en outils CrewAI
3. Utiliser les capacités de collaboration native entre agents

## Workflow et Plan d'Exécution

Pour faire avancer le projet efficacement, nous suivrons ce workflow en 4 phases :

### Phase 1 : Fondation (Semaines 1-3)

1. **Infrastructure de base**
   - [x] Mise en place des couches architecturales
   - [ ] Création de la structure des repositories de données
   - [ ] Implémentation de l'infrastructure de logging
   - [ ] Configuration du système de tests unitaires

2. **Message Bus**
   - [ ] Conception de l'API du message bus
   - [ ] Implémentation de la version synchrone
   - [ ] Tests d'intégration entre deux services

3. **Agent Memory**
   - [ ] Implémentation de l'interface d'accès mémoire
   - [ ] Implémentation du backend Redis ou SQLite
   - [ ] Tests des opérations CRUD

### Phase 2 : GeoAgent Amélioré (Semaines 4-7)

1. **Réfactoring du GeoAgent**
   - [ ] Extraction de la logique métier vers des services de domaine
   - [ ] Implémentation de l'interface de communication
   - [ ] Tests unitaires des services

2. **Services Géospatiaux**
   - [ ] Implémentation de ParcelService
   - [ ] Implémentation de TerrainAnalysisService
   - [ ] Implémentation de ForestPotentialService

3. **Chargement de Données**
   - [ ] Implémentation des loaders pour données cadastrales
   - [ ] Implémentation des loaders pour BD TOPO
   - [ ] Implémentation des loaders pour Corine Land Cover
   - [ ] Tests d'intégration avec des données réelles

4. **Délivrables Phase 2**
   - [ ] API géospatiale fonctionnelle
   - [ ] Documentation des services
   - [ ] Jeu de données test

### Phase 3 : Réglementation et Subventions (Semaines 8-12)

1. **ReglementationAgent**
   - [ ] Extraction des règles du Code Forestier
   - [ ] Implémentation de RegulatoryFrameworkService
   - [ ] Implémentation de ComplianceCheckerService

2. **SubventionAgent**
   - [ ] Implémentation du crawler de subventions
   - [ ] Implémentation du système d'analyse d'éligibilité
   - [ ] Implémentation du générateur de dossiers

3. **Intégration**
   - [ ] Tests d'intégration GeoAgent ↔ ReglementationAgent
   - [ ] Tests d'intégration ReglementationAgent ↔ SubventionAgent

4. **Délivrables Phase 3**
   - [ ] API de conformité réglementaire
   - [ ] Base de données de subventions
   - [ ] Générateur de rapports de conformité

### Phase 4 : Diagnostic et Interface (Semaines 13-16)

1. **DiagnosticAgent**
   - [ ] Implémentation du système d'analyse forestière
   - [ ] Intégration avec les données géospatiales
   - [ ] Tests avec des cas d'usage réels

2. **DocumentAgent**
   - [ ] Implémentation des templates de documents
   - [ ] Intégration avec les autres agents
   - [ ] Tests de génération automatique

3. **Interface Utilisateur**
   - [ ] Conception des wireframes
   - [ ] Implémentation du frontend FastAPI
   - [ ] Tests d'acceptation utilisateur

4. **Délivrables Phase 4**
   - [ ] Système de diagnostic complet
   - [ ] Documents administratifs automatisés
   - [ ] Interface utilisateur fonctionnelle

## Méthodologie de Développement

Pour chaque composant majeur, nous suivrons ce processus :

1. **Conception** (1-2 jours)
   - Définir les interfaces
   - Établir les contrats
   - Documenter les comportements attendus

2. **Développement** (3-5 jours)
   - Implémentation TDD
   - Revue de code
   - Documentation inline

3. **Tests** (1-2 jours)
   - Tests unitaires
   - Tests d'intégration
   - Tests de performance (si pertinent)

4. **Livraison** (1 jour)
   - Documentation d'utilisation
   - Exemples d'utilisation
   - Mise à jour du README

## Suivi du Projet

Le suivi du projet est réalisé via :

- GitHub Issues pour les tâches spécifiques
- GitHub Projects pour la vue d'ensemble
- Réunions hebdomadaires de synchronisation
- Revues de code avant chaque merge

## Roadmap Détaillée

- [x] Architecture de base du système
- [x] Implémentation de l'agent de géotraitement avec données locales
- [ ] Refactoring en architecture multi-couches (S2)
- [ ] Implémentation du message bus (S3)
- [ ] Implémentation de l'agent memory (S3)
- [ ] Réfactoring du GeoAgent (S4-S5)
- [ ] Services géospatiaux complets (S6-S7)
- [ ] Implémentation de l'agent de réglementation forestière (S8-S10)
- [ ] Implémentation de l'agent de subventions (S10-S12)
- [ ] Implémentation de l'agent de diagnostic (S13-S14)
- [ ] Interface utilisateur (S15-S16)
- [ ] Documentation finale et déploiement (S16)

## Licence

Ce projet est sous licence MIT.
