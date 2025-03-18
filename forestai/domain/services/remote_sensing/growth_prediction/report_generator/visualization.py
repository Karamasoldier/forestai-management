#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de visualisation pour les rapports de prédiction forestière.

Ce module contient des services pour générer des visualisations graphiques
pour les prédictions de croissance forestière.
"""

import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Pour générer des graphiques sans serveur X
import seaborn as sns
import base64
from io import BytesIO
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from forestai.domain.services.remote_sensing.models import ForestMetrics, RemoteSensingData
from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionResult

class VisualizationService:
    """Service de création de visualisations pour les rapports forestiers."""
    
    def __init__(self):
        """Initialise le service de visualisation."""
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configurations pour les graphiques
        self.plt_style = 'seaborn-v0_8-whitegrid'
        self.figure_dpi = 120
        self.figure_format = 'png'
    
    def create_growth_plots(self, prediction_result: GrowthPredictionResult) -> Dict[str, str]:
        """
        Crée des graphiques pour chaque métrique prédite.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            
        Returns:
            Dictionnaire des graphiques encodés en base64
        """
        plots = {}
        
        # S'assurer que nous avons des prédictions
        if not prediction_result.predictions:
            return plots
        
        # Obtenir les dates et métriques de toutes les prédictions
        dates = []
        metrics_by_type = {}
        confidence_intervals = {}
        
        # Extraire les données historiques si disponibles
        historical_dates = []
        historical_metrics_by_type = {}
        
        if prediction_result.historical_data:
            for data in prediction_result.historical_data:
                historical_dates.append(data.acquisition_date)
                
                # Pour chaque attribut des métriques
                for attr in dir(data.metrics):
                    if attr.startswith('_') or callable(getattr(data.metrics, attr)):
                        continue
                    
                    value = getattr(data.metrics, attr)
                    if not isinstance(value, (int, float)):
                        continue
                    
                    if attr not in historical_metrics_by_type:
                        historical_metrics_by_type[attr] = []
                    
                    historical_metrics_by_type[attr].append(value)
        
        # Extraire les données de prédiction
        for date, metrics, intervals in prediction_result.predictions:
            dates.append(date)
            
            # Pour chaque attribut des métriques
            for attr in dir(metrics):
                if attr.startswith('_') or callable(getattr(metrics, attr)):
                    continue
                
                value = getattr(metrics, attr)
                if not isinstance(value, (int, float)):
                    continue
                
                if attr not in metrics_by_type:
                    metrics_by_type[attr] = []
                    confidence_intervals[attr] = []
                
                metrics_by_type[attr].append(value)
                
                # Ajouter l'intervalle de confiance s'il est disponible
                if intervals and attr in intervals:
                    confidence_intervals[attr].append(intervals[attr])
                else:
                    confidence_intervals[attr].append((None, None))
        
        # Créer un graphique pour chaque métrique
        with plt.style.context(self.plt_style):
            for attr, values in metrics_by_type.items():
                plt.figure(figsize=(10, 6))
                
                # Tracer les données historiques si disponibles
                if attr in historical_metrics_by_type:
                    plt.plot(historical_dates, historical_metrics_by_type[attr], 'o-', 
                             label='Données historiques', color='black')
                
                # Tracer les prédictions
                plt.plot(dates, values, 's-', label='Prédiction', color='blue')
                
                # Tracer les intervalles de confiance si disponibles
                lower_bound = []
                upper_bound = []
                valid_intervals = True
                
                for lower, upper in confidence_intervals[attr]:
                    if lower is None or upper is None:
                        valid_intervals = False
                        break
                    lower_bound.append(lower)
                    upper_bound.append(upper)
                
                if valid_intervals:
                    plt.fill_between(dates, lower_bound, upper_bound, 
                                     alpha=0.2, color='blue', label='Intervalle de confiance')
                
                # Configurer le graphique
                plt.xlabel('Date')
                plt.ylabel(attr.replace('_', ' ').title())
                plt.title(f"Prédiction de {attr.replace('_', ' ').title()}")
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Convertir le graphique en base64
                buf = BytesIO()
                plt.savefig(buf, format=self.figure_format, dpi=self.figure_dpi)
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                plt.close()
                
                plots[attr] = img_str
        
        return plots
    
    def create_comparison_chart(self, metric: str, plot_data: Dict[str, Any]) -> str:
        """
        Crée un graphique comparatif pour une métrique entre différents scénarios.
        
        Args:
            metric: Nom de la métrique
            plot_data: Données du graphique (dates et valeurs par scénario)
            
        Returns:
            Image du graphique encodée en base64
        """
        with plt.style.context(self.plt_style):
            plt.figure(figsize=(12, 7))
            
            # Palettes de couleurs pour les différents scénarios
            colors = plt.cm.tab10.colors
            
            # Tracer les valeurs pour chaque scénario
            for i, (scenario, values) in enumerate(plot_data['values'].items()):
                color = colors[i % len(colors)]
                plt.plot(plot_data['dates'], values, 'o-', 
                         label=f"Scénario: {scenario}", color=color)
            
            # Configurer le graphique
            plt.xlabel('Date')
            plt.ylabel(metric.replace('_', ' ').title())
            plt.title(f"Comparaison des scénarios: {metric.replace('_', ' ').title()}")
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convertir le graphique en base64
            buf = BytesIO()
            plt.savefig(buf, format=self.figure_format, dpi=self.figure_dpi)
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return img_str
    
    def create_scenario_comparison_plots(self, scenario_predictions: Dict[str, GrowthPredictionResult]) -> Dict[str, Dict[str, Any]]:
        """
        Crée des graphiques de comparaison pour chaque métrique entre différents scénarios.
        
        Args:
            scenario_predictions: Dictionnaire des résultats de prédiction par scénario
            
        Returns:
            Dictionnaire des graphiques de comparaison par métrique
        """
        comparison_charts = {}
        
        # S'assurer qu'il y a des scénarios à comparer
        if not scenario_predictions:
            return comparison_charts
        
        # Identifier les métriques communes à tous les scénarios
        common_metrics = set()
        first_scenario = next(iter(scenario_predictions.values()))
        
        if first_scenario.predictions:
            _, first_metrics, _ = first_scenario.predictions[0]
            
            for attr in dir(first_metrics):
                if attr.startswith('_') or callable(getattr(first_metrics, attr)):
                    continue
                
                value = getattr(first_metrics, attr)
                if isinstance(value, (int, float)):
                    common_metrics.add(attr)
        
        # Pour chaque métrique commune, créer un graphique de comparaison
        for metric in common_metrics:
            # Récupérer les données pour le graphique comparatif
            plot_data = {
                'dates': [],
                'values': {}
            }
            
            for scenario, prediction in scenario_predictions.items():
                if not prediction.predictions:
                    continue
                
                # Collecter les données pour le graphique
                if not plot_data['dates']:
                    plot_data['dates'] = [pred[0] for pred in prediction.predictions]
                
                plot_data['values'][scenario] = []
                for _, metrics, _ in prediction.predictions:
                    value = getattr(metrics, metric)
                    plot_data['values'][scenario].append(value)
            
            # Créer le graphique comparatif
            if plot_data['dates'] and plot_data['values']:
                comparison_charts[metric] = self.create_comparison_chart(metric, plot_data)
        
        return comparison_charts
