# -*- coding: utf-8 -*-
"""
Module de génération de rapports pour le DiagnosticAgent.

Ce module permet de générer des rapports forestiers au format PDF, HTML, etc.
à partir des diagnostics et plans de gestion produits par le DiagnosticAgent.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import datetime
import jinja2
from io import BytesIO

from forestai.agents.diagnostic_agent.templates import (
    create_default_diagnostic_template,
    create_default_management_plan_template
)
from forestai.agents.diagnostic_agent.graph_generators import (
    generate_diagnostic_graphs,
    generate_management_plan_graphs
)

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Générateur de rapports forestiers."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialise le générateur de rapports.
        
        Args:
            templates_dir: Répertoire des modèles de rapports
        """
        self.templates_dir = templates_dir or Path("templates/diagnostic")
        
        # S'assurer que le répertoire des modèles existe
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser l'environnement Jinja
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Ajouter des filtres personnalisés
        self.jinja_env.filters['format_date'] = lambda d: d.strftime('%d/%m/%Y') if isinstance(d, datetime.datetime) else d
        self.jinja_env.filters['format_number'] = lambda n: f"{n:,.2f}" if isinstance(n, (int, float)) else n
        self.jinja_env.filters['format_percent'] = lambda n: f"{n:.1f}%" if isinstance(n, (int, float)) else n
        
        logger.debug(f"ReportGenerator initialisé avec templates_dir={self.templates_dir}")
    
    def generate_diagnostic_report_html(self, diagnostic: Dict[str, Any], parcel_data: Optional[Dict[str, Any]] = None) -> str:
        """Génère un rapport de diagnostic forestier au format HTML.
        
        Args:
            diagnostic: Données du diagnostic forestier
            parcel_data: Données supplémentaires sur la parcelle (optionnel)
            
        Returns:
            Rapport HTML
        """
        try:
            # Charger le modèle
            try:
                template = self.jinja_env.get_template('diagnostic_report.html')
            except jinja2.exceptions.TemplateNotFound:
                # Si le modèle n'existe pas, créer un modèle par défaut
                template_str = create_default_diagnostic_template()
                template = self.jinja_env.from_string(template_str)
            
            # Générer des graphiques
            graphs = generate_diagnostic_graphs(diagnostic)
            
            # Préparer le contexte
            context = {
                'diagnostic': diagnostic,
                'parcel_data': parcel_data or {},
                'graphs': graphs,
                'generation_date': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                'report_id': f"DIAG-{diagnostic.get('parcel_id', 'UNKNOWN')}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Générer le HTML
            html = template.render(**context)
            
            return html
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport HTML: {str(e)}")
            # Générer un rapport d'erreur simple
            error_html = f"""<html>
            <head><title>Erreur de génération du rapport</title></head>
            <body>
                <h1>Erreur lors de la génération du rapport</h1>
                <p>Une erreur est survenue: {str(e)}</p>
                <h2>Données de diagnostic brutes:</h2>
                <pre>{json.dumps(diagnostic, indent=2)}</pre>
            </body>
            </html>"""
            return error_html
    
    def generate_diagnostic_report_pdf(self, diagnostic: Dict[str, Any], parcel_data: Optional[Dict[str, Any]] = None) -> bytes:
        """Génère un rapport de diagnostic forestier au format PDF.
        
        Args:
            diagnostic: Données du diagnostic forestier
            parcel_data: Données supplémentaires sur la parcelle (optionnel)
            
        Returns:
            Contenu PDF en bytes
        """
        try:
            # Générer d'abord le HTML
            html = self.generate_diagnostic_report_html(diagnostic, parcel_data)
            
            # Convertir HTML en PDF avec WeasyPrint
            import weasyprint
            pdf = weasyprint.HTML(string=html).write_pdf()
            
            return pdf
            
        except ImportError:
            logger.warning("WeasyPrint non disponible, tentative avec pdfkit")
            try:
                # Essayer avec pdfkit comme alternative
                import pdfkit
                html = self.generate_diagnostic_report_html(diagnostic, parcel_data)
                pdf = pdfkit.from_string(html, False)
                return pdf
                
            except ImportError:
                logger.error("Ni WeasyPrint ni pdfkit ne sont disponibles")
                # Retourner une erreur en PDF généré avec reportlab
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                c.drawString(100, 800, "Erreur de génération du rapport")
                c.drawString(100, 780, "Aucune librairie de conversion HTML vers PDF n'est disponible")
                c.drawString(100, 760, "Veuillez installer WeasyPrint ou pdfkit")
                c.save()
                pdf = buffer.getvalue()
                buffer.close()
                return pdf
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport PDF: {str(e)}")
            # Générer un PDF d'erreur avec reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 800, "Erreur de génération du rapport")
            c.drawString(100, 780, f"Erreur: {str(e)}")
            c.save()
            pdf = buffer.getvalue()
            buffer.close()
            return pdf
    
    def generate_management_plan_report_html(self, plan: Dict[str, Any], diagnostic: Optional[Dict[str, Any]] = None) -> str:
        """Génère un rapport de plan de gestion au format HTML.
        
        Args:
            plan: Données du plan de gestion
            diagnostic: Données du diagnostic associé (optionnel)
            
        Returns:
            Rapport HTML
        """
        try:
            # Charger le modèle
            try:
                template = self.jinja_env.get_template('management_plan_report.html')
            except jinja2.exceptions.TemplateNotFound:
                # Si le modèle n'existe pas, créer un modèle par défaut
                template_str = create_default_management_plan_template()
                template = self.jinja_env.from_string(template_str)
            
            # Générer des graphiques
            graphs = generate_management_plan_graphs(plan, diagnostic)
            
            # Préparer le contexte
            context = {
                'plan': plan,
                'diagnostic': diagnostic or {},
                'graphs': graphs,
                'generation_date': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                'report_id': f"PLAN-{plan.get('parcel_id', 'UNKNOWN')}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Générer le HTML
            html = template.render(**context)
            
            return html
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport HTML: {str(e)}")
            # Générer un rapport d'erreur simple
            error_html = f"""<html>
            <head><title>Erreur de génération du rapport</title></head>
            <body>
                <h1>Erreur lors de la génération du rapport</h1>
                <p>Une erreur est survenue: {str(e)}</p>
                <h2>Données du plan de gestion brutes:</h2>
                <pre>{json.dumps(plan, indent=2)}</pre>
            </body>
            </html>"""
            return error_html
    
    def generate_management_plan_report_pdf(self, plan: Dict[str, Any], diagnostic: Optional[Dict[str, Any]] = None) -> bytes:
        """Génère un rapport de plan de gestion au format PDF.
        
        Args:
            plan: Données du plan de gestion
            diagnostic: Données du diagnostic associé (optionnel)
            
        Returns:
            Contenu PDF en bytes
        """
        try:
            # Générer d'abord le HTML
            html = self.generate_management_plan_report_html(plan, diagnostic)
            
            # Convertir HTML en PDF avec WeasyPrint
            import weasyprint
            pdf = weasyprint.HTML(string=html).write_pdf()
            
            return pdf
            
        except ImportError:
            logger.warning("WeasyPrint non disponible, tentative avec pdfkit")
            try:
                # Essayer avec pdfkit comme alternative
                import pdfkit
                html = self.generate_management_plan_report_html(plan, diagnostic)
                pdf = pdfkit.from_string(html, False)
                return pdf
                
            except ImportError:
                logger.error("Ni WeasyPrint ni pdfkit ne sont disponibles")
                # Retourner une erreur en PDF généré avec reportlab
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                c.drawString(100, 800, "Erreur de génération du rapport")
                c.drawString(100, 780, "Aucune librairie de conversion HTML vers PDF n'est disponible")
                c.drawString(100, 760, "Veuillez installer WeasyPrint ou pdfkit")
                c.save()
                pdf = buffer.getvalue()
                buffer.close()
                return pdf
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport PDF: {str(e)}")
            # Générer un PDF d'erreur avec reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 800, "Erreur de génération du rapport")
            c.drawString(100, 780, f"Erreur: {str(e)}")
            c.save()
            pdf = buffer.getvalue()
            buffer.close()
            return pdf
