@echo off
setlocal enabledelayedexpansion
title ForestAI Docker

echo ForestAI - Déploiement Docker
echo ==============================
echo.

:: Vérifier si Docker est installé
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Docker n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Docker Desktop depuis https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [1/3] Vérification de Docker...
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Docker n'est pas démarré ou n'a pas les permissions requises.
    echo Veuillez démarrer Docker Desktop et réessayer.
    pause
    exit /b 1
)

echo [2/3] Création et démarrage des conteneurs...
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo [ERREUR] Une erreur s'est produite lors du démarrage des conteneurs.
    pause
    exit /b 1
)

echo [3/3] ForestAI est maintenant accessible à l'adresse:
echo.
echo     http://localhost:8000/docs    (API Documentation)
echo.
echo Pour arrêter les conteneurs, utilisez: docker-compose down
echo Pour voir les logs, utilisez: docker-compose logs -f
echo.
echo Appuyez sur une touche pour ouvrir la documentation dans votre navigateur...
pause > nul

start "" http://localhost:8000/docs

endlocal
