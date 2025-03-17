#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module d'amélioration du système de recommandation d'espèces basé sur ML.

Ce module étend les capacités du recommandeur ML avec des fonctionnalités
d'analyse climatique avancées et de comparaison de scénarios.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.ml_recommender import MLSpeciesRecommender
from forestai.domain.services.species_recommender.ml_models.climate_analyzer import ClimateScenarioAnalyzer
from forestai.domain.services.species_recommender.climate_recommendations import ClimateRecommendationAnalyzer
from forestai.domain.services.species_recommender.climate_report_generator import ClimateReportGenerator
from forestai.domain.services.species_recommender.models import (
    SpeciesData,
    SpeciesRecommendation
)

logger = get_logger(__name__)


class EnhancedMLRecommender(MLSpeciesRecommender):
    """
    Version améliorée du recommandeur ML avec analyse climatique intégrée.
    
    Cette classe étend le recommandeur ML standard avec des capacités d'analyse
    des scénarios climatiques et d'identification des espèces résilientes face au
    changement climatique.
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialise le recommandeur ML amélioré.
        
        Args:
            models_dir: Répertoire de stockage des modèles entraînés (facultatif)
        """
        # Initialiser la classe parente
        super().__init__(models_dir)
        
        # Initialiser les composants
        self.climate_analyzer = ClimateScenarioAnalyzer(self)
        self.recommendation_analyzer = ClimateRecommendationAnalyzer()
        self.report_generator = ClimateReportGenerator()
        
        logger.info("EnhancedMLRecommender initialisé")
    
    def predict_climate_adaptation_score(self, species: SpeciesData, 
                                        current_climate: Dict[str, Any],
                                        future_climate: Dict[str, Any]) -> float:
        """
        Prédit le score d'adaptation au changement climatique d'une espèce.
        
        Args:
            species: Données de l'espèce
            current_climate: Données climatiques actuelles
            future_climate: Données climatiques futures
            
        Returns:
            Score d'adaptation au changement climatique (0-1)
        """
        if not self.initialized:
            logger.warning("Modèles ML non initialisés, impossible de faire des prédictions")
            return 0.5  # Valeur neutre par défaut
        
        try:
            # Prédire les scores pour le climat actuel
            current_scores = self.predict_scores(species, current_climate, {}, {})
            
            # Prédire les scores pour le climat futur
            future_scores = self.predict_scores(species, future_climate, {}, {})
            
            if not current_scores or not future_scores:
                # Recourir à l'approche traditionnelle en cas d'échec
                analysis = self.climate_analyzer.analyze_species_climate_adaptability(
                    species, current_climate, future_climate
                )
                return analysis["adaptability_score"]
            
            # Analyser les différences entre les scores
            climate_impact = future_scores["climate_score"] - current_scores["climate_score"]
            risk_impact = current_scores["risk_score"] - future_scores["risk_score"]
            
            # Calculer un score d'adaptation combiné
            # Un score positif indique une bonne adaptation (score climatique amélioré, risque diminué)
            adaptation_score = (climate_impact + risk_impact) / 2
            
            # Normaliser entre 0 et 1
            normalized_score = (adaptation_score + 1) / 2  # -1 à 1 -> 0 à 1
            
            # Retourner le score normalisé et arrondi
            return round(max(0, min(1, normalized_score)), 3)
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction du score d'adaptation: {str(e)}")
            return 0.5  # Valeur neutre par défaut
    
    def recommend_adapted_species(self, parcel_id: str, 
                                 current_climate: Dict[str, Any],
                                 soil_data: Dict[str, Any],
                                 scenario_id: str,
                                 context: Dict[str, Any] = None) -> Tuple[SpeciesRecommendation, SpeciesRecommendation, Dict[str, Any]]:
        """
        Recommande des espèces adaptées aux conditions actuelles et futures.
        
        Args:
            parcel_id: Identifiant de la parcelle
            current_climate: Données climatiques actuelles
            soil_data: Données pédologiques
            scenario_id: Identifiant du scénario climatique à utiliser
            context: Contexte de la recommandation (facultatif)
            
        Returns:
            Tuple contenant (recommandation actuelle, recommandation future, analyse)
        """
        # Initialiser le contexte si non fourni
        if context is None:
            context = {"objective": "balanced"}
        
        # Obtenir les informations du scénario
        scenario = self.climate_analyzer.get_predefined_scenario(scenario_id)
        if not scenario:
            logger.warning(f"Scénario non trouvé: {scenario_id}, utilisation d'un scénario par défaut")
            # Scénario par défaut modéré 2050
            scenario = {
                "name": "RCP 4.5 - 2050 (défaut)",
                "description": "Scénario modéré",
                "temperature_increase": 1.8,
                "precipitation_change_factor": 0.92,
                "drought_index_increase": 2.0
            }
        
        # Projeter le climat futur
        future_climate = self.climate_analyzer.project_climate_data(current_climate, scenario)
        
        # Créer les contextes pour les scénarios actuel et futur
        current_context = context.copy()
        current_context["climate_change_scenario"] = "none"
        
        future_context = context.copy()
        future_context["climate_change_scenario"] = scenario_id
        
        # Générer la recommandation pour le climat actuel
        from forestai.domain.services.species_recommender.recommender import SpeciesRecommender
        recommender = SpeciesRecommender(use_ml=True)
        
        current_recommendation = recommender.recommend_species(
            f"{parcel_id}_current", current_climate, soil_data, current_context
        )
        
        # Générer la recommandation pour le climat futur
        future_recommendation = recommender.recommend_species(
            f"{parcel_id}_future", future_climate, soil_data, future_context
        )
        
        # Analyser les différences entre les recommandations
        analysis = self.recommendation_analyzer.analyze_climate_recommendations(
            current_recommendation, future_recommendation, recommender.get_species_data(),
            current_climate, future_climate
        )
        
        return current_recommendation, future_recommendation, analysis
    
    def generate_climate_adaptation_report(self, parcel_id: str, 
                                         current_climate: Dict[str, Any],
                                         soil_data: Dict[str, Any],
                                         scenarios: List[str],
                                         context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Génère un rapport d'adaptation au changement climatique pour une parcelle.
        
        Args:
            parcel_id: Identifiant de la parcelle
            current_climate: Données climatiques actuelles
            soil_data: Données pédologiques
            scenarios: Liste des identifiants de scénarios à analyser
            context: Contexte de la recommandation (facultatif)
            
        Returns:
            Rapport d'adaptation au changement climatique
        """
        # Initialiser le contexte si non fourni
        if context is None:
            context = {"objective": "balanced"}
        
        # Récupérer les données d'espèces
        from forestai.domain.services.species_recommender.recommender import SpeciesRecommender
        recommender = SpeciesRecommender(use_ml=True)
        species_data = recommender.get_species_data()
        
        # Initialiser les données de rapport
        report_data = {
            "parcel_id": parcel_id,
            "current_climate": current_climate,
            "soil_data": soil_data,
            "context": context,
            "scenarios": scenarios,
            "climate_analyzer": self.climate_analyzer,
            "recommendations": {},
            "species_data": species_data
        }
        
        # Générer des recommandations pour chaque scénario
        for scenario_id in scenarios:
            try:
                current_rec, future_rec, analysis = self.recommend_adapted_species(
                    parcel_id, current_climate, soil_data, scenario_id, context
                )
                
                report_data["recommendations"][scenario_id] = {
                    "current": current_rec,
                    "future": future_rec,
                    "analysis": analysis
                }
            except Exception as e:
                logger.error(f"Erreur lors de la génération des recommandations pour le scénario {scenario_id}: {str(e)}")
        
        # Générer le rapport complet
        return self.report_generator.generate_report(report_data)
