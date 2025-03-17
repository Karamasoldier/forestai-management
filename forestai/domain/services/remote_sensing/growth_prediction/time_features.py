#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Générateur de caractéristiques temporelles pour modèles de prédiction.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TimeFeatureGenerator:
    """
    Classe pour générer des caractéristiques temporelles à partir de dates.
    
    Cette classe permet de transformer des dates en caractéristiques
    numériques utilisables par des modèles d'apprentissage automatique.
    """
    
    def __init__(self, cyclical_features: bool = True, trend_features: bool = True):
        """
        Initialise le générateur de caractéristiques temporelles.
        
        Args:
            cyclical_features: Si True, crée des caractéristiques cycliques (sin/cos)
            trend_features: Si True, crée des caractéristiques de tendance temporelle
        """
        self.cyclical_features = cyclical_features
        self.trend_features = trend_features
        self.min_date = None
    
    def fit(self, date_index: pd.DatetimeIndex) -> 'TimeFeatureGenerator':
        """
        Adapte le générateur aux données (trouve la date minimale pour les tendances).
        
        Args:
            date_index: Index de dates à partir duquel adapter
            
        Returns:
            Le générateur lui-même (pour le chaînage)
        """
        if self.trend_features:
            self.min_date = date_index.min()
        
        return self
    
    def transform(self, date_index: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Transforme un index de dates en DataFrame de caractéristiques.
        
        Args:
            date_index: Index de dates à transformer
            
        Returns:
            DataFrame contenant les caractéristiques temporelles
        """
        # Si pas encore adapté, le faire maintenant
        if self.trend_features and self.min_date is None:
            self.fit(date_index)
        
        # Créer un DataFrame avec diverses features temporelles
        features = pd.DataFrame(index=date_index)
        
        # Features temporelles basiques
        features['year'] = date_index.year
        features['month'] = date_index.month
        features['day'] = date_index.day
        features['dayofyear'] = date_index.dayofyear
        features['quarter'] = date_index.quarter
        features['week'] = date_index.isocalendar().week
        features['day_of_week'] = date_index.dayofweek
        
        # Features cycliques pour représenter la saisonnalité
        if self.cyclical_features:
            # Mois (cycle annuel)
            features['month_sin'] = np.sin(2 * np.pi * date_index.month / 12)
            features['month_cos'] = np.cos(2 * np.pi * date_index.month / 12)
            
            # Jour (cycle annuel)
            features['day_sin'] = np.sin(2 * np.pi * date_index.dayofyear / 365.25)
            features['day_cos'] = np.cos(2 * np.pi * date_index.dayofyear / 365.25)
            
            # Jour de la semaine (cycle hebdomadaire)
            features['weekday_sin'] = np.sin(2 * np.pi * date_index.dayofweek / 7)
            features['weekday_cos'] = np.cos(2 * np.pi * date_index.dayofweek / 7)
            
            # Heure (cycle journalier) - si l'index contient des heures
            if not (date_index.hour == 0).all():
                features['hour_sin'] = np.sin(2 * np.pi * date_index.hour / 24)
                features['hour_cos'] = np.cos(2 * np.pi * date_index.hour / 24)
        
        # Tendance temporelle (nombre de jours depuis le début)
        if self.trend_features:
            features['time_idx'] = (date_index - self.min_date).days
            features['time_idx_sqrt'] = np.sqrt(features['time_idx'])  # Croissance sous-linéaire
            features['time_idx_squared'] = features['time_idx'] ** 2  # Croissance quadratique
        
        return features
    
    def fit_transform(self, date_index: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Adapte le générateur aux données puis transforme l'index en caractéristiques.
        
        Args:
            date_index: Index de dates à adapter et transformer
            
        Returns:
            DataFrame contenant les caractéristiques temporelles
        """
        return self.fit(date_index).transform(date_index)
    
    def add_holidays(self, df: pd.DataFrame, country_code: str = 'FR') -> pd.DataFrame:
        """
        Ajoute des indicateurs de jours fériés au DataFrame.
        
        Args:
            df: DataFrame contenant déjà des caractéristiques temporelles
            country_code: Code pays ISO à deux lettres pour les jours fériés
            
        Returns:
            DataFrame avec caractéristiques de jours fériés ajoutées
        """
        try:
            from holidays import country_holidays
            
            # Créer une liste de jours fériés pour le pays
            years = df.index.year.unique()
            country_holiday_dict = {}
            
            for year in years:
                country_holiday_dict.update(country_holidays(country_code, years=year))
            
            # Ajouter indicateur de jour férié
            df['is_holiday'] = df.index.date.map(lambda date: date in country_holiday_dict).astype(int)
            
            # Ajouter distance au jour férié le plus proche
            date_array = np.array([d.date() for d in df.index])
            holiday_dates = np.array(list(country_holiday_dict.keys()))
            
            closest_holiday_distance = []
            for date in date_array:
                days_diff = np.abs([(date - holiday).days for holiday in holiday_dates])
                closest_holiday_distance.append(np.min(days_diff))
            
            df['days_to_holiday'] = closest_holiday_distance
            
        except ImportError:
            logger.warning("Package 'holidays' non disponible, impossible d'ajouter les jours fériés.")
        
        return df
    
    def add_seasonality_indicators(self, df: pd.DataFrame, 
                                  hemisphere: str = 'N') -> pd.DataFrame:
        """
        Ajoute des indicateurs de saison au DataFrame.
        
        Args:
            df: DataFrame contenant déjà des caractéristiques temporelles
            hemisphere: 'N' pour hémisphère nord, 'S' pour hémisphère sud
            
        Returns:
            DataFrame avec indicateurs de saison ajoutés
        """
        month = df.index.month
        day = df.index.day
        
        if hemisphere == 'N':
            # Hémisphère nord
            df['is_spring'] = ((month == 3) & (day >= 21) | (month == 4) | (month == 5) | 
                             (month == 6) & (day < 21)).astype(int)
            df['is_summer'] = ((month == 6) & (day >= 21) | (month == 7) | (month == 8) | 
                             (month == 9) & (day < 23)).astype(int)
            df['is_autumn'] = ((month == 9) & (day >= 23) | (month == 10) | (month == 11) | 
                             (month == 12) & (day < 21)).astype(int)
            df['is_winter'] = ((month == 12) & (day >= 21) | (month == 1) | (month == 2) | 
                             (month == 3) & (day < 21)).astype(int)
        else:
            # Hémisphère sud
            df['is_spring'] = ((month == 9) & (day >= 23) | (month == 10) | (month == 11) | 
                             (month == 12) & (day < 21)).astype(int)
            df['is_summer'] = ((month == 12) & (day >= 21) | (month == 1) | (month == 2) | 
                             (month == 3) & (day < 21)).astype(int)
            df['is_autumn'] = ((month == 3) & (day >= 21) | (month == 4) | (month == 5) | 
                             (month == 6) & (day < 21)).astype(int)
            df['is_winter'] = ((month == 6) & (day >= 21) | (month == 7) | (month == 8) | 
                             (month == 9) & (day < 23)).astype(int)
        
        # Saison comme variable catégorielle
        seasons = {0: 'winter', 1: 'spring', 2: 'summer', 3: 'autumn'}
        season_values = df['is_spring'] * 1 + df['is_summer'] * 2 + df['is_autumn'] * 3
        df['season'] = season_values.map(seasons)
        
        # Saison comme variable cyclique (pour la continuité entre hiver et printemps)
        season_month = month % 12  # 0-11
        if hemisphere == 'S':
            # Décalage de 6 mois pour l'hémisphère sud
            season_month = (season_month + 6) % 12
        
        df['season_sin'] = np.sin(2 * np.pi * season_month / 12)
        df['season_cos'] = np.cos(2 * np.pi * season_month / 12)
        
        return df
