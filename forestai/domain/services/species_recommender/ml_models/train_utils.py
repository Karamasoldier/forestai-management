#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module pour l'entraînement des modèles ML du recommandeur d'espèces.

Ce module fournit les fonctions nécessaires pour entraîner, évaluer et
générer des données d'entraînement pour les modèles d'apprentissage automatique.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.models import (
    SpeciesData,
    SoilType,
    MoistureRegime,
    DroughtResistance,
    FrostResistance,
    GrowthRate
)
from forestai.domain.services.species_recommender.ml_models.data_transformer import (
    create_climate_transformer,
    create_soil_transformer,
    create_context_transformer,
    create_species_transformer
)

logger = get_logger(__name__)


def normalize_scores(scores: Dict[str, float]) -> Dict[str, float]:
    """
    Normalise les scores de prédiction entre 0 et 1 et les arrondit.
    
    Args:
        scores: Dictionnaire des scores à normaliser
        
    Returns:
        Dictionnaire des scores normalisés
    """
    normalized = {}
    
    for name, score in scores.items():
        # S'assurer que le score est entre 0 et 1
        normalized_score = min(1.0, max(0.0, score))
        # Arrondir à 3 décimales
        normalized[name] = round(normalized_score, 3)
    
    return normalized


def train_models(training_data: pd.DataFrame, validation_split: float = 0.2, random_state: int = 42) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Entraîne les modèles ML pour la recommandation d'espèces.
    
    Args:
        training_data: DataFrame avec les données d'entraînement
        validation_split: Proportion des données à utiliser pour la validation (0-1)
        random_state: Graine aléatoire pour la reproductibilité
        
    Returns:
        Tuple de (modèles, transformateurs, métriques)
    """
    # Vérifier les données d'entraînement
    required_columns = [
        'species_id', 'latin_name', 'common_name', 'family', 'native',
        'frost_resistance', 'drought_resistance', 'growth_rate',
        'mean_temperature', 'min_temperature', 'max_temperature', 'annual_precipitation',
        'drought_index', 'soil_type', 'moisture_regime', 'pH',
        'objective', 'wood_use', 'climate_change_scenario',
        'climate_score', 'soil_score', 'economic_score', 'ecological_score', 'risk_score', 'overall_score'
    ]
    
    missing_columns = [col for col in required_columns if col not in training_data.columns]
    if missing_columns:
        logger.error(f"Colonnes manquantes dans les données d'entraînement: {missing_columns}")
        return {}, {}, {'status': 'error', 'message': f"Colonnes manquantes: {missing_columns}"}
    
    try:
        # Prétraitement des données
        logger.info("Prétraitement des données d'entraînement...")
        
        # Créer les transformateurs
        climate_transformer = create_climate_transformer()
        soil_transformer = create_soil_transformer()
        context_transformer = create_context_transformer()
        species_transformer = create_species_transformer()
        
        # Stocker les transformateurs
        transformers = {
            'climate': climate_transformer,
            'soil': soil_transformer,
            'context': context_transformer,
            'species': species_transformer
        }
        
        # Créer des jeux de données pour chaque modèle
        climate_data = training_data[['mean_temperature', 'min_temperature', 'max_temperature', 
                                     'annual_precipitation', 'drought_index', 'frost_resistance', 
                                     'drought_resistance', 'climate_score']]
        
        soil_data = training_data[['soil_type', 'moisture_regime', 'pH', 'soil_score']]
        
        economic_data = training_data[['growth_rate', 'objective', 'wood_use', 'economic_score']]
        
        ecological_data = training_data[['native', 'drought_resistance', 'objective', 'ecological_score']]
        
        risk_data = training_data[['frost_resistance', 'drought_resistance', 'climate_change_scenario', 'risk_score']]
        
        overall_data = training_data[['climate_score', 'soil_score', 'economic_score', 
                                     'ecological_score', 'risk_score', 'objective', 'overall_score']]
        
        # Division train/test pour chaque modèle
        # Modèle climatique
        X_climate = climate_data.drop('climate_score', axis=1)
        y_climate = climate_data['climate_score']
        X_climate_train, X_climate_test, y_climate_train, y_climate_test = train_test_split(
            X_climate, y_climate, test_size=validation_split, random_state=random_state
        )
        
        # Modèle pédologique
        X_soil = soil_data.drop('soil_score', axis=1)
        y_soil = soil_data['soil_score']
        X_soil_train, X_soil_test, y_soil_train, y_soil_test = train_test_split(
            X_soil, y_soil, test_size=validation_split, random_state=random_state
        )
        
        # Modèle économique
        X_economic = economic_data.drop('economic_score', axis=1)
        y_economic = economic_data['economic_score']
        X_economic_train, X_economic_test, y_economic_train, y_economic_test = train_test_split(
            X_economic, y_economic, test_size=validation_split, random_state=random_state
        )
        
        # Modèle écologique
        X_ecological = ecological_data.drop('ecological_score', axis=1)
        y_ecological = ecological_data['ecological_score']
        X_ecological_train, X_ecological_test, y_ecological_train, y_ecological_test = train_test_split(
            X_ecological, y_ecological, test_size=validation_split, random_state=random_state
        )
        
        # Modèle de risque
        X_risk = risk_data.drop('risk_score', axis=1)
        y_risk = risk_data['risk_score']
        X_risk_train, X_risk_test, y_risk_train, y_risk_test = train_test_split(
            X_risk, y_risk, test_size=validation_split, random_state=random_state
        )
        
        # Modèle global
        X_overall = overall_data.drop('overall_score', axis=1)
        y_overall = overall_data['overall_score']
        X_overall_train, X_overall_test, y_overall_train, y_overall_test = train_test_split(
            X_overall, y_overall, test_size=validation_split, random_state=random_state
        )
        
        # Création et entraînement des modèles
        logger.info("Entraînement des modèles ML...")
        
        # Modèle climatique
        climate_model = Pipeline([
            ('preprocessor', climate_transformer),
            ('regressor', GradientBoostingRegressor(random_state=random_state))
        ])
        climate_model.fit(X_climate_train, y_climate_train)
        
        # Modèle pédologique
        soil_model = Pipeline([
            ('preprocessor', soil_transformer),
            ('regressor', RandomForestRegressor(random_state=random_state))
        ])
        soil_model.fit(X_soil_train, y_soil_train)
        
        # Modèle économique
        economic_model = Pipeline([
            ('preprocessor', context_transformer),
            ('regressor', RandomForestRegressor(random_state=random_state))
        ])
        economic_model.fit(X_economic_train, y_economic_train)
        
        # Modèle écologique
        ecological_model = Pipeline([
            ('preprocessor', species_transformer),
            ('regressor', RandomForestRegressor(random_state=random_state))
        ])
        ecological_model.fit(X_ecological_train, y_ecological_train)
        
        # Modèle de risque
        risk_model = Pipeline([
            ('preprocessor', context_transformer),
            ('regressor', GradientBoostingRegressor(random_state=random_state))
        ])
        risk_model.fit(X_risk_train, y_risk_train)
        
        # Modèle global
        overall_model = Pipeline([
            ('regressor', GradientBoostingRegressor(random_state=random_state))
        ])
        overall_model.fit(X_overall_train[['climate_score', 'soil_score', 'economic_score', 'ecological_score', 'risk_score']], y_overall_train)
        
        # Stocker les modèles
        models = {
            'climate': climate_model,
            'soil': soil_model,
            'economic': economic_model,
            'ecological': ecological_model,
            'risk': risk_model,
            'overall': overall_model
        }
        
        # Évaluation des modèles
        metrics = evaluate_models(
            models,
            {
                'climate': (X_climate_test, y_climate_test),
                'soil': (X_soil_test, y_soil_test),
                'economic': (X_economic_test, y_economic_test),
                'ecological': (X_ecological_test, y_ecological_test),
                'risk': (X_risk_test, y_risk_test),
                'overall': (X_overall_test[['climate_score', 'soil_score', 'economic_score', 'ecological_score', 'risk_score']], y_overall_test)
            }
        )
        
        logger.info("Entraînement des modèles ML terminé avec succès")
        
        return models, transformers, metrics
        
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement des modèles: {str(e)}")
        return {}, {}, {'status': 'error', 'message': f"Erreur: {str(e)}"}


def evaluate_models(models: Dict[str, Any], test_data: Dict[str, Tuple[pd.DataFrame, pd.Series]]) -> Dict[str, Any]:
    """
    Évalue les performances des modèles ML.
    
    Args:
        models: Dictionnaire des modèles à évaluer
        test_data: Dictionnaire des données de test (X_test, y_test) pour chaque modèle
        
    Returns:
        Dictionnaire des métriques d'évaluation
    """
    metrics = {'status': 'success'}
    
    try:
        for name, model in models.items():
            if name in test_data:
                X_test, y_test = test_data[name]
                y_pred = model.predict(X_test)
                
                # Calculer les métriques
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                
                metrics[name] = {
                    'r2': r2,
                    'rmse': rmse
                }
                
                logger.info(f"Évaluation du modèle {name}: R² = {r2:.3f}, RMSE = {rmse:.3f}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation des modèles: {str(e)}")
        return {'status': 'error', 'message': f"Erreur: {str(e)}"}


def generate_training_data(species_data: Dict[str, SpeciesData], n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """
    Génère des données d'entraînement synthétiques pour les modèles.
    
    Args:
        species_data: Dictionnaire des données d'espèces
        n_samples: Nombre d'échantillons à générer
        random_state: Graine aléatoire pour la reproductibilité
        
    Returns:
        DataFrame avec les données d'entraînement
    """
    np.random.seed(random_state)
    
    logger.info(f"Génération de {n_samples} échantillons d'entraînement...")
    
    try:
        # Créer un DataFrame pour stocker les données
        data = []
        
        # Listes des valeurs possibles pour les caractéristiques catégorielles
        species_ids = list(species_data.keys())
        objectives = ['balanced', 'production_rapide', 'qualite_bois', 'biodiversite', 'carbon_sequestration', 'erosion_control']
        wood_uses = ['construction', 'ameublement', 'placage', 'pâte à papier', 'énergie/chauffage', 'artisanat']
        climate_scenarios = ['none', 'moderate', 'high', 'extreme']
        
        soil_types = [st.value for st in SoilType]
        moisture_regimes = [mr.value for mr in MoistureRegime]
        frost_resistances = [fr.value for fr in FrostResistance]
        drought_resistances = [dr.value for dr in DroughtResistance]
        growth_rates = [gr.value for gr in GrowthRate]
        
        # Générer des échantillons
        for _ in range(n_samples):
            # Sélectionner une espèce aléatoire
            species_id = np.random.choice(species_ids)
            species = species_data[species_id]
            
            # Générer des données climatiques
            mean_temp = np.random.uniform(0, 20)
            min_temp = mean_temp - np.random.uniform(5, 25)
            max_temp = mean_temp + np.random.uniform(10, 25)
            annual_precipitation = np.random.uniform(300, 2000)
            drought_index = np.random.uniform(0, 10)
            
            # Générer des données pédologiques
            soil_type = np.random.choice(soil_types)
            moisture_regime = np.random.choice(moisture_regimes)
            pH = np.random.uniform(3.5, 8.5)
            
            # Générer des données de contexte
            objective = np.random.choice(objectives)
            wood_use = np.random.choice(wood_uses)
            climate_change_scenario = np.random.choice(climate_scenarios)
            
            # Extraire ou générer des caractéristiques d'espèces
            latin_name = species.latin_name
            common_name = species.common_name
            family = species.family
            native = species.native
            
            frost_resistance = species.frost_resistance.value if species.frost_resistance else np.random.choice(frost_resistances)
            drought_resistance = species.drought_resistance.value if species.drought_resistance else np.random.choice(drought_resistances)
            growth_rate = species.growth_rate.value if species.growth_rate else np.random.choice(growth_rates)
            
            # Ajouter du bruit aux scores pour la diversité des données
            def add_noise(base_value, noise_range=0.2):
                noise = np.random.uniform(-noise_range, noise_range)
                return min(1.0, max(0.0, base_value + noise))
            
            # Calculer des scores "simulés" basés sur les caractéristiques
            # Ces formules sont simplifiées et devraient être adaptées selon les besoins
            
            # Score climatique (influencé par la température, précipitations et résistances)
            climate_base = 0.7 if (5 <= mean_temp <= 15) else 0.4
            climate_base += 0.2 if (600 <= annual_precipitation <= 1200) else 0.0
            climate_base += 0.1 if frost_resistance in ["élevée", "très élevée"] else 0.0
            climate_base += 0.1 if drought_resistance in ["élevée", "très élevée"] else 0.0
            climate_score = add_noise(climate_base / 2)  # Normaliser
            
            # Score pédologique (influencé par le type de sol et le pH)
            soil_base = 0.7 if soil_type in [st.value for st in species.suitable_soil_types] else 0.3
            soil_base += 0.3 if moisture_regime in [mr.value for mr in species.suitable_moisture_regimes] else 0.0
            soil_score = add_noise(soil_base / 1.5)  # Normaliser
            
            # Score économique (influencé par le taux de croissance et l'objectif)
            economic_base = 0.0
            if objective == "production_rapide" and growth_rate in ["rapide", "très rapide"]:
                economic_base = 0.9
            elif objective == "qualite_bois" and growth_rate == "lent":
                economic_base = 0.8
            else:
                economic_base = 0.5
            economic_score = add_noise(economic_base)
            
            # Score écologique (influencé par le statut natif et l'objectif)
            ecological_base = 0.8 if native else 0.4
            if objective in ["biodiversite", "carbon_sequestration"]:
                ecological_base += 0.2
            ecological_score = add_noise(ecological_base / 1.2)  # Normaliser
            
            # Score de risque (influencé par les résistances et le scénario climatique)
            risk_base = 0.7
            if climate_change_scenario != "none":
                risk_base -= 0.1
                if climate_change_scenario == "extreme":
                    risk_base -= 0.2
            risk_base += 0.2 if drought_resistance in ["élevée", "très élevée"] else 0.0
            risk_base += 0.1 if frost_resistance in ["élevée", "très élevée"] else 0.0
            risk_score = add_noise(risk_base)
            
            # Score global (combinaison pondérée des scores individuels)
            weights = {
                'climate': 0.3,
                'soil': 0.3,
                'economic': 0.15,
                'ecological': 0.15,
                'risk': 0.1
            }
            if objective in ["production_rapide", "qualite_bois"]:
                weights['economic'] = 0.3
                weights['ecological'] = 0.05
                weights['climate'] = 0.25
                weights['soil'] = 0.25
            elif objective in ["biodiversite", "carbon_sequestration"]:
                weights['ecological'] = 0.3
                weights['economic'] = 0.05
                weights['climate'] = 0.25
                weights['soil'] = 0.25
            
            overall_score = (
                weights['climate'] * climate_score +
                weights['soil'] * soil_score +
                weights['economic'] * economic_score +
                weights['ecological'] * ecological_score +
                weights['risk'] * risk_score
            )
            # Ajouter un peu de bruit pour que le score global ne soit pas une simple somme pondérée
            overall_score = add_noise(overall_score, 0.1)
            
            # Créer un échantillon
            sample = {
                'species_id': species_id,
                'latin_name': latin_name,
                'common_name': common_name,
                'family': family,
                'native': native,
                'frost_resistance': frost_resistance,
                'drought_resistance': drought_resistance,
                'growth_rate': growth_rate,
                'mean_temperature': mean_temp,
                'min_temperature': min_temp,
                'max_temperature': max_temp,
                'annual_precipitation': annual_precipitation,
                'drought_index': drought_index,
                'soil_type': soil_type,
                'moisture_regime': moisture_regime,
                'pH': pH,
                'objective': objective,
                'wood_use': wood_use,
                'climate_change_scenario': climate_change_scenario,
                'climate_score': climate_score,
                'soil_score': soil_score,
                'economic_score': economic_score,
                'ecological_score': ecological_score,
                'risk_score': risk_score,
                'overall_score': overall_score
            }
            
            data.append(sample)
        
        # Créer un DataFrame à partir des données
        df = pd.DataFrame(data)
        
        logger.info(f"Génération de {n_samples} échantillons d'entraînement terminée")
        
        return df
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des données d'entraînement: {str(e)}")
        return pd.DataFrame()
