# Interface Web ForestAI

Interface utilisateur web pour le projet ForestAI, permettant d'accéder aux fonctionnalités des différents agents via une interface graphique moderne.

## Fonctionnalités

- Authentification des utilisateurs
- Interface pour la recherche et l'analyse des parcelles cadastrales
- Visualisation des diagnostics forestiers
- Analyse des subventions disponibles
- Génération de rapports et documents

## Architecture

L'interface web ForestAI est construite selon une architecture modulaire pour faciliter la maintenance et les évolutions futures :

- **Vue.js** : Framework frontend progressif
- **Pinia** : Gestion d'état centralisée
- **Vue Router** : Routage côté client
- **Axios** : Client HTTP pour la communication avec l'API
- **Bootstrap 5** : Framework CSS pour l'interface utilisateur
- **Leaflet** : Bibliothèque pour la visualisation cartographique

## Organisation du code

Le code est organisé selon une structure claire et modulaire :

- `/src` - Code source de l'application
  - `/assets` - Ressources statiques (images, styles, etc.)
  - `/components` - Composants Vue.js réutilisables
    - `/common` - Composants communs (boutons, alertes, etc.)
    - `/dashboard` - Composants pour le tableau de bord
    - `/layout` - Composants de mise en page (navbar, footer, etc.)
    - `/parcels` - Composants liés aux parcelles
    - `/subsidies` - Composants liés aux subventions
    - `/diagnostics` - Composants liés aux diagnostics
    - `/reports` - Composants liés aux rapports
  - `/views` - Pages de l'application
  - `/services` - Services pour la communication avec l'API REST
  - `/stores` - Stores Pinia pour la gestion de l'état global
  - `/router` - Configuration du routeur Vue Router
  - `/utils` - Fonctions utilitaires

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

## Configuration

Le projet utilise un fichier `.env` pour la configuration :

```
VITE_API_URL=http://localhost:8000
```

## Utilisation avec l'API REST

L'interface web communique avec l'API REST ForestAI. Par défaut, elle se connecte à `http://localhost:8000`, qui correspond à l'API lancée en local avec `python api_server.py`.

Pour utiliser une autre instance de l'API, modifiez le fichier `.env`.

## Fonctionnement de l'authentification

L'authentification utilise le protocole OAuth2 avec JSON Web Tokens (JWT) :

1. L'utilisateur se connecte via le formulaire de login
2. Le token JWT est stocké dans le localStorage
3. Ce token est automatiquement ajouté à toutes les requêtes API
4. Un intercepteur Axios vérifie la validité du token et gère la déconnexion si nécessaire

## Déploiement

```bash
# Construction
npm run build

# Les fichiers sont générés dans le dossier 'dist'
# Copiez-les vers votre serveur web
cp -r dist/* /var/www/forestai/
```

Pour plus d'informations sur le déploiement, consultez la [documentation Vue.js](https://vuejs.org/guide/best-practices/production-deployment.html).
