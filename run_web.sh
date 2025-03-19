#!/bin/bash
# Script pour démarrer l'interface web de ForestAI

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Vérifier si Node.js est installé
if ! command -v node &> /dev/null; then
    echo "Node.js n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier si les dépendances sont installées
if [ ! -f "venv/installed" ]; then
    echo "Installation des dépendances..."
    pip install -r requirements.txt
    touch venv/installed
fi

# Vérifier et créer les fichiers .env si nécessaire
if [ ! -f ".env" ]; then
    echo "Création du fichier .env..."
    cp .env.example .env
fi

if [ ! -f "web/.env" ]; then
    echo "Création du fichier web/.env..."
    echo "VITE_API_URL=http://localhost:8000" > web/.env
fi

if [ ! -f "webui/.env" ]; then
    echo "Création du fichier webui/.env..."
    echo "VUE_APP_API_URL=http://localhost:8000" > webui/.env
fi

# Créer les répertoires nécessaires s'ils n'existent pas
echo "Vérification des répertoires de données..."
mkdir -p data/raw/cadastre data/raw/bdtopo data/raw/mnt data/raw/occupation_sol data/raw/orthophotos
mkdir -p data/outputs data/processed
mkdir -p logs

# Démarrer l'application
echo "Démarrage de ForestAI..."
python start_web.py "$@"
