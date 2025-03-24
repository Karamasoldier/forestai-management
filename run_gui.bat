@echo off
REM =========================================================
REM Script de démarrage de l'interface GUI ForestAI (Windows)
REM =========================================================

echo ForestAI - Interface de test des agents
echo =======================================
echo.

REM Vérification de l'existence de l'environnement virtuel
IF NOT EXIST venv (
    echo Environnement virtuel non trouvé. Création...
    python -m venv venv
    
    IF %ERRORLEVEL% NEQ 0 (
        echo Erreur lors de la création de l'environnement virtuel.
        pause
        exit /b 1
    )
    
    echo Environnement virtuel créé avec succès.
)

REM Activation de l'environnement virtuel
call venv\Scripts\activate

IF %ERRORLEVEL% NEQ 0 (
    echo Erreur lors de l'activation de l'environnement virtuel.
    pause
    exit /b 1
)

REM Installation des dépendances si nécessaire
echo Vérification des dépendances...
python -c "import PyQt6" 2>nul

IF %ERRORLEVEL% NEQ 0 (
    echo Installation des dépendances PyQt6...
    pip install -r requirements-gui.txt
    
    IF %ERRORLEVEL% NEQ 0 (
        echo Erreur lors de l'installation des dépendances.
        pause
        exit /b 1
    )
    
    echo Dépendances installées avec succès.
)

REM Vérification des paramètres pour démarrer en mode API ou direct
IF "%1"=="--direct" (
    echo Démarrage en mode direct (sans API REST)...
    python run_gui.py --direct
) ELSE IF NOT "%1"=="" (
    echo Démarrage avec l'URL d'API personnalisée: %1
    python run_gui.py --api-url %1
) ELSE (
    echo Démarrage avec l'API REST par défaut (http://localhost:8000)...
    python run_gui.py
)

REM Désactivation de l'environnement virtuel
call venv\Scripts\deactivate

pause
