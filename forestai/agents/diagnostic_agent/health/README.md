# Module d'analyse sanitaire forestière

Ce module fournit des outils pour analyser l'état sanitaire des peuplements forestiers, identifier les problèmes, et générer des recommandations de gestion.

## Composants principaux

### HealthAnalyzer

Analyseur sanitaire standard qui détecte les problèmes forestiers et évalue l'état de santé global.

```python
from forestai.agents.diagnostic_agent.health.health_analyzer import HealthAnalyzer

analyzer = HealthAnalyzer()
result = analyzer.analyze_health(inventory_data, additional_symptoms, climate_data)
```

### OptimizedHealthAnalyzer

Version optimisée de l'analyseur sanitaire pour les grands volumes de données.

```python
from forestai.agents.diagnostic_agent.health.optimized_analyzer import OptimizedHealthAnalyzer

# Configuration personnalisée
config = {
    "optimization": {
        "parallel_enabled": True,
        "max_processes": 4,
        "batch_size": 100
    }
}

analyzer = OptimizedHealthAnalyzer(config)
result = analyzer.analyze_health(inventory_data, additional_symptoms, climate_data)
```

### Modules complémentaires

- **health_issue.py** - Modèle pour les problèmes sanitaires
- **database_loader.py** - Chargeur de la base de référence de problèmes
- **species_analyzer.py** - Analyseur par espèce d'arbre
- **indicator_calculator.py** - Calcul des indicateurs sanitaires
- **issue_detector.py** - Détection des problèmes sanitaires
- **risk_evaluator.py** - Évaluation des risques sanitaires
- **recommendation_generator.py** - Générateur de recommandations
- **summary_generator.py** - Générateur de résumés sanitaires
- **performance_optimizer.py** - Optimisations de performance

## Fonctionnalités clés

- Détection de 50+ problèmes sanitaires forestiers
- Analyse par espèce avec recommandations ciblées
- Évaluation des risques futurs basée sur les données climatiques
- Génération de recommandations de gestion adaptées
- Traitement optimisé pour les grands inventaires (>1000 arbres)
- Support pour l'intégration dans les rapports de diagnostic

## Format des données d'entrée

```python
# Format minimum d'inventaire
inventory_data = {
    "items": [
        {
            "species": "quercus_ilex",
            "diameter": 25.5,
            "height": 12.0,
            "health_status": "moyen"
        }
    ]
}

# Symptômes supplémentaires (optionnels)
additional_symptoms = {
    "leaf_discoloration": 0.35,
    "observed_pests": ["bark_beetle"],
    "crown_thinning": 0.25
}

# Données climatiques (optionnelles)
climate_data = {
    "annual_temp": 14.2,
    "annual_precip": 650,
    "drought_index": 0.4
}
```

## Format des données de sortie

L'analyse sanitaire produit une structure de données détaillée contenant:

- Score sanitaire global (0-10)
- État sanitaire général (Bon, Moyen, Mauvais)
- Liste des problèmes détectés avec gravité et confiance
- Indicateurs sanitaires (transparence du houppier, perte foliaire, etc.)
- Analyses par espèce
- Recommandations de gestion avec priorités d'action
- Métadonnées (date d'analyse, version, etc.)

## Optimisation des performances

Pour les grands inventaires, utilisez l'`OptimizedHealthAnalyzer` qui offre:

- Parallélisation des calculs sur plusieurs cœurs
- Traitement par lots pour optimiser la mémoire
- Sélection automatique du mode d'analyse selon la taille des données

Pour plus de détails, consultez la [documentation d'optimisation](/docs/PerformanceOptimization.md).

## Exemples d'utilisation

Des exemples complets sont disponibles dans:

- `examples/api_health_analysis_example.py` - Utilisation via l'API REST
- `examples/optimized_health_analysis_example.py` - Tests de performance

## Guide de dépannage

### Problèmes courants

1. **Lenteur d'analyse** - Pour les grands inventaires, utilisez `OptimizedHealthAnalyzer`
2. **Manque de précision** - Fournissez des données plus détaillées (notamment espèces et diamètres)

### Activation des logs de débogage

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("forestai.agents.diagnostic_agent.health").setLevel(logging.DEBUG)
```