# -*- coding: utf-8 -*-
"""
Module de génération de rapports pour le DiagnosticAgent.

Ce module permet de générer des rapports forestiers au format PDF, HTML, etc.
à partir des diagnostics et plans de gestion produits par le DiagnosticAgent.
"""

import logging
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import datetime
import jinja2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Mode non-interactif
import seaborn as sns
import base64
import io

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
            template = self.jinja_env.get_template('diagnostic_report.html')
            if template is None:
                # Si le modèle n'existe pas, créer un modèle par défaut
                template_str = self._create_default_diagnostic_template()
                template = self.jinja_env.from_string(template_str)
            
            # Générer des graphiques
            graphs = self._generate_diagnostic_graphs(diagnostic)
            
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