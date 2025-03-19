# ForestAI - Guide de démarrage des interfaces web

Ce document fournit des instructions détaillées pour installer, configurer et tester les interfaces web du projet ForestAI.

## Prérequis

- Python 3.9+ 
- Node.js 16+ et npm
- Commandes Git standard
- Un éditeur de code (VSCode recommandé)

## Installation automatisée

Le projet inclut maintenant un script d'installation simplifié qui configure automatiquement l'environnement :

```bash
# Cloner le dépôt (si ce n'est pas déjà fait)
git clone https://github.com/Karamasoldier/forestai-management.git
cd forestai-management

# Créer l'environnement virtuel Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate    # Windows

# Exécuter le script d'installation
python setup.py
```

Le script `setup.py` effectue automatiquement les actions suivantes :
- Crée les répertoires de données nécessaires
- Vérifie et crée les fichiers .env nécessaires
- Installe les dépendances Python et JavaScript

## Démarrage de l'application

ForestAI dispose désormais d'un script de démarrage unifié qui lance à la fois l'API backend et l'interface web :

```bash
# Avec l'environnement virtuel activé
python start_web.py
```

Options disponibles :
- `--api-only` : Démarre uniquement l'API
- `--web-only` : Démarre uniquement l'interface web
- `--web-type vue|vite` : Choisir l'interface (webui/ ou web/)
- `--api-port XXXX` : Spécifier un port pour l'API (défaut: 8000)
- `--reload` : Activer le rechargement automatique pour l'API

## Connexion et authentification

Pour tester l'interface, utilisez l'un des comptes suivants :

1. **Administrateur**
   - Nom d'utilisateur : `admin`
   - Mot de passe : `adminpassword`
   - Droits : Accès complet à toutes les fonctionnalités

2. **Utilisateur standard**
   - Nom d'utilisateur : `user`
   - Mot de passe : `userpassword`
   - Droits : Accès en lecture aux données géographiques, subventions, diagnostics et réglementations

3. **Agent de diagnostic**
   - Nom d'utilisateur : `diagnostic`
   - Mot de passe : `diagnosticpassword`
   - Droits : Accès aux fonctionnalités de diagnostic

## Interfaces web disponibles

Le projet propose deux interfaces web différentes :

### 1. Interface Vite.js (répertoire `web/`)

Interface moderne utilisant Vite.js et Vue 3 :
- Architecture composants
- UI basée sur Bootstrap 5
- Intégration Leaflet pour la cartographie
- Visualisations avec Chart.js

Pour la lancer individuellement :
```bash
cd web
npm install
npm run dev
```

### 2. Interface Vue CLI (répertoire `webui/`)

Interface alternative utilisant Vue CLI :
- Architecture modulaire avec Vuex et Vue Router
- UI basée sur PrimeVue
- Visualisations avec Chart.js et D3.js

Pour la lancer individuellement :
```bash
cd webui
npm install
npm run serve
```

## Structure des API disponibles

L'API REST est accessible à l'adresse `http://localhost:8000` et propose les endpoints suivants :

- **Authentification** : `/auth/token` (POST) pour obtenir un token JWT
- **GeoAgent** : 
  - `/geo/search` (POST) : Recherche de parcelles
  - `/geo/analyze` (POST) : Analyse d'une parcelle
- **SubsidyAgent** : 
  - `/subsidies/search` (POST) : Recherche de subventions
  - `/subsidies/eligibility` (POST) : Analyse d'éligibilité
  - `/subsidies/application` (POST) : Génération de dossier
- **DiagnosticAgent** : 
  - `/diagnostic/generate` (POST) : Génération de diagnostic
  - `/diagnostic/management-plan` (POST) : Plan de gestion
  - `/diagnostic/health-analysis` (POST) : Analyse sanitaire
  - `/diagnostic/report` (POST) : Génération de rapport

Documentation interactive disponible à l'adresse : `http://localhost:8000/docs`

## Dépannage

### Problèmes d'authentification
- Vérifiez que le fichier `.env` contient la valeur `JWT_SECRET`
- Assurez-vous que les appels API utilisent le bon format d'authentification (`Bearer TOKEN`)

### L'API ne démarre pas
- Vérifiez que toutes les dépendances sont installées : `pip install -r requirements.txt`
- Vérifiez que le port 8000 n'est pas déjà utilisé

### L'interface web ne se connecte pas à l'API
- Vérifiez les fichiers `.env` dans les répertoires `web/` et `webui/`
- Assurez-vous que l'API est bien démarrée et accessible
- Vérifiez les erreurs CORS dans la console du navigateur

## Développement

Pour contribuer au développement des interfaces web :

1. Les composants web dans `web/src/components` sont organisés par fonctionnalité
2. Les services API dans `web/src/services` gèrent les appels HTTP
3. Les stores dans `web/src/stores` gèrent l'état global de l'application

Même principe pour le répertoire `webui/` avec une organisation légèrement différente.

## Roadmap des interfaces

- [x] Structure de base des interfaces
- [x] Authentification JWT
- [x] Intégration avec l'API GeoAgent
- [ ] Intégration complète SubsidyAgent
- [ ] Visualisations avancées des diagnostics
- [ ] Interface de génération de rapports
- [ ] Mode hors ligne et synchronisation
