# ForestAI - Correctifs pour les erreurs de récursion

Ce document décrit les correctifs mis en place pour résoudre les erreurs de récursion maximum dépassée lors de l'utilisation de l'interface web du projet ForestAI.

## Problème identifié

L'erreur `RecursionError: maximum recursion depth exceeded` se produit lors du démarrage de l'API REST, spécifiquement dans les modèles Pydantic utilisés pour les modèles de données API. Le problème est lié aux méthodes `__repr_args__` et `display_as_type` qui entrent dans une boucle infinie à cause de références circulaires dans certains modèles de données.

## Solution recommandée

Pour Pydantic v1.x (version utilisée dans ce projet), la solution recommandée est:

```bash
# Appliquer le correctif spécifique pour Pydantic v1
python fix_pydantic_v1_recursion.py

# Démarrer l'API avec le correctif pré-appliqué
python run_api_with_fix.py --host 0.0.0.0 --port 8000
```

## Fichiers correctifs ajoutés

Les principaux fichiers de correctif sont:

1. **fix_pydantic_v1_recursion.py**
   - Correctif direct pour Pydantic v1.x
   - Patch les fonctions internes de Pydantic responsables des erreurs de récursion
   - Spécifiquement conçu pour les environnements où Pydantic v1 est installé

2. **run_api_with_fix.py**
   - Script de démarrage de l'API qui applique d'abord le correctif pour Pydantic v1
   - Compatible avec la version de Pydantic utilisée dans le projet

## Détails techniques

### Solution pour Pydantic v1.x

Le correctif pour Pydantic v1 fonctionne en modifiant directement les fonctions internes de Pydantic :

1. `BaseModel.__repr_args__` - Remplacée par une version sécurisée qui détecte les références circulaires
2. `display_as_type` - Modifiée pour éviter les récursions infinies dans l'affichage des types
3. Utilise un système de "visite" des objets pour éviter de traiter deux fois le même objet

## Causes techniques spécifiques

Les erreurs de récursion sont principalement dues à :

1. **Références circulaires** : Des modèles qui se référencent mutuellement (directement ou indirectement)
   - Exemple : `DiagnosticRequest` contient `InventoryData` qui contient `InventoryItem`

2. **Auto-références dans la méthode `__repr__`** : La méthode standard de Pydantic pour afficher les instances de modèles tente d'inclure les représentations complètes de tous les sous-objets, créant ainsi des boucles infinies.

3. **Problèmes dans `display_as_type`** : Pour Pydantic v1, cette fonction peut entrer dans une boucle infinie lors de l'affichage de types complexes avec références circulaires.

## Modèles problématiques

Les modèles qui présentent le plus souvent des problèmes de récursion sont:

- `InventoryItem`
- `InventoryData`
- `ProjectModel`
- `ApplicantModel`
- `ApplicationRequest`
- `DiagnosticRequest`
- `HealthAnalysisRequest`
- `EligibilityRequest`

Ces modèles contiennent des références circulaires qui causent les erreurs de récursion.
