"""
Module définissant la classe de base pour tous les scrapers de subventions.

Cette classe fournit une interface commune et des fonctionnalités partagées
pour tous les scrapers de subventions.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from forestai.core.utils.logging_config import LoggingConfig


class BaseSubsidyScraper(ABC):
    """
    Classe abstraite servant de base pour tous les scrapers de subventions.
    
    Les scrapers dérivés doivent implémenter les méthodes fetch_data et parse_data
    pour extraire et traiter les informations sur les subventions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le scraper avec une configuration.
        
        Args:
            config: Dictionnaire de configuration (optionnel)
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        
        # Configuration du logging
        self.logger = LoggingConfig.get_instance().get_logger(
            self.name,
            module=__name__
        )
        self.logger.info(f"Initialisation du scraper: {self.name}")
    
    def fetch_subsidies(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des subventions disponibles.
        
        Cette méthode coordonne le processus d'extraction et de traitement
        des données de subvention en appelant fetch_data puis parse_data.
        
        Returns:
            Liste des subventions au format standardisé
        """
        self.logger.info(f"Récupération des subventions avec le scraper {self.name}")
        
        try:
            # 1. Récupérer les données brutes
            raw_data = self.fetch_data()
            self.logger.info(f"Données brutes récupérées: {len(raw_data)} éléments")
            
            # 2. Traiter les données
            subsidies = self.parse_data(raw_data)
            self.logger.info(f"Subventions extraites: {len(subsidies)}")
            
            # 3. Standardiser et enrichir les données
            standardized_subsidies = self._standardize_subsidies(subsidies)
            self.logger.info(f"Subventions standardisées: {len(standardized_subsidies)}")
            
            return standardized_subsidies
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des subventions: {e}", exc_info=True)
            return []
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Récupère les données brutes sur les subventions.
        
        Cette méthode doit être implémentée par les classes dérivées pour
        extraire les données spécifiques à chaque source de subventions.
        
        Returns:
            Liste de dictionnaires contenant les données brutes des subventions
        """
        pass
    
    @abstractmethod
    def parse_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Traite les données brutes pour extraire les informations pertinentes.
        
        Cette méthode doit être implémentée par les classes dérivées pour
        transformer les données brutes en informations structurées.
        
        Args:
            raw_data: Données brutes récupérées par fetch_data
            
        Returns:
            Liste de dictionnaires contenant les informations structurées des subventions
        """
        pass
    
    def _standardize_subsidies(self, subsidies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Standardise les données de subventions pour garantir un format cohérent.
        
        Args:
            subsidies: Liste des subventions à standardiser
            
        Returns:
            Liste des subventions au format standardisé
        """
        standardized = []
        
        for i, subsidy in enumerate(subsidies, start=1):
            # Générer un ID unique si non présent
            if not subsidy.get("id"):
                source_prefix = subsidy.get("source", "").upper()[:3] + "-"
                year_prefix = datetime.now().strftime("%Y-")
                subsidy["id"] = f"{source_prefix}{year_prefix}{i:02d}"
            
            # Convertir les données au format standardisé
            standard_subsidy = {
                "id": subsidy.get("id"),
                "title": subsidy.get("title", "Sans titre"),
                "source": subsidy.get("source", "Inconnu"),
                "organization": subsidy.get("organization", subsidy.get("source", "Inconnu")),
                "description": subsidy.get("description", ""),
                "url": subsidy.get("url", ""),
                "regions": subsidy.get("regions", [subsidy.get("region", "")]) if isinstance(subsidy.get("regions"), list) else [subsidy.get("region", "")],
                "deadline": subsidy.get("deadline", subsidy.get("application_deadline", "")),
                "eligible_projects": subsidy.get("eligible_projects", []),
                "eligible_owners": subsidy.get("eligible_owners", ["all"]),
                "min_area_ha": float(subsidy.get("min_area_ha", 0)),
                "max_area_ha": float(subsidy.get("max_area_ha", 0)) if subsidy.get("max_area_ha") else None,
                "amount_per_ha": subsidy.get("amount_per_ha", subsidy.get("min_amount", 0)),
                "max_funding": subsidy.get("max_funding", subsidy.get("max_amount", 0)),
                "funding_rate": subsidy.get("funding_rate", subsidy.get("financing_rate", "")),
                "eligibility_criteria": subsidy.get("eligibility_criteria", []),
                "application_process": subsidy.get("application_process", []),
                "contact": subsidy.get("contact", ""),
                "created_at": subsidy.get("created_at", datetime.now().isoformat()),
                "updated_at": subsidy.get("updated_at", datetime.now().isoformat()),
            }
            
            # Convertir les chaînes en listes si nécessaire
            for field in ["eligible_projects", "eligible_owners", "eligibility_criteria", "application_process"]:
                if isinstance(standard_subsidy[field], str):
                    standard_subsidy[field] = [standard_subsidy[field]]
            
            standardized.append(standard_subsidy)
        
        return standardized
