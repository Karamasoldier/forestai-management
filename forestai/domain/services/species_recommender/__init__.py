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
    SpeciesData,
    SoilType,
    MoistureRegime,
    DroughtResistance,
    FrostResistance,
    GrowthRate,
    EconomicValue,
    EcologicalValue,
    WoodUse
)
from forestai.domain.services.species_recommender.data_loader import SpeciesDataLoader
from forestai.domain.services.species_recommender.score_calculator import (
    calculate_climate_score,
    calculate_soil_score,
    calculate_economic_score,
    calculate_ecological_score,
    calculate_risk_score,
    calculate_overall_score
)

__all__ = [
    'SpeciesRecommender',
    'SpeciesRecommendation',
    'RecommendationScore',
    'SpeciesData',
    'SpeciesDataLoader',
    'SoilType',
    'MoistureRegime',
    'DroughtResistance',
    'FrostResistance',
    'GrowthRate',
    'EconomicValue',
    'EcologicalValue',
    'WoodUse',
    'calculate_climate_score',
    'calculate_soil_score',
    'calculate_economic_score',
    'calculate_ecological_score',
    'calculate_risk_score',
    'calculate_overall_score'
]
