# -*- coding: utf-8 -*-
"""
Module du formateur PDF pour les rapports de diagnostic.
"""

import logging
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from weasyprint import HTML, CSS

from forestai.agents.diagnostic_agent.report_generator.formatters.html_formatter import HTMLFormatter

logger = logging.getLogger(__name__)

class PDFFormatter(HTMLFormatter):
    """Formateur de rapports au format PDF (utilise HTML comme intermédiaire)."""
    
    def __init__(self, templates_dir: Path, output_dir: Path, custom_css: Optional[Path] = None):
        """Initialise le formateur PDF.
        
        Args:
            templates_dir: Répertoire des templates
            output_dir: Répertoire de sortie des rapports
            custom_css: Chemin vers un fichier CSS personnalisé (optionnel)
        """
        super().__init__(templates_dir, output_dir)
        self.custom_css = custom_css
    
    def generate(self, context: Dict[str, Any], template_name: str, output_path: Optional[Path] = None) -> Path:
        """Génère un rapport au format PDF.
        
        Args:
            context: Contexte de données pour le template
            template_name: Nom du template à utiliser
            output_path: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier généré
        """
        # Générer d'abord le HTML dans un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html:
            temp_html_path = Path(temp_html.name)
            super().generate(context, template_name, temp_html_path)
        
        # Déterminer le chemin de sortie si non spécifié
        if output_path is None:
            parcel_id = context.get("parcel_id", "unknown")
            timestamp = context.get("date", "").replace(" ", "_").replace(":", "").replace("/", "")
            output_path = self.output_dir / f"diagnostic_{parcel_id}_{timestamp}.pdf"
        
        # Convertir le HTML en PDF avec WeasyPrint
        html = HTML(filename=str(temp_html_path))
        
        # CSS personnalisé si spécifié
        css_files: List[CSS] = []
        if self.custom_css is not None:
            css_files.append(CSS(filename=str(self.custom_css)))
        
        # Générer le PDF
        html.write_pdf(str(output_path), stylesheets=css_files or None)
        
        # Supprimer le fichier HTML temporaire
        temp_html_path.unlink()
        
        logger.info(f"Rapport PDF généré: {output_path}")
        return output_path
