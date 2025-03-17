#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module principal de prédiction de croissance forestière.

Ce module contient la classe ForestGrowthPredictor qui coordonne l'ensemble
du processus de prédiction de croissance forestière en utilisant différents services
spécialisés et gère la prédiction et la comparaison de scénarios.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta

from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

from forestai.domain.services.remote_sensing.models import (
    ForestMetrics,
    RemoteSensingData,
    ForestGrowthPrediction
)

from forestai.domain.services.remote_sensing.growth_prediction.data_preparation import DataPreparationService
from forestai.domain.services.remote_sensing.growth_prediction.model_management import ModelManagementService
from forestai.domain.services.remote_sensing.growth_prediction.report_generator import ReportGeneratorService
from forestai.domain.services.remote_sensing.growth_prediction.scenario_service import ScenarioService
from forestai.domain.services.remote_sensing.growth_prediction.growth_analyzer import GrowthDriverAnalyzer

logger = logging.getLogger(__name__)


class ForestGrowthPredictor:
    """
    Classe principale de prédiction de croissance forestière.
    
    Cette classe coordonne l'ensemble du processus de prédiction en utilisant
    différents services spécialisés. Elle orchestre la préparation des données,
    la gestion des modèles, l'analyse des facteurs de croissance, et la génération
    de rapports.
    """
    
    def __init__(self, 
                 models_dir: Optional[str] = None,
                 confidence_level: float = 0.95):
        """
        Initialise le prédicteur de croissance forestière.
        
        Args:
            models_dir: Répertoire pour sauvegarder/charger les modèles entraînés
            confidence_level: Niveau de confiance pour les intervalles de prédiction (défaut: 0.95)
        """
        self.confidence_level = confidence_level
        
        # Initialisation des services
        self.data_preparation_service = DataPreparationService()
        self.model_management_service = ModelManagementService(models_dir)
        self.report_generator_service = ReportGeneratorService()
        self.scenario_service = ScenarioService()
        self.growth_analyzer = GrowthDriverAnalyzer()
        
        logger.info("ForestGrowthPredictor initialisé avec tous les services")
    
    @cached(data_type=CacheType.MODEL_PREDICTION, policy=CachePolicy.MONTHLY)
    def predict_growth(self, 
                      parcel_id: str,
                      historical_data: List[RemoteSensingData],
                      target_metrics: List[str],
                      horizon_months: int = 12,
                      model_type: Optional[str] = None,
                      force_retrain: bool = False,
                      climate_scenario: Optional[str] = None) -> ForestGrowthPrediction:
        """
        Prédit la croissance forestière pour une parcelle donnée.
        
        Args:
            parcel_id: Identifiant de la parcelle
            historical_data: Données historiques de télédétection
            target_metrics: Liste des métriques à prédire (ex: ['canopy_height', 'biomass'])
            horizon_months: Horizon de prédiction en mois
            model_type: Type de modèle à utiliser (None pour sélection automatique)
            force_retrain: Forcer le réentraînement même si un modèle existe
            climate_scenario: Scénario climatique à utiliser (si applicable)
            
        Returns:
            Objet ForestGrowthPrediction contenant les prédictions
        """
        if not historical_data:
            raise ValueError("Les données historiques ne peuvent pas être vides")
        
        if not target_metrics:
            raise ValueError("Au moins une métrique cible doit être spécifiée")
        
        logger.info(f"Prédiction de croissance pour la parcelle {parcel_id} sur {horizon_months} mois")
        
        # Date de prédiction (maintenant)
        prediction_date = datetime.now()
        
        # Ajuster les données historiques selon le scénario climatique
        if climate_scenario:
            historical_data = self.scenario_service.adjust_historical_data_for_scenario(
                historical_data, climate_scenario
            )
        
        # Créer une liste pour stocker les prédictions
        all_predictions = []
        metrics_performance = {}
        used_model_type = model_type
        
        # Pour chaque métrique cible
        for target_metric in target_metrics:
            try:
                # Préparer les données pour cette métrique
                time_series_data = self.data_preparation_service.prepare_time_series_data(
                    historical_data, target_metric
                )
                
                # Sélectionner ou charger le modèle approprié
                if model_type is None:
                    # Sélection automatique du meilleur modèle
                    selected_model_type, model_metrics = self.model_management_service.select_best_model(
                        time_series_data, target_metric
                    )
                    used_model_type = selected_model_type
                    metrics_performance[target_metric] = model_metrics
                else:
                    used_model_type = model_type
                    
                # Vérifier si le modèle est disponible
                if used_model_type not in self.model_management_service.get_available_models():
                    logger.warning(f"Modèle {used_model_type} non disponible, utilisation de SARIMA")
                    used_model_type = "sarima"
                
                # Chemin du modèle
                model_path = self.model_management_service.get_model_path(
                    parcel_id, used_model_type, target_metric
                )
                
                # Charger ou créer le modèle
                model = None
                if not force_retrain:
                    model = self.model_management_service.load_model(model_path)
                
                if model is None:
                    # Créer et entraîner un nouveau modèle
                    model_class = self.model_management_service.get_available_models()[used_model_type]
                    model = model_class()
                    model.train(time_series_data, target_metric)
                    
                    # Sauvegarder le modèle
                    self.model_management_service.save_model(model, model_path)
                    
                    # Évaluer le modèle si ce n'est pas déjà fait
                    if target_metric not in metrics_performance:
                        metrics_performance[target_metric] = model.evaluate(time_series_data, target_metric)
                
                # Générer les prédictions pour l'horizon spécifié
                future_dates = [prediction_date + timedelta(days=30*i) for i in range(1, horizon_months+1)]
                
                # Obtenir les facteurs d'impact climatique si un scénario est spécifié
                climate_factors = {}
                if climate_scenario:
                    climate_factors = self.scenario_service.get_scenario_impact_factors(climate_scenario)
                
                # Prédire pour chaque date future
                for future_date in future_dates:
                    # Effectuer la prédiction
                    prediction, lower, upper = model.predict(
                        time_series_data, 
                        target_metric, 
                        steps=int((future_date - prediction_date).days / 30),
                        confidence_level=self.confidence_level
                    )
                    
                    # Appliquer les facteurs d'impact climatique si nécessaire
                    if climate_scenario and target_metric in climate_factors:
                        impact_factor = climate_factors[target_metric]
                        prediction *= impact_factor
                        lower *= impact_factor
                        upper *= impact_factor
                    
                    # Créer un objet ForestMetrics avec la valeur prédite
                    metrics = ForestMetrics()
                    setattr(metrics, target_metric, prediction)
                    
                    # Créer les intervalles de confiance
                    confidence_intervals = {
                        target_metric: (lower, upper)
                    }
                    
                    # Ajouter la prédiction à la liste
                    all_predictions.append((future_date, metrics, confidence_intervals))
                
            except Exception as e:
                logger.error(f"Erreur lors de la prédiction pour {target_metric}: {str(e)}")
        
        # Si des prédictions ont été générées, les fusionner par date
        if all_predictions:
            # Regrouper les prédictions par date
            predictions_by_date = {}
            for date, metrics, intervals in all_predictions:
                date_str = date.strftime("%Y-%m-%d")
                if date_str not in predictions_by_date:
                    predictions_by_date[date_str] = (date, ForestMetrics(), {})
                
                # Fusionner les métriques et intervalles
                for metric_name in target_metrics:
                    metric_value = getattr(metrics, metric_name, None)
                    if metric_value is not None:
                        setattr(predictions_by_date[date_str][1], metric_name, metric_value)
                    
                    if metric_name in intervals:
                        predictions_by_date[date_str][2][metric_name] = intervals[metric_name]
            
            # Convertir en liste triée par date
            merged_predictions = sorted(
                [(date, metrics, intervals) for date, metrics, intervals in predictions_by_date.values()],
                key=lambda x: x[0]
            )
            
            # Analyser les facteurs de croissance
            growth_factors = self.growth_analyzer.analyze_growth_drivers(
                historical_data=historical_data,
                predictions=merged_predictions,
                target_metrics=target_metrics,
                climate_scenario=climate_scenario
            )
            
            # Ajouter les analyses de facteurs aux métriques de performance
            for metric in target_metrics:
                if metric in metrics_performance and metric in growth_factors:
                    metrics_performance[metric]["growth_factors"] = growth_factors[metric]
            
            # Créer et retourner l'objet de prédiction
            return ForestGrowthPrediction(
                parcel_id=parcel_id,
                prediction_date=prediction_date,
                predictions=merged_predictions,
                model_type=used_model_type,
                confidence_level=self.confidence_level,
                metrics=metrics_performance,
                climate_scenario=climate_scenario
            )
        else:
            raise ValueError("Aucune prédiction n'a pu être générée")
    
    def generate_growth_report(self,
                             prediction: ForestGrowthPrediction,
                             historical_data: Optional[List[RemoteSensingData]] = None,
                             format_type: str = "dict") -> Union[Dict[str, Any], str]:
        """
        Génère un rapport d'analyse de croissance à partir d'une prédiction.
        
        Args:
            prediction: Prédiction de croissance forestière
            historical_data: Données historiques (optionnel, pour contexte)
            format_type: Format du rapport ('dict', 'json', 'html', 'markdown')
            
        Returns:
            Rapport formaté selon le type spécifié
        """
        return self.report_generator_service.generate_growth_report(
            prediction, historical_data, format_type
        )
    
    def compare_climate_scenarios(self,
                                 parcel_id: str,
                                 historical_data: List[RemoteSensingData],
                                 target_metrics: List[str],
                                 scenarios: List[str],
                                 horizon_months: int = 12,
                                 model_type: Optional[str] = None) -> Dict[str, ForestGrowthPrediction]:
        """
        Compare les prédictions de croissance selon différents scénarios climatiques.
        
        Args:
            parcel_id: Identifiant de la parcelle
            historical_data: Données historiques de télédétection
            target_metrics: Liste des métriques à prédire
            scenarios: Liste des scénarios climatiques à comparer
            horizon_months: Horizon de prédiction en mois
            model_type: Type de modèle à utiliser (None pour sélection automatique)
            
        Returns:
            Dictionnaire de prédictions par scénario climatique
        """
        if not scenarios:
            raise ValueError("Au moins un scénario climatique doit être spécifié")
        
        logger.info(f"Comparaison de {len(scenarios)} scénarios climatiques pour {parcel_id}")
        
        # Générer les prédictions pour chaque scénario
        predictions = {}
        for scenario in scenarios:
            try:
                prediction = self.predict_growth(
                    parcel_id=parcel_id,
                    historical_data=historical_data,
                    target_metrics=target_metrics,
                    horizon_months=horizon_months,
                    model_type=model_type,
                    climate_scenario=scenario
                )
                predictions[scenario] = prediction
                logger.info(f"Prédiction générée pour le scénario '{scenario}'")
            except Exception as e:
                logger.error(f"Erreur lors de la prédiction pour le scénario '{scenario}': {str(e)}")
        
        return predictions
    
    def generate_comparison_report(self,
                                  scenario_predictions: Dict[str, ForestGrowthPrediction],
                                  format_type: str = "dict") -> Union[Dict[str, Any], str]:
        """
        Génère un rapport comparatif des prédictions selon différents scénarios.
        
        Args:
            scenario_predictions: Dictionnaire de prédictions par scénario
            format_type: Format du rapport ('dict', 'json', 'html', 'markdown')
            
        Returns:
            Rapport comparatif formaté selon le type spécifié
        """
        return self.report_generator_service.generate_comparison_report(
            scenario_predictions, format_type
        )
    
    def get_adaptation_recommendations(self,
                                     prediction: ForestGrowthPrediction) -> List[Dict[str, str]]:
        """
        Génère des recommandations d'adaptation basées sur les prédictions.
        
        Args:
            prediction: Prédiction de croissance forestière
            
        Returns:
            Liste de recommandations d'adaptation
        """
        if not prediction.climate_scenario:
            # Si aucun scénario climatique n'est spécifié, utiliser le scénario de base
            scenario = "baseline"
        else:
            scenario = prediction.climate_scenario
        
        return self.scenario_service.get_recommended_adaptation_strategies(
            prediction, scenario
        )
    
    def get_available_scenarios(self) -> Dict[str, str]:
        """
        Récupère la liste des scénarios climatiques disponibles.
        
        Returns:
            Dictionnaire des scénarios disponibles (code: description)
        """
        return self.scenario_service.get_available_scenarios()
