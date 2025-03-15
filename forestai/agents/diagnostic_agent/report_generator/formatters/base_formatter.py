# -*- coding: utf-8 -*-
"""
Module de base pour les formateurs de rapports.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseFormatter(ABC):
    """Classe de base abstraite pour tous les formateurs de rapports."""
    
    def __init__(self, templates_dir: Path, output_dir: Path):
        """Initialise le formateur.
        
        Args:
            templates_dir: Répertoire des templates
            output_dir: Répertoire de sortie des rapports
        """
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        
    @abstractmethod
    def generate(self, context: Dict[str, Any], template_name: str, output_path: Optional[Path] = None) -> Path:
        """Génère un rapport dans le format spécifique.
        
        Args:
            context: Contexte de données pour le template
            template_name: Nom du template à utiliser
            output_path: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier généré
        """
        pass
