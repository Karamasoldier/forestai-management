#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module factory pour les générateurs de rapport de croissance forestière.

Ce module fournit une factory pour créer les générateurs de rapport 
selon le format souhaité.
"""

import logging
from typing import Dict, Any, Union

from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionResult
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.base import BaseReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.markdown_generator import MarkdownReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.html_generator import HtmlReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.pdf_generator import PdfReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.comparison_generator import ComparisonReportGenerator

class ReportFactory:
    """Factory pour créer les générateurs de rapport appropriés."""
    
    def __init__(self, template_dir: str = None):
        """
        Initialise la factory de rapports.
        
        Args:
            template_dir: Répertoire contenant les templates de rapports
        """
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.template_dir = template_dir
        self._generators = {}
    
    def get_generator(self, format_type: str) -> BaseReportGenerator:
        """
        Obtient ou crée un générateur de rapport pour le format spécifié.
        
        Args:
            format_type: Format du rapport ('markdown', 'html', or 'pdf')
            
        Returns:
            Générateur de rapport approprié
            
        Raises:
            ValueError: Si le format n'est pas supporté
        """
        if format_type not in ['markdown', 'html', 'pdf']:
            raise ValueError(f"Format de rapport non supporté: {format_type}")
        
        # Vérifier si le générateur existe déjà
        if format_type in self._generators:
            return self._generators[format_type]
        
        # Créer un nouveau générateur selon le format
        if format_type == 'markdown':
            generator = MarkdownReportGenerator(self.template_dir)
        elif format_type == 'html':
            generator = HtmlReportGenerator(self.template_dir)
        elif format_type == 'pdf':
            generator = PdfReportGenerator(self.template_dir)
        
        # Stocker pour réutilisation
        self._generators[format_type] = generator
        
        return generator
    
    def get_comparison_generator(self) -> ComparisonReportGenerator:
        """
        Obtient ou crée un générateur de rapport comparatif.
        
        Returns:
            Générateur de rapport comparatif
        """
        if 'comparison' in self._generators:
            return self._generators['comparison']
        
        # Créer un nouveau générateur de comparaison
        generator = ComparisonReportGenerator(self.template_dir)
        
        # Stocker pour réutilisation
        self._generators['comparison'] = generator
        
        return generator
    
    def generate_report(self, prediction_result: GrowthPredictionResult, 
                        format_type: str = 'markdown', 
                        context: Dict[str, Any] = None) -> Union[str, bytes]:
        """
        Génère un rapport de prédiction de croissance forestière.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            format_type: Format du rapport ('markdown', 'html', or 'pdf')
            context: Contexte supplémentaire pour le rapport
            
        Returns:
            Contenu du rapport au format spécifié (str pour markdown/html, bytes pour pdf)
        """
        generator = self.get_generator(format_type)
        report = generator.generate_report(prediction_result, context)
        return report
    
    def generate_comparison_report(self, scenario_predictions: Dict[str, GrowthPredictionResult],
                                 format_type: str = 'markdown') -> Union[str, bytes]:
        """
        Génère un rapport comparatif de prédictions de croissance forestière.
        
        Args:
            scenario_predictions: Dictionnaire de résultats de prédiction par scénario
            format_type: Format du rapport ('markdown', 'html', or 'pdf')
            
        Returns:
            Contenu du rapport comparatif au format spécifié
        """
        generator = self.get_comparison_generator()
        report = generator.generate_comparison_report(scenario_predictions, format_type)
        return report
