"""
Tests unitaires pour l'API REST ForestAI.
"""

import os
import sys
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Ajout du répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from forestai.api.server import app
from forestai.agents.geo_agent import GeoAgent
from forestai.agents.subsidy_agent import SubsidyAgent

# Créer un client de test
client = TestClient(app)

# Tests des endpoints de base
def test_root_endpoint():
    """Test de l'endpoint racine."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "ForestAI API"

def test_status_endpoint():
    """Test de l'endpoint de statut."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "agents" in data
    assert "geo_agent" in data["agents"]
    assert "subsidy_agent" in data["agents"]

# Tests pour GeoAgent
@patch('forestai.api.dependencies.get_geo_agent')
def test_search_parcels(mock_get_geo_agent):
    """Test de la recherche de parcelles."""
    # Créer un mock pour GeoAgent
    mock_agent = MagicMock()
    mock_agent.execute_action.return_value = {
        "status": "success",
        "result": {
            "parcels": [
                {
                    "id": "13097000B0012",
                    "commune": "Saint-Martin-de-Crau",
                    "section": "B",
                    "numero": "0012",
                    "area_m2": 152340,
                    "address": "Route des Marais"
                }
            ]
        }
    }
    mock_get_geo_agent.return_value = mock_agent
    
    # Exécuter la requête
    response = client.post(
        "/geo/search",
        json={"commune": "Saint-Martin-de-Crau", "section": "B"}
    )
    
    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "parcels" in data["result"]
    assert len(data["result"]["parcels"]) == 1
    assert data["result"]["parcels"][0]["id"] == "13097000B0012"
    
    # Vérifier que le mock a été appelé correctement
    mock_agent.execute_action.assert_called_once_with(
        "search_parcels", 
        {"commune": "Saint-Martin-de-Crau", "section": "B"}
    )

@patch('forestai.api.dependencies.get_geo_agent')
def test_analyze_parcel(mock_get_geo_agent):
    """Test de l'analyse de parcelle."""
    # Créer un mock pour GeoAgent
    mock_agent = MagicMock()
    mock_agent.execute_action.return_value = {
        "status": "success",
        "result": {
            "parcel_id": "13097000B0012",
            "area_ha": 15.234,
            "average_elevation": 42.5,
            "average_slope": 8.3,
            "soil_type": "argileux",
            "forest_potential": {
                "score": 78,
                "recommended_species": ["pinus_pinea", "quercus_ilex"]
            }
        }
    }
    mock_get_geo_agent.return_value = mock_agent
    
    # Exécuter la requête
    response = client.post(
        "/geo/analyze",
        json={"parcel_id": "13097000B0012", "analyses": ["terrain", "forest_potential"]}
    )
    
    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["parcel_id"] == "13097000B0012"
    assert data["result"]["area_ha"] == 15.234
    assert "forest_potential" in data["result"]
    assert data["result"]["forest_potential"]["score"] == 78
    
    # Vérifier que le mock a été appelé correctement
    mock_agent.execute_action.assert_called_once_with(
        "analyze_parcel", 
        {"parcel_id": "13097000B0012", "analyses": ["terrain", "forest_potential"]}
    )

# Tests pour SubsidyAgent
@patch('forestai.api.dependencies.get_subsidy_agent')
def test_search_subsidies(mock_get_subsidy_agent):
    """Test de la recherche de subventions."""
    # Créer un mock pour SubsidyAgent
    mock_agent = MagicMock()
    mock_agent.execute_action.return_value = {
        "status": "success",
        "result": [
            {
                "id": "fr_reforest_2025",
                "title": "Aide au reboisement France Relance 2025",
                "organization": "Ministère de l'Agriculture",
                "deadline": "2025-12-31",
                "funding_rate": 60,
                "amount_per_ha": 3500
            }
        ]
    }
    mock_get_subsidy_agent.return_value = mock_agent
    
    # Exécuter la requête
    response = client.post(
        "/subsidies/search",
        json={
            "project_type": "reboisement",
            "region": "Provence-Alpes-Côte d'Azur",
            "owner_type": "private"
        }
    )
    
    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["result"]) == 1
    assert data["result"][0]["id"] == "fr_reforest_2025"
    assert data["result"][0]["funding_rate"] == 60
    
    # Vérifier que le mock a été appelé correctement
    mock_agent.execute_action.assert_called_once_with(
        "search_subsidies", 
        {
            "project_type": "reboisement",
            "region": "Provence-Alpes-Côte d'Azur",
            "owner_type": "private"
        }
    )

@patch('forestai.api.dependencies.get_subsidy_agent')
def test_analyze_eligibility(mock_get_subsidy_agent):
    """Test de l'analyse d'éligibilité."""
    # Créer un mock pour SubsidyAgent
    mock_agent = MagicMock()
    mock_agent.execute_action.return_value = {
        "status": "success",
        "result": {
            "subsidy_id": "fr_reforest_2025",
            "subsidy_title": "Aide au reboisement France Relance 2025",
            "eligible": True,
            "conditions": [
                {
                    "condition": "Surface minimale",
                    "satisfied": True,
                    "details": "Surface de 5.2 ha > minimum de 1 ha"
                }
            ],
            "funding_details": {
                "base_amount": 18200,
                "bonus_amount": 2600,
                "total_amount": 20800
            }
        }
    }
    mock_get_subsidy_agent.return_value = mock_agent
    
    # Exécuter la requête
    response = client.post(
        "/subsidies/eligibility",
        json={
            "project": {
                "type": "reboisement",
                "area_ha": 5.2,
                "species": ["pinus_pinea", "quercus_suber"],
                "region": "Provence-Alpes-Côte d'Azur",
                "location": "13097000B0012",
                "owner_type": "private",
                "planting_density": 1200
            },
            "subsidy_id": "fr_reforest_2025"
        }
    )
    
    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["subsidy_id"] == "fr_reforest_2025"
    assert data["result"]["eligible"] == True
    assert "funding_details" in data["result"]
    assert data["result"]["funding_details"]["total_amount"] == 20800

# Tests des erreurs
@patch('forestai.api.dependencies.get_geo_agent')
def test_search_parcels_missing_params(mock_get_geo_agent):
    """Test d'erreur avec paramètres manquants."""
    # Exécuter la requête sans commune (paramètre requis)
    response = client.post(
        "/geo/search",
        json={"section": "B"}
    )
    
    # Vérifier que l'erreur est correctement retournée
    assert response.status_code == 422  # Code d'erreur de validation Pydantic
    
@patch('forestai.api.dependencies.get_geo_agent')
def test_analyze_parcel_invalid_id(mock_get_geo_agent):
    """Test d'erreur avec ID de parcelle invalide."""
    # Simuler une erreur dans l'agent
    mock_agent = MagicMock()
    mock_agent.execute_action.side_effect = ValueError("Parcelle non trouvée")
    mock_get_geo_agent.return_value = mock_agent
    
    # Exécuter la requête
    response = client.post(
        "/geo/analyze",
        json={"parcel_id": "invalid_id"}
    )
    
    # Vérifier que l'erreur est correctement retournée
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Parcelle non trouvée"

if __name__ == "__main__":
    pytest.main(["-v"])
