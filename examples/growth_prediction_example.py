#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation du module de prédiction de croissance forestière.

Ce script montre comment utiliser le module ForestGrowthPredictor pour prédire
la croissance forestière à partir de données de télédétection et générer des rapports.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List

# Ajouter le répertoire parent au path pour l'import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forestai.domain.services.remote_sensing.models import (
    RemoteSensingData,
    ForestMetrics,
    RemoteSensingSource,
    VegetationIndex
)
from forestai.domain.services.remote_sensing.growth_prediction import ForestGrowthPredictor

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def generate_sample_data(num_samples: int = 24) -> List[RemoteSensingData]:
    """
    Génère des données de test pour la prédiction de croissance.
    
    Args:
        num_samples: Nombre de points de données à générer
        
    Returns:
        Liste de données de télédétection simulées
    """
    # Date de départ (2 ans en arrière)
    start_date = datetime.now() - timedelta(days=365*2)
    
    # Tendance de croissance pour la hauteur de canopée
    base_canopy_height = 15.0  # hauteur initiale
    yearly_growth = 0.5  # croissance annuelle moyenne
    
    # Tendance pour la biomasse
    base_biomass = 120.0  # biomasse initiale
    yearly_biomass_growth = 5.0  # croissance annuelle moyenne
    
    # Générer les données
    data = []
    for i in range(num_samples):
        # Date d'acquisition (mensuel)
        date = start_date + timedelta(days=30*i)
        
        # Calculer les métriques avec tendance et saisonnalité
        # Saisonnalité: croissance plus rapide au printemps/été
        month = date.month
        seasonal_factor = 1.0 + 0.3 * np.sin((month - 3) * np.pi / 6)  # pic en juin
        
        # Ajouter un peu de bruit aléatoire
        noise = np.random.normal(0, 0.1)
        
        # Calculer la hauteur de canopée avec tendance, saisonnalité et bruit
        days_passed = (date - start_date).days
        years_passed = days_passed / 365.0
        canopy_height = base_canopy_height + yearly_growth * years_passed * seasonal_factor + noise
        
        # Calculer la biomasse
        biomass = base_biomass + yearly_biomass_growth * years_passed * seasonal_factor + np.random.normal(0, 2.0)
        
        # Calculer le stock de carbone (environ 50% de la biomasse)
        carbon_stock = biomass * 0.5 + np.random.normal(0, 1.0)
        
        # Calculer la densité des tiges (inverse à la hauteur - plus les arbres grandissent, moins il y en a)
        initial_density = 1200
        stem_density = initial_density - 50 * years_passed + np.random.normal(0, 20)
        
        # Créer l'objet ForestMetrics
        metrics = ForestMetrics(
            canopy_height=canopy_height,
            biomass=biomass,
            carbon_stock=carbon_stock,
            stem_density=stem_density,
            canopy_cover=65.0 + years_passed * 2.0 + np.random.normal(0, 1.0)
        )
        
        # Créer les indices de végétation
        vegetation_indices = {
            VegetationIndex.NDVI: 0.75 + 0.05 * np.sin((month - 3) * np.pi / 6) + np.random.normal(0, 0.02),
            VegetationIndex.LAI: 3.5 + 0.8 * np.sin((month - 3) * np.pi / 6) + np.random.normal(0, 0.1)
        }
        
        # Créer l'objet RemoteSensingData
        rs_data = RemoteSensingData(
            parcel_id="TEST-PARCEL-001",
            acquisition_date=date,
            source=RemoteSensingSource.SENTINEL_2,
            metrics=metrics,
            vegetation_indices=vegetation_indices
        )
        
        data.append(rs_data)
    
    return data

