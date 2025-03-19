# ForestAI - Correctifs pour les erreurs de récursion

Ce document décrit les correctifs mis en place pour résoudre les erreurs de récursion maximum dépassée lors de l'utilisation de l'interface web du projet ForestAI.

## Problème identifié

L'erreur `RecursionError: maximum recursion depth exceeded` se produit lors du démarrage de l'API REST, spécifiquement dans les modules Pydantic utilisés pour les modèles de données API. Le problème est lié aux méthodes `__repr_args__` et `display_as_type` qui entrent dans une boucle infinie à cause de références circulaires dans certains modèles de données.

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

## Comment utiliser les correctifs

Pour utiliser les versions corrigées et éviter les erreurs de récursion infinie, utilisez les scripts de démarrage alternatifs :

### Linux/macOS

```bash
# Rendre le script exécutable
chmod +x run_web_fix.sh

# Démarrer l'interface web avec l'API corrigée
./run_web_fix.sh
```

### Windows

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

## Notes additionnelles

- Ces correctifs ne modifient pas le comportement fonctionnel de l'API
- Les données JSON envoyées et reçues restent les mêmes
- Seule la manière dont les modèles sont représentés en interne (pour le débogage) est modifiée

Si de nouvelles erreurs de récursion apparaissent, vous devrez peut-être ajouter d'autres modèles à la liste des modèles corrigés dans `forestai/api/models_fix.py`.
