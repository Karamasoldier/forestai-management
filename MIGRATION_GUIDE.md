# Guide de Migration ForestAI

Ce guide explique comment migrer de l'ancienne structure de ForestAI vers la nouvelle structure réorganisée.

## Résumé des changements

### 1. Interface en ligne de commande unifiée

Tous les scripts de démarrage ont été remplacés par un point d'entrée unique :

```bash
# Ancien système
python run_forestai.py                         # Système complet
python run_api_with_fix.py                     # API uniquement
python start_web.py                            # Interface web uniquement
python run.py --agent geoagent                 # Agent spécifique

# Nouveau système
python forestai-cli.py run                     # Système complet
python forestai-cli.py api                     # API uniquement
python forestai-cli.py web --web-only          # Interface web uniquement
python forestai-cli.py agent geoagent          # Agent spécifique
```

### 2. Correctifs pour les erreurs de récursion

Les correctifs pour les erreurs de récursion Pydantic sont maintenant intégrés dans le module `forestai.core.patches` :

```python
# Ancien système
import fix_pydantic_v1_recursion
fix_pydantic_v1_recursion.main()

# Nouveau système
from forestai.core.patches import apply_all_patches
apply_all_patches()
```

Ces correctifs sont automatiquement appliqués au démarrage via le script principal.

### 3. Fichiers supprimés ou remplacés

Les fichiers suivants ont été remplacés par la nouvelle structure :

- `fix_pydantic_v1_recursion.py` → `forestai.core.patches.pydantic_v1_fixes`
- `fix_recursion_errors.py` → `forestai.core.patches.pydantic_v1_fixes`
- `api_server.py`, `api_server_fix.py`, `api_server_run_directly.py` → `forestai.cli.commands.api_command`
- `run_forestai.py`, `run_api_with_fix.py`, `run.py` → `forestai-cli.py`
- `start_web.py`, `start_web_fix.py` → `forestai.cli.commands.web_command`

### 4. Structure de projet améliorée

La nouvelle structure suit les bonnes pratiques Python :

```
forestai/
├── cli/                      # Interface en ligne de commande
│   ├── commands/             # Commandes spécifiques
│   └── main.py               # Point d'entrée CLI
├── core/
│   ├── patches/              # Correctifs centralisés
│   │   ├── pydantic_v1_fixes.py
│   │   └── pydantic_v2_fixes.py
│   ├── domain/
│   └── infrastructure/
├── api/
│   ├── server.py             # Version unifiée du serveur API
└── [reste inchangé]
```

## Instructions de migration

### Pour les utilisateurs

1. **Utiliser le nouveau script d'entrée** :
   ```bash
   python forestai-cli.py
   ```

2. **Consulter l'aide pour les nouvelles options** :
   ```bash
   python forestai-cli.py --help
   python forestai-cli.py <command> --help
   ```

3. **Mettre à jour les scripts batch/shell** :
   Si vous avez des scripts personnalisés qui appellent les anciens points d'entrée, mettez-les à jour pour utiliser `forestai-cli.py`.

### Pour les développeurs

1. **Importer les correctifs du nouveau module** :
   ```python
   from forestai.core.patches import apply_pydantic_patches
   ```

2. **Utiliser l'API CLI pour les tests et l'intégration** :
   ```python
   from forestai.cli.commands.api_command import run_api
   run_api(["--port", "8080"])
   ```

3. **Structure des imports** :
   Mettez à jour vos imports pour refléter la nouvelle structure de modules.

## Notes de compatibilité

- Les scripts existants continueront de fonctionner pendant une période de transition.
- Les fonctionnalités restent identiques, seule l'organisation du code a changé.
- La nouvelle structure est compatible avec les deux versions de Pydantic (v1 et v2).