def run_prediction_example():
    """Exécute l'exemple de prédiction de croissance forestière."""
    logging.info("Génération des données de test...")
    historical_data = generate_sample_data(24)  # 2 ans de données mensuelles
    
    logging.info("Initialisation du prédicteur de croissance forestière...")
    predictor = ForestGrowthPredictor()
    
    # Liste des métriques à prédire
    target_metrics = ['canopy_height', 'biomass', 'carbon_stock', 'stem_density']
    
    # Horizon de prédiction
    horizon_months = 12  # Prédiction sur 1 an
    
    logging.info(f"Prédiction de la croissance forestière sur {horizon_months} mois...")
    prediction = predictor.predict_growth(
        parcel_id="TEST-PARCEL-001",
        historical_data=historical_data,
        target_metrics=target_metrics,
        horizon_months=horizon_months
    )
    
    # Générer un rapport au format Markdown
    logging.info("Génération du rapport...")
    report = predictor.generate_growth_report(prediction, format_type="markdown")
    
    # Afficher une partie du rapport
    logging.info("Exemple de rapport de prédiction (format Markdown):")
    print("\n" + report[:500] + "...\n")
    
    # Sauvegarder le rapport
    with open("growth_prediction_report.md", "w") as f:
        f.write(report)
    logging.info("Rapport sauvegardé dans 'growth_prediction_report.md'")
    
    # Comparer différents scénarios climatiques
    logging.info("Comparaison de différents scénarios climatiques...")
    scenarios = ['baseline', 'rcp4.5', 'rcp8.5']
    
    scenario_predictions = predictor.compare_climate_scenarios(
        parcel_id="TEST-PARCEL-001",
        historical_data=historical_data,
        target_metrics=target_metrics,
        scenarios=scenarios,
        horizon_months=horizon_months
    )
    
    # Générer un rapport de comparaison
    comparison_report = predictor.generate_comparison_report(
        scenario_predictions, format_type="markdown"
    )
    
    # Sauvegarder le rapport de comparaison
    with open("climate_scenarios_comparison.md", "w") as f:
        f.write(comparison_report)
    logging.info("Rapport de comparaison sauvegardé dans 'climate_scenarios_comparison.md'")
    
    # Obtenir des recommandations d'adaptation
    recommendations = predictor.get_adaptation_recommendations(prediction)
    logging.info("Recommandations d'adaptation:")
    for rec in recommendations:
        print(f"- {rec['category']}: {rec['description']}")
    
    # Visualisation des prédictions (exemple pour la hauteur de canopée)
    visualize_predictions(historical_data, scenario_predictions, 'canopy_height')

def visualize_predictions(historical_data, scenario_predictions, metric_name):
    """
    Visualise les prédictions de croissance pour différents scénarios.
    
    Args:
        historical_data: Données historiques
        scenario_predictions: Prédictions par scénario
        metric_name: Nom de la métrique à visualiser
    """
    plt.figure(figsize=(12, 6))
    
    # Préparer les données historiques
    historical_dates = [data.acquisition_date for data in historical_data]
    historical_values = [getattr(data.metrics, metric_name, None) for data in historical_data]
    
    # Tracer les données historiques
    plt.plot(historical_dates, historical_values, 'o-', label='Données historiques', color='black')
    
    # Couleurs pour les différents scénarios
    colors = ['blue', 'green', 'red', 'purple', 'orange']
    
    # Tracer les prédictions pour chaque scénario
    for i, (scenario, prediction) in enumerate(scenario_predictions.items()):
        # Extraire les dates et valeurs prédites
        pred_dates = []
        pred_values = []
        confidence_lower = []
        confidence_upper = []
        
        for date, metrics, intervals in prediction.predictions:
            value = getattr(metrics, metric_name, None)
            if value is not None:
                pred_dates.append(date)
                pred_values.append(value)
                
                if metric_name in intervals:
                    confidence_lower.append(intervals[metric_name][0])
                    confidence_upper.append(intervals[metric_name][1])
        
        # Tracer la prédiction
        color = colors[i % len(colors)]
        plt.plot(pred_dates, pred_values, 's-', label=f'Prédiction ({scenario})', color=color)
        
        # Tracer l'intervalle de confiance si disponible
        if confidence_lower and confidence_upper:
            plt.fill_between(pred_dates, confidence_lower, confidence_upper, alpha=0.2, color=color)
    
    # Configurer le graphique
    plt.xlabel('Date')
    plt.ylabel(f"{metric_name.replace('_', ' ').title()}")
    plt.title(f"Prédiction de croissance: {metric_name}")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Sauvegarder le graphique
    plt.tight_layout()
    plt.savefig(f"growth_prediction_{metric_name}.png")
    plt.close()
    
    logging.info(f"Visualisation sauvegardée dans 'growth_prediction_{metric_name}.png'")

if __name__ == "__main__":
    run_prediction_example()
