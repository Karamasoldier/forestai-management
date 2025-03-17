#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analyseur des facteurs influençant la croissance forestière.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionModel

logger = logging.getLogger(__name__)

class GrowthDriverAnalyzer:
    """
    Classe pour analyser les facteurs influençant la croissance forestière.
    
    Cette classe permet d'analyser les facteurs qui influencent la croissance 
    forestière en se basant sur les modèles prédictifs et les données disponibles.
    """
    
    def __init__(self):
        """Initialise l'analyseur de facteurs de croissance."""
        pass
    
    def analyze_model(self, model: GrowthPredictionModel) -> Dict[str, Any]:
        """
        Analyse les facteurs d'influence à partir d'un modèle prédictif.
        
        Args:
            model: Modèle prédictif entraîné
            
        Returns:
            Dictionnaire des facteurs d'influence
        """
        # Déléguer l'analyse au modèle lui-même 
        return model.analyze_features()
    
    def analyze_seasonal_patterns(self, time_series: pd.DataFrame, 
                                  growth_metrics: List[str]) -> Dict[str, Any]:
        """
        Analyse les patterns saisonniers dans les données de croissance forestière.
        
        Args:
            time_series: Série temporelle avec index de dates
            growth_metrics: Liste des métriques de croissance à analyser
            
        Returns:
            Dictionnaire des patterns saisonniers
        """
        if not isinstance(time_series.index, pd.DatetimeIndex):
            raise ValueError("Le DataFrame doit avoir un index temporel (DatetimeIndex)")
        
        result = {}
        
        # Ajouter des informations temporelles
        df = time_series.copy()
        df['month'] = df.index.month
        df['season'] = df.index.month % 12 // 3 + 1  # 1-4 pour les saisons
        
        # Analyser chaque métrique
        for metric in growth_metrics:
            if metric not in df.columns:
                logger.warning(f"Métrique '{metric}' non trouvée dans les données")
                continue
                
            # Moyenne et écart-type mensuel
            monthly_stats = df.groupby('month')[metric].agg(['mean', 'std', 'count'])
            
            # Moyenne saisonnière
            seasonal_stats = df.groupby('season')[metric].agg(['mean', 'std', 'count'])
            season_names = {1: 'hiver', 2: 'printemps', 3: 'été', 4: 'automne'}
            seasonal_stats.index = [season_names[s] for s in seasonal_stats.index]
            
            # Calculer la force de la saisonnalité
            overall_std = df[metric].std()
            monthly_variation = monthly_stats['mean'].std()
            
            # Force de la saisonnalité (ratio entre variation mensuelle et variation totale)
            seasonality_strength = monthly_variation / overall_std if overall_std > 0 else 0
            
            # Trouver le mois de pic et de creux
            peak_month = monthly_stats['mean'].idxmax()
            trough_month = monthly_stats['mean'].idxmin()
            
            # Traduire les mois en noms
            month_names = {1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril', 
                          5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août', 
                          9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'}
            
            result[metric] = {
                'monthly_stats': monthly_stats.to_dict(),
                'seasonal_stats': seasonal_stats.to_dict(),
                'seasonality_strength': seasonality_strength,
                'peak_month': month_names[peak_month],
                'trough_month': month_names[trough_month],
                'peak_season': seasonal_stats['mean'].idxmax(),
                'trough_season': seasonal_stats['mean'].idxmin(),
                'max_amplitude': monthly_stats['mean'].max() - monthly_stats['mean'].min()
            }
        
        return result
    
    def analyze_trend_components(self, time_series: pd.DataFrame,
                                growth_metrics: List[str]) -> Dict[str, Any]:
        """
        Analyse les composantes de tendance à long terme.
        
        Args:
            time_series: Série temporelle avec index de dates
            growth_metrics: Liste des métriques de croissance à analyser
            
        Returns:
            Dictionnaire des composantes de tendance
        """
        if not isinstance(time_series.index, pd.DatetimeIndex):
            raise ValueError("Le DataFrame doit avoir un index temporel (DatetimeIndex)")
        
        result = {}
        
        # Ajouter une caractéristique numérique pour le temps
        df = time_series.copy()
        df['time_idx'] = (df.index - df.index.min()).days
        
        # Analyser chaque métrique
        for metric in growth_metrics:
            if metric not in df.columns:
                logger.warning(f"Métrique '{metric}' non trouvée dans les données")
                continue
                
            try:
                # Modèle de tendance linéaire
                X = df['time_idx'].values.reshape(-1, 1)
                y = df[metric].values
                
                # Régression linéaire simple
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(X, y)
                
                slope = model.coef_[0]
                intercept = model.intercept_
                
                # Prédictions du modèle
                y_pred = model.predict(X)
                
                # Calcul du R²
                from sklearn.metrics import r2_score
                r2 = r2_score(y, y_pred)
                
                # Analyse des résidus
                residuals = y - y_pred
                residual_std = np.std(residuals)
                
                # Calculer la croissance annuelle moyenne en pourcentage
                if len(df) >= 2:
                    time_span_days = df['time_idx'].max() - df['time_idx'].min()
                    if time_span_days > 0:
                        time_span_years = time_span_days / 365.25
                        total_change = slope * time_span_days
                        
                        # Si la valeur initiale est positive, calculer en pourcentage
                        if y[0] > 0:
                            annual_pct_change = (((y[0] + total_change) / y[0]) ** (1 / time_span_years) - 1) * 100
                        else:
                            annual_pct_change = None
                    else:
                        total_change = 0
                        annual_pct_change = None
                else:
                    total_change = 0
                    annual_pct_change = None
                
                result[metric] = {
                    'trend_type': 'linear',
                    'slope': slope,
                    'intercept': intercept,
                    'r2': r2,
                    'residual_std': residual_std,
                    'total_change': total_change,
                    'annual_pct_change': annual_pct_change,
                    'growth_direction': 'positive' if slope > 0 else 'negative' if slope < 0 else 'stable'
                }
                
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse de tendance pour {metric}: {str(e)}")
                result[metric] = {
                    'trend_type': 'error',
                    'error': str(e)
                }
        
        return result
    
    def analyze_climate_impact(self, time_series: pd.DataFrame, 
                              climate_data: pd.DataFrame,
                              growth_metrics: List[str]) -> Dict[str, Any]:
        """
        Analyse l'impact des variables climatiques sur la croissance.
        
        Args:
            time_series: Série temporelle de croissance avec index de dates
            climate_data: Données climatiques avec index de dates
            growth_metrics: Liste des métriques de croissance à analyser
            
        Returns:
            Dictionnaire des impacts climatiques
        """
        if not isinstance(time_series.index, pd.DatetimeIndex):
            raise ValueError("Le DataFrame time_series doit avoir un index temporel")
            
        if not isinstance(climate_data.index, pd.DatetimeIndex):
            raise ValueError("Le DataFrame climate_data doit avoir un index temporel")
        
        # Fusionner les données
        df = time_series.copy()
        
        # Réindexer les données climatiques sur les mêmes dates
        climate_reindexed = climate_data.reindex(df.index, method='nearest')
        
        # Ajouter les colonnes climatiques
        for col in climate_data.columns:
            df[f'climate_{col}'] = climate_reindexed[col]
        
        result = {}
        
        # Analyser chaque métrique
        for metric in growth_metrics:
            if metric not in df.columns:
                logger.warning(f"Métrique '{metric}' non trouvée dans les données")
                continue
                
            # Analyser les corrélations
            climate_cols = [col for col in df.columns if col.startswith('climate_')]
            correlations = {}
            
            for col in climate_cols:
                # Extraire le nom réel de la variable climatique (sans le préfixe)
                climate_var = col.replace('climate_', '')
                corr = df[[metric, col]].corr().iloc[0, 1]
                correlations[climate_var] = corr
            
            # Trier les corrélations par valeur absolue décroissante
            sorted_correlations = sorted(correlations.items(), 
                                        key=lambda x: abs(x[1]), 
                                        reverse=True)
            
            # Modèle de régression
            try:
                from sklearn.linear_model import LinearRegression
                
                # Sélectionner uniquement les variables climatiques
                X = df[climate_cols].values
                y = df[metric].values
                
                # Standardiser les variables pour comparer les coefficients
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                # Régression linéaire
                model = LinearRegression()
                model.fit(X_scaled, y)
                
                # R² du modèle
                r2 = model.score(X_scaled, y)
                
                # Importance des variables (coefficients standardisés)
                feature_importance = {}
                for i, col in enumerate([c.replace('climate_', '') for c in climate_cols]):
                    feature_importance[col] = model.coef_[i]
                
                # Trier par importance absolue
                sorted_importance = sorted(feature_importance.items(),
                                          key=lambda x: abs(x[1]),
                                          reverse=True)
                
                # Récupérer les variables avec une importance significative
                significant_vars = [var for var, imp in sorted_importance 
                                    if abs(imp) > 0.1 * max(abs(v) for v in model.coef_)]
                
                regression_results = {
                    'r2': r2,
                    'feature_importance': dict(sorted_importance),
                    'significant_vars': significant_vars
                }
                
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse de régression pour {metric}: {str(e)}")
                regression_results = {
                    'error': str(e)
                }
            
            # Analyse de la saisonnalité conjointe
            seasonal_alignment = {}
            
            try:
                # Regrouper par mois pour voir si les pics climatiques correspondent aux pics de croissance
                monthly_growth = df.groupby(df.index.month)[metric].mean()
                
                for col in climate_cols:
                    climate_var = col.replace('climate_', '')
                    monthly_climate = df.groupby(df.index.month)[col].mean()
                    
                    # Corrélation entre moyennes mensuelles
                    seasonal_corr = monthly_growth.corr(monthly_climate)
                    
                    # Décalage pour la corrélation max (pour détecter les effets retardés)
                    max_lag_corr = -1
                    max_lag = 0
                    
                    for lag in range(1, 7):  # Tester des décalages de 1 à 6 mois
                        shifted_climate = monthly_climate.shift(-lag)
                        valid_idxs = ~shifted_climate.isna()
                        if sum(valid_idxs) >= 3:  # Au moins 3 points de données valides
                            lag_corr = monthly_growth[valid_idxs].corr(shifted_climate[valid_idxs])
                            if abs(lag_corr) > abs(max_lag_corr):
                                max_lag_corr = lag_corr
                                max_lag = lag
                    
                    seasonal_alignment[climate_var] = {
                        'seasonal_correlation': seasonal_corr,
                        'max_lag_correlation': max_lag_corr,
                        'optimal_lag_months': max_lag
                    }
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse saisonnière pour {metric}: {str(e)}")
                seasonal_alignment = {
                    'error': str(e)
                }
            
            # Résultats complets pour cette métrique
            result[metric] = {
                'correlations': dict(sorted_correlations),
                'regression': regression_results,
                'seasonal_alignment': seasonal_alignment,
                'top_positive_factors': [var for var, corr in sorted_correlations if corr > 0][:3],
                'top_negative_factors': [var for var, corr in sorted_correlations if corr < 0][:3]
            }
        
        return result
    
    def analyze_spatial_variations(self, spatial_growth_data: Dict[str, pd.DataFrame],
                                  growth_metrics: List[str]) -> Dict[str, Any]:
        """
        Analyse les variations spatiales de croissance entre différentes parcelles.
        
        Args:
            spatial_growth_data: Dictionnaire {id_parcelle: dataframe} avec les séries temporelles de croissance
            growth_metrics: Liste des métriques de croissance à analyser
            
        Returns:
            Dictionnaire des variations spatiales
        """
        result = {}
        
        # Préparer les données pour chaque métrique
        for metric in growth_metrics:
            # Vérifier si la métrique existe dans toutes les parcelles
            metric_exists = all(metric in df.columns for df in spatial_growth_data.values())
            
            if not metric_exists:
                logger.warning(f"Métrique '{metric}' non présente dans toutes les parcelles")
                continue
            
            # Récupérer les statistiques pour chaque parcelle
            parcel_stats = {}
            for parcel_id, df in spatial_growth_data.items():
                parcel_stats[parcel_id] = {
                    'mean': df[metric].mean(),
                    'std': df[metric].std(),
                    'min': df[metric].min(),
                    'max': df[metric].max(),
                    'growth_rate': None  # Sera calculé ci-dessous
                }
                
                # Calculer le taux de croissance si possible
                if len(df) >= 2:
                    # Trier par date
                    sorted_df = df.sort_index()
                    
                    # Calculer le taux de croissance annualisé
                    first_value = sorted_df[metric].iloc[0]
                    last_value = sorted_df[metric].iloc[-1]
                    time_span_days = (sorted_df.index[-1] - sorted_df.index[0]).days
                    
                    if time_span_days > 0 and first_value > 0:
                        time_span_years = time_span_days / 365.25
                        parcel_stats[parcel_id]['growth_rate'] = (
                            ((last_value / first_value) ** (1 / time_span_years) - 1) * 100
                        )
            
            # Calculer les statistiques entre parcelles
            parcel_means = np.array([stats['mean'] for stats in parcel_stats.values()])
            parcel_growth_rates = np.array([
                stats['growth_rate'] for stats in parcel_stats.values() 
                if stats['growth_rate'] is not None
            ])
            
            # Identifier les parcelles avec croissance max/min
            best_parcel = max(parcel_stats.items(), key=lambda x: x[1]['growth_rate'] or -float('inf'))
            worst_parcel = min(parcel_stats.items(), key=lambda x: x[1]['growth_rate'] or float('inf'))
            
            # Analyse de la variation spatiale
            result[metric] = {
                'parcel_stats': parcel_stats,
                'spatial_variation': {
                    'mean_across_parcels': np.mean(parcel_means),
                    'std_across_parcels': np.std(parcel_means),
                    'cv_across_parcels': np.std(parcel_means) / np.mean(parcel_means) if np.mean(parcel_means) > 0 else None,
                    'mean_growth_rate': np.mean(parcel_growth_rates) if len(parcel_growth_rates) > 0 else None,
                    'std_growth_rate': np.std(parcel_growth_rates) if len(parcel_growth_rates) > 0 else None
                },
                'best_performing_parcel': {
                    'id': best_parcel[0],
                    'growth_rate': best_parcel[1]['growth_rate']
                },
                'worst_performing_parcel': {
                    'id': worst_parcel[0],
                    'growth_rate': worst_parcel[1]['growth_rate']
                }
            }
        
        return result
    
    def generate_comprehensive_report(self, 
                                     time_series: pd.DataFrame,
                                     models: Dict[str, GrowthPredictionModel],
                                     growth_metrics: List[str],
                                     climate_data: Optional[pd.DataFrame] = None,
                                     spatial_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Génère un rapport complet sur les facteurs de croissance forestière.
        
        Args:
            time_series: Série temporelle principale avec index de dates
            models: Dictionnaire des modèles prédictifs {nom_métrique: modèle}
            growth_metrics: Liste des métriques de croissance à analyser
            climate_data: Données climatiques avec index de dates (optionnel)
            spatial_data: Données de différentes parcelles (optionnel)
            
        Returns:
            Rapport complet des facteurs de croissance
        """
        report = {
            'generation_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics_analyzed': growth_metrics,
            'data_span': {
                'start': time_series.index.min().strftime('%Y-%m-%d'),
                'end': time_series.index.max().strftime('%Y-%m-%d'),
                'duration_days': (time_series.index.max() - time_series.index.min()).days
            },
            'seasonal_patterns': {},
            'trend_analysis': {},
            'model_analysis': {},
            'climate_impact': {},
            'spatial_variations': {},
            'summary': {}
        }
        
        # Analyse saisonnière
        report['seasonal_patterns'] = self.analyze_seasonal_patterns(time_series, growth_metrics)
        
        # Analyse de tendance
        report['trend_analysis'] = self.analyze_trend_components(time_series, growth_metrics)
        
        # Analyse des modèles
        for metric, model in models.items():
            if metric in growth_metrics:
                report['model_analysis'][metric] = self.analyze_model(model)
        
        # Analyse climatique
        if climate_data is not None:
            report['climate_impact'] = self.analyze_climate_impact(time_series, climate_data, growth_metrics)
        
        # Analyse spatiale
        if spatial_data is not None:
            report['spatial_variations'] = self.analyze_spatial_variations(spatial_data, growth_metrics)
        
        # Générer un résumé pour chaque métrique
        for metric in growth_metrics:
            summary = {
                'growth_rate': None,
                'seasonality': None,
                'key_drivers': [],
                'spatial_insights': None,
                'future_projection': None
            }
            
            # Taux de croissance
            if metric in report['trend_analysis'] and 'annual_pct_change' in report['trend_analysis'][metric]:
                summary['growth_rate'] = report['trend_analysis'][metric]['annual_pct_change']
            
            # Saisonnalité
            if metric in report['seasonal_patterns']:
                seas_strength = report['seasonal_patterns'][metric]['seasonality_strength']
                peak_season = report['seasonal_patterns'][metric]['peak_season']
                summary['seasonality'] = {
                    'strength': seas_strength,
                    'peak_season': peak_season,
                    'significance': 'forte' if seas_strength > 0.5 else 'moyenne' if seas_strength > 0.2 else 'faible'
                }
            
            # Facteurs climatiques clés
            if climate_data is not None and metric in report['climate_impact']:
                if 'top_positive_factors' in report['climate_impact'][metric]:
                    for factor in report['climate_impact'][metric]['top_positive_factors']:
                        summary['key_drivers'].append({
                            'factor': factor,
                            'type': 'climat',
                            'impact': 'positif'
                        })
                
                if 'top_negative_factors' in report['climate_impact'][metric]:
                    for factor in report['climate_impact'][metric]['top_negative_factors']:
                        summary['key_drivers'].append({
                            'factor': factor,
                            'type': 'climat',
                            'impact': 'négatif'
                        })
            
            # Résumé spatial
            if spatial_data is not None and metric in report['spatial_variations']:
                spatial_info = report['spatial_variations'][metric]
                summary['spatial_insights'] = {
                    'variation': spatial_info['spatial_variation']['cv_across_parcels'],
                    'best_parcel': spatial_info['best_performing_parcel']['id'],
                    'worst_parcel': spatial_info['worst_performing_parcel']['id']
                }
            
            # Projection future basée sur le modèle
            if metric in models:
                try:
                    # Prédire pour 5 ans (60 mois)
                    predictions, conf_int = models[metric].predict(horizon=60)
                    
                    # Calculer la croissance projetée
                    first_prediction = predictions.iloc[0]
                    last_prediction = predictions.iloc[-1]
                    
                    if first_prediction > 0:
                        projected_growth_rate = ((last_prediction / first_prediction) ** (1 / 5) - 1) * 100
                        
                        summary['future_projection'] = {
                            'five_year_change_pct': projected_growth_rate,
                            'confidence': 'haute' if models[metric].metrics.get('test_mape', 100) < 10 else 
                                         'moyenne' if models[metric].metrics.get('test_mape', 100) < 20 else 'basse'
                        }
                except Exception as e:
                    logger.warning(f"Erreur lors de la projection future pour {metric}: {str(e)}")
            
            report['summary'][metric] = summary
        
        return report
