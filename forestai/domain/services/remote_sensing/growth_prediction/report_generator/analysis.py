#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'analyse pour les rapports de prédiction forestière.

Ce module contient des services pour générer des analyses textuelles
des prédictions de croissance forestière.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from forestai.domain.services.remote_sensing.models import ForestMetrics
from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionResult

class AnalysisService:
    """Service de création d'analyses textuelles pour les rapports forestiers."""
    
    def __init__(self):
        """Initialise le service d'analyse."""
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_analysis_text(self, prediction_result: GrowthPredictionResult) -> Dict[str, str]:
        """
        Crée des textes d'analyse pour chaque métrique prédite.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            
        Returns:
            Dictionnaire des textes d'analyse par métrique
        """
        analysis = {}
        
        # S'assurer que nous avons des prédictions
        if not prediction_result.predictions:
            return analysis
        
        # Récupérer les noms des métriques disponibles
        first_date, first_metrics, _ = prediction_result.predictions[0]
        last_date, last_metrics, _ = prediction_result.predictions[-1]
        
        for attr in dir(first_metrics):
            if attr.startswith('_') or callable(getattr(first_metrics, attr)):
                continue
            
            initial_value = getattr(first_metrics, attr)
            final_value = getattr(last_metrics, attr)
            
            if not (isinstance(initial_value, (int, float)) and isinstance(final_value, (int, float))):
                continue
            
            change = final_value - initial_value
            change_percent = (change / initial_value * 100) if initial_value != 0 else 0
            change_direction = "augmentation" if change >= 0 else "diminution"
            
            # Générer le texte d'analyse
            text = f"La métrique {attr.replace('_', ' ')} montre une {change_direction} de "
            text += f"{abs(change):.2f} unités ({abs(change_percent):.1f}%) "
            text += f"sur la période de prédiction."
            
            # Ajouter une interprétation spécifique à la métrique
            if attr == 'canopy_height':
                text += f" Cette {change_direction} de la hauteur de canopée indique "
                text += "une croissance verticale de la forêt, "
                text += "ce qui est généralement un signe de développement sain dans des conditions favorables."
            
            elif attr == 'biomass':
                text += f" Cette {change_direction} de la biomasse reflète "
                text += "l'accumulation de matière végétale, "
                text += "un indicateur important de la productivité forestière et de la séquestration de carbone."
            
            elif attr == 'carbon_stock':
                text += f" Cette {change_direction} du stock de carbone est "
                text += "directement liée à la fonction de puits de carbone de la forêt, "
                text += "un service écosystémique essentiel dans le contexte du changement climatique."
            
            elif attr == 'stem_density':
                if change < 0:
                    text += " La diminution de la densité des tiges est souvent normale "
                    text += "dans une forêt en développement en raison de la compétition naturelle, "
                    text += "mais pourrait aussi indiquer des perturbations comme des maladies ou des coupes."
                else:
                    text += " L'augmentation de la densité des tiges suggère "
                    text += "une régénération active ou une croissance de nouveaux arbres, "
                    text += "ce qui peut être positif pour la résilience de la forêt."
            
            analysis[attr] = text
        
        return analysis
    
    def create_comparative_analysis(self, scenario_predictions: Dict[str, GrowthPredictionResult]) -> Dict[str, Any]:
        """
        Crée une analyse comparative des différents scénarios de prédiction.
        
        Args:
            scenario_predictions: Dictionnaire de résultats de prédiction par scénario
            
        Returns:
            Dictionnaire contenant l'analyse comparative
        """
        analysis = {
            'title': 'Analyse comparative des scénarios',
            'description': 'Comparaison des résultats de croissance forestière selon différents scénarios',
            'scenarios': list(scenario_predictions.keys()),
            'metrics': {}
        }
        
        # S'assurer qu'il y a des scénarios à comparer
        if not scenario_predictions:
            return analysis
        
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
        
        # Pour chaque métrique commune, comparer les changements entre les scénarios
        for metric in common_metrics:
            analysis['metrics'][metric] = {
                'name': metric.replace('_', ' ').title(),
                'scenarios': {},
                'comparison_text': ''
            }
            
            scenario_values = []
            
            for scenario, prediction in scenario_predictions.items():
                if not prediction.predictions:
                    continue
                
                # Récupérer les valeurs initiale et finale
                first_date, first_metrics, _ = prediction.predictions[0]
                last_date, last_metrics, _ = prediction.predictions[-1]
                
                initial_value = getattr(first_metrics, metric)
                final_value = getattr(last_metrics, metric)
                
                if not (isinstance(initial_value, (int, float)) and isinstance(final_value, (int, float))):
                    continue
                
                change = final_value - initial_value
                change_percent = (change / initial_value * 100) if initial_value != 0 else 0
                
                analysis['metrics'][metric]['scenarios'][scenario] = {
                    'initial': f"{initial_value:.2f}" if isinstance(initial_value, float) else initial_value,
                    'final': f"{final_value:.2f}" if isinstance(final_value, float) else final_value,
                    'change': f"{change:.2f}" if isinstance(change, float) else change,
                    'change_percent': f"{change_percent:.1f}",
                    'raw_change': change,
                    'raw_change_percent': change_percent
                }
                
                scenario_values.append((scenario, change, change_percent))
            
            # Trier les scénarios par changement et créer un texte de comparaison
            scenario_values.sort(key=lambda x: x[1], reverse=True)
            
            if scenario_values:
                best_scenario, best_change, best_change_percent = scenario_values[0]
                worst_scenario, worst_change, worst_change_percent = scenario_values[-1]
                
                comparison_text = f"Parmi les scénarios analysés, '{best_scenario}' montre la plus forte "
                comparison_text += f"{'augmentation' if best_change >= 0 else 'diminution'} "
                comparison_text += f"de {metric.replace('_', ' ')} ({abs(best_change_percent):.1f}%), "
                comparison_text += f"tandis que '{worst_scenario}' présente la plus faible "
                comparison_text += f"{'augmentation' if worst_change >= 0 else 'diminution'} "
                comparison_text += f"({abs(worst_change_percent):.1f}%)."
                
                if len(scenario_values) > 2:
                    middle_scenario, middle_change, middle_change_percent = scenario_values[len(scenario_values) // 2]
                    comparison_text += f" Le scénario '{middle_scenario}' représente une situation intermédiaire "
                    comparison_text += f"avec une variation de {abs(middle_change_percent):.1f}%."
                
                analysis['metrics'][metric]['comparison_text'] = comparison_text
            
        return analysis
    
    def extract_key_insights(self, prediction_result: GrowthPredictionResult) -> List[Dict[str, str]]:
        """
        Extrait les principales informations des prédictions de croissance.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            
        Returns:
            Liste des principales informations
        """
        insights = []
        
        # S'assurer que nous avons des prédictions
        if not prediction_result.predictions:
            return insights
        
        # Calculer la durée de la prédiction
        first_date, _, _ = prediction_result.predictions[0]
        last_date, _, _ = prediction_result.predictions[-1]
        prediction_days = (last_date - first_date).days
        prediction_years = prediction_days / 365.25
        
        insights.append({
            'title': 'Durée de prédiction',
            'content': f"La prédiction couvre une période de {prediction_days} jours (environ {prediction_years:.1f} ans)."
        })
        
        # Extraire les principales métriques et leurs tendances
        first_date, first_metrics, _ = prediction_result.predictions[0]
        last_date, last_metrics, _ = prediction_result.predictions[-1]
        
        # Tendances importantes à rapporter
        important_metrics = ['canopy_height', 'biomass', 'carbon_stock']
        
        for metric in important_metrics:
            if not (hasattr(first_metrics, metric) and hasattr(last_metrics, metric)):
                continue
                
            initial_value = getattr(first_metrics, metric)
            final_value = getattr(last_metrics, metric)
            
            if not (isinstance(initial_value, (int, float)) and isinstance(final_value, (int, float))):
                continue
                
            change = final_value - initial_value
            change_percent = (change / initial_value * 100) if initial_value != 0 else 0
            annual_growth = change / prediction_years if prediction_years > 0 else 0
            
            insight_title = f"Évolution de {metric.replace('_', ' ')}"
            insight_content = f"{'Augmentation' if change >= 0 else 'Diminution'} de {abs(change):.2f} "
            insight_content += f"({abs(change_percent):.1f}%), soit environ {abs(annual_growth):.2f} par an."
            
            insights.append({
                'title': insight_title,
                'content': insight_content
            })
        
        # Ajouter des insights à partir des facteurs d'influence
        if prediction_result.influence_factors:
            insights.append({
                'title': 'Principaux facteurs d\'influence',
                'content': f"Les facteurs impactant le plus la croissance incluent: " + 
                           ", ".join([f"{factor['name']}" for factor in prediction_result.influence_factors[:3]])
            })
        
        # Ajouter des insights à partir des recommandations
        if prediction_result.recommendations:
            recommendations_text = "Recommandations principales: " + "; ".join(
                [f"{rec['description']}" for rec in prediction_result.recommendations[:2]]
            )
            insights.append({
                'title': 'Recommandations',
                'content': recommendations_text
            })
        
        return insights
