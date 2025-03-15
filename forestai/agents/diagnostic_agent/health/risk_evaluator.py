# -*- coding: utf-8 -*-
"""
Module d'évaluation des risques sanitaires forestiers.
"""

import logging
import math
from typing import Dict, List, Any, Optional

from forestai.agents.diagnostic_agent.health.health_issue import HealthIssue

logger = logging.getLogger(__name__)

class RiskEvaluator:
    """Évaluateur de risques sanitaires forestiers."""
    
    def evaluate_risk(self, detected_issues: List[HealthIssue],
                     species_health: Dict[str, Dict[str, Any]],
                     climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Évalue le risque global sanitaire du peuplement forestier.
        
        Args:
            detected_issues: Liste des problèmes sanitaires détectés
            species_health: Informations de santé par espèce
            climate_data: Données climatiques (optionnel)
            
        Returns:
            Évaluation du risque global
        """
        # Calculer le score de risque actuel
        current_risk_score = self._calculate_current_risk(detected_issues, species_health)
        
        # Facteurs de risque identifiés
        risk_factors = self._identify_risk_factors(detected_issues, species_health)
        
        # Prédiction du risque futur
        future_risk = self._predict_future_risk(current_risk_score, detected_issues, climate_data)
        
        # Calculer le score de santé global
        overall_health_score = self._calculate_health_score(current_risk_score, species_health)
        
        # Déterminer le statut sanitaire global
        health_status = self._determine_health_status(overall_health_score)
        
        return {
            "overall_health_score": overall_health_score,
            "health_status": health_status,
            "current_risk": {
                "score": current_risk_score,
                "level": self._risk_level_from_score(current_risk_score),
                "priority_issues": self._get_priority_issues(detected_issues)
            },
            "future_risk": future_risk,
            "risk_factors": risk_factors
        }
    
    def _calculate_current_risk(self, detected_issues: List[HealthIssue],
                               species_health: Dict[str, Dict[str, Any]]) -> float:
        """
        Calcule le score de risque sanitaire actuel.
        
        Args:
            detected_issues: Liste des problèmes sanitaires détectés
            species_health: Informations de santé par espèce
            
        Returns:
            Score de risque entre 0 et 1
        """
        if not detected_issues:
            # Sans problèmes détectés, le risque est basé uniquement sur la santé des espèces
            species_scores = [data["health_score"] / 10 for data in species_health.values()]
            if not species_scores:
                return 0.0
            avg_species_health = sum(species_scores) / len(species_scores)
            return max(0, 1 - avg_species_health)  # Inverser car risque = 1 - santé
        
        # Calculer le score basé sur les problèmes détectés
        weighted_severity_sum = 0
        weight_sum = 0
        
        for issue in detected_issues:
            weight = issue.confidence
            severity = issue.severity
            
            # Ajustement pour les problèmes à fort risque de propagation
            if issue.spreading_risk > 0.7:
                severity = severity * 1.3
            
            weighted_severity_sum += severity * weight
            weight_sum += weight
        
        issue_risk = weighted_severity_sum / max(weight_sum, 0.001)
        
        # Intégrer la santé des espèces
        species_scores = [data["health_score"] / 10 for data in species_health.values()]
        if species_scores:
            avg_species_health = sum(species_scores) / len(species_scores)
            species_risk = max(0, 1 - avg_species_health)
            
            # Combiner les deux types de risque (problèmes et santé des espèces)
            return 0.7 * issue_risk + 0.3 * species_risk
        else:
            return issue_risk
    
    def _identify_risk_factors(self, detected_issues: List[HealthIssue],
                              species_health: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifie les principaux facteurs de risque sanitaire.
        
        Args:
            detected_issues: Liste des problèmes sanitaires détectés
            species_health: Informations de santé par espèce
            
        Returns:
            Liste des facteurs de risque avec leur importance
        """
        risk_factors = []
        
        # Facteurs liés aux problèmes sanitaires détectés
        for issue in detected_issues:
            # Ne conserver que les problèmes avec une confiance suffisante
            if issue.confidence >= 0.4:
                risk_factors.append({
                    "type": "health_issue",
                    "name": issue.name,
                    "importance": issue.severity * issue.confidence,
                    "description": issue.description,
                    "spreading_risk": issue.spreading_risk
                })
        
        # Facteurs liés à la santé des espèces
        for species, data in species_health.items():
            if data["health_status"] in ["Critique", "Mauvais"]:
                symptoms_desc = ""
                if data["main_symptoms"]:
                    top_symptoms = [s["name"] for s in data["main_symptoms"][:2]]
                    symptoms_desc = f" présentant {', '.join(top_symptoms)}"
                
                risk_factors.append({
                    "type": "species_health",
                    "name": f"Santé dégradée de {species}",
                    "importance": (10 - data["health_score"]) / 10,
                    "description": f"L'espèce {species} présente un état sanitaire {data['health_status'].lower()}{symptoms_desc}.",
                    "affected_species": [species]
                })
        
        # Trier par importance décroissante
        risk_factors.sort(key=lambda x: x["importance"], reverse=True)
        
        return risk_factors
    
    def _predict_future_risk(self, current_risk: float,
                            detected_issues: List[HealthIssue],
                            climate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prédit l'évolution du risque sanitaire dans le futur.
        
        Args:
            current_risk: Score de risque actuel
            detected_issues: Liste des problèmes sanitaires détectés
            climate_data: Données climatiques (optionnel)
            
        Returns:
            Prédiction de risque futur
        """
        # Risque de base = risque actuel
        future_risk_score = current_risk
        evolution_factors = []
        
        # Facteurs d'évolution basés sur les problèmes détectés
        has_spreading_issues = False
        for issue in detected_issues:
            if issue.spreading_risk > 0.6 and issue.confidence > 0.5:
                has_spreading_issues = True
                evolution_factors.append({
                    "factor": f"Propagation de {issue.name}",
                    "impact": "negative",
                    "description": f"Risque élevé de propagation ({int(issue.spreading_risk*100)}%)"
                })
                future_risk_score += 0.1  # Augmenter le risque futur
        
        # Intégrer les facteurs climatiques si disponibles
        climate_impact = 0
        if climate_data:
            if "drought_trend" in climate_data and climate_data["drought_trend"] > 0.1:
                evolution_factors.append({
                    "factor": "Augmentation de la sécheresse",
                    "impact": "negative",
                    "description": "Tendance à l'augmentation des périodes de sécheresse"
                })
                climate_impact += 0.15
            
            if "temperature_trend" in climate_data and climate_data["temperature_trend"] > 0.1:
                evolution_factors.append({
                    "factor": "Augmentation des températures",
                    "impact": "negative",
                    "description": "Tendance au réchauffement"
                })
                climate_impact += 0.1
                
            if "precipitation_trend" in climate_data and climate_data["precipitation_trend"] < -0.1:
                evolution_factors.append({
                    "factor": "Diminution des précipitations",
                    "impact": "negative",
                    "description": "Tendance à la baisse des précipitations"
                })
                climate_impact += 0.1
        
        # Ajouter l'impact climatique au risque futur
        future_risk_score += climate_impact
        
        # Facteurs d'atténuation du risque
        if not has_spreading_issues and len(detected_issues) <= 1:
            evolution_factors.append({
                "factor": "Problèmes sanitaires limités",
                "impact": "positive",
                "description": "Faible nombre de problèmes sanitaires détectés sans risque majeur de propagation"
            })
            future_risk_score -= 0.1
        
        # Limiter le score entre 0 et 1
        future_risk_score = max(0, min(1, future_risk_score))
        
        return {
            "score": future_risk_score,
            "level": self._risk_level_from_score(future_risk_score),
            "evolution": future_risk_score - current_risk,
            "evolution_factors": evolution_factors
        }
    
    def _calculate_health_score(self, risk_score: float, 
                              species_health: Dict[str, Dict[str, Any]]) -> float:
        """
        Calcule le score de santé global sur une échelle de 0 à 10.
        
        Args:
            risk_score: Score de risque global
            species_health: Informations de santé par espèce
            
        Returns:
            Score de santé global (0-10)
        """
        # Convertir le risque en score de santé (inverse)
        risk_based_health = (1 - risk_score) * 10
        
        # Intégrer les scores de santé par espèce si disponibles
        if species_health:
            # Pondérer par le nombre d'arbres de chaque espèce
            total_trees = sum(data["count"] for data in species_health.values())
            weighted_species_health = sum(data["health_score"] * data["count"] for data in species_health.values())
            species_health_score = weighted_species_health / total_trees if total_trees > 0 else 0
            
            # Combiner les deux scores
            return 0.6 * risk_based_health + 0.4 * species_health_score
        else:
            return risk_based_health
    
    def _determine_health_status(self, health_score: float) -> str:
        """
        Détermine le statut sanitaire en fonction du score de santé.
        
        Args:
            health_score: Score de santé global
            
        Returns:
            Statut sanitaire descriptif
        """
        if health_score >= 8.5:
            return "Excellent"
        elif health_score >= 7:
            return "Bon"
        elif health_score >= 5.5:
            return "Satisfaisant"
        elif health_score >= 4:
            return "Moyen"
        elif health_score >= 2.5:
            return "Mauvais"
        else:
            return "Critique"
    
    def _risk_level_from_score(self, risk_score: float) -> str:
        """
        Convertit un score de risque en niveau descriptif.
        
        Args:
            risk_score: Score de risque entre 0 et 1
            
        Returns:
            Niveau de risque descriptif
        """
        if risk_score < 0.2:
            return "Faible"
        elif risk_score < 0.4:
            return "Modéré"
        elif risk_score < 0.6:
            return "Élevé"
        elif risk_score < 0.8:
            return "Très élevé"
        else:
            return "Critique"
    
    def _get_priority_issues(self, detected_issues: List[HealthIssue]) -> List[Dict[str, Any]]:
        """
        Identifie les problèmes sanitaires prioritaires.
        
        Args:
            detected_issues: Liste des problèmes sanitaires détectés
            
        Returns:
            Liste des problèmes prioritaires avec leur niveau d'urgence
        """
        priority_issues = []
        
        for issue in detected_issues:
            # Calculer un score de priorité
            priority_score = issue.severity * issue.confidence
            
            # Ajustement pour les problèmes à fort risque de propagation
            if issue.spreading_risk > 0.7:
                priority_score *= 1.5
            
            # Définir le niveau d'urgence
            if priority_score >= 0.8:
                urgency = "Immédiate"
            elif priority_score >= 0.6:
                urgency = "Élevée"
            elif priority_score >= 0.4:
                urgency = "Modérée"
            else:
                urgency = "Faible"
            
            # Ajouter uniquement les problèmes avec une urgence significative
            if urgency in ["Immédiate", "Élevée", "Modérée"]:
                priority_issues.append({
                    "issue_id": issue.id,
                    "name": issue.name,
                    "type": issue.type,
                    "urgency": urgency,
                    "priority_score": round(priority_score, 2),
                    "confidence": issue.confidence
                })
        
        # Trier par niveau d'urgence et score de priorité
        priority_issues.sort(key=lambda x: (
            {"Immédiate": 0, "Élevée": 1, "Modérée": 2, "Faible": 3}[x["urgency"]],
            -x["priority_score"]
        ))
        
        return priority_issues
