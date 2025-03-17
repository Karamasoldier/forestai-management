#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module pour la génération de rapports d'adaptation climatique pour les espèces forestières.

Ce module fournit des fonctionnalités pour générer des rapports détaillés
sur l'adaptation des espèces forestières au changement climatique.
"""

import pandas as pd
from typing import Dict, List, Any

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.climate_recommendations import ClimateRecommendationAnalyzer

logger = get_logger(__name__)


class ClimateReportGenerator:
    """
    Générateur de rapports d'adaptation climatique pour les espèces forestières.
    
    Cette classe fournit des méthodes pour générer des rapports détaillés
    sur l'adaptation des espèces forestières aux différents scénarios climatiques.
    """
    
    def __init__(self):
        """Initialise le générateur de rapports climatiques."""
        self.recommendation_analyzer = ClimateRecommendationAnalyzer()
        logger.info("ClimateReportGenerator initialisé")
    
    def generate_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport complet d'adaptation au changement climatique.
        
        Args:
            report_data: Données pour le rapport
            
        Returns:
            Rapport d'adaptation au changement climatique
        """
        # Extraire les données nécessaires
        parcel_id = report_data["parcel_id"]
        current_climate = report_data["current_climate"]
        soil_data = report_data["soil_data"]
        context = report_data["context"]
        species_data = report_data["species_data"]
        climate_analyzer = report_data["climate_analyzer"]
        scenarios = report_data["scenarios"]
        recommendations = report_data["recommendations"]
        
        # Initialiser le rapport
        report = {
            "parcel_id": parcel_id,
            "current_climate": current_climate,
            "soil_data": soil_data,
            "context": context,
            "generated_at": pd.Timestamp.now().isoformat(),
            "scenarios": [],
            "recommendations": {},
            "comparative_analysis": {},
            "adaptive_strategies": []
        }
        
        # Ajouter les informations des scénarios au rapport
        for scenario_id in scenarios:
            scenario = climate_analyzer.get_predefined_scenario(scenario_id)
            if not scenario:
                logger.warning(f"Scénario non trouvé: {scenario_id}, ignoré")
                continue
            
            report["scenarios"].append({
                "id": scenario_id,
                "name": scenario["name"],
                "description": scenario["description"],
                "parameters": {
                    "temperature_increase": scenario["temperature_increase"],
                    "precipitation_change_factor": scenario["precipitation_change_factor"],
                    "drought_index_increase": scenario["drought_index_increase"]
                }
            })
        
        # Ajouter les recommandations au rapport
        for scenario_id, recs in recommendations.items():
            current_rec = recs["current"]
            future_rec = recs["future"]
            analysis = recs["analysis"]
            
            report["recommendations"][scenario_id] = {
                "current": {
                    "id": current_rec.id,
                    "top_recommendations": [
                        {
                            "rank": rec["rank"],
                            "species_id": rec["species_id"],
                            "common_name": rec["common_name"],
                            "latin_name": rec["latin_name"],
                            "overall_score": rec["scores"]["overall_score"],
                            "climate_score": rec["scores"]["climate_score"],
                            "risk_score": rec["scores"]["risk_score"]
                        }
                        for rec in current_rec.recommendations[:10]
                    ]
                },
                "future": {
                    "id": future_rec.id,
                    "top_recommendations": [
                        {
                            "rank": rec["rank"],
                            "species_id": rec["species_id"],
                            "common_name": rec["common_name"],
                            "latin_name": rec["latin_name"],
                            "overall_score": rec["scores"]["overall_score"],
                            "climate_score": rec["scores"]["climate_score"],
                            "risk_score": rec["scores"]["risk_score"]
                        }
                        for rec in future_rec.recommendations[:10]
                    ]
                },
                "analysis": analysis
            }
        
        # Effectuer une analyse comparative entre les scénarios
        if len(scenarios) > 1:
            report["comparative_analysis"] = self.recommendation_analyzer.compare_scenarios(
                report["recommendations"], species_data
            )
        
        # Générer des stratégies d'adaptation
        report["adaptive_strategies"] = self._generate_adaptive_strategies(report)
        
        return report
    
    def _generate_adaptive_strategies(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère des stratégies d'adaptation basées sur les recommandations.
        
        Args:
            report: Rapport d'adaptation climatique
            
        Returns:
            Liste des stratégies d'adaptation
        """
        strategies = []
        
        # Stratégie 1: Diversification avec espèces résilientes
        resilient_species = []
        
        for scenario_id, recs in report["recommendations"].items():
            analysis = recs["analysis"]
            if "summary" in analysis and "most_resilient_species" in analysis["summary"]:
                for species in analysis["summary"]["most_resilient_species"]:
                    if species not in resilient_species:
                        resilient_species.append(species)
        
        if resilient_species:
            strategies.append({
                "strategy": "Diversification avec espèces résilientes",
                "description": "Intégrer des espèces identifiées comme résilientes face au changement climatique",
                "recommended_species": resilient_species[:5],
                "implementation": [
                    "Planter ces espèces résilientes en mélange avec d'autres",
                    "Établir des parcelles d'essai pour vérifier l'adaptation réelle",
                    "Surveiller la croissance et la santé sur plusieurs années"
                ]
            })
        
        # Stratégie 2: Plantation progressive avec suivi
        if "comparative_analysis" in report and "consistent_species" in report["comparative_analysis"]:
            consistent_species = report["comparative_analysis"]["consistent_species"]
            
            if consistent_species:
                strategies.append({
                    "strategy": "Plantation progressive avec suivi",
                    "description": "Favoriser des espèces consistantes dans tous les scénarios climatiques",
                    "recommended_species": consistent_species[:5],
                    "implementation": [
                        "Réaliser des plantations progressives par phases",
                        "Commencer avec un mélange d'espèces consistantes dans tous les scénarios",
                        "Ajuster le choix des espèces en fonction des observations de terrain",
                        "Documenter l'adaptation des différentes espèces"
                    ]
                })
        
        # Stratégie 3: Adaptations sylvicoles spécifiques
        adaptations = []
        
        # Vérifier s'il y a des augmentations significatives de sécheresse
        significant_drought_increase = False
        for scenario in report["scenarios"]:
            if scenario["parameters"]["drought_index_increase"] > 2.0:
                significant_drought_increase = True
                break
        
        if significant_drought_increase:
            adaptations.append({
                "type": "Gestion de la sécheresse",
                "measures": [
                    "Espacement accru entre les plants pour réduire la compétition pour l'eau",
                    "Mise en place de cuvettes de rétention d'eau autour des jeunes plants",
                    "Paillage organique pour conserver l'humidité du sol",
                    "Plantation sur les versants nord (ubac) pour réduire l'exposition à la chaleur"
                ]
            })
        
        # Vérifier s'il y a des augmentations significatives de température
        significant_temp_increase = False
        for scenario in report["scenarios"]:
            if scenario["parameters"]["temperature_increase"] > 2.5:
                significant_temp_increase = True
                break
        
        if significant_temp_increase:
            adaptations.append({
                "type": "Gestion des températures accrues",
                "measures": [
                    "Protection des jeunes plants contre l'ensoleillement direct (abris)",
                    "Sylviculture favorisant des peuplements plus denses pour créer un microclimat",
                    "Réduction des coupes rases sur grandes surfaces exposant les sols aux températures extrêmes",
                    "Favoriser les mélanges d'espèces pour réduire les risques"
                ]
            })
        
        if adaptations:
            strategies.append({
                "strategy": "Adaptations sylvicoles spécifiques",
                "description": "Ajuster les pratiques sylvicoles pour atténuer les impacts du changement climatique",
                "adaptations": adaptations,
                "implementation": [
                    "Former le personnel aux nouvelles pratiques sylvicoles",
                    "Mettre en place des parcelles de démonstration",
                    "Suivre et documenter l'efficacité des mesures d'adaptation",
                    "Ajuster les itinéraires sylvicoles en fonction des résultats"
                ]
            })
        
        # Stratégie 4: Monitoring et ajustement adaptatif
        strategies.append({
            "strategy": "Monitoring et ajustement adaptatif",
            "description": "Établir un système de suivi continu pour ajuster les stratégies en fonction de l'évolution réelle du climat",
            "implementation": [
                "Installer des stations météo locales pour collecter des données climatiques précises",
                "Établir des parcelles permanentes de suivi de la croissance et de la santé des arbres",
                "Documenter les performances des différentes espèces face aux événements climatiques extrêmes",
                "Réviser régulièrement les stratégies de gestion en fonction des observations"
            ]
        })
        
        # Stratégie 5: Migration assistée
        if any(scenario["parameters"]["temperature_increase"] >= 3.0 for scenario in report["scenarios"]):
            strategies.append({
                "strategy": "Migration assistée",
                "description": "Introduction d'espèces ou de provenances adaptées aux conditions climatiques futures prévues",
                "implementation": [
                    "Identifier des espèces adaptées aux conditions climatiques futures",
                    "Localiser des provenances d'espèces existantes venant de régions plus chaudes/sèches",
                    "Tester ces espèces/provenances dans des parcelles expérimentales",
                    "Intégrer progressivement les espèces/provenances performantes"
                ]
            })
        
        return strategies
    
    def export_report_json(self, report: Dict[str, Any], output_path: str) -> bool:
        """
        Exporte le rapport au format JSON.
        
        Args:
            report: Rapport d'adaptation climatique
            output_path: Chemin de sortie pour le fichier JSON
            
        Returns:
            True si l'export a réussi, False sinon
        """
        try:
            import json
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Rapport exporté au format JSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export du rapport au format JSON: {str(e)}")
            return False
    
    def export_report_summary(self, report: Dict[str, Any], output_path: str) -> bool:
        """
        Exporte un résumé du rapport au format texte.
        
        Args:
            report: Rapport d'adaptation climatique
            output_path: Chemin de sortie pour le fichier texte
            
        Returns:
            True si l'export a réussi, False sinon
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"RAPPORT D'ADAPTATION AU CHANGEMENT CLIMATIQUE\n")
                f.write(f"============================================\n\n")
                
                f.write(f"Parcelle: {report['parcel_id']}\n")
                f.write(f"Date de génération: {report['generated_at']}\n\n")
                
                f.write(f"SCÉNARIOS CLIMATIQUES ANALYSÉS\n")
                f.write(f"-----------------------------\n")
                for scenario in report["scenarios"]:
                    f.write(f"- {scenario['name']}: {scenario['description']}\n")
                    f.write(f"  Augmentation de température: +{scenario['parameters']['temperature_increase']}°C\n")
                    f.write(f"  Facteur de précipitations: {scenario['parameters']['precipitation_change_factor']}\n")
                    f.write(f"  Augmentation de l'indice de sécheresse: +{scenario['parameters']['drought_index_increase']}\n\n")
                
                f.write(f"ESPÈCES LES PLUS ADAPTÉES AU CHANGEMENT CLIMATIQUE\n")
                f.write(f"----------------------------------------------\n")
                
                # Collecter les espèces résilientes de tous les scénarios
                resilient_species = {}
                for scenario_id, recs in report["recommendations"].items():
                    if "summary" in recs["analysis"] and "most_resilient_species" in recs["analysis"]["summary"]:
                        for species in recs["analysis"]["summary"]["most_resilient_species"]:
                            if species["species_id"] not in resilient_species:
                                resilient_species[species["species_id"]] = species
                
                # Afficher les espèces résilientes
                for species in resilient_species.values():
                    f.write(f"- {species['common_name']}\n")
                    if "rank_improvement" in species:
                        f.write(f"  Amélioration de classement: +{species['rank_improvement']} places\n")
                
                # Afficher les espèces consistantes
                if "comparative_analysis" in report and "consistent_species" in report["comparative_analysis"]:
                    f.write(f"\nESPÈCES CONSISTANTES DANS TOUS LES SCÉNARIOS\n")
                    f.write(f"------------------------------------------\n")
                    for species in report["comparative_analysis"]["consistent_species"]:
                        f.write(f"- {species['common_name']} ({species['latin_name']})\n")
                        f.write(f"  Rang moyen: {species['average_rank']:.1f}\n")
                
                # Afficher les stratégies d'adaptation
                f.write(f"\nSTRATÉGIES D'ADAPTATION RECOMMANDÉES\n")
                f.write(f"----------------------------------\n")
                for strategy in report["adaptive_strategies"]:
                    f.write(f"- {strategy['strategy']}: {strategy['description']}\n")
                    if "implementation" in strategy:
                        for step in strategy["implementation"]:
                            f.write(f"  * {step}\n")
                    f.write("\n")
            
            logger.info(f"Résumé du rapport exporté: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export du résumé du rapport: {str(e)}")
            return False
    
    def create_visual_report(self, report: Dict[str, Any], output_dir: str) -> bool:
        """
        Crée un rapport visuel avec des graphiques d'adaptabilité des espèces.
        
        Args:
            report: Rapport d'adaptation climatique
            output_dir: Répertoire de sortie pour les graphiques
            
        Returns:
            True si la création a réussi, False sinon
        """
        try:
            import os
            import matplotlib.pyplot as plt
            import numpy as np
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Générer le graphique des espèces résilientes par scénario
            for scenario_id, recs in report["recommendations"].items():
                scenario_name = next((s["name"] for s in report["scenarios"] if s["id"] == scenario_id), scenario_id)
                
                # Récupérer les 10 premières recommandations pour le climat futur
                top_recommendations = recs["future"]["top_recommendations"][:10]
                
                # Préparer les données pour le graphique
                species_names = [r["common_name"] for r in top_recommendations]
                overall_scores = [r["overall_score"] for r in top_recommendations]
                climate_scores = [r["climate_score"] for r in top_recommendations]
                risk_scores = [r["risk_score"] for r in top_recommendations]
                
                # Créer le graphique
                plt.figure(figsize=(12, 8))
                
                x = np.arange(len(species_names))
                width = 0.25
                
                plt.bar(x - width, overall_scores, width, label='Score global', color='skyblue')
                plt.bar(x, climate_scores, width, label='Score climatique', color='lightgreen')
                plt.bar(x + width, risk_scores, width, label='Score de risque', color='salmon')
                
                plt.xlabel('Espèces')
                plt.ylabel('Scores')
                plt.title(f'Top 10 des espèces recommandées - Scénario {scenario_name}')
                plt.xticks(x, species_names, rotation=45, ha='right')
                plt.legend()
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                # Sauvegarder le graphique
                output_path = os.path.join(output_dir, f'recommendations_{scenario_id}.png')
                plt.savefig(output_path, bbox_inches='tight', dpi=300)
                plt.close()
                
                logger.info(f"Graphique des recommandations généré: {output_path}")
            
            # Si une analyse comparative est disponible, générer un graphique des espèces robustes
            if "comparative_analysis" in report and "robustness_ranking" in report["comparative_analysis"]:
                robust_species = report["comparative_analysis"]["robustness_ranking"][:10]
                
                if robust_species:
                    # Préparer les données pour le graphique
                    species_names = [s["common_name"] for s in robust_species]
                    robustness_scores = [s["robustness_score"] for s in robust_species]
                    
                    # Créer le graphique
                    plt.figure(figsize=(12, 8))
                    bars = plt.barh(species_names, robustness_scores, color='lightseagreen')
                    
                    # Ajouter les valeurs sur les barres
                    for i, bar in enumerate(bars):
                        plt.text(
                            bar.get_width() + 0.01,
                            bar.get_y() + bar.get_height()/2,
                            f"{robustness_scores[i]:.3f}",
                            va='center'
                        )
                    
                    plt.xlabel('Score de robustesse')
                    plt.ylabel('Espèces')
                    plt.title('Espèces les plus robustes à travers tous les scénarios')
                    plt.grid(axis='x', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    
                    # Sauvegarder le graphique
                    output_path = os.path.join(output_dir, 'robust_species.png')
                    plt.savefig(output_path, bbox_inches='tight', dpi=300)
                    plt.close()
                    
                    logger.info(f"Graphique des espèces robustes généré: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du rapport visuel: {str(e)}")
            return False
