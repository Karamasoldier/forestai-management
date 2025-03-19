@echo off
REM Script pour démarrer l'interface web de ForestAI sur Windows

REM Vérifier si Python est installé
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python n'est pas installé ou n'est pas dans le PATH. Veuillez l'installer.
    exit /b 1
)

REM Vérifier si Node.js est installé
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Node.js n'est pas installé ou n'est pas dans le PATH. Veuillez l'installer.
    exit /b 1
)

REM Vérifier si l'environnement virtuel existe
if not exist venv (
    echo Création de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
call venv\Scripts\activate

REM Vérifier si les dépendances sont installées
if not exist venv\installed (
    echo Installation des dépendances...
    pip install -r requirements.txt
    echo. > venv\installed
)

REM Vérifier et créer les fichiers .env si nécessaire
if not exist .env (
    echo Création du fichier .env...
    copy .env.example .env
)

if not exist web\.env (
    echo Création du fichier web\.env...
    echo VITE_API_URL=http://localhost:8000 > web\.env
)

if not exist webui\.env (
    echo Création du fichier webui\.env...
    echo VUE_APP_API_URL=http://localhost:8000 > webui\.env
)

REM Créer les répertoires nécessaires s'ils n'existent pas
echo Vérification des répertoires de données...
if not exist data\raw\cadastre mkdir data\raw\cadastre
if not exist data\raw\bdtopo mkdir data\raw\bdtopo
if not exist data\raw\mnt mkdir data\raw\mnt
if not exist data\raw\occupation_sol mkdir data\raw\occupation_sol
if not exist data\raw\orthophotos mkdir data\raw\orthophotos
if not exist data\outputs mkdir data\outputs
if not exist data\processed mkdir data\processed
if not exist logs mkdir logs

REM Démarrer l'application
echo Démarrage de ForestAI...
python start_web.py %*
