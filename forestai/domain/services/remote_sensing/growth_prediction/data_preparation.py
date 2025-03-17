#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de préparation des données pour la prédiction de croissance forestière.

Ce module contient les fonctions nécessaires pour transformer les données
de télédétection brutes en séries temporelles adaptées pour l'analyse
et la prédiction de croissance forestière.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime, timedelta

from forestai.domain.services.remote_sensing.models import RemoteSensingData, ForestMetrics, VegetationIndex

# Configuration du logger
logger = logging.getLogger(__name__)

class DataPreparationService:
    """Service de préparation des données pour l'analyse de séries temporelles forestières."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialise le service de préparation des données.
        
        Args:
            verbose: Si True, affiche des informations détaillées pendant le traitement
        """
        self.verbose = verbose
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if verbose:
            self._logger.setLevel(logging.DEBUG)
    
    def convert_to_time_series(self, data: List[RemoteSensingData], target_metrics: List[str]) -> pd.DataFrame:
        """
        Convertit une liste de données de télédétection en série temporelle.
        
        Args:
            data: Liste des données de télédétection
            target_metrics: Liste des métriques à extraire
            
        Returns:
            DataFrame contenant les séries temporelles des métriques ciblées
        """
        if not data:
            raise ValueError("Aucune donnée de télédétection fournie")
        
        # Trier les données par date d'acquisition
        sorted_data = sorted(data, key=lambda x: x.acquisition_date)
        
        # Créer le DataFrame
        time_series_data = []
        
        for rs_data in sorted_data:
            row = {"date": rs_data.acquisition_date}
            
            # Extraire les métriques demandées
            for metric in target_metrics:
                if hasattr(rs_data.metrics, metric):
                    row[metric] = getattr(rs_data.metrics, metric)
                else:
                    self._logger.warning(f"Métrique '{metric}' non disponible dans les données")
                    row[metric] = None
            
            # Ajouter les indices de végétation s'ils sont disponibles
            if rs_data.vegetation_indices:
                for index_name, index_value in rs_data.vegetation_indices.items():
                    row[f"index_{index_name.name.lower()}"] = index_value
            
            time_series_data.append(row)
        
        df = pd.DataFrame(time_series_data)
        df.set_index("date", inplace=True)
        
        # Vérifier la fréquence et l'uniformité des données
        self._check_data_quality(df)
        
        return df
    
    def _check_data_quality(self, df: pd.DataFrame) -> None:
        """
        Vérifie la qualité des données et émet des avertissements si nécessaire.
        
        Args:
            df: DataFrame contenant les séries temporelles
        """
        # Vérifier s'il y a des valeurs manquantes
        missing_values = df.isnull().sum()
        if missing_values.any():
            self._logger.warning(f"Valeurs manquantes détectées: {missing_values[missing_values > 0].to_dict()}")
        
        # Vérifier l'uniformité des intervalles de temps
        date_diffs = pd.Series(df.index).diff().dropna()
        
        if len(date_diffs.unique()) > 1:
            self._logger.warning("Intervalles de temps non uniformes détectés dans les données")
            if self.verbose:
                self._logger.debug(f"Intervalles de temps (jours): {[d.days for d in date_diffs]}")
    
    def resample_time_series(self, df: pd.DataFrame, frequency: str = 'M') -> pd.DataFrame:
        """
        Rééchantillonne la série temporelle à une fréquence régulière.
        
        Args:
            df: DataFrame contenant les séries temporelles
            frequency: Fréquence de rééchantillonnage ('D': jour, 'W': semaine, 'M': mois)
            
        Returns:
            DataFrame rééchantillonné
        """
        # Convertir l'index en datetime si ce n'est pas déjà le cas
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Rééchantillonner les données
        resampled = df.resample(frequency).mean()
        
        # Interpoler les valeurs manquantes (résultat du rééchantillonnage)
        resampled_interpolated = resampled.interpolate(method='linear')
        
        return resampled_interpolated
    
    def add_seasonal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute des caractéristiques saisonnières à la série temporelle.
        
        Args:
            df: DataFrame contenant les séries temporelles
            
        Returns:
            DataFrame enrichi avec des caractéristiques saisonnières
        """
        # Convertir l'index en datetime si ce n'est pas déjà le cas
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Créer une copie pour éviter les modifications sur le DataFrame original
        enhanced_df = df.copy()
        
        # Ajouter le mois comme caractéristique cyclique
        enhanced_df['month'] = df.index.month
        
        # Ajouter des caractéristiques saisonnières sinusoïdales
        enhanced_df['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)
        enhanced_df['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)
        
        # Ajouter le jour de l'année comme caractéristique
        enhanced_df['day_of_year'] = df.index.dayofyear
        enhanced_df['day_of_year_sin'] = np.sin(2 * np.pi * df.index.dayofyear / 365.25)
        enhanced_df['day_of_year_cos'] = np.cos(2 * np.pi * df.index.dayofyear / 365.25)
        
        return enhanced_df
    
    def detect_anomalies(self, df: pd.DataFrame, window_size: int = 3, sigma: float = 2.0) -> pd.DataFrame:
        """
        Détecte et marque les anomalies dans les séries temporelles.
        
        Args:
            df: DataFrame contenant les séries temporelles
            window_size: Taille de la fenêtre mobile pour calculer les statistiques
            sigma: Nombre d'écarts-types pour définir un point comme anomalie
            
        Returns:
            DataFrame avec colonnes supplémentaires indiquant les anomalies
        """
        # Créer une copie pour éviter les modifications sur le DataFrame original
        anomaly_df = df.copy()
        
        # Pour chaque colonne numérique
        for column in df.select_dtypes(include=[np.number]).columns:
            # Calculer la moyenne mobile et l'écart-type
            rolling_mean = df[column].rolling(window=window_size, center=True).mean()
            rolling_std = df[column].rolling(window=window_size, center=True).std()
            
            # Détecter les anomalies
            anomalies = np.abs(df[column] - rolling_mean) > (sigma * rolling_std)
            
            # Ajouter la colonne d'anomalies
            anomaly_df[f"{column}_anomaly"] = anomalies
        
        # Compter le nombre total d'anomalies par date
        anomaly_columns = [col for col in anomaly_df.columns if col.endswith('_anomaly')]
        if anomaly_columns:
            anomaly_df['total_anomalies'] = anomaly_df[anomaly_columns].sum(axis=1)
        
        return anomaly_df
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: str = 'interpolate') -> pd.DataFrame:
        """
        Gère les valeurs manquantes dans la série temporelle selon la stratégie spécifiée.
        
        Args:
            df: DataFrame contenant les séries temporelles
            strategy: Stratégie de gestion ('interpolate', 'ffill', 'bfill', 'drop')
            
        Returns:
            DataFrame avec valeurs manquantes traitées
        """
        if strategy == 'interpolate':
            return df.interpolate(method='time')
        elif strategy == 'ffill':
            return df.fillna(method='ffill')
        elif strategy == 'bfill':
            return df.fillna(method='bfill')
        elif strategy == 'drop':
            return df.dropna()
        else:
            raise ValueError(f"Stratégie inconnue: {strategy}")
