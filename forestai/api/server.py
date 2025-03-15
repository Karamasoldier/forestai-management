"""
Module serveur FastAPI pour l'API REST ForestAI.
Définit les routes et endpoints pour accéder aux fonctionnalités des agents ForestAI.
"""

import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, List, Optional
import os
import json
from pathlib import Path
from io import BytesIO
from datetime import timedelta
from pydantic import BaseModel, Field

from forestai.core.utils.config import Config
from forestai.api.models import (
    ParcelSearchRequest, 
    ParcelAnalysisRequest,
    SubsidySearchRequest,
    EligibilityRequest,
    ApplicationRequest,
    DiagnosticRequest,
    ManagementPlanRequest,
    HealthAnalysisRequest,
    ReportRequest,
    ErrorResponse,
    SuccessResponse
)
from forestai.api.dependencies import get_geo_agent, get_subsidy_agent, get_diagnostic_agent
from forestai.api.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user, 
    User,
    TokenResponse,
    JWT_EXPIRATION_MINUTES,
    geo_read, 
    geo_write,
    subsidy_read,
    subsidy_write,
    diagnostic_read,
    diagnostic_write,
    regulation_read,
    admin_only
)
from forestai.agents.geo_agent import GeoAgent
from forestai.agents.subsidy_agent import SubsidyAgent
from forestai.agents.diagnostic_agent import DiagnosticAgent
from forestai.agents.diagnostic_agent.health.health_analyzer import HealthAnalyzer
from forestai.agents.diagnostic_agent.report_generator import ReportGenerator

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

