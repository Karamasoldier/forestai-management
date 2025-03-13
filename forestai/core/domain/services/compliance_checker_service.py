"""
Service de vérification de conformité réglementaire.

Ce service est responsable de l'analyse de conformité des projets forestiers
par rapport aux réglementations applicables, et de la génération de recommandations
pour la mise en conformité.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
import datetime

from forestai.core.domain.models.regulation import Regulation, RegulatoryRequirement
from forestai.core.domain.models.parcel import Parcel, ParcelProject
from forestai.core.domain.services.regulatory_framework_service import RegulatoryFrameworkService
from forestai.core.utils.logging_config import LoggingConfig

# Configuration du logger
logger = LoggingConfig.get_instance().get_logger(__name__)

class ComplianceCheckerService:
    """
    Service de vérification de conformité réglementaire.
    
    Ce service permet de:
    - Vérifier la conformité d'un projet avec les réglementations applicables
    - Générer des recommandations pour la mise en conformité
    - Identifier les autorisations nécessaires
    - Générer des rapports de conformité
    """
    
    def __init__(self, regulatory_service: RegulatoryFrameworkService):
        """
        Initialise le service de vérification de conformité.
        
        Args:
            regulatory_service: Service de gestion du cadre réglementaire
        """
        self.regulatory_service = regulatory_service
        logger.info("Service de vérification de conformité initialisé")
    
    def check_project_compliance(self, project: ParcelProject) -> List[Dict[str, Any]]:
        """
        Vérifie la conformité d'un projet avec les réglementations applicables.
        
        Args:
            project: Projet à analyser
        
        Returns:
            Liste des résultats de conformité par réglementation
        """
        logger.info(f"Vérification de conformité pour le projet {project.id} de type {project.project_type}")
        
        # Déterminer les régions concernées par le projet
        regions = []
        for parcel in project.parcels:
            if hasattr(parcel, "region") and parcel.region:
                regions.append(parcel.region)
        
        # Si aucune région n'est déterminée, utiliser le caractère générique
        if not regions:
            regions = ["*"]
        
        # Récupérer les réglementations applicables
        applicable_regulations = self.regulatory_service.filter_applicable_regulations(
            project_type=project.project_type,
            regions=regions,
            parameters=project.parameters
        )
        
        logger.debug(f"Trouvé {len(applicable_regulations)} réglementations applicables")
        
        # Vérifier la conformité avec chaque règlement
        compliance_results = []
        for regulation in applicable_regulations:
            result = self._check_regulation_compliance(regulation, project)
            compliance_results.append(result)
        
        return compliance_results
    
    def _check_regulation_compliance(self, regulation: Regulation, project: ParcelProject) -> Dict[str, Any]:
        """
        Vérifie la conformité d'un projet avec une réglementation spécifique.
        
        Args:
            regulation: Réglementation à vérifier
            project: Projet à analyser
        
        Returns:
            Résultat de l'analyse de conformité
        """
        requirement_results = []
        
        for requirement in regulation.requirements:
            # Évaluer la condition de l'exigence
            compliant = True
            reason = ""
            
            try:
                # Créer un contexte d'évaluation avec les propriétés du projet
                eval_context = {
                    "project_type": project.project_type,
                    "parameters": project.parameters if project.parameters else {}
                }
                
                # Ajouter des propriétés agrégées des parcelles
                total_area = sum(getattr(p, "area", 0) for p in project.parcels)
                eval_context["area"] = total_area
                eval_context["parcel_count"] = len(project.parcels)
                
                # Évaluer la condition
                if requirement.condition:
                    compliant = eval(requirement.condition, {"__builtins__": {}}, eval_context)
                
                # Vérifier les seuils
                if requirement.threshold is not None:
                    if "area" in requirement.condition and total_area > requirement.threshold:
                        compliant = True
                    elif "parcel_count" in requirement.condition and len(project.parcels) > requirement.threshold:
                        compliant = True
                
                reason = "Condition évaluée"
            except Exception as e:
                logger.error(f"Erreur lors de l'évaluation de la condition {requirement.condition}: {e}")
                compliant = False
                reason = f"Erreur d'évaluation: {str(e)}"
            
            requirement_results.append({
                "requirement_id": requirement.id,
                "description": requirement.description,
                "compliant": compliant,
                "reason": reason,
                "category": requirement.category,
                "severity": requirement.severity
            })
        
        # Une réglementation est conforme si toutes ses exigences sont respectées
        regulation_compliant = all(r["compliant"] for r in requirement_results)
        
        return {
            "regulation_id": regulation.id,
            "name": regulation.name,
            "description": regulation.description,
            "reference": regulation.reference_text,
            "authority": regulation.authority,
            "compliant": regulation_compliant,
            "requirement_results": requirement_results
        }
    
    def generate_recommendations(self, compliance_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Génère des recommandations pour la mise en conformité.
        
        Args:
            compliance_results: Résultats de l'analyse de conformité
        
        Returns:
            Liste des recommandations
        """
        recommendations = []
        
        for result in compliance_results:
            if not result["compliant"]:
                # Générer des recommandations pour chaque exigence non conforme
                for req_result in result["requirement_results"]:
                    if not req_result["compliant"]:
                        recommendation = {
                            "regulation_id": result["regulation_id"],
                            "requirement_id": req_result["requirement_id"],
                            "issue": req_result["description"],
                            "priority": "high" if req_result["severity"] == "high" else "medium",
                            "action": self._get_recommendation_action(req_result["category"], result["regulation_id"]),
                            "authority": result["authority"]
                        }
                        recommendations.append(recommendation)
        
        return recommendations
    
    def _get_recommendation_action(self, category: str, regulation_id: str) -> str:
        """
        Génère une action recommandée en fonction de la catégorie d'exigence.
        
        Args:
            category: Catégorie de l'exigence
            regulation_id: Identifiant de la réglementation
        
        Returns:
            Action recommandée
        """
        if category == "autorisation":
            return "Obtenir une autorisation préalable auprès de l'autorité compétente"
        elif category == "compensation":
            return "Prévoir des mesures de compensation forestière"
        elif category == "document":
            return "Élaborer un document de gestion durable"
        elif category == "notification":
            return "Notifier le projet auprès de l'autorité compétente"
        elif category == "evaluation":
            return "Réaliser une évaluation d'impact environnemental"
        else:
            return f"Se conformer aux exigences réglementaires ({regulation_id})"
    
    def get_required_authorizations(self, project: ParcelProject) -> List[Dict[str, Any]]:
        """
        Identifie les autorisations nécessaires pour un projet.
        
        Args:
            project: Projet à analyser
        
        Returns:
            Liste des autorisations nécessaires
        """
        authorizations = []
        
        # Déterminer les régions concernées par le projet
        regions = []
        for parcel in project.parcels:
            if hasattr(parcel, "region") and parcel.region:
                regions.append(parcel.region)
        
        # Si aucune région n'est déterminée, utiliser le caractère générique
        if not regions:
            regions = ["*"]
        
        # Récupérer les réglementations applicables
        applicable_regulations = self.regulatory_service.filter_applicable_regulations(
            project_type=project.project_type,
            regions=regions,
            parameters=project.parameters
        )
        
        # Extraire les exigences d'autorisation
        for regulation in applicable_regulations:
            for requirement in regulation.requirements:
                if requirement.category == "autorisation":
                    try:
                        # Vérifier si l'autorisation est nécessaire
                        eval_context = {
                            "project_type": project.project_type,
                            "area": sum(getattr(p, "area", 0) for p in project.parcels),
                            "parcel_count": len(project.parcels),
                            "parameters": project.parameters if project.parameters else {}
                        }
                        
                        is_required = True
                        if requirement.condition:
                            is_required = eval(requirement.condition, {"__builtins__": {}}, eval_context)
                        
                        if is_required:
                            authorizations.append({
                                "id": requirement.id,
                                "description": requirement.description,
                                "regulation_name": regulation.name,
                                "reference": requirement.reference,
                                "authority": regulation.authority
                            })
                    except Exception as e:
                        logger.error(f"Erreur lors de l'évaluation de la condition d'autorisation: {e}")
        
        return authorizations
    
    def check_water_protection(self, parcels: List[Parcel]) -> Dict[str, Any]:
        """
        Vérifie les protections des eaux pour des parcelles.
        
        Args:
            parcels: Liste des parcelles à vérifier
        
        Returns:
            Rapport sur les protections des eaux
        """
        water_regulations = self.regulatory_service.get_water_protection_regulations()
        results = []
        
        # Créer un projet fictif pour chaque parcelle pour analyser les réglementations
        for parcel in parcels:
            project = ParcelProject(
                id=f"WATER-{parcel.id}",
                parcels=[parcel],
                project_type="any",
                parameters={}
            )
            
            # Vérifier la conformité avec chaque réglementation liée à l'eau
            parcel_results = []
            for regulation in water_regulations:
                result = self._check_regulation_compliance(regulation, project)
                parcel_results.append(result)
            
            # Déterminer si la parcelle est dans une zone de protection
            is_protected = any(
                not result["compliant"] for result in parcel_results
            )
            
            results.append({
                "parcel_id": parcel.id,
                "is_water_protected": is_protected,
                "protection_details": [
                    {
                        "regulation_id": result["regulation_id"],
                        "name": result["name"],
                        "description": result["description"],
                        "compliant": result["compliant"]
                    }
                    for result in parcel_results
                    if not result["compliant"]
                ]
            })
        
        # Agréger les résultats
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_parcels": len(parcels),
            "protected_parcels": sum(1 for r in results if r["is_water_protected"]),
            "parcel_results": results
        }
    
    def generate_formatted_report(self, compliance_results: Dict[str, Any], output_format: str = "json") -> str:
        """
        Génère un rapport de conformité formaté.
        
        Args:
            compliance_results: Résultats de l'analyse de conformité
            output_format: Format de sortie (json, txt, html)
        
        Returns:
            Rapport formaté
        """
        if output_format == "json":
            return json.dumps(compliance_results, ensure_ascii=False, indent=2)
        
        elif output_format == "txt":
            report = []
            
            # En-tête
            report.append("="*80)
            report.append(f"RAPPORT DE CONFORMITÉ RÉGLEMENTAIRE - PROJET {compliance_results['project_id']}")
            report.append("="*80)
            
            # Résumé
            report.append(f"\nType de projet: {compliance_results['project_type']}")
            report.append(f"Parcelles concernées: {', '.join(compliance_results['parcels'])}")
            report.append(f"Date d'analyse: {compliance_results['timestamp']}")
            report.append(f"Conformité globale: {'OUI' if compliance_results['overall_compliant'] else 'NON'}")
            
            # Résumé de conformité
            summary = compliance_results['compliance_summary']
            report.append(f"\nRéglementations analysées: {summary['total_regulations']}")
            report.append(f"Réglementations conformes: {summary['compliant']}")
            report.append(f"Réglementations non conformes: {summary['non_compliant']}")
            
            # Détails
            report.append("\n" + "-"*80)
            report.append("DÉTAILS DES RÉGLEMENTATIONS")
            report.append("-"*80)
            
            for result in compliance_results['detailed_results']:
                report.append(f"\n{result['regulation_id']} - {result['name']}")
                report.append(f"Référence: {result['reference']}")
                report.append(f"Autorité: {result['authority']}")
                report.append(f"Conformité: {'OUI' if result['compliant'] else 'NON'}")
                
                if not result['compliant']:
                    report.append("\nExigences non conformes:")
                    for req in result['requirement_results']:
                        if not req['compliant']:
                            report.append(f"- {req['description']} ({req['requirement_id']})")
                            report.append(f"  Raison: {req['reason']}")
            
            # Recommandations
            if compliance_results['recommendations']:
                report.append("\n" + "-"*80)
                report.append("RECOMMANDATIONS")
                report.append("-"*80)
                
                for i, rec in enumerate(compliance_results['recommendations'], 1):
                    report.append(f"\n{i}. {rec['issue']}")
                    report.append(f"   Action recommandée: {rec['action']}")
                    report.append(f"   Autorité compétente: {rec['authority']}")
                    report.append(f"   Priorité: {rec['priority']}")
            
            return "\n".join(report)
        
        elif output_format == "html":
            html = []
            
            # En-tête
            html.append("<!DOCTYPE html>")
            html.append("<html lang='fr'>")
            html.append("<head>")
            html.append("<meta charset='UTF-8'>")
            html.append("<title>Rapport de conformité réglementaire</title>")
            html.append("<style>")
            html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
            html.append("h1, h2 { color: #2c3e50; }")
            html.append(".compliant { color: green; }")
            html.append(".non-compliant { color: red; }")
            html.append(".summary { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }")
            html.append(".regulation { margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }")
            html.append(".high { color: red; font-weight: bold; }")
            html.append(".medium { color: orange; }")
            html.append(".normal { color: blue; }")
            html.append("</style>")
            html.append("</head>")
            html.append("<body>")
            
            # Titre
            html.append(f"<h1>Rapport de conformité réglementaire - Projet {compliance_results['project_id']}</h1>")
            
            # Résumé
            html.append("<div class='summary'>")
            html.append(f"<p><strong>Type de projet:</strong> {compliance_results['project_type']}</p>")
            html.append(f"<p><strong>Parcelles concernées:</strong> {', '.join(compliance_results['parcels'])}</p>")
            html.append(f"<p><strong>Date d'analyse:</strong> {compliance_results['timestamp']}</p>")
            
            if compliance_results['overall_compliant']:
                html.append("<p><strong>Conformité globale:</strong> <span class='compliant'>CONFORME</span></p>")
            else:
                html.append("<p><strong>Conformité globale:</strong> <span class='non-compliant'>NON CONFORME</span></p>")
            
            # Résumé de conformité
            summary = compliance_results['compliance_summary']
            html.append(f"<p><strong>Réglementations analysées:</strong> {summary['total_regulations']}</p>")
            html.append(f"<p><strong>Réglementations conformes:</strong> {summary['compliant']}</p>")
            html.append(f"<p><strong>Réglementations non conformes:</strong> {summary['non_compliant']}</p>")
            html.append("</div>")
            
            # Détails
            html.append("<h2>Détails des réglementations</h2>")
            
            for result in compliance_results['detailed_results']:
                html.append("<div class='regulation'>")
                html.append(f"<h3>{result['regulation_id']} - {result['name']}</h3>")
                html.append(f"<p><strong>Référence:</strong> {result['reference']}</p>")
                html.append(f"<p><strong>Autorité:</strong> {result['authority']}</p>")
                
                if result['compliant']:
                    html.append("<p><strong>Conformité:</strong> <span class='compliant'>CONFORME</span></p>")
                else:
                    html.append("<p><strong>Conformité:</strong> <span class='non-compliant'>NON CONFORME</span></p>")
                    
                    html.append("<h4>Exigences non conformes:</h4>")
                    html.append("<ul>")
                    for req in result['requirement_results']:
                        if not req['compliant']:
                            html.append(f"<li><strong>{req['description']}</strong> ({req['requirement_id']})<br>")
                            html.append(f"Raison: {req['reason']}</li>")
                    html.append("</ul>")
                
                html.append("</div>")
            
            # Recommandations
            if compliance_results['recommendations']:
                html.append("<h2>Recommandations</h2>")
                html.append("<ol>")
                
                for rec in compliance_results['recommendations']:
                    html.append("<li>")
                    html.append(f"<p><strong class='{rec['priority']}'>{rec['issue']}</strong></p>")
                    html.append(f"<p>Action recommandée: {rec['action']}</p>")
                    html.append(f"<p>Autorité compétente: {rec['authority']}</p>")
                    html.append(f"<p>Priorité: {rec['priority']}</p>")
                    html.append("</li>")
                
                html.append("</ol>")
            
            html.append("</body>")
            html.append("</html>")
            
            return "\n".join(html)
        
        else:
            raise ValueError(f"Format de sortie non pris en charge: {output_format}")
