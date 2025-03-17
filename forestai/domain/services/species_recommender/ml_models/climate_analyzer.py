#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module d'analyse climatique avancée pour le système de recommandation d'espèces.

Ce module fournit des fonctionnalités d'analyse climatique avancée pour
comparer l'adaptabilité des espèces forestières dans différents scénarios
de changement climatique.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import logging

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.models import (
    SpeciesData,
    DroughtResistance,
    FrostResistance
)

logger = get_logger(__name__)


class ClimateScenarioAnalyzer:
    """
    Analyseur de scénarios climatiques pour les recommandations d'espèces.
    
    Cette classe fournit des méthodes pour analyser l'adaptabilité des espèces
    dans différents scénarios de changement climatique et générer des
    recommandations adaptées à ces scénarios.
    """
    
    def __init__(self, ml_recommender=None):
        """
        Initialise l'analyseur de scénarios climatiques.
        
        Args:
            ml_recommender: Recommandeur ML à utiliser (facultatif)
        """
        self.ml_recommender = ml_recommender
        
        # Définir les scénarios de changement climatique prédéfinis
        self.predefined_scenarios = {
            "rcp26_2050": {
                "name": "RCP 2.6 - 2050",
                "description": "Scénario optimiste (réchauffement limité à 2°C)",
                "temperature_increase": 1.0,
                "precipitation_change_factor": 0.95,
                "drought_index_increase": 1.5
            },
            "rcp45_2050": {
                "name": "RCP 4.5 - 2050",
                "description": "Scénario modéré",
                "temperature_increase": 1.8,
                "precipitation_change_factor": 0.92,
                "drought_index_increase": 2.0
            },
            "rcp85_2050": {
                "name": "RCP 8.5 - 2050",
                "description": "Scénario pessimiste",
                "temperature_increase": 2.4,
                "precipitation_change_factor": 0.85,
                "drought_index_increase": 3.0
            },
            "rcp26_2100": {
                "name": "RCP 2.6 - 2100",
                "description": "Scénario optimiste (réchauffement limité à 2°C)",
                "temperature_increase": 1.5,
                "precipitation_change_factor": 0.92,
                "drought_index_increase": 2.0
            },
            "rcp45_2100": {
                "name": "RCP 4.5 - 2100",
                "description": "Scénario modéré",
                "temperature_increase": 2.5,
                "precipitation_change_factor": 0.85,
                "drought_index_increase": 3.0
            },
            "rcp85_2100": {
                "name": "RCP 8.5 - 2100",
                "description": "Scénario pessimiste",
                "temperature_increase": 4.5,
                "precipitation_change_factor": 0.75,
                "drought_index_increase": 5.0
            }
        }
        
        logger.info("ClimateScenarioAnalyzer initialisé")
    
    def get_predefined_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """
        Récupère un scénario de changement climatique prédéfini.
        
        Args:
            scenario_id: Identifiant du scénario
            
        Returns:
            Définition du scénario ou None si non trouvé
        """
        if scenario_id in self.predefined_scenarios:
            return self.predefined_scenarios[scenario_id]
        else:
            logger.warning(f"Scénario non trouvé: {scenario_id}")
            return None
    
    def project_climate_data(self, current_climate_data: Dict[str, Any], 
                            scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Projette les données climatiques actuelles selon un scénario de changement.
        
        Args:
            current_climate_data: Données climatiques actuelles
            scenario: Scénario de changement climatique à appliquer
            
        Returns:
            Données climatiques projetées
        """
        # Extraire les facteurs de changement du scénario
        temp_increase = scenario.get("temperature_increase", 0)
        precip_factor = scenario.get("precipitation_change_factor", 1.0)
        drought_increase = scenario.get("drought_index_increase", 0)
        
        # Projeter les données climatiques
        projected_data = current_climate_data.copy()
        
        # Augmenter les températures
        if "mean_annual_temperature" in projected_data:
            projected_data["mean_annual_temperature"] += temp_increase
        
        if "min_temperature" in projected_data:
            projected_data["min_temperature"] += temp_increase
        
        if "max_temperature" in projected_data:
            projected_data["max_temperature"] += temp_increase
        
        # Modifier les précipitations
        if "annual_precipitation" in projected_data:
            projected_data["annual_precipitation"] *= precip_factor
        
        # Augmenter l'indice de sécheresse
        if "drought_index" in projected_data:
            projected_data["drought_index"] = min(10, projected_data["drought_index"] + drought_increase)
        
        return projected_data
    
    def analyze_species_climate_adaptability(self, species: SpeciesData, 
                                           current_climate: Dict[str, Any], 
                                           future_climate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse l'adaptabilité d'une espèce face au changement climatique.
        
        Args:
            species: Données de l'espèce
            current_climate: Données climatiques actuelles
            future_climate: Données climatiques futures
            
        Returns:
            Analyse d'adaptabilité
        """
        # Calculer les différences climatiques
        temp_diff = future_climate.get("mean_annual_temperature", 0) - current_climate.get("mean_annual_temperature", 0)
        precip_diff = current_climate.get("annual_precipitation", 0) - future_climate.get("annual_precipitation", 0)
        drought_diff = future_climate.get("drought_index", 0) - current_climate.get("drought_index", 0)
        
        # Évaluer l'adaptabilité selon les caractéristiques de l'espèce
        adaptability_score = 0.5  # Score de base neutre
        
        # Facteur de résistance à la sécheresse
        if species.drought_resistance:
            if species.drought_resistance in [DroughtResistance.ELEVEE, DroughtResistance.TRES_ELEVEE]:
                adaptability_score += 0.2
            elif species.drought_resistance == DroughtResistance.MODEREE:
                adaptability_score += 0.1
            elif species.drought_resistance in [DroughtResistance.FAIBLE, DroughtResistance.TRES_FAIBLE]:
                adaptability_score -= 0.2
        
        # Facteur de résistance au gel (moins important si les températures augmentent)
        if species.frost_resistance:
            if temp_diff > 2.0:  # Si l'augmentation de température est significative
                # La résistance au gel devient moins importante
                pass
            else:
                if species.frost_resistance in [FrostResistance.ELEVEE, FrostResistance.TRES_ELEVEE]:
                    adaptability_score += 0.1
                elif species.frost_resistance in [FrostResistance.FAIBLE, FrostResistance.TRES_FAIBLE]:
                    adaptability_score -= 0.1
        
        # Facteur de résilience au changement climatique (si disponible)
        if hasattr(species, 'climate_change_resilience') and species.climate_change_resilience:
            if species.climate_change_resilience == "ELEVEE":
                adaptability_score += 0.2
            elif species.climate_change_resilience == "MODEREE":
                adaptability_score += 0.1
            elif species.climate_change_resilience == "FAIBLE":
                adaptability_score -= 0.1
        
        # Ajustement selon l'importance des changements
        impact_severity = (abs(temp_diff) / 5.0 + abs(precip_diff) / 300.0 + abs(drought_diff) / 3.0) / 3
        impact_severity = min(1.0, impact_severity)
        
        # Conversion en catégorie d'adaptabilité
        adaptability_level = "moyenne"
        if adaptability_score > 0.7:
            adaptability_level = "excellente"
        elif adaptability_score > 0.5:
            adaptability_level = "bonne"
        elif adaptability_score < 0.3:
            adaptability_level = "faible"
        elif adaptability_score < 0.5:
            adaptability_level = "moyenne-faible"
        
        return {
            "adaptability_score": round(adaptability_score, 2),
            "adaptability_level": adaptability_level,
            "impact_severity": round(impact_severity, 2),
            "key_factors": {
                "temperature_change": round(temp_diff, 1),
                "precipitation_change": round(precip_diff, 1),
                "drought_increase": round(drought_diff, 1)
            },
            "recommendations": self._generate_adaptation_recommendations(species, adaptability_score, impact_severity)
        }
    
    def _generate_adaptation_recommendations(self, species: SpeciesData, 
                                           adaptability_score: float,
                                           impact_severity: float) -> List[str]:
        """
        Génère des recommandations pour l'adaptation au changement climatique.
        
        Args:
            species: Données de l'espèce
            adaptability_score: Score d'adaptabilité
            impact_severity: Sévérité de l'impact climatique
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        # Recommandations selon le score d'adaptabilité
        if adaptability_score < 0.4:
            recommendations.append("Éviter cette espèce dans les scénarios de changement climatique sévère.")
            
            if hasattr(species, 'drought_resistance') and species.drought_resistance in [DroughtResistance.FAIBLE, DroughtResistance.TRES_FAIBLE]:
                recommendations.append("Prévoir un système d'irrigation adapté en cas de plantation.")
        
        elif adaptability_score < 0.6:
            recommendations.append("Surveiller attentivement l'adaptation de cette espèce aux changements climatiques.")
            
            if impact_severity > 0.6:
                recommendations.append("Considérer une diversification des espèces pour réduire les risques.")
        
        else:
            recommendations.append("Cette espèce présente une bonne adaptabilité au changement climatique prévu.")
            
            if impact_severity > 0.7:
                recommendations.append("Malgré sa bonne adaptabilité, prévoir des mesures de suivi régulier en raison de l'importance des changements.")
        
        # Recommandations spécifiques selon les caractéristiques de l'espèce
        if hasattr(species, 'drought_resistance') and species.drought_resistance:
            if species.drought_resistance in [DroughtResistance.FAIBLE, DroughtResistance.TRES_FAIBLE] and impact_severity > 0.5:
                recommendations.append("Privilégier les zones moins exposées à la sécheresse (ubacs, zones de rétention d'eau).")
        
        return recommendations
    
    def compare_species_across_scenarios(self, species_data: Dict[str, SpeciesData], 
                                       current_climate: Dict[str, Any],
                                       scenarios: List[str]) -> Dict[str, Any]:
        """
        Compare l'adaptabilité de plusieurs espèces à travers différents scénarios climatiques.
        
        Args:
            species_data: Dictionnaire des données d'espèces
            current_climate: Données climatiques actuelles
            scenarios: Liste des identifiants de scénarios à comparer
            
        Returns:
            Analyse comparative des espèces
        """
        comparison = {
            "scenarios": [],
            "species_rankings": {},
            "most_resilient_species": [],
            "most_vulnerable_species": []
        }
        
        scenario_results = {}
        
        # Analyser chaque scénario
        for scenario_id in scenarios:
            scenario_info = self.get_predefined_scenario(scenario_id)
            if not scenario_info:
                continue
                
            # Ajouter les informations du scénario
            comparison["scenarios"].append({
                "id": scenario_id,
                "name": scenario_info["name"],
                "description": scenario_info["description"]
            })
            
            # Projeter le climat pour ce scénario
            future_climate = self.project_climate_data(current_climate, scenario_info)
            
            # Analyser chaque espèce
            species_scores = {}
            
            for species_id, species in species_data.items():
                adaptability = self.analyze_species_climate_adaptability(
                    species, current_climate, future_climate
                )
                species_scores[species_id] = {
                    "species_id": species_id,
                    "common_name": species.common_name,
                    "latin_name": species.latin_name,
                    "adaptability_score": adaptability["adaptability_score"],
                    "adaptability_level": adaptability["adaptability_level"]
                }
            
            # Trier les espèces par score d'adaptabilité
            sorted_species = sorted(
                species_scores.values(),
                key=lambda x: x["adaptability_score"],
                reverse=True
            )
            
            # Stocker les résultats du scénario
            scenario_results[scenario_id] = sorted_species
        
        # Comparer les classements d'espèces entre les scénarios
        all_species_ids = list(species_data.keys())
        
        for species_id in all_species_ids:
            species = species_data[species_id]
            species_name = species.common_name
            
            # Créer un dictionnaire pour stocker les classements de cette espèce dans chaque scénario
            rankings = {}
            avg_score = 0
            
            for scenario_id, results in scenario_results.items():
                # Trouver le rang de cette espèce dans ce scénario
                for i, species_result in enumerate(results):
                    if species_result["species_id"] == species_id:
                        rankings[scenario_id] = {
                            "rank": i + 1,
                            "score": species_result["adaptability_score"],
                            "level": species_result["adaptability_level"]
                        }
                        avg_score += species_result["adaptability_score"]
                        break
            
            # Calculer le score moyen
            if rankings:
                avg_score /= len(rankings)
            
            comparison["species_rankings"][species_id] = {
                "species_id": species_id,
                "common_name": species_name,
                "latin_name": species.latin_name,
                "scenario_rankings": rankings,
                "average_adaptability": round(avg_score, 2)
            }
        
        # Identifier les espèces les plus résilientes et les plus vulnérables
        sorted_by_avg = sorted(
            comparison["species_rankings"].values(),
            key=lambda x: x["average_adaptability"],
            reverse=True
        )
        
        comparison["most_resilient_species"] = [
            {
                "species_id": s["species_id"],
                "common_name": s["common_name"],
                "latin_name": s["latin_name"],
                "average_adaptability": s["average_adaptability"]
            }
            for s in sorted_by_avg[:5]  # Top 5 des plus résilientes
        ]
        
        comparison["most_vulnerable_species"] = [
            {
                "species_id": s["species_id"],
                "common_name": s["common_name"],
                "latin_name": s["latin_name"],
                "average_adaptability": s["average_adaptability"]
            }
            for s in sorted_by_avg[-5:]  # 5 dernières (les plus vulnérables)
        ]
        
        return comparison
