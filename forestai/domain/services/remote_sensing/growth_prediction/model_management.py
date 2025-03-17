#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de gestion des modèles pour la prédiction de croissance forestière.

Ce module contient la classe ModelManagementService qui s'occupe de la
sélection, persistance et évaluation des modèles de prédiction.
"""

import os
import logging
import pandas as pd
import joblib
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionModel
from forestai.domain.services.remote_sensing.growth_prediction.model_sarima import SarimaGrowthModel

logger = logging.getLogger(__name__)

class ModelManagementService:
    """
    Service de gestion des modèles pour la prédiction de croissance forestière.
    """
    
    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialise le service de gestion des modèles.
        
        Args:
            models_dir: Répertoire pour sauvegarder/charger les modèles entraînés
        """
        self.models_dir = models_dir or os.path.join(os.path.dirname(__file__), 'saved_models')
        
        # Création du répertoire si nécessaire
        Path(self.models_dir).mkdir(parents=True, exist_ok=True)
        
        # Dictionnaire des modèles disponibles
        self._available_models = {
            'sarima': SarimaGrowthModel
            # D'autres modèles pourront être ajoutés ici (exp_smoothing, random_forest, etc.)
        }
        
        logger.info(f"ModelManagementService initialisé avec {len(self._available_models)} modèles disponibles")
    
    def get_available_models(self) -> Dict[str, type]:
        """
        Récupère le dictionnaire des modèles disponibles.
        
        Returns:
            Dictionnaire des modèles disponibles
        """
        return self._available_models
    
    def get_model_path(self, parcel_id: str, model_type: str, target_metric: str) -> str:
        """
        Génère le chemin pour sauvegarder/charger un modèle.
        
        Args:
            parcel_id: Identifiant de la parcelle
            model_type: Type de modèle (ex: 'sarima')
            target_metric: Métrique cible (ex: 'canopy_height')
            
        Returns:
            Chemin complet du fichier modèle
        """
        return os.path.join(
            self.models_dir, 
            f"{parcel_id}_{model_type}_{target_metric}.joblib"
        )
    
    def save_model(self, model: GrowthPredictionModel, model_path: str) -> None:
        """
        Sauvegarde un modèle entraîné.
        
        Args:
            model: Modèle entraîné à sauvegarder
            model_path: Chemin où sauvegarder le modèle
        """
        try:
            joblib.dump(model, model_path)
            logger.info(f"Modèle sauvegardé avec succès: {model_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle {model_path}: {str(e)}")
    
    def load_model(self, model_path: str) -> Optional[GrowthPredictionModel]:
        """
        Charge un modèle précédemment entraîné.
        
        Args:
            model_path: Chemin du modèle à charger
            
        Returns:
            Modèle chargé ou None si le chargement échoue
        """
        if not os.path.exists(model_path):
            logger.info(f"Aucun modèle existant trouvé à {model_path}")
            return None
        
        try:
            model = joblib.load(model_path)
            logger.info(f"Modèle chargé avec succès: {model_path}")
            return model
        except Exception as e:
            logger.warning(f"Erreur lors du chargement du modèle {model_path}: {str(e)}")
            return None
    
    def select_best_model(self, 
                        time_series_data: pd.DataFrame, 
                        target_metric: str,
                        test_ratio: float = 0.2) -> Tuple[str, Dict[str, float]]:
        """
        Sélectionne le meilleur modèle pour les données fournies.
        
        Args:
            time_series_data: DataFrame contenant les données de série temporelle
            target_metric: Métrique cible pour la prédiction
            test_ratio: Proportion des données à utiliser pour le test
            
        Returns:
            Tuple contenant le nom du meilleur modèle et ses métriques
        """
        best_score = float('inf')
        best_model_name = None
        best_metrics = {}
        
        # Pour chaque type de modèle disponible
        for model_name, model_class in self._available_models.items():
            try:
                # Diviser les données en ensembles d'entraînement et de test
                split_idx = int(len(time_series_data) * (1 - test_ratio))
                if split_idx < 5:  # Vérifier qu'il y a suffisamment de données
                    logger.warning("Pas assez de données pour une sélection fiable de modèle")
                    return "sarima", {}  # Retourner le modèle par défaut
                
                train_data = time_series_data.iloc[:split_idx]
                test_data = time_series_data.iloc[split_idx:]
                
                # Initialiser et entraîner le modèle
                model = model_class()
                model.train(train_data, target_metric)
                
                # Évaluer le modèle
                metrics = model.evaluate(test_data, target_metric)
                mse = metrics.get('mse', float('inf'))
                
                if mse < best_score:
                    best_score = mse
                    best_model_name = model_name
                    best_metrics = metrics
                    
                logger.info(f"Modèle {model_name} évalué, MSE: {mse}")
                
            except Exception as e:
                logger.warning(f"Erreur lors de l'évaluation du modèle {model_name}: {str(e)}")
        
        if best_model_name is None:
            logger.warning("Aucun modèle n'a pu être évalué correctement, utilisation du modèle par défaut")
            best_model_name = "sarima"
            
        return best_model_name, best_metrics
