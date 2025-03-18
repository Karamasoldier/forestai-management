#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de génération de rapports au format HTML.

Ce module contient une classe spécialisée pour générer des rapports 
de prédiction de croissance forestière au format HTML.
"""

import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionResult
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.base import BaseReportGenerator
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.visualization import VisualizationService
from forestai.domain.services.remote_sensing.growth_prediction.report_generator.analysis import AnalysisService

class HtmlReportGenerator(BaseReportGenerator):
    """Générateur de rapports au format HTML pour les prédictions de croissance forestière."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialise le générateur de rapports HTML.
        
        Args:
            template_dir: Répertoire contenant les templates de rapports
                         (si None, utilise le répertoire par défaut)
        """
        super().__init__(template_dir)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.visualization_service = VisualizationService()
        self.analysis_service = AnalysisService()
    
    def _create_default_templates_if_needed(self) -> None:
        """
        Crée le template HTML par défaut s'il n'existe pas déjà.
        """
        template_path = os.path.join(self.template_dir, 'growth_report_html.html')
        
        if not os.path.exists(template_path):
            html_template = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de croissance forestière - {{ parcel_id }}</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        h1, h2, h3 { color: #2c5e1a; }
        .header { 
            background-color: #f0f7ed; 
            padding: 20px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }
        .summary { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .metric-card { 
            background-color: #f9f9f9; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            padding: 15px; 
        }
        .metric-title { 
            font-weight: bold; 
            margin-bottom: 10px; 
            color: #2c5e1a; 
        }
        .plot-container { 
            margin: 20px 0; 
            text-align: center; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-bottom: 20px; 
        }
        th, td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }
        th { background-color: #f0f7ed; }
        .recommendations { 
            background-color: #f0f7ed; 
            padding: 20px; 
            border-radius: 5px; 
            margin-top: 30px; 
        }
        .footer { 
            margin-top: 50px; 
            font-size: 0.9em; 
            color: #666; 
            text-align: center; 
        }
        .positive-change { color: green; }
        .negative-change { color: red; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Rapport de prédiction de croissance forestière</h1>
        <p><strong>Parcelle:</strong> {{ parcel_id }}</p>
        <p><strong>Date du rapport:</strong> {{ report_date }}</p>
        <p><strong>Période de prédiction:</strong> {{ prediction_start_date }} à {{ prediction_end_date }}</p>
    </div>

    <h2>Résumé des prédictions</h2>
    <div class="summary">
        {% for metric, values in summary.items() %}
        <div class="metric-card">
            <div class="metric-title">{{ metric | replace('_', ' ') | title }}</div>
            <p><strong>Valeur initiale:</strong> {{ values.initial }}</p>
            <p><strong>Valeur finale prédite:</strong> {{ values.final }}</p>
            <p>
                <strong>Changement:</strong> 
                <span class="{% if values.change >= 0 %}positive-change{% else %}negative-change{% endif %}">
                    {{ values.change }} ({{ values.change_percent }}%)
                </span>
            </p>
        </div>
        {% endfor %}
    </div>

    <h2>Analyse détaillée</h2>
    {% for metric in metrics %}
    <h3>{{ metric | replace('_', ' ') | title }}</h3>
    <div class="plot-container">
        <img src="data:image/png;base64,{{ plots[metric] }}" alt="Graphique {{ metric }}" style="max-width: 100%;">
    </div>
    <p>{{ analysis[metric] }}</p>
    {% endfor %}

    <h2>Facteurs d'influence</h2>
    <table>
        <tr>
            <th>Facteur</th>
            <th>Description</th>
        </tr>
        {% for factor in factors %}
        <tr>
            <td><strong>{{ factor.name }}</strong></td>
            <td>{{ factor.description }}</td>
        </tr>
        {% endfor %}
    </table>

    <div class="recommendations">
        <h2>Recommandations</h2>
        <ul>
            {% for recommendation in recommendations %}
            <li><strong>{{ recommendation.category }}:</strong> {{ recommendation.description }}</li>
            {% endfor %}
        </ul>
    </div>

    <h2>Métadonnées du modèle</h2>
    <table>
        <tr>
            <th>Attribut</th>
            <th>Valeur</th>
        </tr>
        <tr>
            <td>Type de modèle</td>
            <td>{{ model_type }}</td>
        </tr>
        <tr>
            <td>Précision du modèle</td>
            <td>{{ model_accuracy }}</td>
        </tr>
        <tr>
            <td>Dernière mise à jour</td>
            <td>{{ last_updated }}</td>
        </tr>
    </table>

    {% if notes %}
    <h2>Notes</h2>
    <p>{{ notes }}</p>
    {% endif %}

    <div class="footer">
        <p>Généré par ForestAI - {{ report_date }}</p>
    </div>
</body>
</html>"""
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            
            # Écrire le template
            with open(template_path, 'w') as f:
                f.write(html_template)
            
            self._logger.info(f"Template HTML par défaut créé: {template_path}")
    
    def generate_report(self, prediction_result: GrowthPredictionResult, 
                        additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Génère un rapport HTML pour les prédictions de croissance forestière.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            additional_context: Contexte supplémentaire à inclure dans le rapport
            
        Returns:
            Contenu du rapport au format HTML
        """
        # Vérifier que le template existe
        template_path = os.path.join(self.template_dir, 'growth_report_html.html')
        if not os.path.exists(template_path):
            self._create_default_templates_if_needed()
        
        # Créer le contexte de base pour le template
        context = {
            'parcel_id': prediction_result.parcel_id,
            'report_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'prediction_start_date': prediction_result.predictions[0][0].strftime('%d/%m/%Y') if prediction_result.predictions else "N/A",
            'prediction_end_date': prediction_result.predictions[-1][0].strftime('%d/%m/%Y') if prediction_result.predictions else "N/A",
            'summary': self._create_prediction_summary(prediction_result),
            'metrics': [attr for attr in prediction_result.summary.keys() if attr not in ['parcel_id', 'datetime']],
            'plots': self.visualization_service.create_growth_plots(prediction_result),
            'analysis': self.analysis_service.create_analysis_text(prediction_result),
            'factors': prediction_result.influence_factors,
            'recommendations': prediction_result.recommendations,
            'model_type': prediction_result.model_info.get('type', 'Inconnu'),
            'model_accuracy': f"{prediction_result.model_info.get('accuracy', 0):.2f}" if 'accuracy' in prediction_result.model_info else "Inconnu",
            'last_updated': prediction_result.model_info.get('last_updated', 'Inconnu'),
            'notes': prediction_result.notes
        }
        
        # Ajouter le contexte supplémentaire s'il est fourni
        if additional_context:
            context.update(additional_context)
        
        # Charger le template
        template = self.env.get_template('growth_report_html.html')
        
        # Rendre le template
        rendered_content = template.render(**context)
        
        return rendered_content
    
    def combine_reports(self, individual_reports: Dict[str, str], comparative_analysis: Dict[str, Any]) -> str:
        """
        Combine des rapports individuels avec une analyse comparative.
        
        Args:
            individual_reports: Dictionnaire de rapports individuels par scénario
            comparative_analysis: Analyse comparative des scénarios
            
        Returns:
            Rapport combiné au format HTML
        """
        # Créer l'en-tête du rapport combiné
        combined_report = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport comparatif des scénarios de croissance forestière</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        h1, h2, h3 { color: #2c5e1a; }
        .header { 
            background-color: #f0f7ed; 
            padding: 20px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }
        .plot-container { 
            margin: 20px 0; 
            text-align: center; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-bottom: 20px; 
        }
        th, td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }
        th { background-color: #f0f7ed; }
        .scenario-section {
            margin-top: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
        }
        .scenario-header {
            background-color: #f0f7ed;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 5px;
        }
        .footer { 
            margin-top: 50px; 
            font-size: 0.9em; 
            color: #666; 
            text-align: center; 
        }
        .comparison-container {
            margin-bottom: 30px;
        }
        .tabs {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            border-radius: 5px 5px 0 0;
        }
        .tab-button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 16px;
        }
        .tab-button:hover {
            background-color: #ddd;
        }
        .tab-button.active {
            background-color: #2c5e1a;
            color: white;
        }
        .tab-content {
            display: none;
            padding: 6px 12px;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }
        .positive-change { color: green; }
        .negative-change { color: red; }
    </style>
    <script>
        function openScenario(evt, scenarioName) {
            var i, tabcontent, tabbuttons;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tabbuttons = document.getElementsByClassName("tab-button");
            for (i = 0; i < tabbuttons.length; i++) {
                tabbuttons[i].className = tabbuttons[i].className.replace(" active", "");
            }
            document.getElementById(scenarioName).style.display = "block";
            evt.currentTarget.className += " active";
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>Rapport comparatif des scénarios de croissance forestière</h1>
        <p><strong>Date du rapport:</strong> """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
    </div>
    
    <h2>""" + comparative_analysis['title'] + """</h2>
    <p>""" + comparative_analysis['description'] + """</p>
    
    <h2>Comparaison des métriques</h2>
"""
        
        # Ajouter la comparaison pour chaque métrique
        for metric, data in comparative_analysis['metrics'].items():
            combined_report += f"""
    <div class="comparison-container">
        <h3>{data['name']}</h3>
"""
            
            if 'charts' in comparative_analysis and metric in comparative_analysis['charts']:
                combined_report += f"""
        <div class="plot-container">
            <img src="data:image/png;base64,{comparative_analysis['charts'][metric]}" alt="Comparaison {metric}" style="max-width: 100%;">
        </div>
"""
            
            if 'comparison_text' in data:
                combined_report += f"""
        <p>{data['comparison_text']}</p>
"""
            
            # Ajouter un tableau comparatif
            combined_report += """
        <table>
            <tr>
                <th>Scénario</th>
                <th>Valeur initiale</th>
                <th>Valeur finale</th>
                <th>Changement</th>
                <th>Changement (%)</th>
            </tr>
"""
            
            for scenario, values in data['scenarios'].items():
                change_class = "positive-change" if float(values['change'].replace(',', '.')) >= 0 else "negative-change"
                combined_report += f"""
            <tr>
                <td>{scenario}</td>
                <td>{values['initial']}</td>
                <td>{values['final']}</td>
                <td class="{change_class}">{values['change']}</td>
                <td class="{change_class}">{values['change_percent']}%</td>
            </tr>
"""
            
            combined_report += """
        </table>
    </div>
"""
        
        # Ajouter les onglets pour les rapports individuels
        combined_report += """
    <h2>Rapports détaillés par scénario</h2>
    
    <div class="tabs">
"""
        
        # Ajouter les boutons d'onglet
        for i, scenario in enumerate(individual_reports.keys()):
            active = " active" if i == 0 else ""
            combined_report += f"""
        <button class="tab-button{active}" onclick="openScenario(event, '{scenario.replace(' ', '_')}')">{scenario}</button>
"""
        
        combined_report += """
    </div>
"""
        
        # Ajouter le contenu des onglets
        for i, (scenario, report) in enumerate(individual_reports.items()):
            display = "block" if i == 0 else "none"
            combined_report += f"""
    <div id="{scenario.replace(' ', '_')}" class="tab-content" style="display: {display};">
        {report}
    </div>
"""
        
        # Ajouter le pied de page
        combined_report += """
    <div class="footer">
        <p>Généré par ForestAI - """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
    </div>
</body>
</html>
"""
        
        return combined_report
