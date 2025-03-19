@echo off
setlocal enabledelayedexpansion

REM Script batch amélioré pour démarrer l'API ForestAI sur Windows

REM Vérification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Erreur : Python n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Python et ajouter au PATH.
    pause
    exit /b 1
)

REM Création de l'environnement virtuel
if not exist venv (
    echo Création de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo Erreur lors de la création de l'environnement virtuel.
        pause
        exit /b 1
    )
)

REM Activation de l'environnement virtuel
call venv\Scripts\activate
if errorlevel 1 (
    echo Erreur lors de l'activation de l'environnement virtuel.
    pause
    exit /b 1
)

REM Mise à jour de pip et installation des dépendances
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Erreur lors de l'installation des dépendances.
    pause
    exit /b 1
)

REM Préparation des répertoires de données
if not exist data\raw mkdir data\raw
if not exist data\raw\cadastre mkdir data\raw\cadastre
if not exist data\raw\bdtopo mkdir data\raw\bdtopo
if not exist data\raw\mnt mkdir data\raw\mnt
if not exist data\raw\occupation_sol mkdir data\raw\occupation_sol
if not exist data\raw\orthophotos mkdir data\raw\orthophotos
if not exist data\outputs mkdir data\outputs
if not exist data\processed mkdir data\processed
if not exist logs mkdir logs

REM Vérification du fichier .env
if not exist .env (
    echo Copie du fichier .env.example en .env...
    copy .env.example .env
)

REM Démarrage de l'API avec gestion des erreurs
echo Démarrage de l'API ForestAI...
python api_server_run_directly.py
if errorlevel 1 (
    echo Erreur lors du démarrage de l'API.
    echo Vérifiez les logs et les dépendances.
    pause
    exit /b 1
)

pause
