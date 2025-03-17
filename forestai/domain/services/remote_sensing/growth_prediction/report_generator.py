#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de génération de rapports pour la prédiction de croissance forestière.

Ce module contient la classe ReportGeneratorService qui s'occupe de la
génération de rapports et de visualisations à partir des prédictions de croissance.
"""

import logging
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from forestai.domain.services.remote_sensing.models import (
    RemoteSensingData,
    ForestGrowthPrediction
)

logger = logging.getLogger(__name__)

class ReportGeneratorService:
    """
    Service de génération de rapports pour la prédiction de croissance forestière.
    """
    
    def __init__(self):
        """Initialise le service de génération de rapports."""
        pass
    
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
        # Analyser les taux de croissance pour chaque métrique
        growth_rates = {}
        for date, metrics, _ in prediction.predictions:
            for field_name in dir(metrics):
                # Ignorer les méthodes et attributs spéciaux
                if field_name.startswith('_') or callable(getattr(metrics, field_name)):
                    continue
                
                value = getattr(metrics, field_name)
                if value is not None:
                    growth_rate = prediction.get_growth_rate(field_name)
                    if growth_rate:
                        growth_rates[field_name] = growth_rate
        
        # Extraire les métriques de performance des modèles
        model_metrics = prediction.metrics
        
        # Créer le contenu du rapport
        report = {
            "parcel_id": prediction.parcel_id,
            "prediction_date": prediction.prediction_date.strftime("%Y-%m-%d"),
            "model_type": prediction.model_type,
            "confidence_level": prediction.confidence_level,
            "horizon": len(prediction.predictions),
            "predictions": [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "metrics": {
                        field_name: getattr(metrics, field_name)
                        for field_name in dir(metrics)
                        if not field_name.startswith('_') and not callable(getattr(metrics, field_name))
                        and getattr(metrics, field_name) is not None
                    },
                    "confidence_intervals": intervals
                }
                for date, metrics, intervals in prediction.predictions
            ],
            "growth_rates": growth_rates,
            "model_metrics": model_metrics,
            "climate_scenario": prediction.climate_scenario
        }
        
        # Formater selon le type demandé
        if format_type == "dict":
            return report
        elif format_type == "json":
            return json.dumps(report, indent=2, default=str)
        elif format_type == "html":
            return self._generate_html_report(report, prediction)
        elif format_type == "markdown":
            return self._generate_markdown_report(report, prediction)
        else:
            raise ValueError(f"Format de rapport non supporté: {format_type}")
    
    def _generate_html_report(self, report: Dict[str, Any], prediction: ForestGrowthPrediction) -> str:
        """
        Génère un rapport au format HTML.
        
        Args:
            report: Contenu du rapport au format dict
            prediction: Objet de prédiction de croissance
            
        Returns:
            Rapport au format HTML
        """
        # Générer un rapport HTML simple
        html_content = ["<html><head><title>Rapport de prédiction de croissance forestière</title></head><body>"]
        html_content.append(f"<h1>Rapport de prédiction pour la parcelle {report['parcel_id']}</h1>")
        html_content.append(f"<p><strong>Date de prédiction:</strong> {report['prediction_date']}</p>")
        html_content.append(f"<p><strong>Modèle utilisé:</strong> {report['model_type']}</p>")
        html_content.append(f"<p><strong>Niveau de confiance:</strong> {report['confidence_level']*100}%</p>")
        
        if report['climate_scenario']:
            html_content.append(f"<p><strong>Scénario climatique:</strong> {report['climate_scenario']}</p>")
        
        # Table des prédictions
        html_content.append("<h2>Prédictions</h2>")
        html_content.append("<table border='1'><tr><th>Date</th>")
        
        # Déterminer les métriques disponibles
        available_metrics = set()
        for pred in report['predictions']:
            for metric in pred['metrics'].keys():
                available_metrics.add(metric)
        
        # Ajouter les en-têtes
        for metric in sorted(available_metrics):
            html_content.append(f"<th>{metric}</th>")
        html_content.append("</tr>")
        
        # Ajouter les lignes
        for pred in report['predictions']:
            html_content.append(f"<tr><td>{pred['date']}</td>")
            for metric in sorted(available_metrics):
                value = pred['metrics'].get(metric, None)
                html_content.append(f"<td>{value if value is not None else '-'}</td>")
            html_content.append("</tr>")
        
        html_content.append("</table>")
        
        # Taux de croissance
        if report['growth_rates']:
            html_content.append("<h2>Taux de croissance annuels</h2>")
            html_content.append("<table border='1'>")
            html_content.append("<tr><th>Métrique</th><th>Taux moyen (%)</th></tr>")
            
            for metric, rates in report['growth_rates'].items():
                avg_rate = sum(rates.values()) / len(rates) if rates else 0
                html_content.append(f"<tr><td>{metric}</td><td>{avg_rate:.2f}%</td></tr>")
            
            html_content.append("</table>")
        
        html_content.append("</body></html>")
        return "\n".join(html_content)
    
    def _generate_markdown_report(self, report: Dict[str, Any], prediction: ForestGrowthPrediction) -> str:
        """
        Génère un rapport au format Markdown.
        
        Args:
            report: Contenu du rapport au format dict
            prediction: Objet de prédiction de croissance
            
        Returns:
            Rapport au format Markdown
        """
        # Générer un rapport Markdown
        md_content = []
        md_content.append(f"# Rapport de prédiction pour la parcelle {report['parcel_id']}")
        md_content.append(f"**Date de prédiction:** {report['prediction_date']}")
        md_content.append(f"**Modèle utilisé:** {report['model_type']}")
        md_content.append(f"**Niveau de confiance:** {report['confidence_level']*100}%")
        
        if report['climate_scenario']:
            md_content.append(f"**Scénario climatique:** {report['climate_scenario']}")
        
        md_content.append("\n## Prédictions")
        
        # Table des prédictions
        header = "| Date "
        separator = "|---"
        
        # Déterminer les métriques disponibles
        available_metrics = set()
        for pred in report['predictions']:
            for metric in pred['metrics'].keys():
                available_metrics.add(metric)
                    
        # Compléter l'en-tête et le séparateur
        for metric in sorted(available_metrics):
            header += f"| {metric} "
            separator += "|---"
        
        md_content.append(header + "|")
        md_content.append(separator + "|")
        
        # Ajouter les lignes de données
        for pred in report['predictions']:
            row = f"| {pred['date']} "
            for metric in sorted(available_metrics):
                value = pred['metrics'].get(metric, None)
                row += f"| {value if value is not None else '-'} "
            md_content.append(row + "|")
        
        # Taux de croissance
        if report['growth_rates']:
            md_content.append("\n## Taux de croissance annuels")
            md_content.append("| Métrique | Taux moyen (%) |")
            md_content.append("|------|------|")
            
            for metric, rates in report['growth_rates'].items():
                avg_rate = sum(rates.values()) / len(rates) if rates else 0
                md_content.append(f"| {metric} | {avg_rate:.2f}% |")
        
        # Ajouter les métriques de performance si disponibles
        if report['model_metrics']:
            md_content.append("\n## Métriques de performance du modèle")
            for metric, metrics_dict in report['model_metrics'].items():
                md_content.append(f"\n### {metric}")
                for metric_name, metric_value in metrics_dict.items():
                    # Exclure les facteurs de croissance qui ont leur propre section
                    if metric_name != "growth_factors":
                        md_content.append(f"- **{metric_name}**: {metric_value}")
        
        return "\n".join(md_content)
    
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
        if not scenario_predictions:
            raise ValueError("Le dictionnaire de prédictions ne peut pas être vide")
        
        # Extraire un exemple de prédiction pour référence
        sample_prediction = next(iter(scenario_predictions.values()))
        parcel_id = sample_prediction.parcel_id
        
        # Extraire les métriques disponibles
        all_metrics = set()
        for prediction in scenario_predictions.values():
            for _, metrics, _ in prediction.predictions:
                for field_name in dir(metrics):
                    if not field_name.startswith('_') and not callable(getattr(metrics, field_name)) and getattr(metrics, field_name) is not None:
                        all_metrics.add(field_name)
        
        # Structurer le rapport pour tous les scénarios
        report = {
            "parcel_id": parcel_id,
            "comparison_date": datetime.now().strftime("%Y-%m-%d"),
            "scenarios": list(scenario_predictions.keys()),
            "metrics": sorted(list(all_metrics)),
            "comparisons": {}
        }
        
        # Pour chaque métrique, comparer les valeurs dans les différents scénarios
        for metric in all_metrics:
            metric_comparison = {
                "values_by_date": {},
                "growth_rates": {}
            }
            
            # Collecter toutes les dates disponibles dans les prédictions
            all_dates = set()
            for prediction in scenario_predictions.values():
                for date, _, _ in prediction.predictions:
                    all_dates.add(date.strftime("%Y-%m-%d"))
            
            # Pour chaque date, comparer les valeurs de la métrique dans les différents scénarios
            for date_str in sorted(all_dates):
                metric_comparison["values_by_date"][date_str] = {}
                
                for scenario, prediction in scenario_predictions.items():
                    # Trouver la prédiction pour cette date
                    for pred_date, metrics, intervals in prediction.predictions:
                        if pred_date.strftime("%Y-%m-%d") == date_str:
                            value = getattr(metrics, metric, None)
                            if value is not None:
                                metric_comparison["values_by_date"][date_str][scenario] = {
                                    "value": value,
                                    "confidence_interval": intervals.get(metric, (None, None))
                                }
            
            # Calculer les taux de croissance pour chaque scénario
            for scenario, prediction in scenario_predictions.items():
                growth_rate = prediction.get_growth_rate(metric)
                if growth_rate:
                    metric_comparison["growth_rates"][scenario] = growth_rate
            
            report["comparisons"][metric] = metric_comparison
        
        # Formater selon le type demandé
        if format_type == "dict":
            return report
        elif format_type == "json":
            return json.dumps(report, indent=2, default=str)
        elif format_type == "html":
            return self._generate_comparison_html(report)
        elif format_type == "markdown":
            return self._generate_comparison_markdown(report)
        else:
            raise ValueError(f"Format de rapport non supporté: {format_type}")
    
    def _generate_comparison_html(self, report: Dict[str, Any]) -> str:
        """
        Génère un rapport de comparaison au format HTML.
        
        Args:
            report: Contenu du rapport au format dict
            
        Returns:
            Rapport de comparaison au format HTML
        """
        # Générer un rapport HTML simple pour la comparaison
        html_content = ["<html><head><title>Rapport comparatif de scénarios de croissance forestière</title></head><body>"]
        html_content.append(f"<h1>Rapport comparatif pour la parcelle {report['parcel_id']}</h1>")
        html_content.append(f"<p><strong>Date de comparaison:</strong> {report['comparison_date']}</p>")
        html_content.append(f"<p><strong>Scénarios comparés:</strong> {', '.join(report['scenarios'])}</p>")
        
        # Pour chaque métrique, générer un tableau comparatif
        for metric in report['metrics']:
            html_content.append(f"<h2>Comparaison pour la métrique: {metric}</h2>")
            
            # Table des valeurs par date
            html_content.append("<h3>Valeurs prédites</h3>")
            html_content.append("<table border='1'><tr><th>Date</th>")
            
            # En-têtes des scénarios
            for scenario in report['scenarios']:
                html_content.append(f"<th>{scenario}</th>")
            html_content.append("</tr>")
            
            # Lignes de données
            metric_data = report['comparisons'][metric]['values_by_date']
            for date in sorted(metric_data.keys()):
                html_content.append(f"<tr><td>{date}</td>")
                
                for scenario in report['scenarios']:
                    scenario_value = metric_data[date].get(scenario, {}).get('value', None)
                    html_content.append(f"<td>{scenario_value if scenario_value is not None else '-'}</td>")
                
                html_content.append("</tr>")
            
            html_content.append("</table>")
            
            # Table des taux de croissance
            growth_rates = report['comparisons'][metric]['growth_rates']
            if growth_rates:
                html_content.append("<h3>Taux de croissance annuels (%)</h3>")
                html_content.append("<table border='1'><tr><th>Scénario</th><th>Taux moyen</th></tr>")
                
                for scenario, rates in growth_rates.items():
                    avg_rate = sum(rates.values()) / len(rates) if rates else 0
                    html_content.append(f"<tr><td>{scenario}</td><td>{avg_rate:.2f}%</td></tr>")
                
                html_content.append("</table>")
        
        html_content.append("</body></html>")
        return "\n".join(html_content)
    
    def _generate_comparison_markdown(self, report: Dict[str, Any]) -> str:
        """
        Génère un rapport de comparaison au format Markdown.
        
        Args:
            report: Contenu du rapport au format dict
            
        Returns:
            Rapport de comparaison au format Markdown
        """
        # Générer un rapport Markdown pour la comparaison
        md_content = []
        md_content.append(f"# Rapport comparatif pour la parcelle {report['parcel_id']}")
        md_content.append(f"**Date de comparaison:** {report['comparison_date']}")
        md_content.append(f"**Scénarios comparés:** {', '.join(report['scenarios'])}")
        
        # Pour chaque métrique, générer un tableau comparatif
        for metric in report['metrics']:
            md_content.append(f"\n## Comparaison pour la métrique: {metric}")
            
            # Table des valeurs par date
            md_content.append("\n### Valeurs prédites")
            
            # En-têtes
            header = "| Date "
            separator = "|---"
            
            for scenario in report['scenarios']:
                header += f"| {scenario} "
                separator += "|---"
            
            md_content.append(header + "|")
            md_content.append(separator + "|")
            
            # Lignes de données
            metric_data = report['comparisons'][metric]['values_by_date']
            for date in sorted(metric_data.keys()):
                row = f"| {date} "
                
                for scenario in report['scenarios']:
                    scenario_value = metric_data[date].get(scenario, {}).get('value', None)
                    row += f"| {scenario_value if scenario_value is not None else '-'} "
                
                md_content.append(row + "|")
            
            # Table des taux de croissance
            growth_rates = report['comparisons'][metric]['growth_rates']
            if growth_rates:
                md_content.append("\n### Taux de croissance annuels (%)")
                md_content.append("| Scénario | Taux moyen |")
                md_content.append("|------|------|")
                
                for scenario, rates in growth_rates.items():
                    avg_rate = sum(rates.values()) / len(rates) if rates else 0
                    md_content.append(f"| {scenario} | {avg_rate:.2f}% |")
        
        return "\n".join(md_content)
