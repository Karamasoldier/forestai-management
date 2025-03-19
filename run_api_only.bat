@echo off
REM Script batch pour démarrer uniquement l'API ForestAI sur Windows

echo Activation de l'environnement virtuel Python...
if not exist venv\Scripts\activate.bat (
    echo Création de l'environnement virtuel...
    python -m venv venv
)

call venv\Scripts\activate.bat

REM Vérification des dépendances
if not exist venv\installed (
    echo Installation des dépendances...
    pip install -r requirements.txt
    echo. > venv\installed
)

REM Vérification du fichier .env
if not exist .env (
    echo Création du fichier .env...
    copy .env.example .env
)

REM Création des répertoires nécessaires
echo Vérification des répertoires de données...
if not exist data\raw\cadastre mkdir data\raw\cadastre
if not exist data\raw\bdtopo mkdir data\raw\bdtopo
if not exist data\raw\mnt mkdir data\raw\mnt
if not exist data\raw\occupation_sol mkdir data\raw\occupation_sol
if not exist data\raw\orthophotos mkdir data\raw\orthophotos
if not exist data\outputs mkdir data\outputs
if not exist data\processed mkdir data\processed
if not exist logs mkdir logs

REM Démarrage de l'API uniquement
echo Démarrage de l'API ForestAI...
python api_server_run_directly.py
