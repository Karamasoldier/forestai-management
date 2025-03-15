#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation de l'API REST ForestAI avec authentification.

Ce script démontre comment:
1. Obtenir un jeton d'authentification
2. Utiliser ce jeton pour accéder aux endpoints protégés
3. Gérer les erreurs d'authentification

Usage:
    python api_auth_example.py

Requirements:
    - requests
    - json
    - os
"""

import json
import requests
import os
from pathlib import Path
from datetime import datetime

# Configuration de l'API
API_URL = "http://localhost:8000"  # Remplacer par l'URL de production si nécessaire

# Crédentials pour l'authentification
USERNAME = "diagnostic"
PASSWORD = "diagnosticpassword"

def get_access_token(username, password):
    """Obtient un jeton d'accès en utilisant le flux OAuth2 Password."""
    print(f"\n🔑 Authentification avec l'utilisateur {username}...")
    
    try:
        response = requests.post(
            f"{API_URL}/auth/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Authentification réussie")
            print(f"   Utilisateur: {token_data['user_info']['username']}")
            print(f"   Permissions: {', '.join(token_data['user_info']['scopes'])}")
            print(f"   Expiration: {token_data['expires_in'] // 60} minutes")
            return token_data["access_token"]
        else:
            print(f"❌ Authentification échouée : {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur d'authentification: {str(e)}")
        return None

