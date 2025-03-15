# -*- coding: utf-8 -*-
"""
Générateur de cahiers des charges pour le DocumentAgent.

Ce module fournit les fonctionnalités nécessaires pour générer des cahiers
des charges liés aux travaux forestiers.
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from forestai.agents.document_agent.templates.template_manager import TemplateManager
from forestai.agents.document_agent.models.document_models import (
    DocumentType,
    DocumentFormat,
    DocumentRequest,
    DocumentResult
)
from forestai.core.utils.html_to_pdf import html_to_pdf
from forestai.core.utils.html_to_docx import html_to_docx

logger = logging.getLogger(__name__)

class SpecificationGenerator:
    """
    Générateur de cahiers des charges forestiers.
    
    Cette classe est responsable de la génération de cahiers des charges
    pour les travaux forestiers, en utilisant des templates adaptés.
    """
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """
        Initialise le générateur de cahiers des charges.
        
        Args:
            template_manager: Gestionnaire de templates à utiliser
        """
        self.template_manager = template_manager or TemplateManager()
        logger.info("SpecificationGenerator initialisé")
    
    def generate(self, request: DocumentRequest) -> DocumentResult:
        """
        Génère un cahier des charges à partir des données fournies.
        
        Args:
            request: Requête de génération de document
            
        Returns:
            Résultat de la génération du document
        """
        start_time = time.time()
        logger.info(f"Génération d'un cahier des charges")
        
        # Valider que le type de document est bien un cahier des charges
        if request.document_type != DocumentType.SPECIFICATION:
            error_msg = f"Type de document invalide: {request.document_type}, attendu: SPECIFICATION"
            logger.error(error_msg)
            return DocumentResult(
                request_id=request.request_id,
                document_type=request.document_type,
                documents={},
                success=False,
                error_message=error_msg
            )
        
        # Déterminer le template à utiliser
        template_id = request.template_name or self._select_template(request.data)
        
        # Préparer et enrichir les données
        context_data = self._prepare_data(request.data)
        
        # Générer le contenu HTML
        html_content = self.template_manager.render_template(template_id, context_data)
        
        if not html_content:
            error_msg = f"Échec de la génération du contenu HTML pour le template {template_id}"
            logger.error(error_msg)
            return DocumentResult(
                request_id=request.request_id,
                document_type=request.document_type,
                documents={},
                success=False,
                error_message=error_msg
            )
        
        # Générer les documents dans les formats demandés
        documents = {}
        
        # Par défaut, toujours inclure le HTML
        documents[DocumentFormat.HTML] = html_content
        
        # Générer les autres formats demandés
        for doc_format in request.formats:
            if doc_format == DocumentFormat.HTML:
                continue  # Déjà fait
            
            if doc_format == DocumentFormat.PDF:
                try:
                    pdf_content = html_to_pdf(html_content)
                    documents[DocumentFormat.PDF] = pdf_content
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion en PDF: {str(e)}")
            
            elif doc_format == DocumentFormat.DOCX:
                try:
                    docx_content = html_to_docx(html_content)
                    documents[DocumentFormat.DOCX] = docx_content
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion en DOCX: {str(e)}")
            
            elif doc_format == DocumentFormat.TXT:
                try:
                    # Conversion simpliste HTML -> TXT
                    import html2text
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    txt_content = h.handle(html_content)
                    documents[DocumentFormat.TXT] = txt_content
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion en TXT: {str(e)}")
        
        generation_time = time.time() - start_time
        logger.info(f"Cahier des charges généré en {generation_time:.2f} secondes dans {len(documents)} formats")
        
        # Créer les métadonnées
        metadata = {
            "template_id": template_id,
            "specification_type": context_data.get("spec_type", ""),
            "specification_title": context_data.get("title", ""),
            "generation_date": datetime.now().isoformat(),
            "generation_time_seconds": generation_time,
            "formats": list(documents.keys())
        }
        
        # Ajouter des métadonnées spécifiques au cahier des charges
        if "reference" in context_data:
            metadata["reference"] = context_data["reference"]
        if "client" in context_data:
            metadata["client"] = context_data["client"].get("name", "")
        if "work_types" in context_data:
            metadata["work_types"] = context_data["work_types"]
        if "parcels" in context_data:
            metadata["parcels_count"] = len(context_data["parcels"])
        
        return DocumentResult(
            request_id=request.request_id,
            document_type=request.document_type,
            documents={str(k): v for k, v in documents.items()},
            metadata=metadata,
            generation_time=generation_time,
            success=True
        )
    
    def _select_template(self, data: Dict[str, Any]) -> str:
        """
        Sélectionne le template le plus approprié pour les données fournies.
        
        Args:
            data: Données pour lesquelles sélectionner un template
            
        Returns:
            Identifiant du template sélectionné
        """
        # Par défaut, utiliser un template générique
        default_template_id = "spec_generic"
        
        # Si le type de cahier des charges est spécifié, utiliser un template spécifique
        spec_type = data.get("spec_type", "").lower()
        
        if "coupe" in spec_type or "exploitation" in spec_type:
            return "spec_logging"
        elif "plantation" in spec_type or "reboisement" in spec_type:
            return "spec_planting"
        elif "entretien" in spec_type or "maintenance" in spec_type:
            return "spec_maintenance"
        elif "inventaire" in spec_type:
            return "spec_inventory"
        
        # Vérifier si le template par défaut existe
        try:
            if self.template_manager.get_template(default_template_id):
                return default_template_id
            else:
                # Obtenir le premier template de cahier des charges disponible
                spec_templates = self.template_manager.get_available_templates(DocumentType.SPECIFICATION)
                if spec_templates:
                    return spec_templates[0].template_id
                else:
                    # Créer un template générique si aucun n'existe
                    self.template_manager.create_template_skeleton(
                        default_template_id,
                        DocumentType.SPECIFICATION,
                        "Cahier des Charges Forestier Générique",
                        "Template générique pour les cahiers des charges forestiers"
                    )
                    return default_template_id
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du template: {str(e)}")
            return default_template_id
    
    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare et enrichit les données pour la génération du cahier des charges.
        
        Args:
            data: Données brutes à préparer
            
        Returns:
            Données préparées et enrichies
        """
        # Copier les données pour ne pas modifier l'original
        context = data.copy()
        
        # Ajouter la date actuelle si non fournie
        if "date" not in context:
            context["date"] = datetime.now()
        
        # Formater les dates si nécessaire
        if isinstance(context.get("date"), str):
            try:
                context["date"] = datetime.strptime(context["date"], "%Y-%m-%d")
            except ValueError:
                try:
                    context["date"] = datetime.strptime(context["date"], "%d/%m/%Y")
                except ValueError:
                    pass
        
        # Ajouter des métadonnées génériques
        context["generated_by"] = "ForestAI DocumentAgent"
        context["generation_date"] = datetime.now()
        
        # Enrichir avec le titre si non fourni
        if "title" not in context:
            spec_type = context.get("spec_type", "travaux forestiers")
            context["title"] = f"Cahier des charges - {spec_type.capitalize()}"
        
        # Générer une référence si non fournie
        if "reference" not in context:
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            spec_type_code = "".join([c[0].upper() for c in context.get("spec_type", "CDC").split() if c])[:3]
            context["reference"] = f"CDC-{spec_type_code}-{timestamp}"
        
        # Enrichir les lots si nécessaires
        if "lots" not in context and "parcels" in context:
            context["lots"] = self._generate_lots_from_parcels(context["parcels"])
        
        # Enrichir les clauses techniques si nécessaires
        if "technical_clauses" not in context:
            context["technical_clauses"] = self._generate_default_technical_clauses(context)
        
        # Enrichir les clauses administratives si nécessaires
        if "administrative_clauses" not in context:
            context["administrative_clauses"] = self._generate_default_administrative_clauses(context)
        
        return context
    
    def _generate_lots_from_parcels(self, parcels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Génère des lots à partir des parcelles fournies.
        
        Args:
            parcels: Liste de parcelles forestières
            
        Returns:
            Liste de lots générés
        """
        lots = []
        
        # Si une seule parcelle ou peu de parcelles, un seul lot
        if len(parcels) <= 3:
            lot = {
                "number": 1,
                "title": "Lot unique",
                "description": "Ensemble des travaux sur toutes les parcelles concernées",
                "parcels": parcels,
                "total_area_ha": sum([p.get("area_ha", 0) for p in parcels])
            }
            lots.append(lot)
        else:
            # Regrouper les parcelles par secteur ou commune si possible
            sectors = {}
            for parcel in parcels:
                sector = parcel.get("sector", parcel.get("commune", "secteur-1"))
                if sector not in sectors:
                    sectors[sector] = []
                sectors[sector].append(parcel)
            
            # Créer un lot par secteur
            for i, (sector, sector_parcels) in enumerate(sectors.items(), 1):
                lot = {
                    "number": i,
                    "title": f"Lot {i} - {sector}",
                    "description": f"Travaux sur {len(sector_parcels)} parcelles du secteur {sector}",
                    "parcels": sector_parcels,
                    "total_area_ha": sum([p.get("area_ha", 0) for p in sector_parcels])
                }
                lots.append(lot)
        
        return lots
    
    def _generate_default_technical_clauses(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère des clauses techniques par défaut pour le cahier des charges en fonction du contexte.
        
        Args:
            data: Données du cahier des charges
            
        Returns:
            Liste de clauses techniques générées
        """
        clauses = []
        spec_type = data.get("spec_type", "").lower()
        
        # Clause sur les normes générales
        clauses.append({
            "title": "Normes et réglementations",
            "content": "Les travaux devront être réalisés en conformité avec les normes et réglementations forestières en vigueur, notamment le Code Forestier et les directives régionales de gestion forestière."
        })
        
        # Clauses spécifiques selon le type de travaux
        if "coupe" in spec_type or "exploitation" in spec_type:
            clauses.append({
                "title": "Modalités d'exploitation",
                "content": "L'exploitation devra respecter les modalités suivantes : débardage par les cloisonnements existants, préservation des sols, respect strict des zones de protection et des semis d'avenir."
            })
            clauses.append({
                "title": "Calendrier d'intervention",
                "content": "Les travaux d'abattage et de débardage devront être réalisés hors période de nidification (mars à juillet) et en période de portance des sols suffisante."
            })
        
        elif "plantation" in spec_type or "reboisement" in spec_type:
            clauses.append({
                "title": "Qualité des plants",
                "content": "Les plants forestiers utilisés devront être certifiés MFR (Matériels Forestiers de Reproduction), adaptés à la station forestière, et accompagnés des documents de traçabilité réglementaires."
            })
            clauses.append({
                "title": "Méthode de plantation",
                "content": "Les plants seront installés selon les espacements définis dans les prescriptions techniques par lot, avec un travail du sol préalable si nécessaire. Chaque plant bénéficiera d'une protection contre le gibier adaptée au contexte local."
            })
        
        elif "entretien" in spec_type:
            clauses.append({
                "title": "Nature des interventions",
                "content": "Les travaux d'entretien comprennent le dégagement des plants, la taille de formation si nécessaire, et le maintien des protections contre le gibier en bon état. Les produits phytosanitaires sont proscrits sauf autorisation expresse du maître d'ouvrage."
            })
        
        # Clauses générales pour tous types de travaux
        clauses.append({
            "title": "Protection de l'environnement",
            "content": "L'entreprise prestataire s'engage à minimiser l'impact environnemental des travaux, notamment en évitant toute pollution (huiles, carburants), en respectant la faune et la flore protégées, et en préservant les zones sensibles (cours d'eau, zones humides)."
        })
        
        clauses.append({
            "title": "Sécurité du chantier",
            "content": "L'entreprise prestataire est responsable de la sécurité du chantier, de la signalisation adaptée, et du respect des règles de sécurité pour son personnel et les tiers. Elle devra disposer des qualifications professionnelles et des assurances requises pour ce type de travaux."
        })
        
        return clauses
    
    def _generate_default_administrative_clauses(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère des clauses administratives par défaut pour le cahier des charges.
        
        Args:
            data: Données du cahier des charges
            
        Returns:
            Liste de clauses administratives générées
        """
        clauses = []
        
        # Clause sur les conditions de réponse
        clauses.append({
            "title": "Conditions de réponse à l'appel d'offres",
            "content": "Les candidats doivent fournir une offre détaillée, comprenant un devis détaillé par lot, les qualifications professionnelles de l'entreprise, les références pour des travaux similaires, ainsi qu'une attestation d'assurance responsabilité civile professionnelle."
        })
        
        # Clause sur les conditions d'exécution
        clauses.append({
            "title": "Délais d'exécution",
            "content": f"Les travaux devront démarrer au plus tard le {data.get('start_date', '...')} et être achevés avant le {data.get('end_date', '...')}. Un calendrier prévisionnel d'intervention par lot devra être fourni par le prestataire avant le démarrage des travaux."
        })
        
        # Clause sur les conditions de paiement
        clauses.append({
            "title": "Conditions de paiement",
            "content": "Le paiement sera effectué selon les modalités suivantes : 30% à la signature du contrat, 40% à mi-parcours des travaux après validation par le maître d'ouvrage, et 30% à la réception définitive des travaux."
        })
        
        # Clause sur la réception des travaux
        clauses.append({
            "title": "Modalités de réception des travaux",
            "content": "Une réception provisoire sera effectuée à l'achèvement des travaux, suivie d'une période d'observation de 3 mois. La réception définitive sera prononcée à l'issue de cette période, sous réserve de la bonne exécution des éventuelles reprises demandées."
        })
        
        # Clause sur les pénalités
        clauses.append({
            "title": "Pénalités",
            "content": "Des pénalités pourront être appliquées en cas de retard (150€ par jour calendaire de retard), de non-respect des clauses techniques (10% du montant du lot concerné), ou de dommages environnementaux (selon la gravité, jusqu'à 20% du montant total)."
        })
        
        # Clause sur la résiliation
        clauses.append({
            "title": "Résiliation",
            "content": "Le maître d'ouvrage se réserve le droit de résilier le contrat en cas de manquement grave aux clauses du cahier des charges, après mise en demeure restée sans effet pendant 15 jours."
        })
        
        # Clause sur les litiges
        clauses.append({
            "title": "Règlement des litiges",
            "content": "En cas de litige, les parties s'efforceront de trouver une solution amiable. À défaut, le litige sera porté devant le tribunal compétent du ressort du maître d'ouvrage."
        })
        
        return clauses
