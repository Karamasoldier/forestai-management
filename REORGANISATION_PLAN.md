# Plan de réorganisation du projet ForestAI

Ce document décrit le plan détaillé pour réorganiser le projet ForestAI afin d'améliorer sa structure, sa maintenabilité et résoudre les problèmes existants.

## 1. Problèmes identifiés

1. **Problèmes de références circulaires dans les modèles Pydantic**
   - Erreurs de récursion maximum dépassée dans la représentation des modèles
   - Correctifs dispersés à plusieurs endroits

2. **Multiplication de scripts correctifs**
   - `fix_pydantic_v1_recursion.py`
   - `fix_recursion_errors.py`
   - Autres fichiers contenant des correctifs partiels

3. **Duplication de code**
   - Plusieurs versions du même serveur API (`api_server.py`, `api_server_fix.py`, `api_server_run_directly.py`)
   - Multiples scripts de démarrage avec fonctionnalités similaires

4. **Points d'entrée multiples et confus**
   - `run.py`, `run_forestai.py`, `run_api_with_fix.py`, etc.
   - Scripts batch Windows et shell Linux redondants

5. **Structure de projet incohérente**
   - Fichiers qui devraient être dans des modules placés à la racine
   - Organisation non conforme aux bonnes pratiques Python

## 2. Plan de réorganisation

### 2.1 Restructuration des modèles de données

1. **Modulariser les modèles Pydantic**
   - Séparer les modèles en unités logiques (domaines)
   - Éviter les imports circulaires

2. **Adopter une solution permanente pour les références circulaires**
   - Utiliser des références par ID plutôt que des objets imbriqués
   - Utiliser l'approche `ForwardRef` lorsque nécessaire

3. **Améliorer la sérialisation**
   - Créer des fonctions de sérialisation/désérialisation personnalisées
   - Utiliser des décorateurs pour contrôler la profondeur de sérialisation

### 2.2 Module de correctifs centralisé

1. **Créer un module dédié pour les patches**
   - `forestai/core/patches/` pour centraliser tous les correctifs
   - Documenter chaque correctif et son utilisation

2. **Fournir une API claire**
   - `apply_all_patches()` pour appliquer tous les correctifs nécessaires
   - Options granulaires pour des correctifs spécifiques

3. **Compatibilité avec les deux versions de Pydantic**
   - Support pour Pydantic v1 et v2
   - Détection automatique de la version

### 2.3 Réorganisation des points d'entrée

1. **Créer un module CLI unifié**
   - `forestai/cli/` pour toutes les commandes en ligne
   - Interface cohérente avec sous-commandes

2. **Simplifier les scripts de démarrage**
   - Un point d'entrée principal `forestai-cli`
   - Options de ligne de commande pour toutes les fonctionnalités

3. **Consolider les scripts d'environnement**
   - Un seul script Windows (.bat)
   - Un seul script Linux/macOS (.sh)

### 2.4 Structure de code propre

1. **Organiser selon les bonnes pratiques Python**
   - Suivre la structure de package standard
   - Utiliser des imports relatifs appropriés

2. **Déplacer les fichiers utilitaires**
   - De la racine vers des modules appropriés
   - Grouper par fonctionnalité

3. **Supprimer la duplication**
   - Fusionner les versions multiples de serveurs API
   - Partager le code commun via des fonctions utilitaires

### 2.5 Documentation améliorée

1. **Mise à jour des READMEs**
   - Documentation claire du nouveau système
   - Guides d'utilisation simplifiés

2. **Guide de développement**
   - Instructions pour les contributeurs
   - Documentation de l'architecture

3. **Exemples de code mis à jour**
   - Exemples reflétant la nouvelle structure
   - Tutoriels pour les cas d'utilisation courants

## 3. Procédure de réorganisation

1. **Phase préparatoire**
   - Créer la branche `reorganisation`
   - Établir les tests de base pour valider les modifications

2. **Restructuration par module**
   - Réorganiser un module à la fois
   - Tester après chaque changement majeur

3. **Consolidation et test**
   - Fusionner les scripts dupliqués
   - Vérifier les fonctionnalités de bout en bout

4. **Documentation et nettoyage**
   - Mettre à jour toute la documentation
   - Supprimer les fichiers obsolètes

5. **Validation finale**
   - Tests complets
   - Vérification des performances
   - Validation par les utilisateurs

## 4. Structure finale proposée

```
forestai/
├── cli/                      # Interface en ligne de commande
│   ├── __init__.py
│   ├── commands/             # Commandes spécifiques
│   └── main.py               # Point d'entrée principal
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── patches/              # Correctifs centralisés 
│   │   ├── __init__.py
│   │   ├── pydantic_fixes.py
│   │   └── api_fixes.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── models/           # Modèles de données restructurés
│   └── infrastructure/
├── api/
│   ├── __init__.py
│   ├── server.py             # Version unifiée du serveur API
│   ├── models.py             # Modèles d'API optimisés
│   └── routes/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   └── [agents spécifiques...]
├── utils/                    # Utilitaires consolidés
├── web/                      # Interface web Vite.js
└── webui/                    # Interface web Vue CLI
```

## 5. Avantages de la réorganisation

1. **Meilleure maintenabilité**
   - Structure claire et intuitive
   - Réduction significative de la duplication

2. **Facilité d'utilisation**
   - Points d'entrée simplifiés
   - Documentation améliorée

3. **Performance et stabilité**
   - Élimination des erreurs de récursion
   - Meilleure gestion des dépendances

4. **Évolutivité**
   - Facilité d'ajout de nouveaux agents
   - Infrastructure plus modulaire
