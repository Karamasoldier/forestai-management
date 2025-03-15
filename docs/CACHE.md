# Système de cache ForestAI

Ce document décrit le système de cache intégré à ForestAI pour optimiser les performances et réduire les appels redondants aux sources de données.

## Présentation générale

Le système de cache ForestAI est conçu pour améliorer les performances en stockant les résultats de calculs coûteux ou d'accès à des données externes. Il offre une architecture multi-niveaux avec des stratégies de mise à jour adaptatives selon le type de données.

Principales caractéristiques :
- Cache hiérarchique (mémoire, disque, base de données)
- Stratégies de fraîcheur adaptatives par type de données
- Mécanismes de préchargement pour les données fréquemment utilisées
- Décorations de fonction pour une intégration facile

## Architecture du cache

Le système de cache est organisé en plusieurs niveaux :

```
┌─────────────────────────────────────────────────────┐
│            Interface de cache unifiée                │
│   (CacheManager, décorateurs, utilitaires)          │
└───────────────────┬─────────────────────────────────┘
          ┌─────────┴──────────┐
┌─────────▼─────┐    ┌─────────▼─────┐    ┌───────────▼──────┐
│  Cache mémoire │    │  Cache disque  │    │ Cache base de   │
│  (rapide,      │    │  (persistant,  │    │ données (future │
│   volatile)    │    │   plus lent)   │    │ implémentation) │
└───────────────┘    └───────────────┘    └──────────────────┘
```

## Types de données et politiques

Le système définit différents types de données avec des politiques de mise à jour appropriées :

| Type | Description | Politique par défaut | Commentaire |
|------|-------------|---------------------|------------|
| `GEODATA` | Données géographiques | `WEEKLY` | Mises à jour peu fréquentes |
| `REGULATION` | Données réglementaires | `MONTHLY` | Mises à jour rares (lois) |
| `SUBSIDY` | Données de subventions | `DAILY` | Mises à jour régulières |
| `CLIMATE` | Données climatiques | `WEEKLY` | Données semi-statiques |
| `EXTERNAL_API` | Données d'API externes | `DAILY` | Fraîcheur importante |
| `GENERIC` | Données génériques | `DAILY` | Cas par défaut |

## Utilisation du cache

### Décorateur simple

```python
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

@cached(data_type=CacheType.GEODATA, policy=CachePolicy.WEEKLY)
def fetch_parcel_data(parcel_id):
    # Opération coûteuse...
    return data
```

### Gestion du cache manuel

```python
from forestai.core.infrastructure.cache.cache_manager import get_cache_manager
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy

# Récupérer le gestionnaire de cache
cache_manager = get_cache_manager()

# Récupérer depuis le cache
data = cache_manager.get(
    data_type=CacheType.GEODATA,
    identifier="13097000B0012",
    policy=CachePolicy.WEEKLY,
    refresh_callback=lambda: compute_expensive_data()
)

# Stocker manuellement dans le cache
cache_manager.set(
    data_type=CacheType.GEODATA,
    identifier="13097000B0012",
    data=result,
    policy=CachePolicy.WEEKLY
)
```

### Propriété mise en cache

```python
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import CachedProperty

class MyClass:
    @CachedProperty(CacheType.REGULATION, CachePolicy.MONTHLY)
    def regulations(self):
        # Calcul coûteux...
        return result
```

### Préchargement de données

```python
from forestai.core.infrastructure.cache.cache_utils import preload_cache
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy

# Fonction de chargement des données
def load_common_data():
    return {
        "id1": data1,
        "id2": data2,
        # ...
    }

# Précharger les données
count = preload_cache(
    data_type=CacheType.REGULATION,
    data_loader=load_common_data,
    policy=CachePolicy.MONTHLY
)
```

## Stratégies de fraîcheur

Le système propose plusieurs politiques de mise à jour :

- `ALWAYS_FRESH` : Considère les données comme toujours périmées (utile pour les données très volatiles)
- `DAILY` : Mise à jour quotidienne (24 heures)
- `WEEKLY` : Mise à jour hebdomadaire (7 jours)
- `MONTHLY` : Mise à jour mensuelle (30 jours)
- `STATIC` : Données statiques (pas d'expiration)
- `CUSTOM` : Politique personnalisée (avec TTL spécifique)

## Invalidation du cache

Pour forcer le rafraîchissement des données :

```python
from forestai.core.infrastructure.cache.cache_utils import invalidate_cache, force_refresh
from forestai.core.infrastructure.cache.base import CacheType

# Invalider une entrée
invalidate_cache(
    data_type=CacheType.GEODATA,
    identifier="13097000B0012"
)

# Forcer le rafraîchissement
fresh_data = force_refresh(
    data_type=CacheType.GEODATA,
    identifier="13097000B0012",
    refresh_func=lambda: compute_expensive_data()
)
```

## Fonctionnalités avancées

### Chargement par batch

Pour charger efficacement de grandes quantités de données :

```python
from forestai.core.infrastructure.cache.cache_utils import BatchCacheLoader
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy

# Créer un chargeur de batch
loader = BatchCacheLoader(
    data_type=CacheType.GEODATA,
    policy=CachePolicy.WEEKLY,
    batch_size=100
)

# Charger des données par batch
count = loader.load_from_generator(data_generator)
```

### Mémo-isation simple

Pour mettre en cache les résultats d'une fonction en mémoire sans persistance :

```python
from forestai.core.infrastructure.cache.cache_utils import memoize

@memoize
def expensive_calculation(param1, param2):
    # Calcul coûteux...
    return result

# Vider le cache de la fonction
expensive_calculation.clear_cache()
```

## Intégration avec les agents

Les agents peuvent être facilement étendus pour utiliser le cache :

```python
from forestai.agents.geo_agent import GeoAgent
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

class CachedGeoAgent(GeoAgent):
    @cached(
        data_type=CacheType.GEODATA,
        identifier_key="parcel_id",
        policy=CachePolicy.WEEKLY
    )
    def analyze_parcel(self, parcel_id, analyses=None):
        return super().analyze_parcel(parcel_id, analyses)
```

## Statistiques et monitoring

Le système fournit des statistiques d'utilisation :

```python
from forestai.core.infrastructure.cache.cache_utils import get_cache_stats

stats = get_cache_stats()
print(f"Hit ratio: {stats['hit_ratio']:.2f}")
print(f"Memory hits: {stats['memory_hits']}")
print(f"Disk hits: {stats['disk_hits']}")
```

## Exemple complet

Voir le fichier `examples/cache_usage_example.py` pour un exemple complet d'utilisation.

## Optimisations futures

- Extension du backend de base de données pour les grands volumes de données
- Gestion intelligente de l'expulsion basée sur la fréquence d'utilisation (LFU/LRU)
- Distribution du cache pour les déploiements multi-serveurs
- Compression des données volumineuses
