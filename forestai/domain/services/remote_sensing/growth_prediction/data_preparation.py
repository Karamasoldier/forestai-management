#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de préparation des données pour la prédiction de croissance forestière.

Ce module contient la classe DataPreparationService qui s'occupe de la 
transformation et du prétraitement des données pour la prédiction.
"""

import logging
import pandas as pd
import numpy as np
from typing import List

from forestai.domain.services.remote_sensing.models import RemoteSensingData
from forestai.domain.services.remote_sensing.growth_prediction.time_features import TimeFeatureGenerator

logger = logging.getLogger(__name__)

class DataPreparationService:
    """
    Service de préparation des données pour les modèles de prédiction de croissance.
    """
    
    def __init__(self):
        """Initialise le service de préparation des données."""
        self.time_feature_generator = TimeFeatureGenerator()
        
    def prepare_time_series_data(self, 
                                historical_data: List[RemoteSensingData],
                                target_metric: str) -> pd.DataFrame:
        """
        Prépare les données historiques sous forme de série temporelle.
        
        Args:
            historical_data: Liste des données de télédétection historiques
            target_metric: Métrique cible pour la prédiction (ex: 'canopy_height')
            
        Returns:
            DataFrame contenant la série temporelle préparée
        """
        if not historical_data:
            raise ValueError("Les données historiques ne peuvent pas être vides")
        
        # Trier par date d'acquisition
        sorted_data = sorted(historical_data, key=lambda x: x.acquisition_date)
        
        # Créer le DataFrame
        dates = [data.acquisition_date for data in sorted_data]
        
        # Extraire les valeurs de la métrique cible
        values = []
        for data in sorted_data:
            metric_value = getattr(data.metrics, target_metric, None)
            if metric_value is None:
                logger.warning(f"Métrique {target_metric} manquante pour la date {data.acquisition_date}")
                # Utiliser NaN pour les valeurs manquantes
                values.append(np.nan)
            else:
                values.append(metric_value)
        
        # Créer le DataFrame avec index de date
        df = pd.DataFrame({target_metric: values}, index=dates)
        
        # Rééchantillonner les données à une fréquence régulière si nécessaire
        # et interpoler les valeurs manquantes
        if len(df) > 1:
            min_date = df.index.min()
            max_date = df.index.max()
            
            # Déterminer la fréquence la plus appropriée
            date_diffs = pd.Series(df.index[1:]) - pd.Series(df.index[:-1])
            median_diff_days = date_diffs.median().days
            
            if median_diff_days <= 7:
                freq = 'D'  # Journalier
            elif median_diff_days <= 31:
                freq = 'MS'  # Début de mois
            else:
                freq = 'QS'  # Début de trimestre
            
            # Créer un nouvel index régulier
            regular_index = pd.date_range(start=min_date, end=max_date, freq=freq)
            
            # Rééchantillonner et interpoler
            df = df.reindex(regular_index)
            df = df.interpolate(method='time')
        
        # Ajouter des caractéristiques temporelles
        df = self.time_feature_generator.add_time_features(df, target_metric)
        
        return df