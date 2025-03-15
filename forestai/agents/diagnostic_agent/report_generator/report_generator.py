# -*- coding: utf-8 -*-
"""
Module principal de génération de rapports de diagnostic forestier.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from enum import Enum
import datetime

from forestai.agents.diagnostic_agent.report_generator.formatters.html_formatter import HTMLFormatter
from forestai.agents.diagnostic_agent.report_generator.formatters.pdf_formatter import PDFFormatter
from forestai.agents.diagnostic_agent.report_generator.formatters.docx_formatter import DOCXFormatter
from forestai.agents.diagnostic_agent.report_generator.formatters.txt_formatter import TXTFormatter
from forestai.agents.diagnostic_agent.report_generator.formatters.json_formatter import JSONFormatter
from forestai.agents.diagnostic_agent.report_generator.formatters.health_section_formatter import HealthSectionFormatter

logger = logging.getLogger(__name__)

class ReportFormat(Enum):
    """Formats de rapport disponibles."""
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    JSON = "json"
    TXT = "txt"

class ReportGenerator:
    """Classe principale responsable de la génération de rapports de diagnostic forestier."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialise le générateur de rapports.
        
        Args:
            config: Configuration optionnelle comprenant:
                - templates_dir: Répertoire des templates de rapports
                - output_dir: Répertoire de sortie des rapports générés
                - company_info: Informations sur la compagnie (logo, nom, etc.)
                - custom_css: Chemin vers un fichier CSS personnalisé
        """
        self.config = config or {}
        
        # Répertoires par défaut
        self.templates_dir = Path(self.config.get("templates_dir", "./templates/diagnostic"))
        self.output_dir = Path(self.config.get("output_dir", "./output/diagnostic"))
        
        # Création des répertoires s'ils n'existent pas
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Informations sur la compagnie
        self.company_info = self.config.get("company_info", {
            "name": "ForestAI",
            "logo": None,
            "contact": "contact@forestai.com",
            "website": "www.forestai.com"
        })
        
        # Chemin vers un CSS personnalisé
        self.custom_css = self.config.get("custom_css")
        
        # Initialisation des formateurs
        self._init_formatters()
        
        # Création des templates par défaut si nécessaire
        self._create_default_templates()
        
        logger.info(f"ReportGenerator initialisé avec templates_dir={self.templates_dir}")
    
    def _init_formatters(self):
        """Initialise les formateurs pour chaque format supporté."""
        self.formatters = {
            ReportFormat.HTML: HTMLFormatter(self.templates_dir, self.output_dir),
            ReportFormat.PDF: PDFFormatter(self.templates_dir, self.output_dir, self.custom_css),
            ReportFormat.DOCX: DOCXFormatter(self.templates_dir, self.output_dir),
            ReportFormat.TXT: TXTFormatter(self.templates_dir, self.output_dir),
            ReportFormat.JSON: JSONFormatter(self.templates_dir, self.output_dir)
        }
        
        # Formateur de section sanitaire spécifique
        self.health_formatter = HealthSectionFormatter()
    
    def _create_default_templates(self):
        """Crée les templates par défaut s'ils n'existent pas déjà."""
        # Template HTML par défaut
        html_template_path = self.templates_dir / "diagnostic_report.html"
        if not html_template_path.exists():
            html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            border-bottom: 1px solid #ddd;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        header .logo {
            max-height: 60px;
        }
        header .title {
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
        }
        header .subtitle {
            font-size: 18px;
            color: #666;
        }
        header .meta {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
        section {
            margin-bottom: 30px;
        }
        h1 {
            font-size: 24px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        h2 {
            font-size: 20px;
            margin-top: 25px;
        }
        h3 {
            font-size: 18px;
            color: #444;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th {
            background-color: #f5f5f5;
            padding: 10px;
            text-align: left;
        }
        td {
            padding: 10px;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .chart {
            margin: 20px 0;
            text-align: center;
        }
        .chart img {
            max-width: 100%;
            height: auto;
        }
        footer {
            margin-top: 50px;
            text-align: center;
            font-size: 14px;
            color: #777;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }
        .summary-box {
            background-color: #f5f7fa;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        .highlight {
            color: #2c3e50;
            font-weight: bold;
        }
        .recommendation {
            background-color: #e8f4f8;
            padding: 15px;
            border-left: 5px solid #3498db;
            margin: 15px 0;
        }
        .warning {
            background-color: #fff5e6;
            padding: 15px;
            border-left: 5px solid #e67e22;
            margin: 15px 0;
        }
        .health-section {
            background-color: #f0f8f0;
            border: 1px solid #c8e6c8;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        .health-section h2 {
            color: #2d682d;
        }
        .health-section h3 {
            color: #3c8c3c;
        }
        @media print {
            body {
                font-size: 12px;
            }
            h1 {
                font-size: 20px;
            }
            h2 {
                font-size: 18px;
            }
            h3 {
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <header>
        {% if company_logo %}
        <div class="logo">
            <img src="{{ company_logo }}" alt="{{ company_name }} Logo">
        </div>
        {% endif %}
        <div class="title">{{ title }}</div>
        <div class="subtitle">{{ subtitle }}</div>
        <div class="meta">
            <div>Date: {{ date }}</div>
            <div>Référence: {{ reference }}</div>
        </div>
    </header>

    <section class="summary">
        <h1>Résumé du diagnostic</h1>
        <div class="summary-box">
            <p>{{ summary }}</p>
            {% if summary_highlights %}
            <ul>
                {% for highlight in summary_highlights %}
                <li class="highlight">{{ highlight }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </section>

    <section class="parcel-info">
        <h1>Informations sur la parcelle</h1>
        <table>
            <tr>
                <th>Identifiant</th>
                <td>{{ parcel_id }}</td>
                <th>Surface</th>
                <td>{{ parcel_area }} ha</td>
            </tr>
            <tr>
                <th>Commune</th>
                <td>{{ parcel_commune }}</td>
                <th>Propriétaire</th>
                <td>{{ parcel_owner }}</td>
            </tr>
            <tr>
                <th>Type de peuplement</th>
                <td>{{ forest_type }}</td>
                <th>Exposition</th>
                <td>{{ parcel_exposition }}</td>
            </tr>
        </table>
    </section>

    {% if health_section %}
    <section class="health">
        {{ health_section|safe }}
    </section>
    {% endif %}

    {% if inventory_analysis %}
    <section class="inventory">
        <h1>Analyse de l'inventaire forestier</h1>
        
        <h2>Vue d'ensemble</h2>
        <p>L'inventaire comprend un total de <strong>{{ inventory_analysis.summary.total_trees }}</strong> arbres répartis sur <strong>{{ inventory_analysis.summary.unique_species }}</strong> espèces différentes.</p>
        
        {% if inventory_analysis.visualizations.species_distribution %}
        <div class="chart">
            <h3>Distribution des espèces</h3>
            <img src="data:image/png;base64,{{ inventory_analysis.visualizations.species_distribution }}" alt="Distribution des espèces">
        </div>
        {% endif %}
        
        {% if inventory_analysis.visualizations.diameter_distribution %}
        <div class="chart">
            <h3>Distribution des diamètres</h3>
            <img src="data:image/png;base64,{{ inventory_analysis.visualizations.diameter_distribution }}" alt="Distribution des diamètres">
        </div>
        {% endif %}
        
        <h2>Analyse par espèce</h2>
        <table>
            <tr>
                <th>Espèce</th>
                <th>Nombre</th>
                <th>Pourcentage</th>
                <th>Diamètre moyen (cm)</th>
                <th>Hauteur moyenne (m)</th>
                <th>Volume moyen (m³)</th>
            </tr>
            {% for species, data in inventory_analysis.species_analysis.items() %}
            <tr>
                <td>{{ species }}</td>
                <td>{{ data.count }}</td>
                <td>{{ "%.1f"|format(data.percentage) }}%</td>
                <td>{{ "%.1f"|format(data.diameter.mean) if data.diameter else "-" }}</td>
                <td>{{ "%.1f"|format(data.height.mean) if data.height else "-" }}</td>
                <td>{{ "%.2f"|format(data.volume.mean) if data.volume else "-" }}</td>
            </tr>
            {% endfor %}
        </table>
        
        {% if inventory_analysis.per_hectare %}
        <h2>Métriques à l'hectare</h2>
        <table>
            <tr>
                <th>Densité (arbres/ha)</th>
                <td>{{ "%.0f"|format(inventory_analysis.per_hectare.density) }}</td>
            </tr>
            <tr>
                <th>Surface terrière (m²/ha)</th>
                <td>{{ "%.1f"|format(inventory_analysis.per_hectare.basal_area) }}</td>
            </tr>
            <tr>
                <th>Volume sur pied (m³/ha)</th>
                <td>{{ "%.1f"|format(inventory_analysis.per_hectare.volume) }}</td>
            </tr>
        </table>
        {% endif %}
        
        {% if inventory_analysis.economic_value %}
        <h2>Valeur économique estimée</h2>
        <table>
            <tr>
                <th>Valeur totale</th>
                <td>{{ "%.0f"|format(inventory_analysis.economic_value.total_value) }} €</td>
            </tr>
            <tr>
                <th>Volume total</th>
                <td>{{ "%.1f"|format(inventory_analysis.economic_value.total_volume) }} m³</td>
            </tr>
            <tr>
                <th>Valeur moyenne par m³</th>
                <td>{{ "%.0f"|format(inventory_analysis.economic_value.mean_value_per_m3) }} €/m³</td>
            </tr>
        </table>
        <p><em>{{ inventory_analysis.economic_value.disclaimer }}</em></p>
        {% endif %}
    </section>
    {% endif %}

    {% if climate_analysis %}
    <section class="climate">
        <h1>Analyse climatique</h1>
        
        <h2>Climat actuel</h2>
        <table>
            <tr>
                <th>Température moyenne annuelle</th>
                <td>{{ "%.1f"|format(climate_analysis.current.temperature_avg) }} °C</td>
            </tr>
            <tr>
                <th>Précipitations annuelles</th>
                <td>{{ "%.0f"|format(climate_analysis.current.precipitation_annual) }} mm</td>
            </tr>
            <tr>
                <th>Indice de sécheresse estival</th>
                <td>{{ "%.1f"|format(climate_analysis.current.drought_index) }}</td>
            </tr>
        </table>
        
        <h2>Projections climatiques (2050)</h2>
        <table>
            <tr>
                <th>Température moyenne annuelle</th>
                <td>{{ "%.1f"|format(climate_analysis.future.temperature_avg) }} °C</td>
                <td>{{ "%+.1f"|format(climate_analysis.future.temperature_avg - climate_analysis.current.temperature_avg) }} °C</td>
            </tr>
            <tr>
                <th>Précipitations annuelles</th>
                <td>{{ "%.0f"|format(climate_analysis.future.precipitation_annual) }} mm</td>
                <td>{{ "%+.0f"|format(climate_analysis.future.precipitation_annual - climate_analysis.current.precipitation_annual) }} mm</td>
            </tr>
            <tr>
                <th>Indice de sécheresse estival</th>
                <td>{{ "%.1f"|format(climate_analysis.future.drought_index) }}</td>
                <td>{{ "%+.1f"|format(climate_analysis.future.drought_index - climate_analysis.current.drought_index) }}</td>
            </tr>
        </table>
        
        {% if climate_analysis.risks %}
        <h2>Risques climatiques identifiés</h2>
        <ul>
            {% for risk in climate_analysis.risks %}
            <li class="{% if risk.level == 'high' %}warning{% else %}recommendation{% endif %}">
                <strong>{{ risk.name }}:</strong> {{ risk.description }}
            </li>
            {% endfor %}
        </ul>
        {% endif %}
    </section>
    {% endif %}

    {% if recommendations %}
    <section class="recommendations">
        <h1>Recommandations</h1>
        
        <h2>Essences recommandées</h2>
        <table>
            <tr>
                <th>Essence</th>
                <th>Adaptation climatique</th>
                <th>Potentiel productif</th>
                <th>Commentaires</th>
            </tr>
            {% for sp in recommendations.species %}
            <tr>
                <td>{{ sp.name }}</td>
                <td>{{ sp.climate_score }}/5</td>
                <td>{{ sp.productivity_score }}/5</td>
                <td>{{ sp.comments }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Interventions sylvicoles proposées</h2>
        <table>
            <tr>
                <th>Opération</th>
                <th>Priorité</th>
                <th>Période</th>
                <th>Description</th>
            </tr>
            {% for op in recommendations.operations %}
            <tr>
                <td>{{ op.name }}</td>
                <td>{{ op.priority }}</td>
                <td>{{ op.timeframe }}</td>
                <td>{{ op.description }}</td>
            </tr>
            {% endfor %}
        </table>
    </section>
    {% endif %}

    <footer>
        <p>Rapport généré par {{ company_name }} - {{ date }}</p>
        <p>{{ company_contact }} | {{ company_website }}</p>
    </footer>
</body>
</html>"""
            
            with open(html_template_path, "w", encoding="utf-8") as f:
                f.write(html_template)
                
        # Template de rapport textuel par défaut
        txt_template_path = self.templates_dir / "diagnostic_report.txt"
        if not txt_template_path.exists():
            txt_template = """RAPPORT DE DIAGNOSTIC FORESTIER
{{ "="*80 }}
{{ title }}
{{ subtitle }}

Date: {{ date }}
Référence: {{ reference }}
{{ "="*80 }}

RÉSUMÉ DU DIAGNOSTIC
{{ "-"*80 }}
{{ summary }}
{% if summary_highlights %}
Points clés:
{% for highlight in summary_highlights %}
- {{ highlight }}
{% endfor %}
{% endif %}

INFORMATIONS SUR LA PARCELLE
{{ "-"*80 }}
Identifiant: {{ parcel_id }}
Surface: {{ parcel_area }} ha
Commune: {{ parcel_commune }}
Propriétaire: {{ parcel_owner }}
Type de peuplement: {{ forest_type }}
Exposition: {{ parcel_exposition }}

{% if health_summary %}
ÉTAT SANITAIRE
{{ "-"*80 }}
{{ health_summary }}

{% endif %}

{% if inventory_analysis %}
ANALYSE DE L'INVENTAIRE FORESTIER
{{ "-"*80 }}
Vue d'ensemble:
L'inventaire comprend un total de {{ inventory_analysis.summary.total_trees }} arbres 
répartis sur {{ inventory_analysis.summary.unique_species }} espèces différentes.

Analyse par espèce:
{% for species, data in inventory_analysis.species_analysis.items() %}
{{ species }}:
  - Nombre: {{ data.count }} ({{ "%.1f"|format(data.percentage) }}%)
  - Diamètre moyen: {{ "%.1f"|format(data.diameter.mean) if data.diameter else "-" }} cm
  - Hauteur moyenne: {{ "%.1f"|format(data.height.mean) if data.height else "-" }} m
  - Volume moyen: {{ "%.2f"|format(data.volume.mean) if data.volume else "-" }} m³
{% endfor %}

{% if inventory_analysis.per_hectare %}
Métriques à l'hectare:
  - Densité: {{ "%.0f"|format(inventory_analysis.per_hectare.density) }} arbres/ha
  - Surface terrière: {{ "%.1f"|format(inventory_analysis.per_hectare.basal_area) }} m²/ha
  - Volume sur pied: {{ "%.1f"|format(inventory_analysis.per_hectare.volume) }} m³/ha
{% endif %}

{% if inventory_analysis.economic_value %}
Valeur économique estimée:
  - Valeur totale: {{ "%.0f"|format(inventory_analysis.economic_value.total_value) }} €
  - Volume total: {{ "%.1f"|format(inventory_analysis.economic_value.total_volume) }} m³
  - Valeur moyenne par m³: {{ "%.0f"|format(inventory_analysis.economic_value.mean_value_per_m3) }} €/m³
{% endif %}
{% endif %}

{% if climate_analysis %}
ANALYSE CLIMATIQUE
{{ "-"*80 }}
Climat actuel:
  - Température moyenne annuelle: {{ "%.1f"|format(climate_analysis.current.temperature_avg) }} °C
  - Précipitations annuelles: {{ "%.0f"|format(climate_analysis.current.precipitation_annual) }} mm
  - Indice de sécheresse estival: {{ "%.1f"|format(climate_analysis.current.drought_index) }}

Projections climatiques (2050):
  - Température moyenne annuelle: {{ "%.1f"|format(climate_analysis.future.temperature_avg) }} °C ({{ "%+.1f"|format(climate_analysis.future.temperature_avg - climate_analysis.current.temperature_avg) }} °C)
  - Précipitations annuelles: {{ "%.0f"|format(climate_analysis.future.precipitation_annual) }} mm ({{ "%+.0f"|format(climate_analysis.future.precipitation_annual - climate_analysis.current.precipitation_annual) }} mm)
  - Indice de sécheresse estival: {{ "%.1f"|format(climate_analysis.future.drought_index) }} ({{ "%+.1f"|format(climate_analysis.future.drought_index - climate_analysis.current.drought_index) }})

{% if climate_analysis.risks %}
Risques climatiques identifiés:
{% for risk in climate_analysis.risks %}
- {{ risk.name }}: {{ risk.description }}
{% endfor %}
{% endif %}
{% endif %}

{% if recommendations %}
RECOMMANDATIONS
{{ "-"*80 }}
Essences recommandées:
{% for sp in recommendations.species %}
- {{ sp.name }} (Adaptation: {{ sp.climate_score }}/5, Productivité: {{ sp.productivity_score }}/5)
  {{ sp.comments }}
{% endfor %}

Interventions sylvicoles proposées:
{% for op in recommendations.operations %}
- {{ op.name }} (Priorité: {{ op.priority }}, Période: {{ op.timeframe }})
  {{ op.description }}
{% endfor %}
{% endif %}

{{ "="*80 }}
Rapport généré par {{ company_name }} - {{ date }}
{{ company_contact }} | {{ company_website }}
"""
            
            with open(txt_template_path, "w", encoding="utf-8") as f:
                f.write(txt_template)
    
    def generate_report(self, diagnostic_data: Dict[str, Any], report_format: Union[ReportFormat, str],
                       template_name: Optional[str] = None, output_path: Optional[Path] = None,
                       health_detail_level: str = "standard") -> Path:
        """Génère un rapport de diagnostic forestier.
        
        Args:
            diagnostic_data: Données du diagnostic
            report_format: Format de sortie du rapport
            template_name: Nom du template à utiliser (optionnel)
            output_path: Chemin du fichier de sortie (optionnel)
            health_detail_level: Niveau de détail pour la section sanitaire ('minimal', 'standard', 'complet')
            
        Returns:
            Chemin du fichier généré
        """
        # Convertir le format de rapport en enum si c'est une chaîne
        if isinstance(report_format, str):
            try:
                report_format = ReportFormat(report_format.lower())
            except ValueError:
                raise ValueError(f"Format de rapport non reconnu: {report_format}")
        
        # Déterminer le template à utiliser
        if template_name is None:
            if report_format == ReportFormat.HTML:
                template_name = "diagnostic_report.html"
            elif report_format == ReportFormat.DOCX:
                template_name = "diagnostic_report.docx"
            elif report_format == ReportFormat.TXT:
                template_name = "diagnostic_report.txt"
            elif report_format == ReportFormat.PDF:
                template_name = "diagnostic_report.html"  # PDF utilise le template HTML
            else:
                template_name = "diagnostic_report.html"
        
        # Préparer les données pour le template
        context = self._prepare_template_context(diagnostic_data, health_detail_level)
        
        # Récupérer le formateur approprié
        formatter = self.formatters.get(report_format)
        if formatter is None:
            raise ValueError(f"Formateur non disponible pour le format: {report_format}")
        
        # Générer le rapport
        return formatter.generate(context, template_name, output_path)
    
    def _prepare_template_context(self, diagnostic_data: Dict[str, Any], health_detail_level: str = "standard") -> Dict[str, Any]:
        """Prépare le contexte pour le template de rapport.
        
        Args:
            diagnostic_data: Données du diagnostic
            health_detail_level: Niveau de détail pour la section sanitaire
            
        Returns:
            Contexte formaté pour le template
        """
        # Extraire et formater les données pour le template
        context = {
            # Informations de base sur le rapport
            "title": diagnostic_data.get("title", "Rapport de diagnostic forestier"),
            "subtitle": diagnostic_data.get("subtitle", "Analyse et recommandations"),
            "date": diagnostic_data.get("date", datetime.datetime.now().strftime("%d/%m/%Y %H:%M")),
            "reference": diagnostic_data.get("reference", ""),
            
            # Informations sur la société
            "company_name": self.company_info.get("name", "ForestAI"),
            "company_logo": self.company_info.get("logo"),
            "company_contact": self.company_info.get("contact", ""),
            "company_website": self.company_info.get("website", ""),
            
            # Informations sur la parcelle
            "parcel_id": diagnostic_data.get("parcel_id", ""),
            "parcel_area": diagnostic_data.get("parcel_area", ""),
            "parcel_commune": diagnostic_data.get("parcel_commune", ""),
            "parcel_owner": diagnostic_data.get("parcel_owner", ""),
            "parcel_exposition": diagnostic_data.get("parcel_exposition", ""),
            "forest_type": diagnostic_data.get("forest_type", ""),
            
            # Résumé du diagnostic
            "summary": diagnostic_data.get("summary", ""),
            "summary_highlights": diagnostic_data.get("summary_highlights", []),
            
            # Analyse détaillée
            "inventory_analysis": diagnostic_data.get("inventory_analysis", {}),
            "climate_analysis": diagnostic_data.get("climate_analysis", {}),
            "recommendations": diagnostic_data.get("recommendations", {}),
        }
        
        # Traitement des données sanitaires si présentes
        health_data = diagnostic_data.get("health_analysis", {})
        if health_data:
            # Formatage selon le type de rapport
            if isinstance(self.formatters.get(ReportFormat.HTML), HTMLFormatter) or isinstance(self.formatters.get(ReportFormat.PDF), PDFFormatter):
                context["health_section"] = self.health_formatter.format_health_section_html(health_data, health_detail_level)
            else:
                context["health_summary"] = self.health_formatter.get_health_summary_for_text(health_data)
                
            # Ajouter des points importants au résumé si nécessaire
            if health_data.get("overall_health_score", 0) < 5 and "summary_highlights" in context:
                context["summary_highlights"].append(f"État sanitaire préoccupant: {health_data.get('health_status', 'Problèmes sanitaires détectés')}")
                
            # Intégrer les recommandations sanitaires aux recommandations générales
            if "recommendations" in health_data and "recommendations" in context:
                health_recs = health_data["recommendations"]
                if isinstance(health_recs, list) and "operations" in context["recommendations"]:
                    for rec in health_recs:
                        if isinstance(rec, dict) and "title" in rec:
                            context["recommendations"]["operations"].append({
                                "name": f"[Sanitaire] {rec.get('title', 'Action sanitaire')}",
                                "priority": rec.get("priority", "Normale"),
                                "timeframe": rec.get("timeframe", "Dès que possible"),
                                "description": rec.get("description", "")
                            })
        
        return context
    
    def get_supported_formats(self) -> List[ReportFormat]:
        """Retourne la liste des formats de rapport supportés.
        
        Returns:
            Liste des formats supportés
        """
        return list(ReportFormat)
