"""
Module définissant la classe de base pour les scrapers de subventions.
"""
import abc
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from forestai.core.utils.logging_config import LoggingConfig

# Obtenir la configuration de logging
logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """
    Classe abstraite définissant l'interface commune à tous les scrapers de subventions.

    Cette classe fournit des méthodes pour extraire, traiter et stocker les informations
    sur les subventions forestières à partir de diverses sources.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le scraper avec la configuration spécifiée.

        Args:
            config: Dictionnaire de configuration spécifique au scraper
        """
        self.config = config
        self.results = []
        self.last_update = None
        self.logger = LoggingConfig.get_instance().get_logger(
            self.__class__.__name__,
            module=__name__
        )
        self.logger.info(f"Initialisation du scraper {self.__class__.__name__}")

    @abc.abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Récupère les données brutes sur les subventions depuis la source.

        Returns:
            Liste de dictionnaires contenant les données brutes des subventions
        """
        pass

    @abc.abstractmethod
    def parse_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Traite les données brutes pour extraire les informations pertinentes.

        Args:
            raw_data: Liste de dictionnaires contenant les données brutes des subventions

        Returns:
            Liste de dictionnaires contenant les informations traitées des subventions
        """
        pass

    def run(self) -> List[Dict[str, Any]]:
        """
        Exécute le processus complet de scraping.

        Returns:
            Liste de dictionnaires contenant les informations sur les subventions
        """
        self.logger.info(f"Démarrage du scraping avec {self.__class__.__name__}")
        try:
            raw_data = self.fetch_data()
            self.logger.info(f"Données brutes récupérées: {len(raw_data)} éléments")
            
            parsed_data = self.parse_data(raw_data)
            self.logger.info(f"Données analysées: {len(parsed_data)} subventions identifiées")
            
            self.results = parsed_data
            self.last_update = datetime.now()
            
            return self.results
        
        except Exception as e:
            self.logger.error(f"Erreur lors du scraping: {str(e)}", exc_info=True)
            raise
    
    def get_results(self) -> List[Dict[str, Any]]:
        """
        Retourne les résultats du dernier scraping.

        Returns:
            Liste de dictionnaires contenant les informations sur les subventions
        """
        return self.results
    
    def get_last_update(self) -> Optional[datetime]:
        """
        Retourne la date de la dernière mise à jour des données.

        Returns:
            Date et heure de la dernière mise à jour, ou None si aucune mise à jour n'a été effectuée
        """
        return self.last_update

    def filter_by_region(self, region: str) -> List[Dict[str, Any]]:
        """
        Filtre les résultats par région.

        Args:
            region: Nom de la région à filtrer

        Returns:
            Liste de subventions pour la région spécifiée
        """
        return [s for s in self.results if s.get("region") == region or s.get("region") == "National"]
    
    def filter_by_project_type(self, project_type: str) -> List[Dict[str, Any]]:
        """
        Filtre les résultats par type de projet.

        Args:
            project_type: Type de projet à filtrer

        Returns:
            Liste de subventions pour le type de projet spécifié
        """
        return [s for s in self.results if project_type.lower() in s.get("eligible_projects", "").lower()]
    
    def filter_by_min_amount(self, min_amount: float) -> List[Dict[str, Any]]:
        """
        Filtre les résultats par montant minimum de subvention.

        Args:
            min_amount: Montant minimum de subvention

        Returns:
            Liste de subventions dont le montant est supérieur ou égal au montant spécifié
        """
        return [s for s in self.results if s.get("min_amount", 0) >= min_amount]