# Routes d'authentification
@app.post("/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Obtenir un jeton d'accès pour l'API ForestAI.
    
    Utilise le flux OAuth2 standard avec vos identifiants.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Tentative d'authentification échouée pour {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer les données de jeton
    token_data = {
        "sub": user.username,
        "scope": user.scopes,
        "name": user.full_name,
        "admin": user.admin
    }
    
    # Créer le jeton
    access_token_expires = timedelta(minutes=JWT_EXPIRATION_MINUTES)
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    
    logger.info(f"Jeton d'accès généré pour {user.username}")
    
    # Préparer les informations utilisateur
    user_info = {
        "username": user.username,
        "scopes": user.scopes,
        "full_name": user.full_name,
        "is_admin": user.admin
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_MINUTES * 60,
        "user_info": user_info
    }

@app.get("/auth/me", response_model=User, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Récupérer les informations sur l'utilisateur authentifié.
    
    Cet endpoint nécessite un jeton d'authentification valide.
    """
    return current_user

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
                "diagnostic_agent": "available",
                "reglementation_agent": "planned"
            },
            "api_version": "0.1.0",
            "authentication": "enabled"
        }
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes pour GeoAgent
@app.post("/geo/search", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["GeoAgent"])
async def search_parcels(
    request: ParcelSearchRequest, 
    geo_agent: GeoAgent = Depends(get_geo_agent),
    current_user: User = Depends(geo_read)
):
    """
    Rechercher des parcelles cadastrales.
    
    - **commune**: Nom ou code INSEE de la commune
    - **section**: Section cadastrale (optionnel)
    - **numero**: Numéro de parcelle (optionnel)
    """
    try:
        logger.info(f"Recherche de parcelles avec {request.dict()} par {current_user.username}")
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
async def analyze_parcel(
    request: ParcelAnalysisRequest, 
    geo_agent: GeoAgent = Depends(get_geo_agent),
    current_user: User = Depends(geo_read)
):
    """
    Analyser une parcelle pour son potentiel forestier.
    
    - **parcel_id**: Identifiant de la parcelle à analyser
    - **analyses**: Liste des analyses à effectuer (optionnel)
    """
    try:
        logger.info(f"Analyse de parcelle {request.parcel_id} par {current_user.username}")
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
async def search_subsidies(
    request: SubsidySearchRequest, 
    subsidy_agent: SubsidyAgent = Depends(get_subsidy_agent),
    current_user: User = Depends(subsidy_read)
):
    """
    Rechercher des subventions disponibles pour un projet forestier.
    
    - **project_type**: Type de projet (reboisement, boisement, etc.)
    - **region**: Région concernée
    - **owner_type**: Type de propriétaire (private, public, etc.)
    - **parcel_id**: Identifiant de parcelle pour l'enrichissement des données (optionnel)
    """
    try:
        logger.info(f"Recherche de subventions avec {request.dict()} par {current_user.username}")
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
async def analyze_eligibility(
    request: EligibilityRequest, 
    subsidy_agent: SubsidyAgent = Depends(get_subsidy_agent),
    current_user: User = Depends(subsidy_read)
):
    """
    Analyser l'éligibilité d'un projet à une subvention.
    
    - **project**: Données du projet forestier
    - **subsidy_id**: Identifiant de la subvention à analyser
    """
    try:
        logger.info(f"Analyse d'éligibilité pour {request.subsidy_id} par {current_user.username}")
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
async def generate_application(
    request: ApplicationRequest, 
    subsidy_agent: SubsidyAgent = Depends(get_subsidy_agent),
    current_user: User = Depends(subsidy_write)
):
    """
    Générer des documents de demande de subvention.
    
    - **project**: Données du projet forestier
    - **subsidy_id**: Identifiant de la subvention
    - **applicant**: Données du demandeur
    - **output_formats**: Formats de sortie souhaités
    """
    try:
        logger.info(f"Génération de demande pour {request.subsidy_id} par {current_user.username}")
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

# Routes pour DiagnosticAgent
@app.post("/diagnostic/generate", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["DiagnosticAgent"])
async def generate_diagnostic(
    request: DiagnosticRequest, 
    diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent),
    current_user: User = Depends(diagnostic_read)
):
    """
    Générer un diagnostic forestier pour une parcelle.
    
    - **parcel_id**: Identifiant de la parcelle
    - **inventory_data**: Données d'inventaire forestier (optionnel)
    - **include_health_analysis**: Inclure l'analyse sanitaire
    """
    try:
        logger.info(f"Génération d'un diagnostic pour la parcelle {request.parcel_id} par {current_user.username}")
        
        # Préparer les paramètres pour le diagnostic
        params = {
            "parcel_id": request.parcel_id,
            "include_health_analysis": request.include_health_analysis
        }
        
        # Ajouter les données d'inventaire si présentes
        if request.inventory_data:
            params["inventory_data"] = request.inventory_data.dict()
        
        # Exécuter l'action
        result = diagnostic_agent.execute_action("generate_diagnostic", params)
        
        return {"status": "success", "result": result.get("result", {})}
    except Exception as e:
        logger.error(f"Error generating diagnostic: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diagnostic/management-plan", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["DiagnosticAgent"])
async def generate_management_plan(
    request: ManagementPlanRequest, 
    diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent),
    current_user: User = Depends(diagnostic_write)
):
    """
    Générer un plan de gestion forestière.
    
    - **parcel_id**: Identifiant de la parcelle
    - **goals**: Objectifs de gestion (production, biodiversité, resilience, etc.)
    - **horizon_years**: Horizon temporel du plan en années
    - **use_existing_diagnostic**: Utiliser un diagnostic existant
    """
    try:
        logger.info(f"Génération d'un plan de gestion pour la parcelle {request.parcel_id} par {current_user.username}")
        
        # Préparer les paramètres
        params = {
            "parcel_id": request.parcel_id,
            "goals": request.goals,
            "horizon_years": request.horizon_years,
            "use_existing_diagnostic": request.use_existing_diagnostic
        }
        
        # Exécuter l'action
        result = diagnostic_agent.execute_action("generate_management_plan", params)
        
        return {"status": "success", "result": result.get("result", {})}
    except Exception as e:
        logger.error(f"Error generating management plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diagnostic/health-analysis", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["DiagnosticAgent"])
async def analyze_health(
    request: HealthAnalysisRequest, 
    diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent),
    current_user: User = Depends(diagnostic_read)
):
    """
    Effectuer une analyse sanitaire forestière.
    
    - **inventory_data**: Données d'inventaire forestier
    - **additional_symptoms**: Observations supplémentaires de symptômes (optionnel)
    - **climate_data**: Données climatiques pour l'analyse de risques (optionnel)
    - **parcel_id**: Identifiant de parcelle pour enrichissement des données (optionnel)
    """
    try:
        logger.info(f"Analyse sanitaire forestière par {current_user.username}")
        
        # Instancier le HealthAnalyzer
        health_analyzer = HealthAnalyzer()
        
        # Préparer les paramètres pour l'analyse
        inventory_data = request.inventory_data.dict()
        additional_symptoms = request.additional_symptoms
        climate_data = request.climate_data
        
        # Enrichir avec les données de parcelle si disponible
        if request.parcel_id:
            logger.info(f"Enrichissement avec les données de la parcelle {request.parcel_id}")
            # Obtenir les données climatiques de la parcelle
            if not climate_data:
                parcel_info = diagnostic_agent.forest_potential_service.get_parcel_info(request.parcel_id)
                if parcel_info and "geometry" in parcel_info:
                    climate_data = diagnostic_agent.climate_analyzer.analyze_climate(parcel_info["geometry"])
        
        # Effectuer l'analyse sanitaire
        health_analysis = health_analyzer.analyze_health(
            inventory_data=inventory_data,
            additional_symptoms=additional_symptoms,
            climate_data=climate_data
        )
        
        return {"status": "success", "result": health_analysis}
    except Exception as e:
        logger.error(f"Error analyzing forest health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diagnostic/report", 
          responses={
              200: {"content": {"application/pdf": {}, "text/html": {}, "text/plain": {}}},
              400: {"model": ErrorResponse}, 
              500: {"model": ErrorResponse}
          },
          tags=["DiagnosticAgent"])
async def generate_report(
    request: ReportRequest, 
    diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent),
    current_user: User = Depends(diagnostic_read)
):
    """
    Générer un rapport forestier au format demandé.
    
    - **report_type**: Type de rapport (diagnostic, management_plan, health)
    - **data_id**: Identifiant des données (parcelle, diagnostic, etc.)
    - **format**: Format du rapport (pdf, html, txt)
    - **health_detail_level**: Niveau de détail sanitaire (minimal, standard, complete)
    """
    try:
        logger.info(f"Génération d'un rapport {request.report_type} pour {request.data_id} par {current_user.username}")
        
        # Initialiser le générateur de rapports
        report_generator = ReportGenerator()
        
        # Récupérer les données appropriées selon le type de rapport
        data = None
        parcel_data = None
        
        if request.report_type == "diagnostic":
            # Générer ou récupérer un diagnostic
            params = {"parcel_id": request.data_id}
            result = diagnostic_agent.execute_action("generate_diagnostic", params)
            data = result.get("result", {})
            
        elif request.report_type == "management_plan":
            # Générer ou récupérer un plan de gestion
            params = {"parcel_id": request.data_id, "goals": ["production", "resilience"]}
            result = diagnostic_agent.execute_action("generate_management_plan", params)
            data = result.get("result", {})
            
            # Si un diagnostic existe, l'ajouter comme contexte
            diagnostic_result = diagnostic_agent.execute_action(
                "generate_diagnostic", {"parcel_id": request.data_id}
            )
            parcel_data = diagnostic_result.get("result", {})
            
        elif request.report_type == "health":
            # Utiliser l'analyse sanitaire fournie ou la générer
            # Pour simplifier, nous supposons que l'analyse est déjà disponible
            # et que data_id est l'identifiant de parcelle
            health_analyzer = HealthAnalyzer()
            inventory_data = {"items": []} # Données fictives, à remplacer par des données réelles
            data = health_analyzer.analyze_health(inventory_data)
        
        if not data:
            raise ValueError(f"Impossible de récupérer les données pour le rapport {request.report_type}")
        
        # Générer le rapport dans le format demandé
        report_content = None
        media_type = "application/pdf"
        
        if request.format == "pdf":
            if request.report_type == "diagnostic":
                report_content = report_generator.generate_diagnostic_report_pdf(data, parcel_data)
            elif request.report_type == "management_plan":
                report_content = report_generator.generate_management_plan_report_pdf(data, parcel_data)
            elif request.report_type == "health":
                # Le générateur de rapports sanitaires utilisera le niveau de détail
                health_detail_level = request.health_detail_level or "standard"
                report_content = report_generator.generate_diagnostic_report_pdf(
                    data, 
                    parcel_data,
                    options={"health_detail_level": health_detail_level}
                )
        
        elif request.format == "html":
            media_type = "text/html"
            if request.report_type == "diagnostic":
                report_content = report_generator.generate_diagnostic_report_html(data, parcel_data)
            elif request.report_type == "management_plan":
                report_content = report_generator.generate_management_plan_report_html(data, parcel_data)
            elif request.report_type == "health":
                health_detail_level = request.health_detail_level or "standard"
                report_content = report_generator.generate_diagnostic_report_html(
                    data, 
                    parcel_data,
                    options={"health_detail_level": health_detail_level}
                )
        
        elif request.format == "txt":
            media_type = "text/plain"
            # Implémentation de la génération de rapport TXT
            # ...
        
        if not report_content:
            raise ValueError(f"Format de rapport non pris en charge: {request.format}")
        
        # Retourner le rapport comme fichier
        if isinstance(report_content, bytes):
            # PDF
            return Response(
                content=report_content,
                media_type=media_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{request.report_type}_{request.data_id}.{request.format}"'
                }
            )
        else:
            # HTML ou TXT
            return Response(
                content=report_content,
                media_type=media_type
            )
            
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Route d'administration (accessible uniquement aux administrateurs)
@app.get("/admin/stats", tags=["Admin"])
async def get_system_stats(current_user: User = Depends(admin_only)):
    """
    Obtenir des statistiques sur l'utilisation du système.
    
    Cet endpoint est réservé aux administrateurs.
    """
    try:
        logger.info(f"Récupération des statistiques du système par l'administrateur {current_user.username}")
        # Ici, on pourrait récupérer des statistiques sur l'utilisation de l'API, les requêtes, etc.
        stats = {
            "api_requests_total": 12345,
            "api_requests_today": 123,
            "users_active": 5,
            "average_response_time_ms": 450,
            "agents_usage": {
                "geo_agent": 4500,
                "subsidy_agent": 3200,
                "diagnostic_agent": 4100,
                "health_analyzer": 2800
            },
            "last_updated": "2025-03-15T17:00:00Z"
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}", exc_info=True)
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
