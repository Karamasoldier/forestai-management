# -*- coding: utf-8 -*-
"""
Module principal coordonnant la génération de rapports forestiers.

Ce module fournit une interface unifiée pour générer des rapports de diagnostic
et des plans de gestion dans différents formats (PDF, HTML, DOCX, TXT, JSON).
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from enum import Enum
import datetime

from forestai.agents.diagnostic_agent.report_generator.report_generator import ReportGenerator, ReportFormat
from forestai.agents.diagnostic_agent.graph_generators import (
    generate_diagnostic_graphs,
    generate_management_plan_graphs
)
from forestai.core.utils.logging_config import setup_logger

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Types de rapports disponibles."""
    DIAGNOSTIC = "diagnostic"
    MANAGEMENT_PLAN = "management_plan"
    INVENTORY = "inventory"
    CLIMATE = "climate"
    SUBSIDY = "subsidy"
    HEALTH = "health"  # Nouveau type pour les rapports sanitaires spécifiques

class ReportManager:
    """
    Classe principale pour gérer la génération des rapports forestiers.
    
    Cette classe coordonne l'utilisation des différents formatters pour
    produire des rapports complets et offre une interface unifiée pour
    leur génération.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialise le gestionnaire de rapports.
        
        Args:
            config: Configuration optionnelle contenant:
                - templates_dir: Répertoire des templates
                - output_dir: Répertoire de sortie des rapports
                - company_info: Informations sur la compagnie
                - custom_css: CSS personnalisé pour les rapports
        """
        self.config = config or {}
        
        # Initialiser le générateur de rapports
        self.report_generator = ReportGenerator(self.config)
        
        # Configuration des dossiers
        self.templates_dir = Path(self.config.get("templates_dir", "./templates/diagnostic"))
        self.output_dir = Path(self.config.get("output_dir", "./output/diagnostic"))
        
        # S'assurer que les répertoires existent
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration de la journalisation
        setup_logger()
        
        logger.info(f"ReportManager initialisé avec succès. Templates: {self.templates_dir}, Output: {self.output_dir}")
    
    def generate_report(
        self,
        report_type: Union[ReportType, str],
        data: Dict[str, Any],
        formats: List[Union[ReportFormat, str]] = None,
        additional_data: Dict[str, Any] = None,
        output_dir: Optional[Path] = None,
        filename_prefix: Optional[str] = None,
        health_detail_level: str = "standard"  # Nouveau paramètre pour le niveau de détail sanitaire
    ) -> Dict[ReportFormat, Path]:
        """
        Génère des rapports dans les formats spécifiés.
        
        Args:
            report_type: Type de rapport (DIAGNOSTIC, MANAGEMENT_PLAN, etc.)
            data: Données pour le rapport
            formats: Liste des formats à générer (PDF, HTML, DOCX, TXT, JSON)
            additional_data: Données additionnelles pour le rapport
            output_dir: Répertoire de sortie personnalisé
            filename_prefix: Préfixe personnalisé pour les noms de fichiers
            health_detail_level: Niveau de détail pour les sections sanitaires ('minimal', 'standard', 'complet')
            
        Returns:
            Dictionnaire des chemins de fichiers générés par format
        """
        # Convertir le type de rapport en enum si c'est une chaîne
        if isinstance(report_type, str):
            try:
                report_type = ReportType(report_type.lower())
            except ValueError:
                raise ValueError(f"Type de rapport non reconnu: {report_type}")
        
        # Formats par défaut si non spécifiés
        if formats is None:
            formats = [ReportFormat.PDF, ReportFormat.HTML]
        
        # Convertir les formats en enum si nécessaire
        normalized_formats = []
        for fmt in formats:
            if isinstance(fmt, str):
                try:
                    normalized_formats.append(ReportFormat(fmt.lower()))
                except ValueError:
                    logger.warning(f"Format non reconnu ignoré: {fmt}")
            else:
                normalized_formats.append(fmt)
        
        # Répertoire de sortie
        output_directory = output_dir or self.output_dir
        output_directory.mkdir(parents=True, exist_ok=True)
        
        # Générer un identifiant pour le rapport
        report_id = self._generate_report_id(report_type, data)
        
        # Préfixe pour les noms de fichiers
        prefix = filename_prefix or f"{report_type.value}_{report_id}"
        
        # Enrichir les données si nécessaire
        enriched_data = self._enrich_data(report_type, data, additional_data)
        
        # Générer les rapports dans chaque format
        generated_files = {}
        
        for report_format in normalized_formats:
            try:
                # Déterminer le nom de fichier
                filename = f"{prefix}.{report_format.value}"
                output_path = output_directory / filename
                
                # Générer le rapport
                report_path = self.report_generator.generate_report(
                    enriched_data,
                    report_format,
                    None,  # Utiliser le template par défaut pour le format
                    output_path,
                    health_detail_level  # Transmettre le niveau de détail sanitaire
                )
                
                generated_files[report_format] = report_path
                logger.info(f"Rapport {report_type.value} généré au format {report_format.value}: {report_path}")
            
            except Exception as e:
                logger.error(f"Erreur lors de la génération du rapport {report_type.value} au format {report_format.value}: {str(e)}")
        
        return generated_files
    
    def generate_diagnostic_report(
        self,
        diagnostic_data: Dict[str, Any],
        formats: List[Union[ReportFormat, str]] = None,
        parcel_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        filename_prefix: Optional[str] = None,
        health_detail_level: str = "standard"
    ) -> Dict[ReportFormat, Path]:
        """
        Génère un rapport de diagnostic forestier.
        
        Args:
            diagnostic_data: Données du diagnostic
            formats: Formats de sortie désirés
            parcel_data: Données supplémentaires sur la parcelle
            output_dir: Répertoire de sortie personnalisé
            filename_prefix: Préfixe personnalisé pour les noms de fichiers
            health_detail_level: Niveau de détail pour les sections sanitaires
            
        Returns:
            Dictionnaire des chemins de fichiers générés par format
        """
        return self.generate_report(
            ReportType.DIAGNOSTIC,
            diagnostic_data,
            formats,
            parcel_data,
            output_dir,
            filename_prefix,
            health_detail_level
        )
    
    def generate_management_plan_report(
        self,
        plan_data: Dict[str, Any],
        formats: List[Union[ReportFormat, str]] = None,
        diagnostic_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        filename_prefix: Optional[str] = None,
        health_detail_level: str = "standard"
    ) -> Dict[ReportFormat, Path]:
        """
        Génère un rapport de plan de gestion forestière.
        
        Args:
            plan_data: Données du plan de gestion
            formats: Formats de sortie désirés
            diagnostic_data: Données du diagnostic associé
            output_dir: Répertoire de sortie personnalisé
            filename_prefix: Préfixe personnalisé pour les noms de fichiers
            health_detail_level: Niveau de détail pour les sections sanitaires
            
        Returns:
            Dictionnaire des chemins de fichiers générés par format
        """
        return self.generate_report(
            ReportType.MANAGEMENT_PLAN,
            plan_data,
            formats,
            diagnostic_data,
            output_dir,
            filename_prefix,
            health_detail_level
        )
    
    def generate_inventory_report(
        self,
        inventory_data: Dict[str, Any],
        formats: List[Union[ReportFormat, str]] = None,
        parcel_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        filename_prefix: Optional[str] = None,
        health_detail_level: str = "minimal"  # Par défaut minimal pour les rapports d'inventaire
    ) -> Dict[ReportFormat, Path]:
        """
        Génère un rapport d'inventaire forestier.
        
        Args:
            inventory_data: Données d'inventaire
            formats: Formats de sortie désirés
            parcel_data: Données sur la parcelle
            output_dir: Répertoire de sortie personnalisé
            filename_prefix: Préfixe personnalisé pour les noms de fichiers
            health_detail_level: Niveau de détail pour les sections sanitaires
            
        Returns:
            Dictionnaire des chemins de fichiers générés par format
        """
        return self.generate_report(
            ReportType.INVENTORY,
            inventory_data,
            formats,
            parcel_data,
            output_dir,
            filename_prefix,
            health_detail_level
        )
    
    def generate_health_report(
        self,
        health_data: Dict[str, Any],
        formats: List[Union[ReportFormat, str]] = None,
        parcel_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        filename_prefix: Optional[str] = None
    ) -> Dict[ReportFormat, Path]:
        """
        Génère un rapport sanitaire spécifique.
        
        Args:
            health_data: Données sanitaires
            formats: Formats de sortie désirés
            parcel_data: Données sur la parcelle
            output_dir: Répertoire de sortie personnalisé
            filename_prefix: Préfixe personnalisé pour les noms de fichiers
            
        Returns:
            Dictionnaire des chemins de fichiers générés par format
        """
        return self.generate_report(
            ReportType.HEALTH,
            health_data,
            formats,
            parcel_data,
            output_dir,
            filename_prefix,
            "complet"  # Toujours utiliser le niveau complet pour les rapports sanitaires spécifiques
        )
    
    def _generate_report_id(self, report_type: ReportType, data: Dict[str, Any]) -> str:
        """
        Génère un identifiant unique pour le rapport.
        
        Args:
            report_type: Type de rapport
            data: Données du rapport
            
        Returns:
            Identifiant unique
        """
        # Récupérer l'identifiant de la parcelle ou utiliser "unknown"
        parcel_id = data.get("parcel_id", "unknown")
        
        # Timestamp actuel au format YYYYMMDD_HHMMSS
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{parcel_id}_{timestamp}"
    
    def _enrich_data(
        self,
        report_type: ReportType,
        data: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enrichit les données pour le rapport avec des informations complémentaires.
        
        Args:
            report_type: Type de rapport
            data: Données principales
            additional_data: Données additionnelles
            
        Returns:
            Données enrichies pour le rapport
        """
        enriched_data = data.copy()
        
        # Ajouter les données additionnelles si présentes
        if additional_data:
            if report_type == ReportType.DIAGNOSTIC:
                enriched_data["parcel_data"] = additional_data
            elif report_type == ReportType.MANAGEMENT_PLAN:
                enriched_data["diagnostic_data"] = additional_data
            elif report_type == ReportType.HEALTH:
                # Pour les rapports sanitaires, intégrer les données de parcelle
                for key, value in additional_data.items():
                    if key not in enriched_data:
                        enriched_data[key] = value
            else:
                # Pour les autres types, simplement fusionner les données
                for key, value in additional_data.items():
                    if key not in enriched_data:
                        enriched_data[key] = value
        
        # Ajouter des métadonnées générales
        enriched_data["generation_date"] = datetime.datetime.now().isoformat()
        enriched_data["report_type"] = report_type.value
        
        # Ajouter le titre et sous-titre appropriés selon le type de rapport
        if "title" not in enriched_data:
            if report_type == ReportType.DIAGNOSTIC:
                enriched_data["title"] = "Rapport de diagnostic forestier"
                enriched_data["subtitle"] = "Analyse et recommandations"
            elif report_type == ReportType.MANAGEMENT_PLAN:
                enriched_data["title"] = "Plan de gestion forestière"
                enriched_data["subtitle"] = f"Horizon {enriched_data.get('horizon', {}).get('duration_years', 10)} ans"
            elif report_type == ReportType.INVENTORY:
                enriched_data["title"] = "Rapport d'inventaire forestier"
                enriched_data["subtitle"] = "Analyse des peuplements"
            elif report_type == ReportType.CLIMATE:
                enriched_data["title"] = "Analyse climatique"
                enriched_data["subtitle"] = "Impact sur la gestion forestière"
            elif report_type == ReportType.HEALTH:
                enriched_data["title"] = "Rapport sanitaire forestier"
                enriched_data["subtitle"] = "Analyse des risques et recommandations"
                
                # Pour les rapports sanitaires spécifiques, ajouter une introduction
                if "summary" not in enriched_data and "summary" in data:
                    enriched_data["summary"] = f"Ce rapport présente une analyse détaillée de l'état sanitaire du peuplement forestier. {data.get('summary', '')}"
                
                # Ajouter la date d'analyse si disponible
                if "metadata" in data and "analysis_date" in data["metadata"]:
                    try:
                        date = datetime.datetime.fromisoformat(data["metadata"]["analysis_date"])
                        enriched_data["date"] = date.strftime("%d/%m/%Y %H:%M")
                    except (ValueError, TypeError):
                        enriched_data["date"] = data["metadata"]["analysis_date"]
                else:
                    enriched_data["date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Générer des visualisations si nécessaire et si le module est disponible
        try:
            if report_type == ReportType.DIAGNOSTIC:
                enriched_data["visualizations"] = generate_diagnostic_graphs(data)
            elif report_type == ReportType.MANAGEMENT_PLAN:
                enriched_data["visualizations"] = generate_management_plan_graphs(data, additional_data)
        except Exception as e:
            logger.warning(f"Impossible de générer les visualisations pour le rapport {report_type.value}: {str(e)}")
        
        return enriched_data
    
    def get_available_formats(self) -> List[ReportFormat]:
        """
        Retourne la liste des formats de rapport disponibles.
        
        Returns:
            Liste des formats disponibles
        """
        return self.report_generator.get_supported_formats()
    
    def get_available_report_types(self) -> List[ReportType]:
        """
        Retourne la liste des types de rapport disponibles.
        
        Returns:
            Liste des types de rapport disponibles
        """
        return list(ReportType)
