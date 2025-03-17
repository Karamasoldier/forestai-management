#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module d'apprentissage automatique pour le système de recommandation d'espèces.

Ce module étend le système de recommandation d'espèces avec des capacités
d'apprentissage automatique pour améliorer la précision des recommandations
et prendre en compte des facteurs complexes comme le changement climatique.
"""

import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.models import SpeciesData
from forestai.domain.services.species_recommender.ml_models.model_loader import ModelLoader
from forestai.domain.services.species_recommender.ml_models.data_transformer import (
    prepare_climate_data,
    prepare_soil_data,
    prepare_economic_data,
    prepare_ecological_data,
    prepare_risk_data,
    prepare_overall_data
)
from forestai.domain.services.species_recommender.ml_models.train_utils import normalize_scores

logger = get_logger(__name__)


class MLSpeciesRecommender:
    """
    Recommandeur d'espèces forestières basé sur le Machine Learning.
    
    Utilise des modèles d'apprentissage automatique pour prédire la compatibilité
    et la performance des espèces d'arbres dans des conditions environnementales spécifiques,
    y compris les scénarios de changement climatique.
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialise le recommandeur ML.
        
        Args:
            models_dir: Répertoire de stockage des modèles entraînés (facultatif)
        """
        # Si aucun répertoire n'est spécifié, utiliser le dossier par défaut
        if models_dir is None:
            models_dir = Path(os.environ.get("FORESTAI_MODELS_DIR", ".")) / "models" / "species"
        
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser le chargeur de modèles
        self.model_loader = ModelLoader(self.models_dir)
        
        # Charger les modèles et transformateurs
        self.models = self.model_loader.load_models()
        
        # Statut d'initialisation
        model_names = ['climate', 'soil', 'economic', 'ecological', 'risk', 'overall']
        self.initialized = all(name in self.models and self.models[name] is not None for name in model_names)
        
        if self.initialized:
            logger.info("MLSpeciesRecommender initialisé avec tous les modèles chargés")
        else:
            logger.warning("MLSpeciesRecommender initialisé mais certains modèles sont manquants")
    
    def predict_scores(self, species: SpeciesData, climate_data: Dict[str, Any], 
                     soil_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        """
        Prédit les scores de compatibilité d'une espèce avec les modèles ML.
        
        Args:
            species: Données de l'espèce
            climate_data: Données climatiques de la parcelle
            soil_data: Données pédologiques de la parcelle
            context: Contexte de la recommandation
            
        Returns:
            Dictionnaire des scores prédits
        """
        if not self.initialized:
            logger.warning("Modèles ML non initialisés, impossible de faire des prédictions")
            return None
        
        try:
            # Préparer les données pour chaque modèle
            climate_df = prepare_climate_data(species, climate_data)
            soil_df = prepare_soil_data(species, soil_data)
            economic_df = prepare_economic_data(species, context)
            ecological_df = prepare_ecological_data(species, context)
            risk_df = prepare_risk_data(species, context)
            
            # Prédire les scores individuels
            climate_score = self.models['climate'].predict(climate_df)[0]
            soil_score = self.models['soil'].predict(soil_df)[0]
            economic_score = self.models['economic'].predict(economic_df)[0]
            ecological_score = self.models['ecological'].predict(ecological_df)[0]
            risk_score = self.models['risk'].predict(risk_df)[0]
            
            # Prédire le score global
            overall_df = prepare_overall_data(climate_score, soil_score, economic_score, 
                                             ecological_score, risk_score)
            overall_score = self.models['overall'].predict(overall_df)[0]
            
            # Normaliser et formater les scores
            scores = normalize_scores({
                'climate_score': climate_score,
                'soil_score': soil_score,
                'economic_score': economic_score,
                'ecological_score': ecological_score,
                'risk_score': risk_score,
                'overall_score': overall_score
            })
            
            return scores
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction des scores: {str(e)}")
            return None
