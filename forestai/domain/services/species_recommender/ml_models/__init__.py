"""
Package contenant les modèles et utilitaires ML pour le système de recommandation d'espèces.

Ce package inclut les modules nécessaires au chargement, à l'entraînement, à la transformation
des données et à la prédiction pour le système de recommandation d'espèces basé sur ML.
"""

from forestai.domain.services.species_recommender.ml_models.model_loader import ModelLoader
from forestai.domain.services.species_recommender.ml_models.data_transformer import (
    prepare_climate_data,
    prepare_soil_data,
    prepare_economic_data,
    prepare_ecological_data,
    prepare_risk_data,
    prepare_overall_data
)
from forestai.domain.services.species_recommender.ml_models.train_utils import (
    normalize_scores,
    train_models,
    evaluate_models,
    generate_training_data
)

__all__ = [
    'ModelLoader',
    'prepare_climate_data',
    'prepare_soil_data',
    'prepare_economic_data',
    'prepare_ecological_data',
    'prepare_risk_data',
    'prepare_overall_data',
    'normalize_scores',
    'train_models',
    'evaluate_models',
    'generate_training_data'
]
