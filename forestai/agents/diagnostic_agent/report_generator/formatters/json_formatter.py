# -*- coding: utf-8 -*-
"""
Module du formateur JSON pour les rapports de diagnostic.
"""

import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path

from forestai.agents.diagnostic_agent.report_generator.formatters.base_formatter import BaseFormatter

logger = logging.getLogger(__name__)

class JSONFormatter(BaseFormatter):
    """Formateur de rapports au format JSON."""
    
    def __init__(self, templates_dir: Path, output_dir: Path):
        """Initialise le formateur JSON.
        
        Args:
            templates_dir: Répertoire des templates (non utilisé pour JSON)
            output_dir: Répertoire de sortie des rapports
        """
        super().__init__(templates_dir, output_dir)
    
    def generate(self, context: Dict[str, Any], template_name: str, output_path: Optional[Path] = None) -> Path:
        """Génère un rapport au format JSON.
        
        Args:
            context: Contexte de données pour le template (utilisé directement)
            template_name: Nom du template à utiliser (ignoré pour JSON)
            output_path: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier généré
        """
        # Déterminer le chemin de sortie si non spécifié
        if output_path is None:
            parcel_id = context.get("parcel_id", "unknown")
            timestamp = context.get("date", "").replace(" ", "_").replace(":", "").replace("/", "")
            output_path = self.output_dir / f"diagnostic_{parcel_id}_{timestamp}.json"
        
        # Sérialisation en JSON (avec indentation pour lisibilité)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Rapport JSON généré: {output_path}")
        return output_path
