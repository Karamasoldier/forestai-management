# Interface Web ForestAI

Interface utilisateur web pour le projet ForestAI, permettant d'accéder aux fonctionnalités des différents agents via une interface graphique moderne.

## Fonctionnalités

- Authentification des utilisateurs
- Interface pour la recherche et l'analyse des parcelles cadastrales
- Visualisation des diagnostics forestiers
- Analyse des subventions disponibles
- Génération de rapports et documents

## Technologies utilisées

- HTML5, CSS3, JavaScript
- Vue.js pour l'interface utilisateur
- Axios pour les requêtes API
- Leaflet pour la visualisation cartographique

## Installation

```bash
# Installation des dépendances
cd web
npm install

# Lancement du serveur de développement
npm run dev

# Construction pour la production
npm run build
```

## Structure du projet

- `/src` - Code source de l'application
  - `/assets` - Ressources statiques (images, styles, etc.)
  - `/components` - Composants Vue.js réutilisables
  - `/views` - Pages de l'application
  - `/services` - Services pour la communication avec l'API REST
  - `/store` - Store Vuex pour la gestion de l'état global
  - `/router` - Configuration du routeur Vue Router
- `/public` - Fichiers statiques accessibles publiquement

## Configuration

Le projet utilise un fichier `.env` pour la configuration :

```
VUE_APP_API_URL=http://localhost:8000
```

## Utilisation avec l'API REST

L'interface web est conçue pour communiquer avec l'API REST ForestAI. Par défaut, elle essaie de se connecter à `http://localhost:8000`, qui correspond à l'API lancée en local avec `python api_server.py`.

Pour utiliser une autre instance de l'API, modifiez le fichier `.env`.
