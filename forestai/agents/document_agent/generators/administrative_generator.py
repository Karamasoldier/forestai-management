# -*- coding: utf-8 -*-
"""
Générateur de documents administratifs forestiers.

Ce module implémente le générateur de documents administratifs pour la gestion forestière
tels que les autorisations de coupe, déclarations fiscales, demandes d'aide, etc.
"""

import logging
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from forestai.agents.document_agent.models.document_models import (
    DocumentRequest, DocumentResult, DocumentType, DocumentFormat
)
from forestai.agents.document_agent.templates.template_manager import TemplateManager
from forestai.core.utils.html_to_pdf import html_to_pdf
from forestai.core.utils.html_to_docx import html_to_docx

logger = logging.getLogger(__name__)

class AdministrativeDocumentGenerator:
    """
    Générateur de documents administratifs forestiers.
    
    Cette classe est responsable de la génération de divers documents administratifs
    liés à la gestion forestière, tels que les autorisations de coupe, demandes d'aide, etc.
    """
    
    # Types de documents administratifs supportés
    ADMIN_DOC_TYPES = {
        "autorisation_coupe": "Autorisation de coupe",
        "declaration_fiscale": "Déclaration fiscale forestière",
        "demande_aide": "Demande d'aide forestière",
        "notice_impact": "Notice d'impact environnemental",
        "certification": "Document de certification forestière"
    }
    
    def __init__(self, template_manager: TemplateManager):
        """
        Initialise le générateur de documents administratifs.
        
        Args:
            template_manager: Gestionnaire de templates pour le rendu des documents
        """
        self.template_manager = template_manager
        logger.info("AdministrativeDocumentGenerator initialisé")
    
    def generate(self, request: DocumentRequest) -> DocumentResult:
        """
        Génère un document administratif selon les spécifications demandées.
        
        Args:
            request: Requête de génération contenant les données et formats souhaités
            
        Returns:
            Résultat de génération contenant les documents produits dans les formats demandés
        """
        start_time = time.time()
        
        # Déterminer le type de document administratif
        admin_type = request.options.get("administrative_type", "autorisation_coupe")
        logger.info(f"Génération d'un document administratif de type: {admin_type}")
        
        try:
            # Enrichir et valider les données du document
            enriched_data = self._enrich_admin_doc_data(request.data, admin_type)
            
            # Déterminer le template à utiliser
            template_name = request.template_name
            if not template_name:
                template_name = f"administrative_{admin_type}"
            
            # Générer le HTML à partir du template
            html_content = self.template_manager.render_template(
                template_name,
                enriched_data,
                document_type=DocumentType.ADMINISTRATIVE
            )
            
            # Convertir le HTML dans les formats demandés
            documents = {}
            for format_type in request.formats:
                documents[format_type.value] = self._convert_to_format(
                    html_content, 
                    format_type,
                    enriched_data
                )
            
            generation_time = time.time() - start_time
            logger.info(f"Document administratif généré en {generation_time:.2f} secondes")
            
            return DocumentResult(
                request_id=request.request_id,
                document_type=DocumentType.ADMINISTRATIVE,
                documents=documents,
                metadata=self._generate_metadata(enriched_data, admin_type),
                generation_time=generation_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du document administratif: {str(e)}", exc_info=True)
            return DocumentResult(
                request_id=request.request_id,
                document_type=DocumentType.ADMINISTRATIVE,
                documents={},
                metadata={},
                generation_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def _enrich_admin_doc_data(self, data: Dict[str, Any], admin_type: str) -> Dict[str, Any]:
        """
        Enrichit les données du document administratif avec des informations complémentaires.
        
        Args:
            data: Données brutes du document administratif
            admin_type: Type de document administratif (autorisation_coupe, declaration_fiscale, etc.)
            
        Returns:
            Données enrichies pour le rendu du template
        """
        enriched = data.copy()
        
        # Assurer que les champs communs requis sont présents
        if "reference" not in enriched:
            type_prefix = admin_type[:3].upper()
            enriched["reference"] = f"{type_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
        if "date" not in enriched:
            enriched["date"] = datetime.now().strftime("%Y-%m-%d")
            
        if "title" not in enriched:
            enriched["title"] = self.ADMIN_DOC_TYPES.get(
                admin_type, "Document administratif forestier"
            )
        
        # Enrichissements spécifiques par type de document
        if admin_type == "autorisation_coupe":
            self._enrich_autorisation_coupe(enriched)
        elif admin_type == "declaration_fiscale":
            self._enrich_declaration_fiscale(enriched)
        elif admin_type == "demande_aide":
            self._enrich_demande_aide(enriched)
        elif admin_type == "notice_impact":
            self._enrich_notice_impact(enriched)
        elif admin_type == "certification":
            self._enrich_certification(enriched)
            
        return enriched
    
    def _enrich_autorisation_coupe(self, data: Dict[str, Any]) -> None:
        """
        Enrichit les données spécifiques à une autorisation de coupe.
        
        Args:
            data: Données à enrichir
        """
        if "validity_period" not in data:
            data["validity_period"] = "1 an"
            
        if "volume_m3" in data and "surface_ha" in data:
            try:
                volume = float(data["volume_m3"])
                surface = float(data["surface_ha"])
                data["volume_per_ha"] = round(volume / surface, 2)
            except (ValueError, ZeroDivisionError):
                pass
        
        # Ajout des références légales et conditions par défaut
        if "legal_references" not in data:
            data["legal_references"] = [
                "Article L. 124-5 du Code forestier",
                "Article R. 124-1 du Code forestier"
            ]
            
        if "conditions" not in data:
            data["conditions"] = [
                "Respect des bonnes pratiques sylvicoles",
                "Conservation d'un minimum de 25 arbres adultes par hectare",
                "Reboisement obligatoire après coupe rase"
            ]
    
    def _enrich_declaration_fiscale(self, data: Dict[str, Any]) -> None:
        """
        Enrichit les données spécifiques à une déclaration fiscale forestière.
        
        Args:
            data: Données à enrichir
        """
        if "fiscal_year" not in data:
            data["fiscal_year"] = datetime.now().year
            
        if "submission_deadline" not in data:
            data["submission_deadline"] = f"{datetime.now().year}-05-31"
        
        # Calculs automatiques des montants
        if "parcels" in data:
            total_area = sum(parcel.get("area_ha", 0) for parcel in data["parcels"])
            data["total_area_ha"] = round(total_area, 2)
            
            if "tax_rate_per_ha" in data:
                try:
                    tax_rate = float(data["tax_rate_per_ha"])
                    data["estimated_tax"] = round(total_area * tax_rate, 2)
                except ValueError:
                    pass
    
    def _enrich_demande_aide(self, data: Dict[str, Any]) -> None:
        """
        Enrichit les données spécifiques à une demande d'aide forestière.
        
        Args:
            data: Données à enrichir
        """
        if "submission_date" not in data:
            data["submission_date"] = datetime.now().strftime("%Y-%m-%d")
            
        if "project_summary" not in data and "project_description" in data:
            # Créer un résumé à partir de la description
            description = data["project_description"]
            if len(description) > 200:
                data["project_summary"] = description[:197] + "..."
            else:
                data["project_summary"] = description
        
        # Calcul du budget total
        if "budget_items" in data:
            total_amount = sum(item.get("amount", 0) for item in data["budget_items"])
            data["total_budget"] = round(total_amount, 2)
            
            # Calcul de l'aide demandée si taux défini
            if "funding_rate" in data:
                try:
                    funding_rate = float(data["funding_rate"]) / 100
                    data["requested_amount"] = round(total_amount * funding_rate, 2)
                except ValueError:
                    pass
    
    def _enrich_notice_impact(self, data: Dict[str, Any]) -> None:
        """
        Enrichit les données spécifiques à une notice d'impact environnemental.
        
        Args:
            data: Données à enrichir
        """
        if "evaluation_date" not in data:
            data["evaluation_date"] = datetime.now().strftime("%Y-%m-%d")
            
        # Déterminer automatiquement le niveau d'impact si non spécifié
        if "impact_level" not in data and "impacts" in data:
            impact_scores = [impact.get("severity", 0) for impact in data["impacts"]]
            if impact_scores:
                avg_impact = sum(impact_scores) / len(impact_scores)
                if avg_impact < 2:
                    data["impact_level"] = "Faible"
                elif avg_impact < 3.5:
                    data["impact_level"] = "Modéré"
                else:
                    data["impact_level"] = "Fort"
            else:
                data["impact_level"] = "Non déterminé"
        
        # Générer des mesures correctives si non spécifiées
        if "mitigation_measures" not in data and "impacts" in data:
            data["mitigation_measures"] = []
            default_measures = {
                "habitat": "Création de zones de protection pour la biodiversité",
                "soil": "Techniques de travail du sol à faible impact",
                "water": "Mise en place de zones tampons près des cours d'eau",
                "landscape": "Intégration paysagère des interventions",
                "noise": "Limitation des horaires de travaux",
                "pollution": "Utilisation d'huiles biodégradables pour les équipements"
            }
            
            # Ajouter des mesures selon les types d'impacts
            for impact in data["impacts"]:
                impact_type = impact.get("type", "").lower()
                for key, measure in default_measures.items():
                    if key in impact_type and measure not in data["mitigation_measures"]:
                        data["mitigation_measures"].append(measure)
    
    def _enrich_certification(self, data: Dict[str, Any]) -> None:
        """
        Enrichit les données spécifiques à un document de certification forestière.
        
        Args:
            data: Données à enrichir
        """
        if "issue_date" not in data:
            data["issue_date"] = datetime.now().strftime("%Y-%m-%d")
            
        if "expiry_date" not in data and "validity_years" in data:
            try:
                issue_date = datetime.strptime(data["issue_date"], "%Y-%m-%d")
                validity_years = int(data["validity_years"])
                expiry_date = issue_date.replace(year=issue_date.year + validity_years)
                data["expiry_date"] = expiry_date.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                # En cas d'erreur, expiration par défaut à 5 ans
                data["expiry_date"] = datetime.now().replace(year=datetime.now().year + 5).strftime("%Y-%m-%d")
        
        # Ajouter des critères de certification par défaut si non spécifiés
        if "certification_criteria" not in data:
            data["certification_criteria"] = [
                "Gestion forestière durable conforme aux standards internationaux",
                "Traçabilité des produits forestiers",
                "Respect des droits des travailleurs et populations locales",
                "Protection des zones à haute valeur de conservation",
                "Plan de gestion forestière à jour et conforme"
            ]
    
    def _convert_to_format(self, html_content: str, format_type: DocumentFormat, data: Dict[str, Any]) -> Any:
        """
        Convertit le contenu HTML dans le format demandé.
        
        Args:
            html_content: Contenu HTML du document
            format_type: Format de sortie souhaité
            data: Données du document pour les métadonnées
            
        Returns:
            Contenu converti dans le format demandé
        """
        if format_type == DocumentFormat.HTML:
            return html_content
        
        elif format_type == DocumentFormat.PDF:
            # Conversion vers PDF
            return html_to_pdf(
                html_content, 
                title=data.get("title", "Document Administratif Forestier"),
                author=data.get("author", "ForestAI"),
                subject=f"Document administratif - {data.get('reference', '')}"
            )
        
        elif format_type == DocumentFormat.DOCX:
            # Conversion vers DOCX
            return html_to_docx(
                html_content,
                title=data.get("title", "Document Administratif Forestier"),
                author=data.get("author", "ForestAI"),
                subject=f"Document administratif - {data.get('reference', '')}"
            )
        
        elif format_type == DocumentFormat.TXT:
            # Version simplifiée texte (sans mise en forme)
            from html.parser import HTMLParser
            
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self.in_body = False
                
                def handle_starttag(self, tag, attrs):
                    if tag == "body":
                        self.in_body = True
                    elif tag == "p" or tag == "h1" or tag == "h2" or tag == "h3" or tag == "h4" or tag == "tr":
                        self.text.append("\n")
                    elif tag == "li":
                        self.text.append("\n- ")
                    elif tag == "br":
                        self.text.append("\n")
                
                def handle_endtag(self, tag):
                    if tag == "body":
                        self.in_body = False
                    elif tag == "tr":
                        self.text.append("\n")
                
                def handle_data(self, data):
                    if self.in_body:
                        self.text.append(data.strip())
            
            extractor = TextExtractor()
            extractor.feed(html_content)
            return "".join(extractor.text)
        
        else:
            raise ValueError(f"Format non supporté: {format_type.value}")
    
    def _generate_metadata(self, data: Dict[str, Any], admin_type: str) -> Dict[str, Any]:
        """
        Génère les métadonnées pour le document produit.
        
        Args:
            data: Données du document administratif
            admin_type: Type de document administratif
            
        Returns:
            Métadonnées du document
        """
        metadata = {
            "document_type": admin_type,
            "reference": data.get("reference", ""),
            "title": data.get("title", "Document Administratif Forestier"),
            "timestamp": datetime.now().isoformat(),
            "authority": data.get("authority", "")
        }
        
        # Ajouter des métadonnées spécifiques selon le type de document
        if admin_type == "autorisation_coupe":
            metadata.update({
                "forest_owner": data.get("owner", {}).get("name", ""),
                "volume_m3": data.get("volume_m3", 0),
                "surface_ha": data.get("surface_ha", 0),
                "validity_period": data.get("validity_period", "")
            })
        elif admin_type == "declaration_fiscale":
            metadata.update({
                "taxpayer": data.get("taxpayer", {}).get("name", ""),
                "fiscal_year": data.get("fiscal_year", ""),
                "total_area_ha": data.get("total_area_ha", 0),
                "estimated_tax": data.get("estimated_tax", 0)
            })
        elif admin_type == "demande_aide":
            metadata.update({
                "applicant": data.get("applicant", {}).get("name", ""),
                "aid_program": data.get("aid_program", ""),
                "project_title": data.get("project_title", ""),
                "total_budget": data.get("total_budget", 0),
                "requested_amount": data.get("requested_amount", 0)
            })
        elif admin_type == "notice_impact":
            metadata.update({
                "project_title": data.get("project_title", ""),
                "project_owner": data.get("project_owner", {}).get("name", ""),
                "impact_level": data.get("impact_level", ""),
                "evaluation_date": data.get("evaluation_date", "")
            })
        elif admin_type == "certification":
            metadata.update({
                "certificate_holder": data.get("certificate_holder", {}).get("name", ""),
                "certification_type": data.get("certification_type", ""),
                "issue_date": data.get("issue_date", ""),
                "expiry_date": data.get("expiry_date", ""),
                "certification_body": data.get("certification_body", {}).get("name", "")
            })
            
        return metadata
