# ForestAI Interface Utilisateur Web

Interface utilisateur web pour le système ForestAI de gestion forestière intelligente.

## Fonctionnalités

- Tableau de bord interactif
- Gestion des parcelles forestières
- Recherche et analyse de subventions
- Gestion des diagnostics
- Génération de rapports
- Visualisation géospatiale

## Architecture

L'interface est construite avec Vue.js 3 et utilise l'API REST de ForestAI pour communiquer avec le backend.

## Structure du projet

```
webui/
├── public/            # Ressources statiques
├── src/               # Code source
│   ├── assets/        # Images, styles, etc.
│   ├── components/    # Composants réutilisables
│   ├── layouts/       # Mises en page de l'application
│   ├── modules/       # Modules fonctionnels (parcelles, diagnostics, etc.)
│   ├── router/        # Configuration des routes
│   ├── services/      # Services d'API, utilitaires
│   ├── store/         # Gestion d'état (Vuex)
│   ├── views/         # Pages de l'application
│   ├── App.vue        # Composant racine
│   └── main.js        # Point d'entrée
├── .env.example       # Configuration d'environnement
├── package.json       # Dépendances
└── README.md          # Documentation
```

## Installation et démarrage

```bash
# Installation des dépendances
npm install

# Démarrage du serveur de développement
npm run serve

# Construction pour la production
npm run build
```

## Dépendances principales

- Vue 3
- Vue Router
- Vuex
- Axios
- Leaflet (cartographie)
- Chart.js (visualisations)
- PrimeVue (composants UI)
- SASS (styles)
