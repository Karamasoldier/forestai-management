"""
Module serveur FastAPI pour l'API REST ForestAI.
Définit les routes et endpoints pour accéder aux fonctionnalités des agents ForestAI.
"""

import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import os
import json
from pydantic import BaseModel, Field

from forestai.core.utils.config import Config
from forestai.api.models import (
    ParcelSearchRequest, 
    ParcelAnalysisRequest,
    SubsidySearchRequest,
    EligibilityRequest,
    ApplicationRequest,
    ErrorResponse,
    SuccessResponse
)
from forestai.api.dependencies import get_geo_agent, get_subsidy_agent
from forestai.agents.geo_agent import GeoAgent
from forestai.agents.subsidy_agent import SubsidyAgent

# Configuration du logger
logger = logging.getLogger("forestai.api")

# Création de l'application FastAPI
app = FastAPI(
    title="ForestAI API",
    description="API REST pour accéder aux fonctionnalités de ForestAI",
    version="0.1.0",
)

# Configuration CORS pour permettre l'accès depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # A remplacer par les domaines spécifiques en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route de base
@app.get("/", tags=["General"])
async def root():
    """Endpoint racine de l'API ForestAI."""
    return {
        "name": "ForestAI API",
        "version": "0.1.0",
        "description": "API pour la gestion forestière intelligente"
    }

# Route de statut
@app.get("/status", tags=["General"])
async def status():
    """Vérifier le statut du système ForestAI."""
    try:
        return {
            "status": "operational",
            "agents": {
                "geo_agent": "available",
                "subsidy_agent": "available",
                "reglementation_agent": "planned"
            },
            "api_version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes pour GeoAgent
@app.post("/geo/search", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["GeoAgent"])
async def search_parcels(request: ParcelSearchRequest, geo_agent: GeoAgent = Depends(get_geo_agent)):
    """
    Rechercher des parcelles cadastrales.
    
    - **commune**: Nom ou code INSEE de la commune
    - **section**: Section cadastrale (optionnel)
    - **numero**: Numéro de parcelle (optionnel)
    """
    try:
        logger.info(f"Recherche de parcelles avec {request.dict()}")
        result = geo_agent.execute_action(
            "search_parcels", 
            {key: value for key, value in request.dict().items() if value is not None}
        )
        return {"status": "success", "result": result.get("result", {})}
    except Exception as e:
        logger.error(f"Error searching parcels: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/geo/analyze", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["GeoAgent"])
async def analyze_parcel(request: ParcelAnalysisRequest, geo_agent: GeoAgent = Depends(get_geo_agent)):
    """
    Analyser une parcelle pour son potentiel forestier.
    
    - **parcel_id**: Identifiant de la parcelle à analyser
    - **analyses**: Liste des analyses à effectuer (optionnel)
    """
    try:
        logger.info(f"Analyse de parcelle {request.parcel_id}")
        result = geo_agent.execute_action(
            "analyze_parcel", 
            {key: value for key, value in request.dict().items() if value is not None}
        )
        return {"status": "success", "result": result.get("result", {})}
    except Exception as e:
        logger.error(f"Error analyzing parcel: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Routes pour SubsidyAgent
@app.post("/subsidies/search", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["SubsidyAgent"])
async def search_subsidies(request: SubsidySearchRequest, subsidy_agent: SubsidyAgent = Depends(get_subsidy_agent)):
    """
    Rechercher des subventions disponibles pour un projet forestier.
    
    - **project_type**: Type de projet (reboisement, boisement, etc.)
    - **region**: Région concernée
    - **owner_type**: Type de propriétaire (private, public, etc.)
    - **parcel_id**: Identifiant de parcelle pour l'enrichissement des données (optionnel)
    """
    try:
        logger.info(f"Recherche de subventions avec {request.dict()}")
        result = subsidy_agent.execute_action(
            "search_subsidies", 
            {key: value for key, value in request.dict().items() if value is not None}
        )
        return {"status": "success", "result": result.get("result", [])}
    except Exception as e:
        logger.error(f"Error searching subsidies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subsidies/eligibility", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["SubsidyAgent"])
async def analyze_eligibility(request: EligibilityRequest, subsidy_agent: SubsidyAgent = Depends(get_subsidy_agent)):
    """
    Analyser l'éligibilité d'un projet à une subvention.
    
    - **project**: Données du projet forestier
    - **subsidy_id**: Identifiant de la subvention à analyser
    """
    try:
        logger.info(f"Analyse d'éligibilité pour {request.subsidy_id}")
        result = subsidy_agent.execute_action(
            "analyze_eligibility", 
            {
                "project": request.project.dict(),
                "subsidy_id": request.subsidy_id
            }
        )
        return {"status": "success", "result": result.get("result", {})}
    except Exception as e:
        logger.error(f"Error analyzing eligibility: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subsidies/application", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["SubsidyAgent"])
async def generate_application(request: ApplicationRequest, subsidy_agent: SubsidyAgent = Depends(get_subsidy_agent)):
    """
    Générer des documents de demande de subvention.
    
    - **project**: Données du projet forestier
    - **subsidy_id**: Identifiant de la subvention
    - **applicant**: Données du demandeur
    - **output_formats**: Formats de sortie souhaités
    """
    try:
        logger.info(f"Génération de demande pour {request.subsidy_id}")
        result = subsidy_agent.execute_action(
            "generate_application", 
            {
                "project": request.project.dict(),
                "subsidy_id": request.subsidy_id,
                "applicant": request.applicant.dict(),
                "output_formats": request.output_formats
            }
        )
        return {"status": "success", "result": result.get("result", {})}
    except Exception as e:
        logger.error(f"Error generating application: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Fonction pour démarrer le serveur directement
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Démarrer le serveur FastAPI.
    
    Args:
        host: Hôte d'écoute
        port: Port d'écoute
        reload: Activer le rechargement automatique
    """
    uvicorn.run("forestai.api.server:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    # Initialisation du config singleton
    config = Config.get_instance()
    config.load_config(env_file=".env")
    
    # Démarrer le serveur en mode développement
    run_server(reload=True)
