# Guide d'installation de ForestAI

Ce guide vous accompagne pas à pas dans l'installation et la configuration de ForestAI, un système multi-agents pour l'automatisation et l'optimisation de la gestion forestière.

## Prérequis

Avant de commencer l'installation, assurez-vous que votre système dispose des éléments suivants :

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Accès à un terminal ou invite de commande
- Minimum 4 Go de RAM (8 Go recommandés pour les analyses spatiales complexes)
- Au moins 5 Go d'espace disque pour l'installation et les données

### Dépendances système

Certaines bibliothèques Python utilisées par ForestAI nécessitent des dépendances système spécifiques :

#### Linux (Debian/Ubuntu)
```bash
sudo apt-get update
sudo apt-get install -y \
    libgdal-dev \
    libspatialindex-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    wkhtmltopdf  # Pour la génération de PDF
```

#### macOS (avec Homebrew)
```bash
brew update
brew install gdal
brew install spatialindex
brew install wkhtmltopdf  # Pour la génération de PDF
```

#### Windows
Pour Windows, il est recommandé d'installer les dépendances via les packages binaires précompilés :

1. Téléchargez et installez GDAL depuis [GIS Internals](https://www.gisinternals.com/release.php)
2. Téléchargez et installez wkhtmltopdf depuis [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
3. Assurez-vous d'ajouter les répertoires d'installation aux variables d'environnement PATH

## Installation

Suivez ces étapes pour installer ForestAI :

### 1. Cloner le dépôt GitHub

```bash
git clone https://github.com/Karamasoldier/forestai-management.git
cd forestai-management
```

### 2. Créer un environnement virtuel

L'utilisation d'un environnement virtuel est fortement recommandée pour éviter les conflits de dépendances.

```bash
# Sous Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Sous Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Installer les dépendances Python

```bash
pip install --upgrade pip  # Mise à jour de pip
pip install -r requirements.txt
```

Si vous rencontrez des erreurs lors de l'installation des packages géospatiaux, essayez cette approche alternative (sous Linux/macOS) :

```bash
pip install wheel  # Utile pour les packages natifs
pip install -r requirements-minimal.txt  # Installe les dépendances de base
pip install GDAL==$(gdal-config --version)  # Installe GDAL correspondant à votre version système
pip install -r requirements-geo.txt  # Installe les dépendances géospatiales
```

### 4. Configuration

Pour configurer ForestAI, vous devez créer un fichier `.env` avec vos paramètres spécifiques. Un fichier modèle est fourni :

```bash
cp .env.example .env
```

Ouvrez le fichier `.env` dans un éditeur de texte et modifiez les valeurs selon votre environnement. Les paramètres clés à configurer sont :

```
# Chemins des répertoires
DATA_DIR=data                    # Répertoire de données
OUTPUT_DIR=outputs               # Répertoire de sortie

# Base de données
DB_ENGINE=sqlite                 # Options: sqlite, postgresql
DB_NAME=forestai.db              # Nom de la base de données
# Pour PostgreSQL uniquement
# DB_USER=postgres
# DB_PASSWORD=password
# DB_HOST=localhost
# DB_PORT=5432

# Options pour l'API
API_ACTIVE=false                 # true pour activer l'API web
API_HOST=127.0.0.1               # Hôte de l'API
API_PORT=8000                    # Port de l'API

# Clés d'API tierces (obtenir auprès des fournisseurs respectifs)
ANTHROPIC_API_KEY=               # Pour l'intégration Claude AI
IGN_API_KEY=                     # Pour les données géographiques IGN
GEOPORTAIL_API_KEY=              # Pour les services Géoportail
```

### 5. Structures des répertoires de données

ForestAI nécessite une structure de répertoires spécifique pour fonctionner correctement. Le script suivant crée ces répertoires automatiquement :

```bash
python -c 'from forestai.core.utils.setup import create_data_folders; create_data_folders()'
```

Ou manuellement :

```bash
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/cache
mkdir -p data/templates
mkdir -p outputs/reports
mkdir -p outputs/maps
mkdir -p outputs/documents
```

## Téléchargement des données géospatiales

ForestAI peut fonctionner avec différentes sources de données géospatiales. 

### Données BD TOPO (France)

1. Téléchargez les données BD TOPO depuis le [site de l'IGN](https://geoservices.ign.fr/bdtopo)
2. Extrayez les fichiers téléchargés dans le répertoire `data/raw/bdtopo`

Pour un téléchargement automatisé (nécessite une clé API IGN) :

```bash
python -m forestai.core.utils.data_downloaders.ign_downloader --dataset bdtopo --departments 13,83,84 --output_dir data/raw/bdtopo
```

### Données d'occupation des sols Corine Land Cover

1. Téléchargez les données CLC depuis le [site du Copernicus Land Monitoring Service](https://land.copernicus.eu/pan-european/corine-land-cover)
2. Extrayez les fichiers SHP dans le répertoire `data/raw/clc`

Pour un téléchargement automatisé :

```bash
python -m forestai.core.utils.data_downloaders.corine_downloader --year 2018 --output_dir data/raw/clc
```

### Modèle Numérique de Terrain (MNT)

1. Téléchargez les données du MNT depuis le [site de l'IGN](https://geoservices.ign.fr/bdalti)
2. Placez les fichiers dans `data/raw/mnt`

## Test de l'installation

Exécutez le script de test pour vérifier que tout fonctionne correctement :

```bash
python -m forestai.core.utils.installation_test
```

Ou essayez une requête simple pour tester l'installation :

```bash
python run.py --agent geoagent --action test_connection
```

Si tout fonctionne correctement, vous devriez voir un message indiquant que la connexion est établie.

## Exécution de ForestAI

Pour lancer le système complet :

```bash
python run.py
```

Pour utiliser un agent spécifique :

```bash
python run.py --agent geoagent
```

Pour exécuter une action spécifique avec des paramètres :

```bash
python run.py --agent subsidy --action search_subsidies --params '{"project_type": "reboisement", "region": "Occitanie"}'
```

## Configuration avancée

### Utilisation avec PostgreSQL/PostGIS

Si vous souhaitez utiliser PostgreSQL avec l'extension PostGIS pour de meilleures performances spatiales :

1. Installez PostgreSQL et PostGIS sur votre système
2. Créez une base de données avec l'extension PostGIS :

```sql
CREATE DATABASE forestai;
\c forestai
CREATE EXTENSION postgis;
```

3. Mettez à jour votre fichier `.env` avec les informations de connexion PostgreSQL :

```
DB_ENGINE=postgresql
DB_NAME=forestai
DB_USER=votre_utilisateur
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
```

### Utilisation de l'API REST

ForestAI peut être exposé via une API REST, ce qui permet une intégration avec d'autres systèmes :

1. Installez les dépendances supplémentaires :

```bash
pip install "fastapi[all]" uvicorn
```

2. Activez l'API dans le fichier `.env` :

```
API_ACTIVE=true
API_HOST=0.0.0.0  # Utilisez 0.0.0.0 pour rendre l'API accessible depuis d'autres machines
API_PORT=8000
```

3. Lancez l'API :

```bash
python -m forestai.api.main
```

L'API sera accessible à l'adresse `http://localhost:8000`. La documentation Swagger est disponible à l'adresse `http://localhost:8000/docs`.

## Dépannage

### Problèmes courants

#### 1. Erreurs d'installation de GDAL

```bash
# Solution Linux
sudo apt-get install python3-gdal

# Solution macOS
brew install gdal
export CPLUS_INCLUDE_PATH=/usr/local/include
export C_INCLUDE_PATH=/usr/local/include
pip install GDAL==$(gdal-config --version)
```

#### 2. Erreur "No module named 'forestai'"

Assurez-vous que vous êtes dans le répertoire racine du projet et que l'environnement virtuel est activé.

#### 3. Erreurs lors de l'exécution de l'API

Si vous rencontrez des erreurs lors du lancement de l'API, vérifiez que toutes les dépendances sont installées :

```bash
pip install "fastapi[all]" uvicorn pydantic
```

#### 4. Problèmes avec la génération de PDF

Vérifiez que wkhtmltopdf est correctement installé et accessible dans votre PATH :

```bash
wkhtmltopdf --version
```

### Obtenir de l'aide

Si vous rencontrez des problèmes non résolus par ce guide :

1. Consultez les [issues GitHub](https://github.com/Karamasoldier/forestai-management/issues) pour voir si votre problème a déjà été signalé
2. Vérifiez les logs dans le répertoire `logs/`
3. Créez une nouvelle issue en fournissant des détails sur votre environnement et l'erreur rencontrée

## Ressources supplémentaires

- [Documentation des agents](AGENTS.md)
- [Architecture du système](ARCHITECTURE.md)
- [Services et modules](SERVICES.md)
- [Exemples d'utilisation](EXAMPLES.md)
