#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modèle SARIMA pour la prédiction de croissance forestière.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import joblib
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error

from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionModel

logger = logging.getLogger(__name__)

class SarimaGrowthModel(GrowthPredictionModel):
    """
    Modèle SARIMA pour la prédiction de séries temporelles de croissance forestière.
    
    Ce modèle utilise le framework SARIMA (Seasonal AutoRegressive Integrated Moving Average)
    pour modéliser la croissance forestière et faire des prédictions futures.
    """
    
    def __init__(self, model_params: Dict[str, Any] = None):
        """
        Initialise le modèle SARIMA.
        
        Args:
            model_params: Paramètres du modèle SARIMA
                - order: tuple (p, d, q) - paramètres non saisonniers
                - seasonal_order: tuple (P, D, Q, s) - paramètres saisonniers
                - enforce_stationarity: bool
                - enforce_invertibility: bool
                - autres paramètres compatibles avec SARIMAX
        """
        super().__init__(model_params)
        
        # Paramètres par défaut
        self.default_params = {
            'order': (1, 1, 1),
            'seasonal_order': (1, 1, 1, 12),
            'enforce_stationarity': False,
            'enforce_invertibility': False
        }
        
        # Fusionner avec les paramètres fournis
        if model_params:
            self.model_params = {**self.default_params, **model_params}
        else:
            self.model_params = self.default_params
        
        # Variables d'état
        self.target_column = None
        self.train_data = None
        self.freq = None
    
    def _detect_freq(self, data: pd.DataFrame) -> str:
        """
        Détecte la fréquence des données temporelles.
        
        Args:
            data: DataFrame avec index temporel
            
        Returns:
            Code de fréquence pandas ('M', 'Q', 'A', etc.)
        """
        # Vérifier que les données sont triées
        if not data.index.is_monotonic_increasing:
            data = data.sort_index()
        
        # Calculer la fréquence médiane en jours
        if len(data) >= 2:
            diff_days = np.median(np.diff(data.index.astype(np.int64)) / (1e9 * 86400))
            
            if diff_days < 45:  # Mensuel
                return 'M'
            elif diff_days < 100:  # Trimestriel
                return 'Q'
            else:  # Annuel
                return 'A'
                
            logger.info(f"Fréquence détectée: {self.freq} (intervalle médian de {diff_days:.1f} jours)")
        else:
            # Par défaut si peu de données
            return 'M'
    
    def _adjust_seasonal_period(self, freq: str) -> None:
        """
        Ajuste la période saisonnière dans seasonal_order en fonction de la fréquence.
        
        Args:
            freq: Code de fréquence pandas ('M', 'Q', 'A', etc.)
        """
        # Extraire les composantes du seasonal_order
        P, D, Q, _ = self.model_params['seasonal_order']
        
        # Définir la période saisonnière en fonction de la fréquence
        if freq == 'M':
            s = 12  # Mensuel -> période annuelle
        elif freq == 'Q':
            s = 4   # Trimestriel -> période annuelle
        elif freq == 'W':
            s = 52  # Hebdomadaire -> période annuelle
        elif freq == 'D':
            s = 7   # Journalier -> période hebdomadaire
        else:
            s = 1   # Pas de saisonnalité
        
        # Mettre à jour seasonal_order
        self.model_params['seasonal_order'] = (P, D, Q, s)
    
    def fit(self, train_data: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """
        Entraîne le modèle SARIMA sur les données fournies.
        
        Args:
            train_data: Données d'entraînement avec index temporel
            target_column: Nom de la colonne cible
            
        Returns:
            Dictionnaire contenant le modèle entraîné et métriques
        """
        # Vérifier que les données sont triées
        if not train_data.index.is_monotonic_increasing:
            train_data = train_data.sort_index()
        
        # Stocker les données et le nom de la variable cible
        self.train_data = train_data
        self.target_column = target_column
        
        # Détecter et stocker la fréquence
        self.freq = self._detect_freq(train_data)
        
        # Ajuster la période saisonnière
        self._adjust_seasonal_period(self.freq)
        
        logger.info(f"Entraînement du modèle SARIMA avec les paramètres: {self.model_params}")
        
        try:
            # Entraîner le modèle SARIMA
            model = SARIMAX(
                train_data[target_column],
                **self.model_params
            )
            
            self.model = model.fit(disp=False)
            
            # Calcul des métriques sur l'ensemble d'entraînement
            predictions = self.model.fittedvalues
            residuals = train_data[target_column] - predictions
            
            mse = mean_squared_error(train_data[target_column], predictions)
            mae = mean_absolute_error(train_data[target_column], predictions)
            rmse = np.sqrt(mse)
            
            # Stockage des métriques et informations
            self.metrics = {
                'mse': mse,
                'mae': mae,
                'rmse': rmse,
                'aic': self.model.aic,
                'bic': self.model.bic
            }
            
            # Stockage du modèle et des données pour référence future
            self.trained = True
            
            logger.info(f"Modèle SARIMA entraîné avec succès. AIC: {self.model.aic:.2f}, BIC: {self.model.bic:.2f}")
            
            return {
                'model': self.model,
                'metrics': self.metrics,
                'params': self.model_params,
                'freq': self.freq
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle SARIMA: {str(e)}")
            raise
    
    def predict(self, 
               horizon: int,
               confidence_level: float = 0.95) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Génère des prédictions pour l'horizon spécifié.
        
        Args:
            horizon: Nombre de pas de temps à prédire
            confidence_level: Niveau de confiance pour les intervalles
            
        Returns:
            Tuple contenant (prédictions, intervalles de confiance)
        """
        if not self.trained or self.model is None:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")
        
        try:
            # Faire les prédictions avec intervalles de confiance
            forecast_results = self.model.get_forecast(steps=horizon, alpha=1-confidence_level)
            predictions = forecast_results.predicted_mean
            conf_int = forecast_results.conf_int()
            
            logger.info(f"Prédictions SARIMA générées pour un horizon de {horizon} pas")
            
            return predictions, conf_int
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des prédictions: {str(e)}")
            raise
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str) -> Dict[str, float]:
        """
        Évalue le modèle sur un ensemble de test.
        
        Args:
            test_data: Données de test avec index temporel
            target_column: Nom de la colonne cible
            
        Returns:
            Dictionnaire des métriques d'évaluation
        """
        if not self.trained or self.model is None:
            raise ValueError("Le modèle doit être entraîné avant d'être évalué")
        
        # Vérifier que les données sont triées
        if not test_data.index.is_monotonic_increasing:
            test_data = test_data.sort_index()
        
        try:
            # Nombre de pas à prédire
            horizon = len(test_data)
            
            # Générer les prédictions pour l'ensemble de test
            predictions, _ = self.predict(horizon=horizon)
            
            # Vérifier que les indices temporels correspondent
            if len(predictions) != len(test_data):
                logger.warning(f"Tailles différentes: prédictions ({len(predictions)}) vs test ({len(test_data)})")
                # Ajuster si nécessaire
                predictions = predictions[:len(test_data)]
            
            # Calcul des métriques
            mse = mean_squared_error(test_data[target_column], predictions)
            mae = mean_absolute_error(test_data[target_column], predictions)
            rmse = np.sqrt(mse)
            
            # Calcul de l'erreur relative moyenne
            mape = np.mean(np.abs((test_data[target_column] - predictions) / test_data[target_column])) * 100
            
            eval_metrics = {
                'test_mse': mse,
                'test_mae': mae,
                'test_rmse': rmse,
                'test_mape': mape
            }
            
            logger.info(f"Évaluation du modèle SARIMA - RMSE: {rmse:.4f}, MAPE: {mape:.2f}%")
            
            return eval_metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du modèle: {str(e)}")
            raise
    
    def analyze_features(self) -> Dict[str, Any]:
        """
        Analyse les composantes du modèle SARIMA pour comprendre les facteurs d'influence.
        
        Returns:
            Dictionnaire contenant l'analyse des facteurs d'influence
        """
        if not self.trained or self.model is None:
            raise ValueError("Le modèle doit être entraîné avant l'analyse")
        
        try:
            params = self.model.params
            
            # Extraire les composantes AR, MA, saisonnalité, etc.
            ar_params = {k: v for k, v in params.items() if 'ar.' in k and '.L' in k}
            ma_params = {k: v for k, v in params.items() if 'ma.' in k and '.L' in k}
            seasonal_ar_params = {k: v for k, v in params.items() if 'ar.' in k and '.S' in k}
            seasonal_ma_params = {k: v for k, v in params.items() if 'ma.' in k and '.S' in k}
            
            # Calculer la force des composantes
            ar_strength = np.sum(np.abs(list(ar_params.values()))) if ar_params else 0
            ma_strength = np.sum(np.abs(list(ma_params.values()))) if ma_params else 0
            seasonal_ar_strength = np.sum(np.abs(list(seasonal_ar_params.values()))) if seasonal_ar_params else 0
            seasonal_ma_strength = np.sum(np.abs(list(seasonal_ma_params.values()))) if seasonal_ma_params else 0
            
            # Déterminer les patterns dominants
            total_strength = ar_strength + ma_strength + seasonal_ar_strength + seasonal_ma_strength
            
            if total_strength > 0:
                ar_contribution = ar_strength / total_strength
                ma_contribution = ma_strength / total_strength
                seasonal_ar_contribution = seasonal_ar_strength / total_strength
                seasonal_ma_contribution = seasonal_ma_strength / total_strength
            else:
                ar_contribution = ma_contribution = seasonal_ar_contribution = seasonal_ma_contribution = 0
            
            # Analyser les résidus pour détecter des motifs non capturés
            residual_analysis = {}
            if hasattr(self.model, 'resid'):
                residuals = self.model.resid
                residual_analysis = {
                    'mean': np.mean(residuals),
                    'std': np.std(residuals),
                    'normality': self._check_residual_normality(residuals),
                    'autocorrelation': self._check_residual_autocorrelation(residuals)
                }
            
            analysis = {
                'components': {
                    'ar_params': ar_params,
                    'ma_params': ma_params,
                    'seasonal_ar_params': seasonal_ar_params,
                    'seasonal_ma_params': seasonal_ma_params
                },
                'strengths': {
                    'ar_strength': ar_strength,
                    'ma_strength': ma_strength,
                    'seasonal_ar_strength': seasonal_ar_strength,
                    'seasonal_ma_strength': seasonal_ma_strength
                },
                'contributions': {
                    'ar_contribution': ar_contribution,
                    'ma_contribution': ma_contribution,
                    'seasonal_ar_contribution': seasonal_ar_contribution,
                    'seasonal_ma_contribution': seasonal_ma_contribution
                },
                'residual_analysis': residual_analysis,
                'seasonality': {
                    'period': self.model_params['seasonal_order'][3],
                    'strength': seasonal_ar_strength + seasonal_ma_strength
                },
                'trend': {
                    'presence': ar_strength > 0,
                    'strength': ar_strength
                }
            }
            
            logger.info(f"Analyse des facteurs d'influence SARIMA complétée")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des composantes SARIMA: {str(e)}")
            raise
    
    def _check_residual_normality(self, residuals: pd.Series) -> Dict[str, float]:
        """
        Vérifie la normalité des résidus.
        
        Args:
            residuals: Série de résidus
            
        Returns:
            Résultat des tests de normalité
        """
        try:
            from scipy import stats
            
            # Test de Shapiro-Wilk
            shapiro_test = stats.shapiro(residuals)
            
            # Test de Jarque-Bera
            jarque_bera = stats.jarque_bera(residuals)
            
            return {
                'shapiro_stat': shapiro_test[0],
                'shapiro_pvalue': shapiro_test[1],
                'jarque_bera_stat': jarque_bera[0],
                'jarque_bera_pvalue': jarque_bera[1],
                'skewness': stats.skew(residuals),
                'kurtosis': stats.kurtosis(residuals)
            }
        except ImportError:
            return {'error': 'scipy not available'}
    
    def _check_residual_autocorrelation(self, residuals: pd.Series) -> Dict[str, Any]:
        """
        Vérifie l'autocorrélation des résidus.
        
        Args:
            residuals: Série de résidus
            
        Returns:
            Résultat des tests d'autocorrélation
        """
        try:
            from statsmodels.stats.diagnostic import acorr_ljungbox
            
            # Test de Ljung-Box
            ljung_box = acorr_ljungbox(residuals, lags=[10, 20, 30])
            
            return {
                'ljung_box_stat': ljung_box[0].tolist(),
                'ljung_box_pvalue': ljung_box[1].tolist()
            }
        except ImportError:
            return {'error': 'statsmodels diagnostic not available'}
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Fournit des informations sur le modèle entraîné.
        
        Returns:
            Dictionnaire contenant des métadonnées et caractéristiques du modèle
        """
        if not self.trained or self.model is None:
            return {
                'status': 'not_trained',
                'model_type': 'SARIMA'
            }
        
        return {
            'status': 'trained',
            'model_type': 'SARIMA',
            'params': self.model_params,
            'metrics': self.metrics,
            'target_column': self.target_column,
            'freq': self.freq,
            'data_points': len(self.train_data) if self.train_data is not None else None,
            'date_range': {
                'start': self.train_data.index.min().strftime('%Y-%m-%d') if self.train_data is not None else None,
                'end': self.train_data.index.max().strftime('%Y-%m-%d') if self.train_data is not None else None
            },
            'aic': self.model.aic if hasattr(self.model, 'aic') else None,
            'bic': self.model.bic if hasattr(self.model, 'bic') else None
        }
    
    def save(self, path: str) -> None:
        """
        Sauvegarde le modèle sur le disque.
        
        Args:
            path: Chemin où sauvegarder le modèle
        """
        if not self.trained or self.model is None:
            raise ValueError("Le modèle doit être entraîné avant d'être sauvegardé")
        
        try:
            # Préparer les données à sauvegarder
            model_data = {
                'model': self.model,
                'model_params': self.model_params,
                'metrics': self.metrics,
                'target_column': self.target_column,
                'freq': self.freq,
                'trained': self.trained
            }
            
            # Sauvegarder avec joblib
            joblib.dump(model_data, path)
            logger.info(f"Modèle SARIMA sauvegardé avec succès: {path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle: {str(e)}")
            raise
    
    def load(self, path: str) -> None:
        """
        Charge un modèle depuis le disque.
        
        Args:
            path: Chemin d'où charger le modèle
        """
        try:
            # Charger les données du modèle
            model_data = joblib.load(path)
            
            # Restaurer l'état du modèle
            self.model = model_data['model']
            self.model_params = model_data['model_params']
            self.metrics = model_data['metrics']
            self.target_column = model_data['target_column']
            self.freq = model_data['freq']
            self.trained = model_data['trained']
            
            logger.info(f"Modèle SARIMA chargé avec succès: {path}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            raise
