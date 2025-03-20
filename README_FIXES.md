# ForestAI - Correctifs pour les erreurs de récursion

Ce document décrit les correctifs mis en place pour résoudre les erreurs de récursion maximum dépassée lors de l'utilisation de l'interface web du projet ForestAI.

## Problème identifié

L'erreur `RecursionError: maximum recursion depth exceeded` se produit lors du démarrage de l'API REST, spécifiquement dans les modèles Pydantic utilisés pour les modèles de données API. Le problème est lié aux méthodes `__repr_args__` et `display_as_type` qui entrent dans une boucle infinie à cause de références circulaires dans certains modèles de données.

## Fichiers correctifs ajoutés

Plusieurs fichiers ont été ajoutés pour résoudre ce problème :

1. **forestai/api/models_fix.py**
   - Module contenant une fonction `safe_repr()` pour éviter les récursions infinies
   - Versions alternatives des modèles Pydantic problématiques
   - Fonction `apply_model_fixes()` pour remplacer les modèles originaux

2. **forestai/api/server_fix.py**
   - Version corrigée du module serveur qui applique les correctifs avant de démarrer
   - Fonction `patched_run_server()` qui remplace la fonction originale

3. **api_server_fix.py**
   - Script de démarrage alternatif pour l'API qui utilise les versions corrigées

4. **start_web_fix.py**
   - Version modifiée du script `start_web.py` utilisant l'API corrigée

5. **run_web_fix.sh**
   - Script shell pour démarrer l'interface web avec les correctifs (Linux/macOS)

6. **run_web_fix.bat**
   - Script batch pour démarrer l'interface web avec les correctifs (Windows)

7. **scripts/debug_pydantic_models.py** (Nouveau)
   - Script utilitaire pour diagnostiquer les références circulaires dans les modèles Pydantic
   - Analyse profonde des modèles et leurs relations

8. **test_models_fix.py** (Nouveau)
   - Utilitaire de test pour vérifier que les correctifs fonctionnent correctement
   - Teste la représentation et la sérialisation JSON des modèles
   - Test spécifique des cas imbriqués complexes

9. **fix_recursion_errors.py** (Nouveau)
   - Script automatisé pour détecter et corriger les problèmes de récursion
   - Peut fonctionner en mode vérification ou application
   - Met à jour automatiquement `models_fix.py` avec les correctifs nécessaires

## Comment utiliser les correctifs

Pour utiliser les versions corrigées et éviter les erreurs de récursion infinie, plusieurs méthodes sont disponibles :

### Correctifs automatiques (recommandé)

La méthode la plus simple pour résoudre les problèmes de récursion :

```bash
# Vérifier les modèles problématiques sans modifier les fichiers
python fix_recursion_errors.py --check

# Appliquer automatiquement les correctifs pour tous les modèles problématiques
python fix_recursion_errors.py --apply
```

### Démarrage avec scripts corrigés

#### Linux/macOS

```bash
# Rendre le script exécutable
chmod +x run_web_fix.sh

# Démarrer l'interface web avec l'API corrigée
./run_web_fix.sh
```

#### Windows

```bash
# Démarrer l'interface web avec l'API corrigée
run_web_fix.bat
```

### Options disponibles

Les mêmes options que pour les scripts originaux sont disponibles :

```bash
# Démarrer uniquement l'API corrigée
./run_web_fix.sh --api-only

# Démarrer uniquement l'interface web
./run_web_fix.sh --web-only

# Choisir l'interface (webui/ ou web/)
./run_web_fix.sh --web-type vue
./run_web_fix.sh --web-type vite

# Spécifier un port pour l'API
./run_web_fix.sh --api-port 8080

# Activer le rechargement automatique
./run_web_fix.sh --reload
```

## Détails techniques

Le correctif fonctionne en modifiant le comportement des modèles Pydantic problématiques :

1. Remplace les méthodes `__repr__` par une version sécurisée qui évite les représentations récursives
2. Au lieu d'inclure les objets complets dans les représentations, utilise simplement les noms de classes
3. Remplace dynamiquement les modèles originaux par les versions corrigées au démarrage

Ces modifications permettent d'éviter la récursion infinie tout en maintenant le fonctionnement normal de l'API.

## Diagnostic et tests

Pour diagnostiquer des problèmes de récursion :

```bash
# Exécuter le script de diagnostic pour identifier les modèles problématiques
python scripts/debug_pydantic_models.py

# Tester les correctifs pour vérifier leur efficacité
python test_models_fix.py
```

## Causes techniques spécifiques

Les erreurs de récursion sont principalement dues à :

1. **Références circulaires** : Des modèles qui se référencent mutuellement (directement ou indirectement)
   - Exemple : `DiagnosticRequest` contient `InventoryData` qui contient `InventoryItem`

2. **Auto-références dans la méthode `__repr__`** : La méthode standard de Pydantic pour afficher les instances de modèles tente d'inclure les représentations complètes de tous les sous-objets, créant ainsi des boucles infinies.

3. **Problèmes similaires dans la sérialisation JSON** : Dans certains cas, la sérialisation peut également entrer dans des boucles infinies, bien que Pydantic tente d'éviter cela.

## Notes additionnelles

- Ces correctifs ne modifient pas le comportement fonctionnel de l'API
- Les données JSON envoyées et reçues restent les mêmes
- Seule la manière dont les modèles sont représentés en interne (pour le débogage) est modifiée

Si de nouvelles erreurs de récursion apparaissent, utilisez `fix_recursion_errors.py --apply` pour mettre à jour automatiquement les correctifs.

## Modèles corrigés

Les correctifs s'appliquent notamment aux modèles suivants :

- `InventoryItem`
- `InventoryData`
- `ProjectModel`
- `ApplicantModel`
- `ApplicationRequest`
- `DiagnosticRequest`
- `HealthAnalysisRequest`
- `EligibilityRequest`

Si d'autres modèles présentent des problèmes similaires, le script `fix_recursion_errors.py` les détectera et appliquera les correctifs nécessaires.
