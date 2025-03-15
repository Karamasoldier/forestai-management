# -*- coding: utf-8 -*-
"""
Module principal d'analyse sanitaire forestière pour le DiagnosticAgent.

Ce module coordonne les différentes analyses de santé forestière et fournit
une interface unifiée pour évaluer l'état sanitaire des peuplements.
"""

import logging
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import os

from forestai.core.infrastructure.cache.cache_utils import cached
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.agents.diagnostic_agent.health.health_issue import HealthIssue
from forestai.agents.diagnostic_agent.health.database_loader import HealthDatabaseLoader
from forestai.agents.diagnostic_agent.health.species_analyzer import SpeciesHealthAnalyzer
from forestai.agents.diagnostic_agent.health.indicator_calculator import HealthIndicatorCalculator
from forestai.agents.diagnostic_agent.health.issue_detector import HealthIssueDetector
from forestai.agents.diagnostic_agent.health.risk_evaluator import RiskEvaluator
from forestai.agents.diagnostic_agent.health.recommendation_generator import RecommendationGenerator
from forestai.agents.diagnostic_agent.health.summary_generator import SummaryGenerator

logger = logging.getLogger(__name__)

class HealthAnalyzer:
    """
    Analyseur de santé forestière qui identifie et évalue les problèmes
    sanitaires des peuplements forestiers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise l'analyseur de santé forestière.
        
        Args:
            config: Configuration optionnelle contenant:
                - data_dir: Répertoire des données sanitaires
                - thresholds: Seuils pour différentes analyses
                - reference_db: Base de données de référence des problèmes sanitaires
        """
        self.config = config or {}
        
        # Répertoire des données par défaut si non spécifié
        default_data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / ".." / ".." / "data" / "health"
        self.data_dir = Path(self.config.get("data_dir", default_data_dir))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Seuils pour différentes analyses
        self.thresholds = self.config.get("thresholds", {
            "leaf_loss_critical": 0.3,  # 30% de perte foliaire considéré comme critique
            "defoliation_critical": 0.25,  # 25% de défoliation considéré comme critique
            "bark_damage_critical": 0.15,  # 15% d'arbres avec écorce endommagée considéré comme critique
            "discoloration_critical": 0.2,  # 20% de décoloration considéré comme critique
            "pest_presence_critical": 0.1,  # 10% d'arbres infestés considéré comme critique
            "crown_transparency_critical": 0.35  # 35% de transparence de houppier considéré comme critique
        })
        
        # Chargement de la base de données des problèmes sanitaires
        db_loader = HealthDatabaseLoader(self.data_dir, self.config.get("reference_db"))
        self.health_issues_db = db_loader.load_database()
        
        # Initialisation des analyseurs spécialisés
        self.species_analyzer = SpeciesHealthAnalyzer()
        self.indicator_calculator = HealthIndicatorCalculator(self.thresholds)
        self.issue_detector = HealthIssueDetector(self.health_issues_db)
        self.risk_evaluator = RiskEvaluator()
        self.recommendation_generator = RecommendationGenerator()
        self.summary_generator = SummaryGenerator()
        
        logger.info(f"HealthAnalyzer initialisé avec {len(self.health_issues_db)} problèmes sanitaires en base")
    
    @cached(data_type=CacheType.DIAGNOSTIC, policy=CachePolicy.WEEKLY)
    def analyze_health(self, inventory_data: Dict[str, Any], 
                      additional_symptoms: Optional[Dict[str, Any]] = None,
                      climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyse l'état sanitaire d'une forêt à partir des données d'inventaire
        et d'observations supplémentaires.
        
        Args:
            inventory_data: Données d'inventaire forestier
            additional_symptoms: Observations supplémentaires de symptômes
            climate_data: Données climatiques pour l'analyse de risques
            
        Returns:
            Analyse sanitaire complète comprenant les problèmes identifiés,
            leur gravité, les recommandations de traitement, etc.
        """
        start_time = datetime.datetime.now()
        logger.info("Début de l'analyse sanitaire forestière")
        
        # Récupérer les items d'inventaire
        if "items" in inventory_data:
            trees = inventory_data["items"]
        elif isinstance(inventory_data, list):
            trees = inventory_data
        else:
            trees = []
            logger.warning("Format d'inventaire non reconnu pour l'analyse sanitaire")
        
        # Analyses primaires
        species_health = self.species_analyzer.analyze_species_health(trees)
        overall_health_indicators = self.indicator_calculator.calculate_indicators(trees, additional_symptoms)
        
        # Identifier les problèmes sanitaires probables
        detected_issues = self.issue_detector.detect_issues(trees, additional_symptoms, climate_data, species_health.keys())
        
        # Évaluer le risque global
        global_risk = self.risk_evaluator.evaluate_risk(detected_issues, species_health, climate_data)
        
        # Générer des recommandations de gestion
        management_recommendations = self.recommendation_generator.generate_recommendations(detected_issues, global_risk)
        
        # Générer un résumé court
        summary = self.summary_generator.generate_summary(detected_issues, global_risk, overall_health_indicators)
        
        # Ajouter les données d'origine (si elles ont été fournies)
        source_data = {}
        if additional_symptoms:
            source_data["observed_symptoms"] = additional_symptoms
        if climate_data:
            source_data["climate_context"] = {
                k: v for k, v in climate_data.items() 
                if k in ["current_climate", "drought_index", "temperature_anomaly"]
            }
        
        # Construire le résultat final
        result = {
            "summary": summary,
            "overall_health_score": global_risk["overall_health_score"],
            "health_status": global_risk["health_status"],
            "detected_issues": [issue.to_dict() for issue in detected_issues],
            "species_health": species_health,
            "health_indicators": overall_health_indicators,
            "recommendations": management_recommendations,
            "risk_assessment": {
                "current_risk": global_risk["current_risk"],
                "future_risk": global_risk["future_risk"],
                "risk_factors": global_risk["risk_factors"]
            },
            "metadata": {
                "analysis_date": datetime.datetime.now().isoformat(),
                "analysis_duration_seconds": (datetime.datetime.now() - start_time).total_seconds(),
                "analyzer_version": "1.0.0"
            }
        }
        
        # Ajouter les données source si présentes
        if source_data:
            result["source_data"] = source_data
        
        logger.info(f"Analyse sanitaire terminée: {len(detected_issues)} problèmes détectés, score de santé global: {global_risk['overall_health_score']:.2f}/10")
        return result
