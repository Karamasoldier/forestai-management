#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de génération de rapports au format PDF.

Ce module contient une classe spécialisée pour générer des rapports 
de prédiction de croissance forestière au format PDF.
"""

import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionResult
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.base import BaseReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.html_generator import HtmlReportGenerator

class PdfReportGenerator(BaseReportGenerator):
    """Générateur de rapports au format PDF pour les prédictions de croissance forestière."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialise le générateur de rapports PDF.
        
        Args:
            template_dir: Répertoire contenant les templates de rapports
                         (si None, utilise le répertoire par défaut)
        """
        super().__init__(template_dir)
        # Utiliser le générateur HTML comme base pour le PDF
        self.html_generator = HtmlReportGenerator(template_dir)
    
    def _create_default_templates_if_needed(self) -> None:
        """
        Crée les templates par défaut si nécessaire.
        Pour PDF, nous utilisons les mêmes templates que pour HTML.
        """
        # Déléguer la création des templates à l'instance de HtmlReportGenerator
        self.html_generator._create_default_templates_if_needed()
    
    def _convert_html_to_pdf(self, html_content: str) -> bytes:
        """
        Convertit le contenu HTML en document PDF.
        
        Args:
            html_content: Contenu HTML à convertir
            
        Returns:
            Contenu du document PDF en bytes
            
        Raises:
            ImportError: Si la bibliothèque WeasyPrint n'est pas installée
        """
        try:
            import weasyprint
            pdf_content = weasyprint.HTML(string=html_content).write_pdf()
            return pdf_content
        except ImportError:
            self._logger.error("La bibliothèque WeasyPrint n'est pas installée. Impossible de générer des PDFs.")
            raise ImportError("La bibliothèque WeasyPrint est requise pour la génération de PDFs.")
    
    def generate_report(self, prediction_result: GrowthPredictionResult, 
                        additional_context: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Génère un rapport PDF pour les prédictions de croissance forestière.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            additional_context: Contexte supplémentaire à inclure dans le rapport
            
        Returns:
            Contenu du rapport au format PDF (bytes)
        """
        # Générer d'abord le rapport HTML
        html_content = self.html_generator.generate_report(prediction_result, additional_context)
        
        # Convertir le HTML en PDF
        pdf_content = self._convert_html_to_pdf(html_content)
        
        return pdf_content
    
    def combine_reports(self, individual_reports: Dict[str, str], comparative_analysis: Dict[str, Any]) -> bytes:
        """
        Combine des rapports individuels avec une analyse comparative.
        
        Args:
            individual_reports: Dictionnaire de rapports individuels par scénario
            comparative_analysis: Analyse comparative des scénarios
            
        Returns:
            Rapport combiné au format PDF (bytes)
        """
        # Convertir les rapports HTML en rapports HTML également
        html_individual_reports = {}
        
        for scenario, report in individual_reports.items():
            # Si le rapport est déjà au format HTML, l'utiliser directement
            if report.strip().startswith('<!DOCTYPE html>') or report.strip().startswith('<html'):
                html_individual_reports[scenario] = report
            else:
                # Sinon, supposer qu'il s'agit de Markdown et le convertir en HTML (version simplifiée)
                # Note: une implémentation plus robuste utiliserait une bibliothèque de conversion Markdown->HTML
                self._logger.warning(f"Conversion simplifiée d'un format non-HTML vers HTML pour le scénario {scenario}")
                html_individual_reports[scenario] = f"<div class='markdown-content'><pre>{report}</pre></div>"
        
        # Générer le rapport HTML combiné
        html_combined = self.html_generator.combine_reports(html_individual_reports, comparative_analysis)
        
        # Convertir le HTML en PDF
        pdf_content = self._convert_html_to_pdf(html_combined)
        
        return pdf_content
