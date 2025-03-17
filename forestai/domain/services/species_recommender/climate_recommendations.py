#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module d'analyse des recommandations climatiques pour les espèces forestières.

Ce module fournit des fonctionnalités pour analyser et comparer les recommandations
d'espèces forestières entre différents scénarios climatiques.
"""

from typing import Dict, List, Any
import pandas as pd

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.models import (
    SpeciesData,
    SpeciesRecommendation,
    DroughtResistance,
    FrostResistance
)

logger = get_logger(__name__)


class ClimateRecommendationAnalyzer:
    """
    Analyseur de recommandations climatiques pour les espèces forestières.
    
    Cette classe fournit des méthodes pour analyser et comparer les recommandations
    entre différents scénarios climatiques (actuel et futur).
    """
    
    def __init__(self):
        """Initialise l'analyseur de recommandations climatiques."""
        logger.info("ClimateRecommendationAnalyzer initialisé")
    
    def analyze_climate_recommendations(self, current_rec: SpeciesRecommendation,
                                       future_rec: SpeciesRecommendation,
                                       species_data: Dict[str, SpeciesData],
                                       current_climate: Dict[str, Any],
                                       future_climate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse approfondie des recommandations climatiques actuelles et futures.
        
        Args:
            current_rec: Recommandation pour le climat actuel
            future_rec: Recommandation pour le climat futur
            species_data: Dictionnaire des données d'espèces
            current_climate: Données climatiques actuelles
            future_climate: Données climatiques futures
            
        Returns:
            Analyse détaillée des recommandations
        """
        analysis = {
            "climate_change": {
                "temperature_change": future_climate.get("mean_annual_temperature", 0) - 
                                     current_climate.get("mean_annual_temperature", 0),
                "precipitation_change": future_climate.get("annual_precipitation", 0) - 
                                       current_climate.get("annual_precipitation", 0),
                "drought_index_change": future_climate.get("drought_index", 0) - 
                                       current_climate.get("drought_index", 0)
            },
            "rank_changes": [],
            "score_changes": [],
            "only_current_top10": [],
            "only_future_top10": [],
            "resilient_characteristics": {},
            "vulnerable_characteristics": {}
        }
        
        self._analyze_species_rankings(analysis, current_rec, future_rec, species_data)
        self._analyze_species_turnover(analysis, current_rec, future_rec, species_data)
        self._analyze_species_characteristics(analysis, species_data)
        self._generate_summary(analysis)
        
        return analysis
    
    def _analyze_species_rankings(self, analysis: Dict[str, Any],
                                current_rec: SpeciesRecommendation,
                                future_rec: SpeciesRecommendation,
                                species_data: Dict[str, SpeciesData]):
        """
        Analyse les changements de classement des espèces entre les recommandations.
        
        Args:
            analysis: Dictionnaire d'analyse à compléter
            current_rec: Recommandation pour le climat actuel
            future_rec: Recommandation pour le climat futur
            species_data: Dictionnaire des données d'espèces
        """
        # Extraire les espèces recommandées pour chaque scénario
        current_species = {rec['species_id']: (rec['rank'], rec['scores']) 
                          for rec in current_rec.recommendations}
        future_species = {rec['species_id']: (rec['rank'], rec['scores']) 
                         for rec in future_rec.recommendations}
        
        # Identifier les espèces qui changent de classement
        all_species_ids = set(current_species.keys()) | set(future_species.keys())
        
        for species_id in all_species_ids:
            if species_id in current_species and species_id in future_species:
                current_rank, current_scores = current_species[species_id]
                future_rank, future_scores = future_species[species_id]
                
                rank_diff = current_rank - future_rank
                climate_score_diff = future_scores['climate_score'] - current_scores['climate_score']
                risk_score_diff = current_scores['risk_score'] - future_scores['risk_score']
                overall_score_diff = future_scores['overall_score'] - current_scores['overall_score']
                
                # Calculer le pourcentage de variation des scores
                climate_pct_diff = self._calculate_percentage_diff(
                    current_scores['climate_score'], climate_score_diff
                )
                risk_pct_diff = self._calculate_percentage_diff(
                    current_scores['risk_score'], risk_score_diff
                )
                overall_pct_diff = self._calculate_percentage_diff(
                    current_scores['overall_score'], overall_score_diff
                )
                
                # Stocker les changements
                change = {
                    'species_id': species_id,
                    'common_name': species_data[species_id].common_name,
                    'latin_name': species_data[species_id].latin_name,
                    'current_rank': current_rank,
                    'future_rank': future_rank,
                    'rank_diff': rank_diff,
                    'score_changes': {
                        'climate': {
                            'absolute': round(climate_score_diff, 3),
                            'relative': round(climate_pct_diff, 1),
                        },
                        'risk': {
                            'absolute': round(risk_score_diff, 3),
                            'relative': round(risk_pct_diff, 1),
                        },
                        'overall': {
                            'absolute': round(overall_score_diff, 3),
                            'relative': round(overall_pct_diff, 1),
                        }
                    }
                }
                
                analysis['rank_changes'].append(change)
                
                # Stocker les variations importantes de score
                if abs(climate_pct_diff) > 15 or abs(risk_pct_diff) > 15 or abs(overall_pct_diff) > 15:
                    analysis['score_changes'].append(change)
        
        # Trier les changements de rang par importance
        analysis['rank_changes'] = sorted(
            analysis['rank_changes'],
            key=lambda x: abs(x['rank_diff']),
            reverse=True
        )
        
        # Trier les changements de score par importance
        analysis['score_changes'] = sorted(
            analysis['score_changes'],
            key=lambda x: abs(x['score_changes']['overall']['relative']),
            reverse=True
        )
    
    def _analyze_species_turnover(self, analysis: Dict[str, Any],
                                current_rec: SpeciesRecommendation,
                                future_rec: SpeciesRecommendation,
                                species_data: Dict[str, SpeciesData]):
        """
        Analyse le renouvellement des espèces entre les recommandations.
        
        Args:
            analysis: Dictionnaire d'analyse à compléter
            current_rec: Recommandation pour le climat actuel
            future_rec: Recommandation pour le climat futur
            species_data: Dictionnaire des données d'espèces
        """
        # Identifier les espèces qui sont uniquement dans le top 10 actuel
        only_current_top10_ids = set(rec['species_id'] for rec in current_rec.recommendations[:10]) - \
                        set(rec['species_id'] for rec in future_rec.recommendations[:10])
        
        # Identifier les espèces qui sont uniquement dans le top 10 futur
        only_future_top10_ids = set(rec['species_id'] for rec in future_rec.recommendations[:10]) - \
                       set(rec['species_id'] for rec in current_rec.recommendations[:10])
        
        # Ajouter les détails des espèces uniquement dans le top 10 actuel
        for species_id in only_current_top10_ids:
            species = species_data[species_id]
            current_rank = next(rec['rank'] for rec in current_rec.recommendations 
                              if rec['species_id'] == species_id)
            
            analysis['only_current_top10'].append({
                'species_id': species_id,
                'common_name': species.common_name,
                'latin_name': species.latin_name,
                'current_rank': current_rank
            })
        
        # Ajouter les détails des espèces uniquement dans le top 10 futur
        for species_id in only_future_top10_ids:
            species = species_data[species_id]
            future_rank = next(rec['rank'] for rec in future_rec.recommendations 
                             if rec['species_id'] == species_id)
            
            analysis['only_future_top10'].append({
                'species_id': species_id,
                'common_name': species.common_name,
                'latin_name': species.latin_name,
                'future_rank': future_rank
            })
    
    def _analyze_species_characteristics(self, analysis: Dict[str, Any],
                                       species_data: Dict[str, SpeciesData]):
        """
        Analyse les caractéristiques des espèces résilientes et vulnérables.
        
        Args:
            analysis: Dictionnaire d'analyse à compléter
            species_data: Dictionnaire des données d'espèces
        """
        # Analyser les caractéristiques des espèces résilientes et vulnérables
        resilient_species_ids = [c['species_id'] for c in analysis['rank_changes'][:5] if c['rank_diff'] > 0]
        vulnerable_species_ids = [c['species_id'] for c in analysis['rank_changes'][:5] if c['rank_diff'] < 0]
        
        # Compter les caractéristiques des espèces résilientes
        drought_resist_counts = {dr.value: 0 for dr in DroughtResistance}
        frost_resist_counts = {fr.value: 0 for fr in FrostResistance}
        
        for species_id in resilient_species_ids:
            species = species_data[species_id]
            
            if species.drought_resistance:
                drought_resist_counts[species.drought_resistance.value] += 1
            
            if species.frost_resistance:
                frost_resist_counts[species.frost_resistance.value] += 1
        
        analysis['resilient_characteristics'] = {
            'drought_resistance': drought_resist_counts,
            'frost_resistance': frost_resist_counts,
            'species_count': len(resilient_species_ids)
        }
        
        # Compter les caractéristiques des espèces vulnérables
        drought_resist_counts = {dr.value: 0 for dr in DroughtResistance}
        frost_resist_counts = {fr.value: 0 for fr in FrostResistance}
        
        for species_id in vulnerable_species_ids:
            species = species_data[species_id]
            
            if species.drought_resistance:
                drought_resist_counts[species.drought_resistance.value] += 1
            
            if species.frost_resistance:
                frost_resist_counts[species.frost_resistance.value] += 1
        
        analysis['vulnerable_characteristics'] = {
            'drought_resistance': drought_resist_counts,
            'frost_resistance': frost_resist_counts,
            'species_count': len(vulnerable_species_ids)
        }
    
    def _generate_summary(self, analysis: Dict[str, Any]):
        """
        Génère un résumé de l'analyse des recommandations climatiques.
        
        Args:
            analysis: Dictionnaire d'analyse à compléter
        """
        # Ajouter un résumé global
        analysis['summary'] = {
            'improved_species_count': len([c for c in analysis['rank_changes'] if c['rank_diff'] > 0]),
            'degraded_species_count': len([c for c in analysis['rank_changes'] if c['rank_diff'] < 0]),
            'significant_changes_count': len(analysis['score_changes']),
            'species_turnover_rate': len(analysis['only_current_top10'] + analysis['only_future_top10']) / 10 if analysis['only_current_top10'] or analysis['only_future_top10'] else 0,
            'most_resilient_species': [
                {
                    'species_id': c['species_id'],
                    'common_name': c['common_name'],
                    'rank_improvement': c['rank_diff'],
                    'score_improvement': c['score_changes']['overall']['absolute']
                }
                for c in analysis['rank_changes'][:3] if c['rank_diff'] > 0
            ],
            'most_vulnerable_species': [
                {
                    'species_id': c['species_id'],
                    'common_name': c['common_name'],
                    'rank_degradation': -c['rank_diff'],
                    'score_degradation': -c['score_changes']['overall']['absolute']
                }
                for c in sorted(analysis['rank_changes'], key=lambda x: x['rank_diff'])[:3] if c['rank_diff'] < 0
            ]
        }
    
    def _calculate_percentage_diff(self, original_value: float, difference: float) -> float:
        """
        Calcule la différence en pourcentage.
        
        Args:
            original_value: Valeur originale
            difference: Différence absolue
            
        Returns:
            Différence en pourcentage
        """
        if original_value > 0:
            return difference / original_value * 100
        else:
            return 0
    
    def compare_scenarios(self, recommendations: Dict[str, Any], 
                         species_data: Dict[str, SpeciesData]) -> Dict[str, Any]:
        """
        Compare les recommandations entre différents scénarios.
        
        Args:
            recommendations: Recommandations par scénario
            species_data: Dictionnaire des données d'espèces
            
        Returns:
            Analyse comparative entre scénarios
        """
        comparison = {
            "consistent_species": [],
            "scenario_specific_species": {},
            "robustness_ranking": []
        }
        
        # Identifier les espèces recommandées dans chaque scénario
        scenario_top_species = {}
        for scenario_id, recs in recommendations.items():
            top_species_ids = [r["species_id"] for r in recs["future"]["top_recommendations"][:5]]
            scenario_top_species[scenario_id] = set(top_species_ids)
        
        # Identifier les espèces qui apparaissent dans les top 5 de tous les scénarios
        all_scenarios = set(scenario_top_species.keys())
        
        if all_scenarios:
            consistent_species_ids = set.intersection(*[scenario_top_species[s] for s in all_scenarios])
            
            # Ajouter les détails des espèces consistantes
            for species_id in consistent_species_ids:
                species = species_data[species_id]
                
                # Calculer le rang moyen à travers les scénarios
                ranks = []
                for scenario_id in all_scenarios:
                    for rec in recommendations[scenario_id]["future"]["top_recommendations"]:
                        if rec["species_id"] == species_id:
                            ranks.append(rec["rank"])
                            break
                
                avg_rank = sum(ranks) / len(ranks) if ranks else 0
                
                comparison["consistent_species"].append({
                    "species_id": species_id,
                    "common_name": species.common_name,
                    "latin_name": species.latin_name,
                    "average_rank": avg_rank,
                    "ranks_by_scenario": {s: next((rec["rank"] for rec in recommendations[s]["future"]["top_recommendations"] 
                                               if rec["species_id"] == species_id), None) 
                                          for s in all_scenarios}
                })
        
        # Identifier les espèces qui n'apparaissent que dans un scénario spécifique
        for scenario_id, species_ids in scenario_top_species.items():
            other_scenarios = all_scenarios - {scenario_id}
            other_species = set()
            for s in other_scenarios:
                other_species |= scenario_top_species[s]
            
            unique_species = species_ids - other_species
            
            if unique_species:
                comparison["scenario_specific_species"][scenario_id] = []
                
                for species_id in unique_species:
                    species = species_data[species_id]
                    
                    # Trouver le rang dans ce scénario
                    rank = next((rec["rank"] for rec in recommendations[scenario_id]["future"]["top_recommendations"] 
                              if rec["species_id"] == species_id), None)
                    
                    comparison["scenario_specific_species"][scenario_id].append({
                        "species_id": species_id,
                        "common_name": species.common_name,
                        "latin_name": species.latin_name,
                        "rank": rank
                    })
        
        # Calculer le classement de robustesse
        comparison["robustness_ranking"] = self._calculate_robustness_ranking(
            scenario_top_species, recommendations, all_scenarios, species_data
        )
        
        return comparison
    
    def _calculate_robustness_ranking(self, scenario_top_species: Dict[str, set],
                                    recommendations: Dict[str, Any],
                                    all_scenarios: set,
                                    species_data: Dict[str, SpeciesData]) -> List[Dict[str, Any]]:
        """
        Calcule un classement de robustesse des espèces à travers tous les scénarios.
        
        Args:
            scenario_top_species: Espèces du top par scénario
            recommendations: Recommandations par scénario
            all_scenarios: Ensemble des scénarios
            species_data: Dictionnaire des données d'espèces
            
        Returns:
            Classement de robustesse
        """
        # Calculer un classement de robustesse des espèces à travers tous les scénarios
        all_recommended_species = set()
        for species_set in scenario_top_species.values():
            all_recommended_species |= species_set
        
        robustness_scores = {}
        
        for species_id in all_recommended_species:
            # Calculer le nombre de scénarios où l'espèce apparaît dans le top 10
            scenario_count = sum(1 for s in all_scenarios if species_id in scenario_top_species[s])
            
            # Calculer la moyenne des rangs dans ces scénarios
            ranks = []
            for scenario_id in all_scenarios:
                if species_id in scenario_top_species[scenario_id]:
                    for rec in recommendations[scenario_id]["future"]["top_recommendations"]:
                        if rec["species_id"] == species_id:
                            ranks.append(rec["rank"])
                            break
            
            avg_rank = sum(ranks) / len(ranks) if ranks else 0
            
            # Calculer un score de robustesse (plus élevé = plus robuste)
            robustness = (scenario_count / len(all_scenarios)) * (1 / (avg_rank or 1))
            
            species = species_data[species_id]
            
            robustness_scores[species_id] = {
                "species_id": species_id,
                "common_name": species.common_name,
                "latin_name": species.latin_name,
                "scenario_presence": scenario_count,
                "total_scenarios": len(all_scenarios),
                "average_rank": avg_rank,
                "robustness_score": round(robustness, 4)
            }
        
        # Trier par score de robustesse décroissant
        return sorted(
            robustness_scores.values(),
            key=lambda x: x["robustness_score"],
            reverse=True
        )
