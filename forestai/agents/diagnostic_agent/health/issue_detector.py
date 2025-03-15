# -*- coding: utf-8 -*-
"""
Module de détection des problèmes sanitaires forestiers.
"""

import logging
import copy
from typing import Dict, List, Any, Optional, Set

from forestai.agents.diagnostic_agent.health.health_issue import HealthIssue

logger = logging.getLogger(__name__)

class HealthIssueDetector:
    """Détecteur de problèmes sanitaires forestiers."""
    
    def __init__(self, health_issues_db: Dict[str, HealthIssue]):
        """
        Initialise le détecteur de problèmes sanitaires.
        
        Args:
            health_issues_db: Base de données des problèmes sanitaires
        """
        self.health_issues_db = health_issues_db
    
    def detect_issues(self, trees: List[Dict[str, Any]], 
                    additional_symptoms: Optional[Dict[str, Any]] = None,
                    climate_data: Optional[Dict[str, Any]] = None,
                    species_present: Optional[Set[str]] = None) -> List[HealthIssue]:
        """
        Détecte les problèmes sanitaires potentiels basés sur les symptômes observés.
        
        Args:
            trees: Liste des arbres de l'inventaire
            additional_symptoms: Observations supplémentaires
            climate_data: Données climatiques pour l'analyse contextuelle
            species_present: Ensemble des espèces présentes dans l'inventaire
            
        Returns:
            Liste des problèmes sanitaires détectés avec leur probabilité
        """
        # Extraire les espèces présentes dans l'inventaire si non fournies
        if species_present is None:
            species_present = set()
            for tree in trees:
                if "species" in tree:
                    species_present.add(tree["species"])
        
        # Collecter tous les symptômes observés
        all_symptoms = self._collect_symptoms(trees, additional_symptoms)
        
        # Mapper les symptômes aux problèmes sanitaires potentiels
        detected_issues = []
        
        for issue_id, issue in self.health_issues_db.items():
            # Vérifier si les espèces affectées sont présentes dans l'inventaire
            species_match = False
            for sp in issue.affected_species:
                if sp == "Toutes espèces" or sp in species_present:
                    species_match = True
                    break
            
            if not species_match:
                continue
            
            # Calculer un score de correspondance des symptômes
            symptom_match_count = 0
            symptom_match_score = 0.0
            max_possible_score = len(issue.symptoms)
            
            for issue_symptom in issue.symptoms:
                best_match_score = 0.0
                
                # Rechercher la meilleure correspondance parmi les symptômes observés
                for observed_symptom, data in all_symptoms.items():
                    # Vérifier si le symptôme observé correspond à celui du problème
                    if issue_symptom.lower() in observed_symptom.lower() or observed_symptom.lower() in issue_symptom.lower():
                        match_score = data["severity_avg"] * min(1.0, data["count"] / len(trees) * 5)
                        best_match_score = max(best_match_score, match_score)
                
                if best_match_score > 0:
                    symptom_match_count += 1
                    symptom_match_score += best_match_score
            
            # Calculer le score de confiance
            if max_possible_score > 0:
                symptom_coverage = symptom_match_count / max_possible_score
                match_quality = symptom_match_score / max_possible_score
                base_confidence = (symptom_coverage + match_quality) / 2
                adjusted_confidence = base_confidence * issue.confidence
            else:
                adjusted_confidence = 0.0
            
            # Ajuster la confiance en fonction des données climatiques
            if climate_data and issue.type == "abiotic":
                adjusted_confidence = self._adjust_confidence_based_on_climate(issue, adjusted_confidence, climate_data)
            
            # Seuil de confiance minimal
            if adjusted_confidence >= 0.2:  # Au moins 20% de confiance pour considérer le problème
                detected_issue = copy.deepcopy(issue)
                detected_issue.confidence = round(adjusted_confidence, 2)
                detected_issues.append(detected_issue)
        
        # Trier par confiance décroissante
        detected_issues.sort(key=lambda x: x.confidence, reverse=True)
        
        return detected_issues
    
    def _collect_symptoms(self, trees: List[Dict[str, Any]], 
                          additional_symptoms: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Collecte tous les symptômes observés dans les arbres inventoriés.
        
        Args:
            trees: Liste des arbres de l'inventaire
            additional_symptoms: Observations supplémentaires
            
        Returns:
            Dictionnaire des symptômes observés avec leur fréquence et sévérité
        """
        all_symptoms = {}
        
        # A partir des arbres individuels
        for tree in trees:
            if "symptoms" in tree and isinstance(tree["symptoms"], list):
                for symptom in tree["symptoms"]:
                    if isinstance(symptom, str):
                        sympt_name = symptom
                        severity = 1.0  # Sévérité par défaut
                    else:
                        sympt_name = symptom.get("name", "unknown")
                        severity = symptom.get("severity", 1.0)
                    
                    if sympt_name not in all_symptoms:
                        all_symptoms[sympt_name] = {
                            "count": 0,
                            "severity_sum": 0,
                            "tree_species": set()
                        }
                    
                    all_symptoms[sympt_name]["count"] += 1
                    all_symptoms[sympt_name]["severity_sum"] += severity
                    
                    if "species" in tree:
                        all_symptoms[sympt_name]["tree_species"].add(tree["species"])
        
        # Ajouter les symptômes des observations supplémentaires
        if additional_symptoms and "observed_symptoms" in additional_symptoms:
            for symptom in additional_symptoms["observed_symptoms"]:
                if isinstance(symptom, str):
                    sympt_name = symptom
                    severity = 1.0
                else:
                    sympt_name = symptom.get("name", "unknown")
                    severity = symptom.get("severity", 1.0)
                
                if sympt_name not in all_symptoms:
                    all_symptoms[sympt_name] = {
                        "count": 1,
                        "severity_sum": severity,
                        "tree_species": set()
                    }
                else:
                    all_symptoms[sympt_name]["count"] += 1
                    all_symptoms[sympt_name]["severity_sum"] += severity
                
                # Ajouter les espèces affectées si spécifiées
                if isinstance(symptom, dict) and "affected_species" in symptom:
                    for sp in symptom["affected_species"]:
                        all_symptoms[sympt_name]["tree_species"].add(sp)
        
        # Calculer les scores moyens de sévérité
        for sympt, data in all_symptoms.items():
            data["severity_avg"] = data["severity_sum"] / data["count"]
            data["tree_species"] = list(data["tree_species"])
        
        return all_symptoms
    
    def _adjust_confidence_based_on_climate(self, issue: HealthIssue, 
                                           base_confidence: float,
                                           climate_data: Dict[str, Any]) -> float:
        """
        Ajuste le score de confiance en fonction des données climatiques.
        
        Args:
            issue: Problème sanitaire à évaluer
            base_confidence: Score de confiance de base
            climate_data: Données climatiques
            
        Returns:
            Score de confiance ajusté
        """
        adjusted_confidence = base_confidence
        
        # Ajuster en fonction du problème spécifique
        if issue.name == "Sécheresse" and "drought_index" in climate_data:
            # Plus l'indice de sécheresse est élevé, plus la confiance augmente
            drought_index = climate_data["drought_index"]
            if drought_index > 0.7:  # Sécheresse sévère
                adjusted_confidence = min(1.0, base_confidence * 1.5)
            elif drought_index > 0.5:  # Sécheresse modérée
                adjusted_confidence = min(1.0, base_confidence * 1.3)
            elif drought_index < 0.2:  # Pas de sécheresse
                adjusted_confidence = max(0.0, base_confidence * 0.5)
        
        elif issue.name == "Dommages dus au gel" and "min_temperature" in climate_data:
            # Ajustement basé sur la température minimale
            min_temp = climate_data["min_temperature"]
            if min_temp < -15:  # Gel sévère
                adjusted_confidence = min(1.0, base_confidence * 1.5)
            elif min_temp < -5:  # Gel modéré
                adjusted_confidence = min(1.0, base_confidence * 1.2)
            elif min_temp > 0:  # Pas de gel
                adjusted_confidence = max(0.0, base_confidence * 0.3)
        
        return adjusted_confidence
