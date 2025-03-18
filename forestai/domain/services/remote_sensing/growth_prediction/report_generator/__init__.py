#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package de génération de rapports pour les prédictions de croissance forestière.

Ce module fournit des services modulaires pour générer des rapports détaillés
des prédictions de croissance forestière dans différents formats.
"""

from forestai.domain.services.remote_sensing.growth_prediction.report_generator.base import BaseReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.markdown_generator import MarkdownReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.html_generator import HtmlReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.pdf_generator import PdfReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.comparison_generator import ComparisonReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.visualization import VisualizationService
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.analysis import AnalysisService
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.report_factory import ReportFactory

__all__ = [
    'BaseReportGenerator',
    'MarkdownReportGenerator',
    'HtmlReportGenerator', 
    'PdfReportGenerator',
    'ComparisonReportGenerator',
    'VisualizationService',
    'AnalysisService',
    'ReportFactory'
]
