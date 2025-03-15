#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests d'intégration pour l'API Diagnostic et HealthAnalyzer.

Ces tests vérifient que l'API REST expose correctement les fonctionnalités
du DiagnosticAgent et du HealthAnalyzer.
"""

import os
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

from forestai.api.server import app

# Client de test pour l'API
client = TestClient(app)

# Exemple de données d'inventaire pour les tests
SAMPLE_INVENTORY_DATA = {
    "items": [
        {
            "species": "quercus_ilex",
            "diameter": 25.5,
            "height": 12.0,
            "health_status": "moyen",
            "notes": "Présence de taches foliaires"
        },
        {
            "species": "pinus_pinea",
            "diameter": 35.0,
            "height": 18.5,
            "health_status": "bon"
        }
    ],
    "area": 1.5,
    "date": "2025-03-01",
    "method": "placettes"
}


# Exemple de symptômes supplémentaires
SAMPLE_ADDITIONAL_SYMPTOMS = {
    "leaf_discoloration": 0.35,
    "observed_pests": ["bark_beetle"],
    "crown_thinning": 0.25
}


class TestDiagnosticAPI:
    """Tests de l'API Diagnostic."""

    def test_api_status(self):
        """Vérifier que l'API est opérationnelle et que le DiagnosticAgent est disponible."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "diagnostic_agent" in data["agents"]
        assert data["agents"]["diagnostic_agent"] == "available"

    @patch("forestai.agents.diagnostic_agent.DiagnosticAgent.execute_action")
    def test_generate_diagnostic(self, mock_execute_action):
        """Tester la génération d'un diagnostic forestier."""
        # Mock de la réponse de l'agent
        mock_execute_action.return_value = {
            "status": "success",
            "result": {
                "parcel_id": "13097000B0012",
                "parcel_data": {
                    "area_ha": 15.234,
                    "commune": "Saint-Martin-de-Crau",
                },
                "potential": {
                    "score": 78,
                    "recommended_species": ["pinus_pinea", "quercus_ilex"]
                },
                "timestamp": "2025-03-15T16:30:45.123Z"
            }
        }

        # Requête à l'API
        response = client.post(
            "/diagnostic/generate",
            json={
                "parcel_id": "13097000B0012",
                "inventory_data": SAMPLE_INVENTORY_DATA,
                "include_health_analysis": True
            }
        )

        # Vérifications
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["parcel_id"] == "13097000B0012"
        assert "potential" in data["result"]
        assert "recommended_species" in data["result"]["potential"]

        # Vérifier que l'action a été appelée avec les bons paramètres
        mock_execute_action.assert_called_once()
        args, kwargs = mock_execute_action.call_args
        assert args[0] == "generate_diagnostic"
        assert args[1]["parcel_id"] == "13097000B0012"
        assert args[1]["include_health_analysis"] is True
        assert "inventory_data" in args[1]

    @patch("forestai.agents.diagnostic_agent.DiagnosticAgent.execute_action")
    def test_generate_management_plan(self, mock_execute_action):
        """Tester la génération d'un plan de gestion forestière."""
        # Mock de la réponse de l'agent
        mock_execute_action.return_value = {
            "status": "success",
            "result": {
                "parcel_id": "13097000B0012",
                "created_at": "2025-03-15T16:35:12.654Z",
                "horizon": {
                    "start_year": 2025,
                    "end_year": 2040,
                    "duration_years": 15
                },
                "goals": ["production", "resilience"],
                "phases": [
                    {
                        "name": "Diagnostic et préparation",
                        "year": 2025,
                        "actions": ["Analyse complète du terrain"]
                    }
                ]
            }
        }

        # Requête à l'API
        response = client.post(
            "/diagnostic/management-plan",
            json={
                "parcel_id": "13097000B0012",
                "goals": ["production", "resilience"],
                "horizon_years": 15,
                "use_existing_diagnostic": True
            }
        )

        # Vérifications
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["parcel_id"] == "13097000B0012"
        assert data["result"]["goals"] == ["production", "resilience"]
        assert data["result"]["horizon"]["duration_years"] == 15
        assert len(data["result"]["phases"]) > 0

        # Vérifier que l'action a été appelée avec les bons paramètres
        mock_execute_action.assert_called_once()
        args, kwargs = mock_execute_action.call_args
        assert args[0] == "generate_management_plan"
        assert args[1]["parcel_id"] == "13097000B0012"
        assert args[1]["goals"] == ["production", "resilience"]

    @patch("forestai.agents.diagnostic_agent.health.health_analyzer.HealthAnalyzer.analyze_health")
    def test_health_analysis(self, mock_analyze_health):
        """Tester l'analyse sanitaire forestière."""
        # Mock de la réponse de l'analyseur
        mock_analyze_health.return_value = {
            "summary": "État sanitaire moyen nécessitant une vigilance particulière.",
            "overall_health_score": 5.8,
            "health_status": "Moyen",
            "detected_issues": [
                {
                    "id": "leaf_discoloration",
                    "name": "Décoloration foliaire",
                    "type": "physiological",
                    "severity": 0.35,
                    "confidence": 0.9
                }
            ],
            "recommendations": {
                "summary": "Surveillance sanitaire recommandée.",
                "priority_actions": [
                    {
                        "action": "Mise en place d'un système de surveillance sanitaire",
                        "deadline": "Dans les 60 jours"
                    }
                ]
            }
        }

        # Requête à l'API
        response = client.post(
            "/diagnostic/health-analysis",
            json={
                "inventory_data": SAMPLE_INVENTORY_DATA,
                "additional_symptoms": SAMPLE_ADDITIONAL_SYMPTOMS,
                "parcel_id": "13097000B0012"
            }
        )

        # Vérifications
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "overall_health_score" in data["result"]
        assert "detected_issues" in data["result"]
        assert "recommendations" in data["result"]

        # Vérifier que la méthode a été appelée avec les bons paramètres
        mock_analyze_health.assert_called_once()
        args, kwargs = mock_analyze_health.call_args
        assert "inventory_data" in kwargs
        assert "additional_symptoms" in kwargs
        assert kwargs["additional_symptoms"] == SAMPLE_ADDITIONAL_SYMPTOMS

    @patch("forestai.agents.diagnostic_agent.report_generator.ReportGenerator.generate_diagnostic_report_pdf")
    def test_generate_report_pdf(self, mock_generate_pdf):
        """Tester la génération d'un rapport au format PDF."""
        # Mock de la réponse du générateur de rapport
        pdf_content = b"%PDF-1.5\nSample PDF content"
        mock_generate_pdf.return_value = pdf_content

        # Requête à l'API avec mock pour le DiagnosticAgent
        with patch("forestai.agents.diagnostic_agent.DiagnosticAgent.execute_action") as mock_execute_action:
            mock_execute_action.return_value = {
                "status": "success",
                "result": {
                    "parcel_id": "13097000B0012",
                    "parcel_data": {"area_ha": 15.234}
                }
            }
            
            response = client.post(
                "/diagnostic/report",
                json={
                    "report_type": "diagnostic",
                    "data_id": "13097000B0012",
                    "format": "pdf"
                }
            )

        # Vérifications
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert b"%PDF" in response.content
        
        # Vérifier que la méthode a été appelée
        mock_generate_pdf.assert_called_once()

    @patch("forestai.agents.diagnostic_agent.report_generator.ReportGenerator.generate_diagnostic_report_html")
    def test_generate_report_html(self, mock_generate_html):
        """Tester la génération d'un rapport au format HTML."""
        # Mock de la réponse du générateur de rapport
        html_content = "<html><body><h1>Rapport de diagnostic forestier</h1></body></html>"
        mock_generate_html.return_value = html_content

        # Requête à l'API avec mock pour le DiagnosticAgent
        with patch("forestai.agents.diagnostic_agent.DiagnosticAgent.execute_action") as mock_execute_action:
            mock_execute_action.return_value = {
                "status": "success",
                "result": {
                    "parcel_id": "13097000B0012",
                    "parcel_data": {"area_ha": 15.234}
                }
            }
            
            response = client.post(
                "/diagnostic/report",
                json={
                    "report_type": "diagnostic",
                    "data_id": "13097000B0012",
                    "format": "html"
                }
            )

        # Vérifications
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html"
        assert b"<html>" in response.content
        
        # Vérifier que la méthode a été appelée
        mock_generate_html.assert_called_once()

    def test_invalid_parcel_id(self):
        """Tester le comportement lors de l'envoi d'un ID de parcelle invalide."""
        # Requête à l'API avec un ID de parcelle vide
        response = client.post(
            "/diagnostic/generate",
            json={
                "parcel_id": "",  # ID invalide
                "include_health_analysis": True
            }
        )

        # Vérifications
        assert response.status_code == 422  # Validation error

    def test_invalid_report_format(self):
        """Tester le comportement lors de la demande d'un format de rapport non supporté."""
        # Requête à l'API avec un format invalide
        response = client.post(
            "/diagnostic/report",
            json={
                "report_type": "diagnostic",
                "data_id": "13097000B0012",
                "format": "invalid_format"  # Format non supporté
            }
        )

        # Vérifications
        assert response.status_code == 422  # Validation error ou 400 Bad Request

    @patch("forestai.agents.diagnostic_agent.DiagnosticAgent.execute_action")
    def test_error_handling(self, mock_execute_action):
        """Tester la gestion d'erreurs."""
        # Mock d'une erreur dans l'agent
        mock_execute_action.side_effect = ValueError("Parcelle introuvable")

        # Requête à l'API
        response = client.post(
            "/diagnostic/generate",
            json={
                "parcel_id": "13097000B0012",
                "include_health_analysis": True
            }
        )

        # Vérifications
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"].lower()
