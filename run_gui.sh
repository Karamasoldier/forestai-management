#!/bin/bash
# =========================================================
# Script de démarrage de l'interface GUI ForestAI (Linux/Mac)
# =========================================================

echo "ForestAI - Interface de test des agents"
echo "======================================="
echo ""

# Vérification de l'existence de l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "Environnement virtuel non trouvé. Création..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "Erreur lors de la création de l'environnement virtuel."
        exit 1
    fi
    
    echo "Environnement virtuel créé avec succès."
fi

# Activation de l'environnement virtuel
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Erreur lors de l'activation de l'environnement virtuel."
    exit 1
fi

# Installation des dépendances si nécessaire
echo "Vérification des dépendances..."
python -c "import PyQt6" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Installation des dépendances PyQt6..."
    pip install -r requirements-gui.txt
    
    if [ $? -ne 0 ]; then
        echo "Erreur lors de l'installation des dépendances."
        exit 1
    fi
    
    echo "Dépendances installées avec succès."
fi

# Rendre le script exécutable
chmod +x run_gui.py

# Vérification des paramètres pour démarrer en mode API ou direct
if [ "$1" == "--direct" ]; then
    echo "Démarrage en mode direct (sans API REST)..."
    python run_gui.py --direct
elif [ -n "$1" ]; then
    echo "Démarrage avec l'URL d'API personnalisée: $1"
    python run_gui.py --api-url "$1"
else
    echo "Démarrage avec l'API REST par défaut (http://localhost:8000)..."
    python run_gui.py
fi

# Désactivation de l'environnement virtuel
deactivate
