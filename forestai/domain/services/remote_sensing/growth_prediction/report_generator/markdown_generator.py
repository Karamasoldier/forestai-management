#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de génération de rapports au format Markdown.

Ce module contient une classe spécialisée pour générer des rapports 
de prédiction de croissance forestière au format Markdown.
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

class MarkdownReportGenerator(BaseReportGenerator):
    """Générateur de rapports au format Markdown pour les prédictions de croissance forestière."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialise le générateur de rapports Markdown.
        
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
        Crée le template Markdown par défaut s'il n'existe pas déjà.
        """
        template_path = os.path.join(self.template_dir, 'growth_report_markdown.md')
        
        if not os.path.exists(template_path):
            markdown_template = """# Rapport de prédiction de croissance forestière

## Informations générales

- **Parcelle**: {{ parcel_id }}
- **Date du rapport**: {{ report_date }}
- **Période de prédiction**: {{ prediction_start_date }} à {{ prediction_end_date }}

## Résumé des prédictions

{% for metric, values in summary.items() %}
### {{ metric | replace('_', ' ') | title }}
- **Valeur initiale**: {{ values.initial }}
- **Valeur finale prédite**: {{ values.final }}
- **Changement**: {{ values.change }} ({{ values.change_percent }}%)
{% endfor %}

## Analyse détaillée

{% for metric in metrics %}
### {{ metric | replace('_', ' ') | title }}

![Graphique {{ metric }}]({{ plots[metric] }})

{{ analysis[metric] }}

{% endfor %}

## Facteurs d'influence

{% for factor in factors %}
- **{{ factor.name }}**: {{ factor.description }}
{% endfor %}

## Recommandations

{% for recommendation in recommendations %}
- **{{ recommendation.category }}**: {{ recommendation.description }}
{% endfor %}

## Métadonnées du modèle

- **Type de modèle**: {{ model_type }}
- **Précision du modèle**: {{ model_accuracy }}
- **Dernière mise à jour**: {{ last_updated }}

{% if notes %}
## Notes
{{ notes }}
{% endif %}
"""
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            
            # Écrire le template
            with open(template_path, 'w') as f:
                f.write(markdown_template)
            
            self._logger.info(f"Template Markdown par défaut créé: {template_path}")
    
    def generate_report(self, prediction_result: GrowthPredictionResult, 
                        additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Génère un rapport Markdown pour les prédictions de croissance forestière.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            additional_context: Contexte supplémentaire à inclure dans le rapport
            
        Returns:
            Contenu du rapport au format Markdown
        """
        # Vérifier que le template existe
        template_path = os.path.join(self.template_dir, 'growth_report_markdown.md')
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
        template = self.env.get_template('growth_report_markdown.md')
        
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
            Rapport combiné au format Markdown
        """
        # Créer l'en-tête du rapport combiné
        combined_report = "# Rapport comparatif des scénarios de croissance forestière\n\n"
        
        # Ajouter l'analyse comparative
        combined_report += f"## {comparative_analysis['title']}\n\n"
        combined_report += f"{comparative_analysis['description']}\n\n"
        
        # Ajouter la comparaison pour chaque métrique
        combined_report += "## Comparaison des métriques\n\n"
        
        for metric, data in comparative_analysis['metrics'].items():
            combined_report += f"### {data['name']}\n\n"
            
            if 'charts' in comparative_analysis and metric in comparative_analysis['charts']:
                combined_report += f"![Comparaison {metric}]({comparative_analysis['charts'][metric]})\n\n"
            
            if 'comparison_text' in data:
                combined_report += f"{data['comparison_text']}\n\n"
            
            # Ajouter un tableau comparatif
            combined_report += "| Scénario | Valeur initiale | Valeur finale | Changement | Changement (%) |\n"
            combined_report += "|---------|----------------|--------------|------------|---------------|\n"
            
            for scenario, values in data['scenarios'].items():
                combined_report += f"| {scenario} | {values['initial']} | {values['final']} | {values['change']} | {values['change_percent']}% |\n"
            
            combined_report += "\n"
        
        # Ajouter les rapports individuels
        combined_report += "## Rapports détaillés par scénario\n\n"
        
        for scenario, report in individual_reports.items():
            combined_report += f"### Scénario: {scenario}\n\n"
            combined_report += f"<details>\n<summary>Voir le rapport détaillé</summary>\n\n{report}\n\n</details>\n\n"
        
        return combined_report
