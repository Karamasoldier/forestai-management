# Guide d'intégration des agents ForestAI

Ce document présente les méthodes d'intégration entre les différents agents de ForestAI pour créer des solutions complètes de gestion forestière.

## 1. Intégration SubsidyAgent ↔ GeoAgent

L'intégration entre SubsidyAgent et GeoAgent permet d'enrichir les recherches et analyses de subventions avec des données géospatiales précises.

### Flux de travail principal

```
┌──────────────┐            ┌──────────────┐
│   GeoAgent   │            │ SubsidyAgent │
└──────┬───────┘            └──────┬───────┘
       │                           │
       │  1. Recherche parcelle    │
       │←──────────────────────────┤
       │                           │
       │  2. Analyse potentiel     │
       │←──────────────────────────┤
       │                           │
       │  3. Détection zones       │
       │←──────prioritaires────────┤
       │                           │
       │  4. Résultats analyses    │
       │────────────────────────────┤
       │                           │
       │       5. Recherche        │
       │           subventions     │
       │                           │
       │       6. Analyse          │
       │          éligibilité      │
       │                           │
       │       7. Génération       │
       │          documents        │
       │                           │
```

### Méthodes d'intégration

#### Approche synchrone (appel direct)

Le SubsidyAgent appelle directement les méthodes du GeoAgent :

```python
# Dans SubsidyAgent
geo_agent = GeoAgent(self.config)
parcel_data = geo_agent.execute_action("get_parcel_data", {"parcel_id": parcel_id})
priority_zones = geo_agent.execute_action("detect_priority_zones", {"parcel_id": parcel_id})
```

#### Approche asynchrone (bus de messages)

Les agents communiquent via le bus de messages :

```python
# Dans SubsidyAgent
self.publish_message("PRIORITY_ZONE_DETECTION_REQUESTED", {
    "request_id": request_id,
    "parcel_id": parcel_id
})

# Dans GeoAgent, le message est traité et la réponse est publiée
self.publish_message("PRIORITY_ZONE_DETECTION_COMPLETED", {
    "request_id": data.get("request_id"),
    "parcel_id": parcel_id,
    "priority_zones": priority_zones,
    "status": "success"
})
```

### Enrichissement des données

Le SubsidyAgent enrichit les projets avec les données géospatiales :

```python
def _enhance_project_with_geo_data(self, project, parcel_id):
    enhanced_project = project.copy()
    
    # Ajouter les données d'analyse de parcelle
    if parcel_id in self.parcel_analysis_cache:
        analysis = self.parcel_analysis_cache[parcel_id]
        enhanced_project["area_ha"] = analysis.get("area_ha")
        enhanced_project["slope"] = analysis.get("average_slope")
        # ...
    
    # Ajouter les zones prioritaires
    if parcel_id in self.priority_zone_cache:
        enhanced_project["priority_zones"] = self.priority_zone_cache[parcel_id]
    
    return enhanced_project
```

### Exemple complet

Un exemple complet d'intégration est disponible dans `examples/subsidy_geo_integration_example.py`. Il illustre :

1. La recherche de parcelles forestières
2. L'analyse du potentiel forestier
3. La détection des zones prioritaires
4. La recherche de subventions adaptées
5. L'analyse d'éligibilité
6. La génération de documents de demande

## 2. Bonnes pratiques d'intégration

### Communication asynchrone

Pour les intégrations complexes, privilégiez la communication asynchrone via le bus de messages :

1. Publiez des messages avec des identifiants de requête uniques
2. Chaque agent s'abonne aux sujets pertinents
3. Utilisez un système de cache pour stocker les données entre messages

### Format des données

Pour garantir la compatibilité entre agents :

- Utilisez des identifiants cohérents pour les parcelles (`parcel_id`)
- Standardisez les noms d'espèces (`pinus_halepensis` plutôt que `Pin d'Alep`)
- Utilisez des structures de données communes pour les types récurrents (zones prioritaires, risques...)

### Traçabilité

Assurez-vous que toutes les communications entre agents sont tracées :

- Utilisez le logger pour documenter les échanges
- Incluez un `request_id` dans tous les messages
- Ajoutez des timestamps aux événements

## 3. Extension avec d'autres agents

Pour intégrer d'autres agents au système :

### ReglementationAgent

Le ReglementationAgent peut intégrer :
- Les données GeoAgent pour vérifier si une parcelle est dans une zone réglementée
- Les analyses du SubsidyAgent pour vérifier la conformité des projets subventionnés

### ClimateAnalyzer

Le ClimateAnalyzer peut être intégré pour :
- Enrichir les données de parcelles avec des analyses climatiques
- Informer les choix d'essences pour les projets de reboisement
- Prioriser les zones vulnérables au changement climatique

## 4. Projection future

L'architecture permettra d'étendre les intégrations pour inclure :

- L'agent de diagnostic forestier (DiagnosticAgent)
- L'agent de génération de documents (DocumentAgent)
- L'agent de gestion des exploitants forestiers (ExploitantAgent)

Ces intégrations suivront les mêmes principes de communication standardisée.
