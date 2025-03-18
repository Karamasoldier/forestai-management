#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de génération de rapports comparatifs pour les scénarios de croissance forestière.

Ce module fournit une classe spécialisée pour générer des rapports comparatifs
entre différents scénarios de prédiction de croissance forestière.
"""

import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionResult
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.base import BaseReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.markdown_generator import MarkdownReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.html_generator import HtmlReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.pdf_generator import PdfReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.visualization import VisualizationService
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.analysis import AnalysisService

class ComparisonReportGenerator:
    """Générateur de rapports comparatifs pour différents scénarios de prédiction."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialise le générateur de rapports comparatifs.
        
        Args:
            template_dir: Répertoire contenant les templates de rapports
                         (si None, utilise le répertoire par défaut)
        """
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialiser les générateurs de rapports pour différents formats
        self.markdown_generator = MarkdownReportGenerator(template_dir)
        self.html_generator = HtmlReportGenerator(template_dir)
        self.pdf_generator = PdfReportGenerator(template_dir)
        
        # Services pour l'analyse et la visualisation
        self.visualization_service = VisualizationService()
        self.analysis_service = AnalysisService()
    
    def generate_comparison_report(self, scenario_predictions: Dict[str, GrowthPredictionResult], 
                                 format_type: str = 'markdown') -> Any:
        """
        Génère un rapport comparatif pour différents scénarios de prédiction.
        
        Args:
            scenario_predictions: Dictionnaire de résultats de prédiction par scénario
            format_type: Format du rapport ('markdown', 'html', or 'pdf')
            
        Returns:
            Contenu du rapport au format spécifié (str pour markdown/html, bytes pour pdf)
            
        Raises:
            ValueError: Si le format de rapport n'est pas supporté
        """
        if format_type not in ['markdown', 'html', 'pdf']:
            raise ValueError(f"Format de rapport non supporté: {format_type}")
        
        # Générer les rapports individuels pour chaque scénario
        individual_reports = {}
        
        for scenario, prediction in scenario_predictions.items():
            # Ajouter le scénario au contexte
            additional_context = {'scenario': scenario}
            
            # Générer le rapport pour ce scénario
            if format_type == 'markdown':
                report = self.markdown_generator.generate_report(prediction, additional_context)
            elif format_type == 'html':
                report = self.html_generator.generate_report(prediction, additional_context)
            else:  # format_type == 'pdf'
                # Pour PDF, nous générons d'abord en HTML puis convertirons tout à la fin
                report = self.html_generator.generate_report(prediction, additional_context)
            
            individual_reports[scenario] = report
        
        # Créer l'analyse comparative
        comparative_analysis = self.analysis_service.create_comparative_analysis(scenario_predictions)
        
        # Ajouter les graphiques comparatifs
        comparative_analysis['charts'] = self.visualization_service.create_scenario_comparison_plots(scenario_predictions)
        
        # Combiner les rapports individuels avec l'analyse comparative
        if format_type == 'markdown':
            return self.markdown_generator.combine_reports(individual_reports, comparative_analysis)
        elif format_type == 'html':
            return self.html_generator.combine_reports(individual_reports, comparative_analysis)
        else:  # format_type == 'pdf'
            return self.pdf_generator.combine_reports(individual_reports, comparative_analysis)
    
    def extract_key_insights(self, scenario_predictions: Dict[str, GrowthPredictionResult]) -> List[Dict[str, str]]:
        """
        Extrait les principales informations comparatives des prédictions.
        
        Args:
            scenario_predictions: Dictionnaire de résultats de prédiction par scénario
            
        Returns:
            Liste des principales informations comparatives
        """
        insights = []
        
        # Ajouter un aperçu des scénarios
        scenarios_text = f"Comparaison entre {len(scenario_predictions)} scénarios: " + 
                          ", ".join(scenario_predictions.keys())
        insights.append({
            'title': 'Scénarios comparés',
            'content': scenarios_text
        })
        
        # Analyse comparative
        comparative_analysis = self.analysis_service.create_comparative_analysis(scenario_predictions)
        
        # Extraire les insights clés pour chaque métrique
        for metric, data in comparative_analysis['metrics'].items():
            if 'comparison_text' in data:
                insights.append({
                    'title': f"Comparaison de {data['name']}",
                    'content': data['comparison_text']
                })
        
        # Ajouter des recommandations basées sur la comparaison
        # Identifier le "meilleur" scénario pour la biomasse/carbone si disponible
        best_scenario = None
        max_growth = float('-inf')
        
        if 'biomass' in comparative_analysis['metrics']:
            for scenario, values in comparative_analysis['metrics']['biomass']['scenarios'].items():
                if 'raw_change' in values:
                    growth = values['raw_change']
                    if growth > max_growth:
                        max_growth = growth
                        best_scenario = scenario
        
        if best_scenario:
            insights.append({
                'title': 'Recommandation principale',
                'content': f"Le scénario '{best_scenario}' présente le meilleur potentiel de croissance de biomasse " +
                           f"et devrait être considéré comme prioritaire pour maximiser la séquestration de carbone."
            })
        
        return insights
