# Architecture du système ForestAI

ForestAI est conçu selon une architecture en couches avec une approche modulaire pour faciliter l'évolution et la maintenance du système.

## Architecture en couches

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

## Principes architecturaux

### 1. Services de domaine

Le code métier complexe est encapsulé dans des services spécialisés utilisés par les agents :

```python
# Exemple : ForestPotentialService utilisé par le GeoAgent
forest_potential_service = ForestPotentialService(geo_data_repository, climate_repository)
potential_score = forest_potential_service.analyze_parcel_potential(parcel_id)

# Exemple : RegulatoryFrameworkService utilisé par le ReglementationAgent
regulatory_service = RegulatoryFrameworkService(data_path)
regulations = regulatory_service.get_regulations_by_project_type("boisement")

# Exemple : ClimateAnalyzer utilisé par le DiagnosticAgent
climate_analyzer = ClimateAnalyzer()
species_recommendations = climate_analyzer.recommend_species(geometry, scenario="2050_rcp45")

# Exemple : SubsidyAgent recherchant des subventions
subsidy_agent = SubsidyAgent(config)
eligible_subsidies = subsidy_agent.analyze_eligibility(parcel_data, project_data)
```

### 2. Interfaces de communication standardisées

Des structures de données fortement typées sont utilisées pour la communication entre agents :

```python
@dataclass
class ParcelAnalysisRequest:
    parcel_ids: List[str]
    analysis_type: str
    parameters: Dict[str, Any] = None
```

### 3. Bus de messages

Un système de messagerie asynchrone entre agents pour un couplage faible :

```python
message_bus.publish("PARCEL_ANALYZED", {
    "parcel_id": "123456789",
    "potential_score": 0.85,
    "suitable_species": ["pine", "oak"]
})
```

### 4. Configuration modulaire

Les fonctionnalités des agents sont configurables pour faciliter les tests et le déploiement progressif.

### 5. Mémoire partagée entre agents

Système de stockage contextuel pour partager l'état entre les agents :

```python
agent_memory.store("analysis:123456789", analysis_result)
```

### 6. Journalisation et monitoring

Journalisation détaillée des opérations des agents pour faciliter le débogage et l'optimisation.

### 7. Framework de test

Tests automatisés pour valider le comportement des agents.

### 8. Pattern de fédération

Pour les agents complexes, division en sous-agents spécialisés avec un coordinateur :

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

## Infrastructure de Logging

ForestAI intègre une infrastructure de logging avancée qui offre :

- Journalisation multi-niveaux (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Sortie vers console et fichiers avec rotation automatique
- Contexte d'exécution pour une meilleure traçabilité
- Collecte de métriques de performance
- Décorateurs pour le logging automatique des fonctions
- Gestion centralisée de la configuration

### Configuration du logging

La configuration du logging peut être définie via des variables d'environnement ou programmatiquement :

```python
from forestai.core.utils.logging_config import LoggingConfig

# Configuration personnalisée
config = LoggingConfig.get_instance()
config.init({
    "level": "DEBUG",
    "log_dir": "logs/myapp",
    "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
})
```

## Standardisation des géométries

Toutes les analyses spatiales sont standardisées sur la projection Lambert 93 (EPSG:2154) pour :
- Assurer la compatibilité avec les données cadastrales et IGN
- Effectuer des calculs métriques corrects (surface, distance)
- Minimiser les déformations pour le territoire français

## Intégration CrewAI (Optionnelle)

Le système peut être adapté pour utiliser le framework CrewAI qui offre une orchestration avancée des agents IA autonomes. L'approche consisterait à :

1. Convertir les agents actuels en agents CrewAI
2. Transformer les méthodes d'agents en outils CrewAI
3. Utiliser les capacités de collaboration native entre agents
