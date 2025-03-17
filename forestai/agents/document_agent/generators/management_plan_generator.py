# -*- coding: utf-8 -*-
"""
Générateur de documents de plans de gestion forestière.

Ce module implémente le générateur de documents pour les plans de gestion forestière
tels que les plans simples de gestion (PSG) et autres documents d'aménagement.
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

class ManagementPlanGenerator:
    """
    Générateur de documents de plans de gestion forestière.
    
    Cette classe est responsable de la génération de documents de plans de gestion,
    y compris les plans simples de gestion (PSG), documents d'aménagement, etc.
    """
    
    def __init__(self, template_manager: TemplateManager):
        """
        Initialise le générateur de plans de gestion.
        
        Args:
            template_manager: Gestionnaire de templates pour le rendu des documents
        """
        self.template_manager = template_manager
        logger.info("ManagementPlanGenerator initialisé")
    
    def generate(self, request: DocumentRequest) -> DocumentResult:
        """
        Génère un document de plan de gestion selon les spécifications demandées.
        
        Args:
            request: Requête de génération contenant les données et formats souhaités
            
        Returns:
            Résultat de génération contenant les documents produits dans les formats demandés
        """
        start_time = time.time()
        logger.info(f"Génération d'un plan de gestion de type: {request.data.get('plan_type', 'standard')}")
        
        try:
            # Enrichir et valider les données du plan
            enriched_data = self._enrich_plan_data(request.data)
            
            # Déterminer le template à utiliser
            template_name = request.template_name
            if not template_name:
                plan_type = request.data.get("plan_type", "plan_simple_gestion")
                template_name = f"management_plan_{plan_type}"
            
            # Générer le HTML à partir du template
            html_content = self.template_manager.render_template(
                template_name,
                enriched_data,
                document_type=DocumentType.MANAGEMENT_PLAN
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
            logger.info(f"Plan de gestion généré en {generation_time:.2f} secondes")
            
            return DocumentResult(
                request_id=request.request_id,
                document_type=DocumentType.MANAGEMENT_PLAN,
                documents=documents,
                metadata=self._generate_metadata(enriched_data),
                generation_time=generation_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du plan de gestion: {str(e)}", exc_info=True)
            return DocumentResult(
                request_id=request.request_id,
                document_type=DocumentType.MANAGEMENT_PLAN,
                documents={},
                metadata={},
                generation_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def _enrich_plan_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrichit les données du plan de gestion avec des informations complémentaires.
        
        Args:
            data: Données brutes du plan de gestion
            
        Returns:
            Données enrichies pour le rendu du template
        """
        enriched = data.copy()
        
        # Assurer que les champs requis sont présents
        if "reference" not in enriched:
            enriched["reference"] = f"PSG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
        if "date" not in enriched:
            enriched["date"] = datetime.now().strftime("%Y-%m-%d")
            
        if "title" not in enriched:
            plan_type = enriched.get("plan_type", "plan_simple_gestion")
            if plan_type == "plan_simple_gestion":
                title = "Plan Simple de Gestion"
            elif plan_type == "document_amenagement":
                title = "Document d'Aménagement Forestier"
            elif plan_type == "plan_gestion_durable":
                title = "Plan de Gestion Durable"
            else:
                title = "Plan de Gestion Forestière"
                
            enriched["title"] = title
        
        # Enrichir les périodes et dates
        if "start_date" not in enriched:
            enriched["start_date"] = datetime.now().strftime("%Y-%m-%d")
            
        if "end_date" not in enriched and "duration_years" in enriched:
            start_date = datetime.strptime(enriched["start_date"], "%Y-%m-%d")
            end_year = start_date.year + int(enriched["duration_years"])
            enriched["end_date"] = f"{end_year}-{start_date.month:02d}-{start_date.day:02d}"
        
        # Enrichir les informations sur les parcelles
        if "parcels" in enriched:
            total_area = sum(parcel.get("area_ha", 0) for parcel in enriched["parcels"])
            enriched["total_area_ha"] = round(total_area, 2)
            
            # Ajouter des identifiants aux parcelles si non présents
            for idx, parcel in enumerate(enriched["parcels"]):
                if "parcel_id" not in parcel:
                    parcel["parcel_id"] = f"P{idx+1:03d}"
        
        # Enrichir les informations sur les peuplements
        if "stands" in enriched:
            # Calculer les totaux de surface par type de peuplement
            stand_types = {}
            for stand in enriched["stands"]:
                stand_type = stand.get("type", "Autre")
                if stand_type not in stand_types:
                    stand_types[stand_type] = 0
                stand_types[stand_type] += stand.get("area_ha", 0)
            
            enriched["stand_type_summary"] = [
                {"type": stand_type, "area_ha": round(area, 2)}
                for stand_type, area in stand_types.items()
            ]
        
        return enriched
    
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
                title=data.get("title", "Plan de Gestion Forestière"),
                author=data.get("author", "ForestAI"),
                subject=f"Plan de gestion forestière - {data.get('reference', '')}"
            )
        
        elif format_type == DocumentFormat.DOCX:
            # Conversion vers DOCX
            return html_to_docx(
                html_content,
                title=data.get("title", "Plan de Gestion Forestière"),
                author=data.get("author", "ForestAI"),
                subject=f"Plan de gestion forestière - {data.get('reference', '')}"
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
    
    def _generate_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère les métadonnées pour le document produit.
        
        Args:
            data: Données du plan de gestion
            
        Returns:
            Métadonnées du document
        """
        return {
            "document_type": "plan_gestion",
            "plan_type": data.get("plan_type", "plan_simple_gestion"),
            "reference": data.get("reference", ""),
            "title": data.get("title", "Plan de Gestion Forestière"),
            "property_name": data.get("property_name", ""),
            "owner": data.get("owner", {}).get("name", ""),
            "total_area_ha": data.get("total_area_ha", 0),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
            "duration_years": data.get("duration_years", 0),
            "parcels_count": len(data.get("parcels", [])),
            "timestamp": datetime.now().isoformat()
        }