def get_user_info(token):
    """Récupère les informations de l'utilisateur authentifié."""
    print("\n👤 Récupération des informations utilisateur...")
    
    try:
        response = requests.get(
            f"{API_URL}/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Informations récupérées")
            print(f"   Nom complet: {user_data.get('full_name', 'Non disponible')}")
            print(f"   Email: {user_data.get('email', 'Non disponible')}")
            print(f"   Autorisations: {', '.join(user_data.get('scopes', []))}")
            return user_data
        else:
            print(f"❌ Échec de récupération: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None

def get_system_status(token=None):
    """Récupère le statut du système (endpoint non protégé)."""
    print("\n🔍 Vérification du statut du système...")
    
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(
            f"{API_URL}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Statut récupéré")
            print(f"   État: {status_data.get('status', 'inconnu')}")
            print(f"   Agents disponibles: {', '.join(k for k, v in status_data.get('agents', {}).items() if v == 'available')}")
            print(f"   Authentication: {status_data.get('authentication', 'disabled')}")
            return status_data
        else:
            print(f"❌ Échec: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None

def generate_diagnostic(token, parcel_id="13097000B0012"):
    """Génère un diagnostic forestier (endpoint protégé)."""
    print(f"\n🌲 Génération d'un diagnostic pour la parcelle {parcel_id}...")
    
    # Vérifier qu'un token est disponible
    if not token:
        print("❌ Aucun jeton d'authentification disponible")
        return None
    
    # Données de la requête
    request_data = {
        "parcel_id": parcel_id,
        "include_health_analysis": True
    }
    
    try:
        # Envoi de la requête avec le jeton d'authentification
        response = requests.post(
            f"{API_URL}/diagnostic/generate",
            json=request_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            diagnostic_data = result.get("result", {})
            
            print(f"✅ Diagnostic généré avec succès")
            if "parcel_data" in diagnostic_data:
                parcel_data = diagnostic_data.get("parcel_data", {})
                print(f"   Parcelle: {parcel_data.get('commune', '')}, section {parcel_data.get('section', '')}, surface: {parcel_data.get('area_ha', 0):.2f} ha")
            
            if "potential" in diagnostic_data:
                potential = diagnostic_data.get("potential", {})
                print(f"   Score de potentiel: {potential.get('score', 0)}/100")
                print(f"   Espèces recommandées: {', '.join(potential.get('recommended_species', []))}")
            
            if "health" in diagnostic_data:
                health = diagnostic_data.get("health", {})
                print(f"   Score sanitaire: {health.get('overall_health_score', 0):.1f}/10")
                print(f"   État sanitaire: {health.get('health_status', '')}")
                print(f"   Problèmes détectés: {len(health.get('detected_issues', []))}")
            
            # Sauvegarder le résultat
            output_dir = Path("./outputs")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"diagnostic_{parcel_id}_{timestamp}.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(diagnostic_data, f, indent=2, ensure_ascii=False)
            
            print(f"   Résultat sauvegardé dans {output_file}")
            return diagnostic_data
        elif response.status_code == 401:
            print(f"❌ Authentification requise ou jeton invalide")
            return None
        elif response.status_code == 403:
            print(f"❌ Accès refusé: autorisations insuffisantes")
            return None
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Erreur lors de la génération du diagnostic: {str(e)}")
        return None

def analyze_health(token, inventory_data=None):
    """Effectue une analyse sanitaire forestière (endpoint protégé)."""
    print("\n🔬 Analyse sanitaire forestière...")
    
    # Vérifier qu'un token est disponible
    if not token:
        print("❌ Aucun jeton d'authentification disponible")
        return None
    
    # Données d'inventaire par défaut si non fournies
    if inventory_data is None:
        inventory_data = {
            "items": [
                {
                    "species": "quercus_ilex",
                    "diameter": 25.5,
                    "height": 12.0,
                    "health_status": "moyen"
                },
                {
                    "species": "pinus_halepensis",
                    "diameter": 35.0,
                    "height": 18.5,
                    "health_status": "bon"
                }
            ],
            "area": 1.5,
            "date": "2025-03-15",
            "method": "placettes"
        }
    
    # Données de symptômes supplémentaires
    additional_symptoms = {
        "leaf_discoloration": 0.35,
        "observed_pests": ["bark_beetle"],
        "crown_thinning": 0.25
    }
    
    # Construction de la requête
    request_data = {
        "inventory_data": inventory_data,
        "additional_symptoms": additional_symptoms,
        "parcel_id": "13097000B0012"  # Optionnel pour enrichir avec des données climatiques
    }
    
    try:
        # Envoi de la requête avec le jeton d'authentification
        response = requests.post(
            f"{API_URL}/diagnostic/health-analysis",
            json=request_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            health_data = result.get("result", {})
            
            print(f"✅ Analyse sanitaire réalisée avec succès")
            print(f"   Score sanitaire: {health_data.get('overall_health_score', 0):.1f}/10")
            print(f"   État sanitaire: {health_data.get('health_status', '')}")
            print(f"   Problèmes détectés: {len(health_data.get('detected_issues', []))}")
            
            # Sauvegarder le résultat
            output_dir = Path("./outputs")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"health_analysis_{timestamp}.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(health_data, f, indent=2, ensure_ascii=False)
            
            print(f"   Résultat sauvegardé dans {output_file}")
            return health_data
        elif response.status_code == 401:
            print(f"❌ Authentification requise ou jeton invalide")
            return None
        elif response.status_code == 403:
            print(f"❌ Accès refusé: autorisations insuffisantes")
            return None
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse sanitaire: {str(e)}")
        return None

def test_admin_access(token):
    """Teste l'accès à un endpoint réservé aux administrateurs."""
    print("\n👑 Test d'accès à l'interface d'administration...")
    
    try:
        response = requests.get(
            f"{API_URL}/admin/stats",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Accès administrateur réussi")
            print(f"   Requêtes API totales: {stats.get('api_requests_total', 0)}")
            print(f"   Requêtes aujourd'hui: {stats.get('api_requests_today', 0)}")
            print(f"   Utilisateurs actifs: {stats.get('users_active', 0)}")
            return stats
        elif response.status_code == 403:
            print(f"❌ Accès refusé: droits administrateur requis")
            return None
        elif response.status_code == 401:
            print(f"❌ Authentification requise ou jeton invalide")
            return None
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None

def test_invalid_token():
    """Teste l'accès avec un jeton invalide."""
    print("\n❌ Test avec un jeton invalide...")
    
    # Jeton inventé
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnZhbGlkIiwiZXhwIjoxNjE2MjM5MDIyLCJpYXQiOjE2MTYyMzkwMjJ9.invalid_signature"
    
    try:
        response = requests.get(
            f"{API_URL}/auth/me",
            headers={
                "Authorization": f"Bearer {fake_token}",
                "Accept": "application/json"
            }
        )
        
        print(f"   Réponse: {response.status_code} {response.reason}")
        if response.status_code == 401:
            print(f"   ✅ Le serveur a correctement rejeté le jeton invalide")
        else:
            print(f"   ⚠️ Comportement inattendu: le serveur n'a pas rejeté le jeton invalide")
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")

def main():
    """Fonction principale exécutant les différents scénarios d'authentification."""
    print("🔒 Exemple d'utilisation de l'API ForestAI avec authentification 🔒")
    
    # Tester un endpoint non protégé
    get_system_status()
    
    # Obtenir un jeton d'authentification
    token = get_access_token(USERNAME, PASSWORD)
    
    if token:
        # Récupérer les informations de l'utilisateur
        get_user_info(token)
        
        # Effectuer une analyse sanitaire
        analyze_health(token)
        
        # Générer un diagnostic forestier
        generate_diagnostic(token)
        
        # Tester l'accès administrateur (qui devrait échouer avec cet utilisateur)
        test_admin_access(token)
    
    # Tester un jeton invalide
    test_invalid_token()
    
    print("\n✅ Démonstration terminée.")

if __name__ == "__main__":
    main()
