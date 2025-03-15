# -*- coding: utf-8 -*-
"""
Module du formateur HTML pour les rapports de diagnostic.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import jinja2

from forestai.agents.diagnostic_agent.report_generator.formatters.base_formatter import BaseFormatter

logger = logging.getLogger(__name__)

class HTMLFormatter(BaseFormatter):
    """Formateur de rapports au format HTML."""
    
    def __init__(self, templates_dir: Path, output_dir: Path):
        """Initialise le formateur HTML.
        
        Args:
            templates_dir: Répertoire des templates
            output_dir: Répertoire de sortie des rapports
        """
        super().__init__(templates_dir, output_dir)
        
        # Initialisation du moteur de templates Jinja2
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    def generate(self, context: Dict[str, Any], template_name: str, output_path: Optional[Path] = None) -> Path:
        """Génère un rapport au format HTML.
        
        Args:
            context: Contexte de données pour le template
            template_name: Nom du template à utiliser
            output_path: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier généré
        """
        # Charger le template
        template = self.jinja_env.get_template(template_name)
        
        # Générer le HTML
        html_content = template.render(**context)
        
        # Déterminer le chemin de sortie si non spécifié
        if output_path is None:
            parcel_id = context.get("parcel_id", "unknown")
            timestamp = context.get("date", "").replace(" ", "_").replace(":", "").replace("/", "")
            output_path = self.output_dir / f"diagnostic_{parcel_id}_{timestamp}.html"
        
        # Écrire le fichier HTML
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Rapport HTML généré: {output_path}")
        return output_path
