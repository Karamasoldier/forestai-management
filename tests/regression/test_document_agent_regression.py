# -*- coding: utf-8 -*-
"""
Tests de régression pour le DocumentAgent.

Ce module contient les tests de régression automatisés qui vérifient que
les fonctionnalités du DocumentAgent continuent de fonctionner comme prévu
après des modifications du code.
"""

import os
import json
import tempfile
import unittest
import hashlib
from datetime import datetime
from pathlib import Path

from forestai.agents.document_agent import DocumentAgent
from forestai.agents.document_agent.models.document_models import DocumentType, DocumentFormat

# Répertoire pour sauvegarder les résultats de référence
REFERENCE_DIR = Path(__file__).parent / "reference_outputs"
REFERENCE_DIR.mkdir(exist_ok=True)

class DocumentAgentRegressionTest(unittest.TestCase):
    """
    Tests de régression pour vérifier la consistance des sorties du DocumentAgent.
    
    Ces tests génèrent des documents et vérifient que leur sortie correspond
    à des valeurs de référence précédemment générées. Si les sorties changent,
    cela peut indiquer une régression.
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour tous les tests."""
        cls.agent = DocumentAgent()
        cls.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Créer un répertoire temporaire pour les sorties
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.output_dir = Path(cls.temp_dir.name)
        
        # S'assurer que le répertoire de référence existe
        REFERENCE_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après exécution de tous les tests."""
        cls.temp_dir.cleanup()
    
    def test_contract_generation_regression(self):
        """
        Test de régression pour la génération de contrats.
        
        Vérifie que la structure et le contenu des contrats générés
        correspondent aux références attendues.
        """
        # Données de test pour un contrat
        contract_data = {
            "contract_type": "vente de bois",
            "reference": f"TEST-VENTE-{self.timestamp}",
            "title": "Contrat de Test - Vente de Bois",
            "date": "2025-01-01",
            "start_date": "2025-01-15",
            "duration": "3 mois",
            "location": "Forêt de test",
            "parties": [
                {
                    "name": "Propriétaire Test",
                    "address": "1 rue du Test, 75000 Paris",
                    "representative": "M. Test",
                    "function": "Propriétaire",
                    "type": "vendor"
                },
                {
                    "name": "Acheteur Test",
                    "address": "2 rue du Test, 75000 Paris",
                    "representative": "Mme Test",
                    "function": "Directrice",
                    "siret": "12345678900000",
                    "type": "buyer"
                }
            ],
            "parcels": [
                {
                    "id": "TEST001",
                    "section": "X",
                    "numero": "001",
                    "commune": "Testville",
                    "area_ha": 10.0,
                    "volume_estimated_m3": 300
                }
            ],
            "amount": "15000",
            "price_per_m3": "50",
            "payment_terms": "30% à la signature, solde à l'enlèvement",
            "special_conditions": "Conditions de test."
        }
        
        # Générer le contrat au format HTML uniquement pour le test de régression
        result = self.agent.execute_action(
            "generate_contract",
            {
                "contract_data": contract_data,
                "formats": ["html"]
            }
        )
        
        # Vérifier que la génération a réussi
        self.assertTrue(result.get("status") == "success")
        
        # Récupérer le contenu HTML
        html_content = result.get("result", {}).get("files", {}).get("html")
        self.assertIsNotNone(html_content)
        
        # Supprimer les éléments variables comme les timestamps et les identifiants uniques
        normalized_html = self._normalize_html_for_comparison(html_content)
        
        # Calculer un hash du contenu normalisé
        content_hash = hashlib.md5(normalized_html.encode()).hexdigest()
        
        # Vérifier le hash par rapport à une référence
        reference_file = REFERENCE_DIR / "contract_reference_hash.txt"
        
        # Si le fichier de référence n'existe pas, le créer
        if not reference_file.exists():
            with open(reference_file, 'w') as f:
                f.write(content_hash)
            self.skipTest("Fichier de référence créé. Exécutez à nouveau le test pour validation.")
        
        # Sinon, comparer avec la référence existante
        with open(reference_file, 'r') as f:
            reference_hash = f.read().strip()
        
        # Vérifier que le hash correspond
        self.assertEqual(content_hash, reference_hash, 
            "La sortie du contrat a changé. Cela peut indiquer une régression ou une amélioration intentionnelle.")
    
    def test_management_plan_generation_regression(self):
        """
        Test de régression pour la génération de plans de gestion.
        
        Vérifie que la structure et le contenu des plans de gestion générés
        correspondent aux références attendues.
        """
        # Données de test pour un plan de gestion
        plan_data = {
            "plan_type": "plan_simple_gestion",
            "reference": f"TEST-PSG-{self.timestamp}",
            "title": "Plan Simple de Gestion - Test",
            "property_name": "Forêt de Test",
            "owner": {
                "name": "Propriétaire Test",
                "address": "1 rue du Test, 75000 Paris",
                "contact": "M. Test",
                "phone": "01 23 45 67 89",
                "email": "test@example.com"
            },
            "start_date": "2025-01-01",
            "duration_years": 10,
            "parcels": [
                {
                    "id": "TEST001",
                    "section": "X",
                    "numero": "001",
                    "commune": "Testville",
                    "area_ha": 10.0,
                    "cadastral_reference": "X001"
                }
            ],
            "stands": [
                {
                    "id": "S01",
                    "type": "Futaie de test",
                    "area_ha": 10.0,
                    "main_species": "Testus maximus",
                    "age": 50,
                    "volume_per_ha": 100,
                    "objective": "Test de production"
                }
            ],
            "scheduled_operations": [
                {
                    "year": 2025,
                    "stand_id": "S01",
                    "operation": "Test d'éclaircie",
                    "details": "Prélèvement de test",
                    "expected_volume_m3": 100
                }
            ]
        }
        
        # Générer le plan de gestion au format HTML uniquement pour le test de régression
        result = self.agent.execute_action(
            "generate_management_plan_doc",
            {
                "plan_data": plan_data,
                "formats": ["html"]
            }
        )
        
        # Vérifier que la génération a réussi
        self.assertTrue(result.get("status") == "success")
        
        # Récupérer le contenu HTML
        html_content = result.get("result", {}).get("files", {}).get("html")
        self.assertIsNotNone(html_content)
        
        # Supprimer les éléments variables comme les timestamps et les identifiants uniques
        normalized_html = self._normalize_html_for_comparison(html_content)
        
        # Calculer un hash du contenu normalisé
        content_hash = hashlib.md5(normalized_html.encode()).hexdigest()
        
        # Vérifier le hash par rapport à une référence
        reference_file = REFERENCE_DIR / "management_plan_reference_hash.txt"
        
        # Si le fichier de référence n'existe pas, le créer
        if not reference_file.exists():
            with open(reference_file, 'w') as f:
                f.write(content_hash)
            self.skipTest("Fichier de référence créé. Exécutez à nouveau le test pour validation.")
        
        # Sinon, comparer avec la référence existante
        with open(reference_file, 'r') as f:
            reference_hash = f.read().strip()
        
        # Vérifier que le hash correspond
        self.assertEqual(content_hash, reference_hash, 
            "La sortie du plan de gestion a changé. Cela peut indiquer une régression ou une amélioration intentionnelle.")
    
    def test_administrative_doc_generation_regression(self):
        """
        Test de régression pour la génération de documents administratifs.
        
        Vérifie que la structure et le contenu des documents administratifs générés
        correspondent aux références attendues.
        """
        # Données de test pour un document administratif
        admin_data = {
            "reference": f"TEST-ADMIN-{self.timestamp}",
            "title": "Document Administratif - Test",
            "date": "2025-01-01",
            "authority": "Autorité de Test",
            "owner": {
                "name": "Propriétaire Test",
                "address": "1 rue du Test, 75000 Paris",
                "phone": "01 23 45 67 89",
                "email": "test@example.com"
            },
            "parcels": [
                {
                    "id": "TEST001",
                    "section": "X",
                    "numero": "001",
                    "commune": "Testville",
                    "area_ha": 10.0,
                    "cadastral_reference": "X001"
                }
            ],
            "volume_m3": 100,
            "surface_ha": 10.0,
            "forest_type": "Forêt de test",
            "cut_type": "Coupe de test",
            "validity_period": "1 an",
            "validity_start": "2025-01-01",
            "validity_end": "2026-01-01",
            "legal_references": [
                "Référence légale de test 1",
                "Référence légale de test 2"
            ],
            "conditions": [
                "Condition de test 1",
                "Condition de test 2"
            ]
        }
        
        # Générer le document administratif au format HTML uniquement pour le test de régression
        result = self.agent.execute_action(
            "generate_administrative_doc",
            {
                "admin_data": admin_data,
                "doc_type": "autorisation_coupe",
                "formats": ["html"]
            }
        )
        
        # Vérifier que la génération a réussi
        self.assertTrue(result.get("status") == "success")
        
        # Récupérer le contenu HTML
        html_content = result.get("result", {}).get("files", {}).get("html")
        self.assertIsNotNone(html_content)
        
        # Supprimer les éléments variables comme les timestamps et les identifiants uniques
        normalized_html = self._normalize_html_for_comparison(html_content)
        
        # Calculer un hash du contenu normalisé
        content_hash = hashlib.md5(normalized_html.encode()).hexdigest()
        
        # Vérifier le hash par rapport à une référence
        reference_file = REFERENCE_DIR / "administrative_doc_reference_hash.txt"
        
        # Si le fichier de référence n'existe pas, le créer
        if not reference_file.exists():
            with open(reference_file, 'w') as f:
                f.write(content_hash)
            self.skipTest("Fichier de référence créé. Exécutez à nouveau le test pour validation.")
        
        # Sinon, comparer avec la référence existante
        with open(reference_file, 'r') as f:
            reference_hash = f.read().strip()
        
        # Vérifier que le hash correspond
        self.assertEqual(content_hash, reference_hash, 
            "La sortie du document administratif a changé. Cela peut indiquer une régression ou une amélioration intentionnelle.")
    
    def test_specifications_generation_regression(self):
        """
        Test de régression pour la génération de cahiers des charges.
        
        Vérifie que la structure et le contenu des cahiers des charges générés
        correspondent aux références attendues.
        """
        # Données de test pour un cahier des charges
        spec_data = {
            "spec_type": "travaux forestiers",
            "reference": f"TEST-CDC-{self.timestamp}",
            "title": "Cahier des Charges - Test",
            "date": "2025-01-01",
            "client": {
                "name": "Client Test",
                "address": "1 rue du Test, 75000 Paris",
                "contact": "M. Test",
                "phone": "01 23 45 67 89",
                "email": "test@example.com"
            },
            "work_types": ["test1", "test2"],
            "parcels": [
                {
                    "id": "TEST001",
                    "section": "X",
                    "numero": "001",
                    "commune": "Testville",
                    "area_ha": 10.0,
                    "description": "Description de test"
                }
            ],
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "budget_estimate": "10000 €"
        }
        
        # Générer le cahier des charges au format HTML uniquement pour le test de régression
        result = self.agent.execute_action(
            "generate_specifications",
            {
                "spec_data": spec_data,
                "formats": ["html"]
            }
        )
        
        # Vérifier que la génération a réussi
        self.assertTrue(result.get("status") == "success")
        
        # Récupérer le contenu HTML
        html_content = result.get("result", {}).get("files", {}).get("html")
        self.assertIsNotNone(html_content)
        
        # Supprimer les éléments variables comme les timestamps et les identifiants uniques
        normalized_html = self._normalize_html_for_comparison(html_content)
        
        # Calculer un hash du contenu normalisé
        content_hash = hashlib.md5(normalized_html.encode()).hexdigest()
        
        # Vérifier le hash par rapport à une référence
        reference_file = REFERENCE_DIR / "specifications_reference_hash.txt"
        
        # Si le fichier de référence n'existe pas, le créer
        if not reference_file.exists():
            with open(reference_file, 'w') as f:
                f.write(content_hash)
            self.skipTest("Fichier de référence créé. Exécutez à nouveau le test pour validation.")
        
        # Sinon, comparer avec la référence existante
        with open(reference_file, 'r') as f:
            reference_hash = f.read().strip()
        
        # Vérifier que le hash correspond
        self.assertEqual(content_hash, reference_hash, 
            "La sortie du cahier des charges a changé. Cela peut indiquer une régression ou une amélioration intentionnelle.")
    
    def _normalize_html_for_comparison(self, html_content):
        """
        Normalise le contenu HTML pour la comparaison en éliminant les éléments variables.
        
        Args:
            html_content: Contenu HTML à normaliser
            
        Returns:
            Contenu HTML normalisé pour la comparaison
        """
        # Supprimer les dates et heures dynamiques
        import re
        
        # Remplacer les dates au format YYYY-MM-DD
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', html_content)
        
        # Remplacer les timestamps
        normalized = re.sub(r'\d{8}-\d{6}', 'TIMESTAMP', normalized)
        normalized = re.sub(r'\d{8}\d*', 'TIMESTAMP', normalized)
        
        # Remplacer les identifiants uniques
        normalized = re.sub(r'id="[^"]+"', 'id="ID"', normalized)
        normalized = re.sub(r'class="[^"]+"', 'class="CLASS"', normalized)
        
        # Normaliser les espaces et les sauts de ligne
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized

if __name__ == '__main__':
    unittest.main()
