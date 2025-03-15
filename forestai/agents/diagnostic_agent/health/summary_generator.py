# -*- coding: utf-8 -*-
"""
Module de génération de résumés sanitaires forestiers.
"""

import logging
from typing import Dict, List, Any

from forestai.agents.diagnostic_agent.health.health_issue import HealthIssue

logger = logging.getLogger(__name__)

class SummaryGenerator:
    """Générateur de résumés sanitaires pour les forêts."""
    
    def generate_summary(self, detected_issues: List[HealthIssue],
                       global_risk: Dict[str, Any],
                       health_indicators: Dict[str, Any]) -> str:
        """
        Génère un résumé de l'état sanitaire de la forêt.
        
        Args:
            detected_issues: Problèmes sanitaires détectés
            global_risk: Évaluation du risque global
            health_indicators: Indicateurs sanitaires calculés
            
        Returns:
            Résumé sanitaire concis
        """
        health_status = global_risk.get("health_status", "")
        current_risk = global_risk.get("current_risk", {})
        risk_level = current_risk.get("level", "")
        health_score = global_risk.get("overall_health_score", 0)
        
        summary_parts = []
        
        # État sanitaire global
        summary_parts.append(f"État sanitaire global: {health_status} (score: {health_score}/10).")
        
        # Niveau de risque
        summary_parts.append(f"Niveau de risque sanitaire: {risk_level}.")
        
        # Principaux problèmes sanitaires
        if detected_issues:
            high_confidence_issues = [issue for issue in detected_issues if issue.confidence >= 0.6]
            if high_confidence_issues:
                if len(high_confidence_issues) == 1:
                    summary_parts.append(f"Principal problème identifié: {high_confidence_issues[0].name}.")
                else:
                    issue_names = ", ".join(issue.name for issue in high_confidence_issues[:3])
                    summary_parts.append(f"Principaux problèmes identifiés: {issue_names}.")
        
        # Indicateurs critiques
        critical_flags = health_indicators.get("critical_flags", {})
        critical_indicators = [key.replace("critical_", "").replace("_", " ").capitalize() 
                             for key, value in critical_flags.items() if value]
        if critical_indicators:
            if len(critical_indicators) == 1:
                summary_parts.append(f"Indicateur critique: {critical_indicators[0]}.")
            else:
                indicators_str = ", ".join(critical_indicators[:3])
                summary_parts.append(f"Indicateurs critiques: {indicators_str}.")
        
        # Risque d'évolution
        future_risk = global_risk.get("future_risk", {})
        evolution = future_risk.get("evolution", 0)
        if evolution > 0.1:
            summary_parts.append("La situation sanitaire risque de se dégrader sans intervention.")
        elif evolution < -0.1:
            summary_parts.append("La situation sanitaire pourrait s'améliorer avec des interventions adaptées.")
        
        # Recommandation générale
        if health_score < 4:
            summary_parts.append("Intervention urgente recommandée.")
        elif health_score < 6:
            summary_parts.append("Plan de traitement sanitaire à mettre en place rapidement.")
        elif health_score < 7.5:
            summary_parts.append("Surveillance accrue et interventions ciblées recommandées.")
        else:
            summary_parts.append("Maintenir la surveillance sanitaire régulière.")
        
        return " ".join(summary_parts)
