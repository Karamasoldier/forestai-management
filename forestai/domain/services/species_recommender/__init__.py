"""
Module pour le système de recommandation d'espèces forestières.

Ce module fournit des services permettant de recommander des espèces d'arbres 
adaptées aux conditions spécifiques d'une parcelle, en tenant compte de facteurs 
climatiques, pédologiques et écologiques.
"""

from forestai.domain.services.species_recommender.recommender import SpeciesRecommender
from forestai.domain.services.species_recommender.models import (
    SpeciesRecommendation,
    RecommendationScore,
    SpeciesData
)

__all__ = [
    'SpeciesRecommender',
    'SpeciesRecommendation',
    'RecommendationScore',
    'SpeciesData'
]
