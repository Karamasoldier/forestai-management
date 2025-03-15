# -*- coding: utf-8 -*-
"""
Formateur de sections sanitaires pour les rapports forestiers.

Ce module permet de formater les données d'analyse sanitaire
pour les intégrer dans les différents types de rapports.
"""

import logging
from typing import Dict, Any, List, Optional
import datetime

logger = logging.getLogger(__name__)

class HealthSectionFormatter:
    """
    Classe responsable de formater les données sanitaires
    pour les différents formats de rapports.
    """
    
    def __init__(self):
        """Initialise le formateur de section sanitaire."""
        logger.debug("Initialisation du formateur de section sanitaire")
    
    def format_health_section_md(self, health_data: Dict[str, Any], detail_level: str = "standard") -> str:
        """
        Formate les données sanitaires au format Markdown.
        
        Args:
            health_data: Données d'analyse sanitaire
            detail_level: Niveau de détail (minimal, standard, complet)
            
        Returns:
            Section sanitaire au format Markdown
        """
        if not health_data:
            return "### État sanitaire\n\nAucune donnée sanitaire disponible."
        
        # Construction de la section
        sections = []
        
        # Titre et résumé
        sections.append("## État sanitaire de la forêt")
        sections.append(health_data.get("summary", "Aucun résumé disponible"))
        sections.append("")
        
        # Score de santé global
        health_score = health_data.get("overall_health_score", 0)
        health_status = health_data.get("health_status", "Inconnu")
        
        sections.append(f"**Score de santé global**: {health_score:.1f}/10 ({health_status})")
        sections.append("")
        
        # Problèmes détectés
        detected_issues = health_data.get("detected_issues", [])
        if detected_issues:
            sections.append("### Problèmes sanitaires identifiés")
            for issue in detected_issues:
                confidence = issue.get("confidence", 0) * 100
                sections.append(f"- **{issue.get('name', 'Problème inconnu')}** - Confiance: {confidence:.0f}%")
                if detail_level in ["standard", "complet"] and "description" in issue:
                    sections.append(f"  - {issue['description']}")
            sections.append("")
        
        # Indicateurs de santé
        if detail_level in ["standard", "complet"] and "health_indicators" in health_data:
            sections.append("### Indicateurs sanitaires")
            indicators = health_data["health_indicators"]
            
            if "average_values" in indicators:
                avg_values = indicators["average_values"]
                sections.append("| Indicateur | Valeur | Seuil critique |")
                sections.append("|------------|--------|----------------|")
                
                thresholds = indicators.get("thresholds", {})
                for key, value in avg_values.items():
                    readable_key = key.replace("_", " ").capitalize()
                    threshold = thresholds.get(f"{key}_critical", "N/A")
                    if isinstance(threshold, float):
                        threshold = f"{threshold:.0%}"
                    sections.append(f"| {readable_key} | {value:.1%} | {threshold} |")
                sections.append("")
        
        # Risques
        if "risk_assessment" in health_data:
            risks = health_data["risk_assessment"]
            sections.append("### Évaluation des risques")
            
            if "current_risk" in risks:
                current = risks["current_risk"]
                sections.append(f"**Risque actuel**: {current.get('level', 'Non évalué')}")
                if "description" in current:
                    sections.append(f"{current['description']}")
                sections.append("")
            
            if detail_level == "complet" and "future_risk" in risks:
                future = risks["future_risk"]
                sections.append(f"**Évolution probable**: {future.get('trend', 'Stable')}")
                if "description" in future:
                    sections.append(f"{future['description']}")
                sections.append("")
        
        # Recommandations
        if "recommendations" in health_data:
            recommendations = health_data["recommendations"]
            sections.append("### Recommandations sanitaires")
            
            for idx, rec in enumerate(recommendations, 1):
                sections.append(f"{idx}. **{rec.get('title', 'Recommandation')}**")
                if "description" in rec:
                    sections.append(f"   {rec['description']}")
                if "priority" in rec:
                    sections.append(f"   *Priorité: {rec['priority']}*")
                sections.append("")
        
        # Métadonnées
        if detail_level == "complet" and "metadata" in health_data:
            metadata = health_data["metadata"]
            sections.append("### Métadonnées de l'analyse")
            
            if "analysis_date" in metadata:
                try:
                    date = datetime.datetime.fromisoformat(metadata["analysis_date"])
                    formatted_date = date.strftime("%d/%m/%Y %H:%M")
                    sections.append(f"- Date d'analyse: {formatted_date}")
                except (ValueError, TypeError):
                    sections.append(f"- Date d'analyse: {metadata['analysis_date']}")
                    
            if "analyzer_version" in metadata:
                sections.append(f"- Version de l'analyseur: {metadata['analyzer_version']}")
            sections.append("")
        
        return "\n".join(sections)
    
    def format_health_section_html(self, health_data: Dict[str, Any], detail_level: str = "standard") -> str:
        """
        Formate les données sanitaires au format HTML.
        
        Args:
            health_data: Données d'analyse sanitaire
            detail_level: Niveau de détail (minimal, standard, complet)
            
        Returns:
            Section sanitaire au format HTML
        """
        if not health_data:
            return "<h3>État sanitaire</h3><p>Aucune donnée sanitaire disponible.</p>"
        
        # Conversion des styles pour le HTML
        md_content = self.format_health_section_md(health_data, detail_level)
        
        # Conversions de base Markdown -> HTML
        html_content = md_content.replace("# ", "<h1>").replace("\n## ", "</p>\n<h2>")
        html_content = html_content.replace("\n### ", "</p>\n<h3>")
        html_content = html_content.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
        html_content = html_content.replace("\n\n", "</p>\n<p>")
        html_content = html_content.replace("\n- ", "</p>\n<ul>\n<li>").replace("\n  - ", "</li>\n  <li>")
        html_content = html_content + "</p>"
        
        # Envelopper dans une div avec classe
        html_content = f'<div class="health-section">\n{html_content}\n</div>'
        
        return html_content
    
    def get_health_summary_for_text(self, health_data: Dict[str, Any]) -> str:
        """
        Extrait un résumé court pour les formats texte simples.
        
        Args:
            health_data: Données d'analyse sanitaire
            
        Returns:
            Résumé sanitaire en format texte simple
        """
        if not health_data:
            return "Aucune donnée sanitaire disponible."
        
        summary = health_data.get("summary", "")
        if not summary:
            health_score = health_data.get("overall_health_score", 0)
            health_status = health_data.get("health_status", "Inconnu")
            summary = f"État sanitaire global: {health_score:.1f}/10 ({health_status})"
        
        return summary
