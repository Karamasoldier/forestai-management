# -*- coding: utf-8 -*-
"""
Module de génération de recommandations sanitaires forestières.
"""

import logging
from typing import Dict, List, Any

from forestai.agents.diagnostic_agent.health.health_issue import HealthIssue

logger = logging.getLogger(__name__)

class RecommendationGenerator:
    """Générateur de recommandations sanitaires pour les forêts."""
    
    def generate_recommendations(self, detected_issues: List[HealthIssue],
                               global_risk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère des recommandations de gestion sanitaire.
        
        Args:
            detected_issues: Liste des problèmes sanitaires détectés
            global_risk: Évaluation du risque global
            
        Returns:
            Recommandations structurées
        """
        # Recommandations spécifiques liées aux problèmes détectés
        specific_recommendations = self._generate_specific_recommendations(detected_issues)
        
        # Recommandations générales basées sur le risque global
        general_recommendations = self._generate_general_recommendations(global_risk)
        
        # Recommandations de surveillance
        monitoring_recommendations = self._generate_monitoring_recommendations(detected_issues, global_risk)
        
        # Définir des actions prioritaires
        priority_actions = self._define_priority_actions(specific_recommendations, global_risk)
        
        return {
            "summary": self._generate_recommendations_summary(specific_recommendations, global_risk),
            "specific_recommendations": specific_recommendations,
            "general_recommendations": general_recommendations,
            "monitoring_recommendations": monitoring_recommendations,
            "priority_actions": priority_actions
        }
    
    def _generate_specific_recommendations(self, detected_issues: List[HealthIssue]) -> List[Dict[str, Any]]:
        """
        Génère des recommandations pour chaque problème sanitaire détecté.
        
        Args:
            detected_issues: Liste des problèmes sanitaires détectés
            
        Returns:
            Liste des recommandations spécifiques
        """
        specific_recommendations = []
        
        for issue in detected_issues:
            # Ne générer des recommandations que pour les problèmes avec une confiance suffisante
            if issue.confidence < 0.3:
                continue
            
            # Sélectionner les traitements les plus efficaces
            treatments = []
            if issue.treatment_options:
                # Trier par efficacité décroissante
                sorted_treatments = sorted(issue.treatment_options, key=lambda x: x.get("efficacy", 0), reverse=True)
                treatments = sorted_treatments[:2]  # Limiter aux 2 plus efficaces
            
            # Sélectionner les mesures de prévention les plus pertinentes
            prevention = issue.prevention_measures[:3] if issue.prevention_measures else []
            
            # Ajouter la recommandation
            specific_recommendations.append({
                "issue_id": issue.id,
                "issue_name": issue.name,
                "confidence": issue.confidence,
                "urgency": "Élevée" if issue.severity > 0.7 else "Modérée",
                "treatments": treatments,
                "prevention": prevention,
                "spreading_risk": issue.spreading_risk
            })
        
        # Trier par confiance et sévérité décroissantes
        specific_recommendations.sort(key=lambda x: (
            x["confidence"],
            1 if x["urgency"] == "Élevée" else 0
        ), reverse=True)
        
        return specific_recommendations
    
    def _generate_general_recommendations(self, global_risk: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Génère des recommandations générales basées sur le risque global.
        
        Args:
            global_risk: Évaluation du risque global
            
        Returns:
            Liste des recommandations générales
        """
        general_recommendations = []
        risk_score = global_risk.get("current_risk", {}).get("score", 0)
        health_status = global_risk.get("health_status", "")
        
        # Recommandations basées sur le niveau de risque
        if risk_score > 0.7:  # Risque très élevé
            general_recommendations.append({
                "type": "sanitary_management",
                "recommendation": "Mettre en place un plan de gestion sanitaire d'urgence et consulter un expert forestier",
                "priority": "Élevée"
            })
            general_recommendations.append({
                "type": "evaluation",
                "recommendation": "Réaliser un diagnostic phytosanitaire complet par un expert",
                "priority": "Élevée"
            })
            
        elif risk_score > 0.5:  # Risque élevé
            general_recommendations.append({
                "type": "sanitary_management",
                "recommendation": "Établir un plan de gestion sanitaire pour traiter les problèmes détectés",
                "priority": "Élevée"
            })
            general_recommendations.append({
                "type": "monitoring",
                "recommendation": "Mettre en place un suivi sanitaire régulier (tous les 3 mois)",
                "priority": "Modérée"
            })
            
        elif risk_score > 0.3:  # Risque modéré
            general_recommendations.append({
                "type": "prevention",
                "recommendation": "Mettre en œuvre des mesures préventives pour limiter les risques sanitaires",
                "priority": "Modérée"
            })
            general_recommendations.append({
                "type": "monitoring",
                "recommendation": "Mettre en place un suivi sanitaire bisannuel",
                "priority": "Modérée"
            })
            
        else:  # Risque faible
            general_recommendations.append({
                "type": "monitoring",
                "recommendation": "Maintenir une veille sanitaire annuelle",
                "priority": "Faible"
            })
        
        # Recommandations basées sur l'état de santé global
        if health_status in ["Critique", "Mauvais"]:
            general_recommendations.append({
                "type": "forest_management",
                "recommendation": "Envisager des coupes sanitaires pour les arbres gravement affectés",
                "priority": "Élevée"
            })
            general_recommendations.append({
                "type": "resilience",
                "recommendation": "Planifier la diversification des essences pour améliorer la résilience du peuplement",
                "priority": "Modérée"
            })
            
        elif health_status == "Moyen":
            general_recommendations.append({
                "type": "forest_management",
                "recommendation": "Pratiquer des éclaircies sanitaires pour renforcer les arbres dominants",
                "priority": "Modérée"
            })
            
        # Recommandations basées sur la tendance d'évolution du risque
        future_evolution = global_risk.get("future_risk", {}).get("evolution", 0)
        if future_evolution > 0.1:  # Risque en augmentation
            general_recommendations.append({
                "type": "anticipation",
                "recommendation": "Anticiper la dégradation sanitaire probable en adaptant la gestion forestière",
                "priority": "Modérée"
            })
        
        return general_recommendations
    
    def _generate_monitoring_recommendations(self, detected_issues: List[HealthIssue],
                                           global_risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère des recommandations de surveillance sanitaire.
        
        Args:
            detected_issues: Liste des problèmes sanitaires détectés
            global_risk: Évaluation du risque global
            
        Returns:
            Liste des recommandations de surveillance
        """
        monitoring_recommendations = []
        risk_level = global_risk.get("current_risk", {}).get("level", "")
        
        # Fréquence de surveillance basée sur le niveau de risque
        frequency = "Annuelle"
        if risk_level in ["Très élevé", "Critique"]:
            frequency = "Trimestrielle"
        elif risk_level == "Élevé":
            frequency = "Semestrielle"
        
        monitoring_recommendations.append({
            "type": "frequency",
            "recommendation": f"Surveillance sanitaire {frequency.lower()}",
            "details": f"Effectuer un suivi sanitaire à fréquence {frequency.lower()}"
        })
        
        # Indicateurs à surveiller en fonction des problèmes détectés
        indicators = []
        for issue in detected_issues:
            if issue.confidence >= 0.4:
                indicators.append(f"Évolution de {issue.name}")
                
                # Ajouter des indicateurs spécifiques selon le type de problème
                if issue.type == "pest":
                    indicators.append(f"Présence d'insectes adultes/larves de {issue.name}")
                    
                elif issue.type == "disease":
                    indicators.append(f"Propagation des symptômes de {issue.name}")
                    
                elif issue.type == "abiotic" and issue.name == "Sécheresse":
                    indicators.append("Humidité du sol et stress hydrique")
        
        # Éliminer les doublons
        unique_indicators = list(set(indicators))
        
        monitoring_recommendations.append({
            "type": "indicators",
            "recommendation": "Indicateurs à surveiller",
            "details": unique_indicators
        })
        
        # Méthodes de surveillance recommandées
        methods = ["Inspection visuelle des symptômes"]
        
        if any(issue.type == "pest" for issue in detected_issues if issue.confidence >= 0.4):
            methods.append("Pièges à insectes/phéromones")
            
        if len(detected_issues) > 2 or global_risk.get("current_risk", {}).get("score", 0) > 0.6:
            methods.append("Consultation d'un expert forestier")
            
        if any(issue.spreading_risk > 0.7 for issue in detected_issues):
            methods.append("Cartographie des foyers d'infestation")
        
        monitoring_recommendations.append({
            "type": "methods",
            "recommendation": "Méthodes de surveillance",
            "details": methods
        })
        
        return monitoring_recommendations
    
    def _define_priority_actions(self, specific_recommendations: List[Dict[str, Any]],
                               global_risk: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Définit les actions prioritaires à entreprendre.
        
        Args:
            specific_recommendations: Recommandations spécifiques générées
            global_risk: Évaluation du risque global
            
        Returns:
            Liste des actions prioritaires
        """
        priority_actions = []
        current_risk_level = global_risk.get("current_risk", {}).get("level", "")
        
        # Actions prioritaires en fonction du niveau de risque
        if current_risk_level in ["Très élevé", "Critique"]:
            priority_actions.append({
                "action": "Consultation urgente d'un expert forestier",
                "deadline": "Immédiate",
                "description": "Faire appel à un expert pour un diagnostic détaillé et un plan d'intervention"
            })
        
        # Actions prioritaires basées sur les recommandations spécifiques
        for rec in specific_recommendations:
            if rec["urgency"] == "Élevée" and rec["confidence"] >= 0.6:
                # Extraire le traitement le plus efficace
                if rec["treatments"]:
                    best_treatment = rec["treatments"][0]
                    priority_actions.append({
                        "action": f"{best_treatment.get('name')} pour {rec['issue_name']}",
                        "deadline": "Dans les 30 jours",
                        "description": best_treatment.get("description", "")
                    })
        
        # Actions de surveillance prioritaires
        if current_risk_level in ["Élevé", "Très élevé", "Critique"]:
            priority_actions.append({
                "action": "Mise en place d'un système de surveillance sanitaire",
                "deadline": "Dans les 60 jours",
                "description": "Établir un protocole de suivi sanitaire régulier des peuplements"
            })
        
        # Si risque de propagation élevé
        has_spreading_risk = any(rec["spreading_risk"] > 0.7 for rec in specific_recommendations)
        if has_spreading_risk:
            priority_actions.append({
                "action": "Mesures de confinement sanitaire",
                "deadline": "Dans les 15 jours",
                "description": "Mettre en place des mesures pour limiter la propagation des problèmes sanitaires"
            })
        
        return priority_actions
    
    def _generate_recommendations_summary(self, specific_recommendations: List[Dict[str, Any]],
                                        global_risk: Dict[str, Any]) -> str:
        """
        Génère un résumé des recommandations sanitaires.
        
        Args:
            specific_recommendations: Recommandations spécifiques générées
            global_risk: Évaluation du risque global
            
        Returns:
            Résumé des recommandations
        """
        health_status = global_risk.get("health_status", "")
        risk_level = global_risk.get("current_risk", {}).get("level", "")
        
        summary_parts = []
        
        # Introduction basée sur l'état sanitaire
        if health_status in ["Critique", "Mauvais"]:
            summary_parts.append(f"État sanitaire {health_status.lower()} nécessitant des interventions rapides.")
        elif health_status == "Moyen":
            summary_parts.append(f"État sanitaire {health_status.lower()} nécessitant une vigilance particulière.")
        else:
            summary_parts.append(f"État sanitaire {health_status.lower()} avec surveillance recommandée.")
        
        # Mention des problèmes prioritaires
        if specific_recommendations:
            high_urgency_recs = [rec for rec in specific_recommendations if rec["urgency"] == "Élevée"]
            if high_urgency_recs:
                issues = [rec["issue_name"] for rec in high_urgency_recs]
                if len(issues) == 1:
                    summary_parts.append(f"Traitement prioritaire pour {issues[0]}.")
                else:
                    summary_parts.append(f"Traitements prioritaires pour {' et '.join(issues)}.")
        
        # Mention du niveau de risque futur
        future_evolution = global_risk.get("future_risk", {}).get("evolution", 0)
        if future_evolution > 0.1:
            summary_parts.append("Risque sanitaire en augmentation nécessitant une attention accrue.")
        elif future_evolution < -0.1:
            summary_parts.append("Prévision d'amélioration de la situation sanitaire avec les mesures appropriées.")
        
        return " ".join(summary_parts)
