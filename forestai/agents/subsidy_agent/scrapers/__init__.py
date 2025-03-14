"""
Package contenant les scrapers de subventions forestières.

Ce package regroupe les différents scrapers pour extraire les informations
de subventions forestières depuis diverses sources.
"""

from .base_scraper import BaseScraper
from .europe_invest_scraper import EuropeInvestScraper
from .france_relance_scraper import FranceRelanceScraper
from .regional_subsidy_scraper import RegionalSubsidyScraper

__all__ = [
    "BaseScraper",
    "EuropeInvestScraper",
    "FranceRelanceScraper",
    "RegionalSubsidyScraper"
]
