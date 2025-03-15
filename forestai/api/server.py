"""
Module serveur FastAPI pour l'API REST ForestAI.
Définit les routes et endpoints pour accéder aux fonctionnalités des agents ForestAI.
"""

import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from typing import Dict, Any, List, Optional
import os
import json
from pathlib import Path
from io import BytesIO
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

# Routes pour DiagnosticAgent
@app.post("/diagnostic/generate", 
          response_model=SuccessResponse, 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
          tags=["DiagnosticAgent"])
async def generate_diagnostic(request: DiagnosticRequest, diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent)):
    """
    Générer un diagnostic forestier pour une parcelle.
    
    - **parcel_id**: Identifiant de la parcelle
    - **inventory_data**: Données d'inventaire forestier (optionnel)
    - **include_health_analysis**: Inclure l'analyse sanitaire
    """
    try:
        logger.info(f"Génération d'un diagnostic pour la parcelle {request.parcel_id}")
        
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
async def generate_management_plan(request: ManagementPlanRequest, diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent)):
    """
    Générer un plan de gestion forestière.
    
    - **parcel_id**: Identifiant de la parcelle
    - **goals**: Objectifs de gestion (production, biodiversité, resilience, etc.)
    - **horizon_years**: Horizon temporel du plan en années
    - **use_existing_diagnostic**: Utiliser un diagnostic existant
    """
    try:
        logger.info(f"Génération d'un plan de gestion pour la parcelle {request.parcel_id}")
        
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
async def analyze_health(request: HealthAnalysisRequest, diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent)):
    """
    Effectuer une analyse sanitaire forestière.
    
    - **inventory_data**: Données d'inventaire forestier
    - **additional_symptoms**: Observations supplémentaires de symptômes (optionnel)
    - **climate_data**: Données climatiques pour l'analyse de risques (optionnel)
    - **parcel_id**: Identifiant de parcelle pour enrichissement des données (optionnel)
    """
    try:
        logger.info("Analyse sanitaire forestière")
        
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
async def generate_report(request: ReportRequest, diagnostic_agent: DiagnosticAgent = Depends(get_diagnostic_agent)):
    """
    Générer un rapport forestier au format demandé.
    
    - **report_type**: Type de rapport (diagnostic, management_plan, health)
    - **data_id**: Identifiant des données (parcelle, diagnostic, etc.)
    - **format**: Format du rapport (pdf, html, txt)
    - **health_detail_level**: Niveau de détail sanitaire (minimal, standard, complete)
    """
    try:
        logger.info(f"Génération d'un rapport {request.report_type} pour {request.data_id}")
        
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
