#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module pour la transformation des données pour les modèles ML du recommandeur d'espèces.

Ce module fournit les fonctions de transformation de données pour préparer
les entrées des modèles d'apprentissage automatique utilisés par le système
de recommandation d'espèces.
"""

import pandas as pd
from typing import Dict, Any
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.models import SpeciesData

logger = get_logger(__name__)


def prepare_climate_data(species: SpeciesData, climate_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Prépare les données climatiques pour la prédiction.
    
    Args:
        species: Données de l'espèce
        climate_data: Données climatiques de la parcelle
        
    Returns:
        DataFrame avec les données formatées pour le modèle climatique
    """
    return pd.DataFrame({
        'mean_temperature': [climate_data.get('mean_annual_temperature', 0)],
        'min_temperature': [climate_data.get('min_temperature', 0)],
        'max_temperature': [climate_data.get('max_temperature', 0)],
        'annual_precipitation': [climate_data.get('annual_precipitation', 0)],
        'drought_index': [climate_data.get('drought_index', 0)],
        'frost_resistance': [species.frost_resistance.value if species.frost_resistance else 'moyenne'],
        'drought_resistance': [species.drought_resistance.value if species.drought_resistance else 'moyenne']
    })


def prepare_soil_data(species: SpeciesData, soil_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Prépare les données pédologiques pour la prédiction.
    
    Args:
        species: Données de l'espèce
        soil_data: Données pédologiques de la parcelle
        
    Returns:
        DataFrame avec les données formatées pour le modèle pédologique
    """
    return pd.DataFrame({
        'soil_type': [soil_data.get('soil_type', 'limoneux')],
        'moisture_regime': [soil_data.get('moisture_regime', 'moyen')],
        'pH': [soil_data.get('pH', 7.0)]
    })


def prepare_economic_data(species: SpeciesData, context: Dict[str, Any]) -> pd.DataFrame:
    """
    Prépare les données économiques pour la prédiction.
    
    Args:
        species: Données de l'espèce
        context: Contexte de la recommandation
        
    Returns:
        DataFrame avec les données formatées pour le modèle économique
    """
    return pd.DataFrame({
        'growth_rate': [species.growth_rate.value if species.growth_rate else 'moyen'],
        'objective': [context.get('objective', 'balanced')],
        'wood_use': [context.get('wood_use', 'construction')]
    })


def prepare_ecological_data(species: SpeciesData, context: Dict[str, Any]) -> pd.DataFrame:
    """
    Prépare les données écologiques pour la prédiction.
    
    Args:
        species: Données de l'espèce
        context: Contexte de la recommandation
        
    Returns:
        DataFrame avec les données formatées pour le modèle écologique
    """
    return pd.DataFrame({
        'native': [species.native],
        'drought_resistance': [species.drought_resistance.value if species.drought_resistance else 'moyenne'],
        'objective': [context.get('objective', 'balanced')]
    })


def prepare_risk_data(species: SpeciesData, context: Dict[str, Any]) -> pd.DataFrame:
    """
    Prépare les données de risque pour la prédiction.
    
    Args:
        species: Données de l'espèce
        context: Contexte de la recommandation
        
    Returns:
        DataFrame avec les données formatées pour le modèle de risque
    """
    return pd.DataFrame({
        'frost_resistance': [species.frost_resistance.value if species.frost_resistance else 'moyenne'],
        'drought_resistance': [species.drought_resistance.value if species.drought_resistance else 'moyenne'],
        'climate_change_scenario': [context.get('climate_change_scenario', 'moderate')]
    })


def prepare_overall_data(climate_score: float, soil_score: float, economic_score: float,
                       ecological_score: float, risk_score: float) -> pd.DataFrame:
    """
    Prépare les données globales pour la prédiction.
    
    Args:
        climate_score: Score climatique
        soil_score: Score pédologique
        economic_score: Score économique
        ecological_score: Score écologique
        risk_score: Score de risque
        
    Returns:
        DataFrame avec les données formatées pour le modèle global
    """
    return pd.DataFrame({
        'climate_score': [climate_score],
        'soil_score': [soil_score],
        'economic_score': [economic_score],
        'ecological_score': [ecological_score],
        'risk_score': [risk_score]
    })


def create_climate_transformer() -> ColumnTransformer:
    """
    Crée un transformateur pour les données climatiques.
    
    Returns:
        Transformateur pour les données climatiques
    """
    return ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['mean_temperature', 'min_temperature', 'max_temperature', 
                                      'annual_precipitation', 'drought_index']),
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['frost_resistance', 'drought_resistance'])
        ],
        remainder='drop'
    )


def create_soil_transformer() -> ColumnTransformer:
    """
    Crée un transformateur pour les données pédologiques.
    
    Returns:
        Transformateur pour les données pédologiques
    """
    return ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['pH']),
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['soil_type', 'moisture_regime'])
        ],
        remainder='drop'
    )


def create_context_transformer() -> ColumnTransformer:
    """
    Crée un transformateur pour les données de contexte.
    
    Returns:
        Transformateur pour les données de contexte
    """
    return ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['objective', 'wood_use', 'climate_change_scenario'])
        ],
        remainder='drop'
    )


def create_species_transformer() -> ColumnTransformer:
    """
    Crée un transformateur pour les données d'espèces.
    
    Returns:
        Transformateur pour les données d'espèces
    """
    return ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['frost_resistance', 'drought_resistance', 'growth_rate']),
            ('bin', 'passthrough', ['native'])
        ],
        remainder='drop'
    )
