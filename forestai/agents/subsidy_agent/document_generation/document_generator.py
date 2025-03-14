"""
Module définissant la classe principale pour la génération de documents liés aux subventions.

Cette classe sert d'interface pour générer différents types de documents
en déléguant le travail aux générateurs spécialisés.
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from forestai.core.utils.logging_config import LoggingConfig
from .pdf_generator import PDFGenerator
from .html_generator import HTMLGenerator
from .docx_generator import DOCXGenerator


class SubsidyDocumentGenerator:
    """
    Générateur de documents pour les subventions forestières.
    
    Cette classe coordonne la génération de différents types de documents :
    - Dossiers de demande de subvention
    - Rapports d'analyse d'éligibilité
    - Fiches de synthèse des subventions disponibles
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le générateur de documents.
        
        Args:
            config: Dictionnaire de configuration avec les paramètres suivants:
                - templates_dir: Répertoire contenant les templates Jinja2
                - output_dir: Répertoire où enregistrer les documents générés
                - logo_path: Chemin vers le logo à inclure dans les documents
        """
        self.config = config
        
        # Configurer les chemins
        self.templates_dir = config.get("templates_dir", "forestai/agents/subsidy_agent/templates")
        self.output_dir = config.get("output_dir", "data/outputs/subsidies")
        self.logo_path = config.get("logo_path", "forestai/agents/subsidy_agent/templates/logo.png")
        
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configuration du logging
        self.logger = LoggingConfig.get_instance().get_logger(
            self.__class__.__name__,
            module=__name__
        )
        self.logger.info("Initialisation du générateur de documents pour subventions")
        
        # Initialiser les générateurs spécifiques
        self.pdf_generator = PDFGenerator(config)
        self.html_generator = HTMLGenerator(config)
        self.docx_generator = DOCXGenerator(config)
    
    def generate_application(
        self,
        subsidy: Dict[str, Any],
        parcel_data: Dict[str, Any],
        project_data: Dict[str, Any],
        applicant_data: Dict[str, Any],
        output_format: str = "pdf",
        output_path: Optional[str] = None
    ) -> str:
        """
        Génère un dossier de demande de subvention.
        
        Args:
            subsidy: Informations sur la subvention
            parcel_data: Données sur la parcelle
            project_data: Données sur le projet
            applicant_data: Informations sur le demandeur
            output_format: Format de sortie ("pdf", "docx" ou "html")
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        self.logger.info(f"Génération d'un dossier de demande pour {subsidy['title']} au format {output_format}")
        
        # Créer le chemin de sortie si non spécifié
        if output_path is None:
            import re
            safe_title = re.sub(r'[^\w\-_.]', '_', subsidy['title'])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"demande_{safe_title}_{timestamp}.{output_format}")
        
        # Préparer les données pour le template
        template_data = {
            "subsidy": subsidy,
            "parcel": parcel_data,
            "project": project_data,
            "applicant": applicant_data,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "logo_path": self.logo_path if os.path.exists(self.logo_path) else None
        }
        
        # Générer le document selon le format demandé
        if output_format.lower() == "pdf":
            return self.pdf_generator.generate_application(template_data, output_path)
        elif output_format.lower() == "html":
            return self.html_generator.generate_application(template_data, output_path)
        elif output_format.lower() == "docx":
            return self.docx_generator.generate_application(template_data, output_path)
        else:
            raise ValueError(f"Format non supporté: {output_format}")
    
    def generate_eligibility_report(
        self,
        eligible_subsidies: List[Dict[str, Any]],
        parcel_data: Dict[str, Any],
        project_data: Dict[str, Any],
        output_format: str = "pdf",
        output_path: Optional[str] = None
    ) -> str:
        """
        Génère un rapport d'analyse d'éligibilité aux subventions.
        
        Args:
            eligible_subsidies: Liste des subventions éligibles avec scores et explications
            parcel_data: Données sur la parcelle
            project_data: Données sur le projet
            output_format: Format de sortie ("pdf", "docx" ou "html")
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        self.logger.info(f"Génération d'un rapport d'éligibilité pour {len(eligible_subsidies)} subventions")
        
        # Créer le chemin de sortie si non spécifié
        if output_path is None:
            import re
            parcel_id = re.sub(r'[^\w\-_.]', '_', str(parcel_data.get("id", "parcelle")))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"eligibilite_{parcel_id}_{timestamp}.{output_format}")
        
        # Préparer les données pour le template
        template_data = {
            "eligible_subsidies": eligible_subsidies,
            "parcel": parcel_data,
            "project": project_data,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "logo_path": self.logo_path if os.path.exists(self.logo_path) else None
        }
        
        # Générer le document selon le format demandé
        if output_format.lower() == "pdf":
            return self.pdf_generator.generate_eligibility_report(template_data, output_path)
        elif output_format.lower() == "html":
            return self.html_generator.generate_eligibility_report(template_data, output_path)
        elif output_format.lower() == "docx":
            return self.docx_generator.generate_eligibility_report(template_data, output_path)
        else:
            raise ValueError(f"Format non supporté: {output_format}")
    
    def generate_subsidies_summary(
        self,
        subsidies: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
        output_format: str = "pdf",
        output_path: Optional[str] = None
    ) -> str:
        """
        Génère une synthèse des subventions disponibles.
        
        Args:
            subsidies: Liste des subventions à inclure dans la synthèse
            filters: Filtres appliqués pour obtenir ces subventions
            output_format: Format de sortie ("pdf", "docx" ou "html")
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        self.logger.info(f"Génération d'une synthèse pour {len(subsidies)} subventions")
        
        # Créer le chemin de sortie si non spécifié
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"synthese_subventions_{timestamp}.{output_format}")
        
        # Préparer les données pour le template
        template_data = {
            "subsidies": subsidies,
            "filters": filters or {},
            "count": len(subsidies),
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "logo_path": self.logo_path if os.path.exists(self.logo_path) else None
        }
        
        # Générer le document selon le format demandé
        if output_format.lower() == "pdf":
            return self.pdf_generator.generate_subsidies_summary(template_data, output_path)
        elif output_format.lower() == "html":
            return self.html_generator.generate_subsidies_summary(template_data, output_path)
        elif output_format.lower() == "docx":
            return self.docx_generator.generate_subsidies_summary(template_data, output_path)
        else:
            raise ValueError(f"Format non supporté: {output_format}")
