# -*- coding: utf-8 -*-
"""
Générateur de contrats forestiers pour le DocumentAgent.

Ce module fournit les fonctionnalités nécessaires pour générer des contrats
liés à la gestion forestière, tels que les contrats de vente de bois,
les contrats de travaux forestiers, etc.
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

class ContractGenerator:
    """
    Générateur de contrats forestiers.
    
    Cette classe est responsable de la génération de contrats liés à la
    gestion forestière, en utilisant des templates et en les remplissant
    avec les données fournies.
    """
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """
        Initialise le générateur de contrats.
        
        Args:
            template_manager: Gestionnaire de templates à utiliser
        """
        self.template_manager = template_manager or TemplateManager()
        logger.info("ContractGenerator initialisé")
    
    def generate(self, request: DocumentRequest) -> DocumentResult:
        """
        Génère un contrat forestier à partir des données fournies.
        
        Args:
            request: Requête de génération de document
            
        Returns:
            Résultat de la génération du document
        """
        start_time = time.time()
        logger.info(f"Génération d'un contrat de type {request.document_type}")
        
        # Valider que le type de document est bien un contrat
        if request.document_type != DocumentType.CONTRACT:
            error_msg = f"Type de document invalide: {request.document_type}, attendu: CONTRACT"
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
        logger.info(f"Contrat généré en {generation_time:.2f} secondes dans {len(documents)} formats")
        
        # Créer les métadonnées
        metadata = {
            "template_id": template_id,
            "contract_type": context_data.get("contract_type", ""),
            "contract_title": context_data.get("title", ""),
            "generation_date": datetime.now().isoformat(),
            "generation_time_seconds": generation_time,
            "formats": list(documents.keys())
        }
        
        # Ajouter des métadonnées spécifiques au contrat
        if "contract_number" in context_data:
            metadata["contract_number"] = context_data["contract_number"]
        if "parties" in context_data:
            metadata["parties"] = [p.get("name", "") for p in context_data["parties"]]
        if "contract_date" in context_data:
            metadata["contract_date"] = context_data["contract_date"]
        if "contract_value" in context_data:
            metadata["contract_value"] = context_data["contract_value"]
        
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
        default_template_id = "contract_generic"
        
        # Si le type de contrat est spécifié, utiliser un template spécifique
        contract_type = data.get("contract_type", "").lower()
        
        if "vente" in contract_type or "bois" in contract_type:
            return "contract_wood_sale"
        elif "travaux" in contract_type or "forestier" in contract_type:
            return "contract_forestry_work"
        elif "bail" in contract_type or "location" in contract_type:
            return "contract_forestry_lease"
        elif "gestion" in contract_type:
            return "contract_management"
        
        # Vérifier si le template par défaut existe
        try:
            if self.template_manager.get_template(default_template_id):
                return default_template_id
            else:
                # Obtenir le premier template de contrat disponible
                contract_templates = self.template_manager.get_available_templates(DocumentType.CONTRACT)
                if contract_templates:
                    return contract_templates[0].template_id
                else:
                    # Créer un template générique si aucun n'existe
                    self.template_manager.create_template_skeleton(
                        default_template_id,
                        DocumentType.CONTRACT,
                        "Contrat Forestier Générique",
                        "Template générique pour les contrats forestiers"
                    )
                    return default_template_id
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du template: {str(e)}")
            return default_template_id
    
    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare et enrichit les données pour la génération du contrat.
        
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
        
        # Enrichir les données de parties contractantes si présentes
        if "parties" in context:
            for i, party in enumerate(context["parties"]):
                # Ajouter des identifiants courts pour un accès facile dans les templates
                if i == 0:
                    context["party1"] = party
                elif i == 1:
                    context["party2"] = party
        
        # Enrichir avec le titre si non fourni
        if "title" not in context and "contract_type" in context:
            context["title"] = f"Contrat de {context['contract_type']}"
        
        # Générer un numéro de contrat si non fourni
        if "contract_number" not in context:
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            contract_type_code = "".join([c[0].upper() for c in context.get("contract_type", "GEN").split() if c])[:3]
            context["contract_number"] = f"CTR-{contract_type_code}-{timestamp}"
        
        # Enrichir les clauses si nécessaires
        if "clauses" not in context:
            context["clauses"] = self._generate_default_clauses(context)
        
        return context
    
    def _generate_default_clauses(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère des clauses par défaut pour le contrat en fonction du contexte.
        
        Args:
            data: Données du contrat
            
        Returns:
            Liste de clauses générées
        """
        contract_type = data.get("contract_type", "").lower()
        clauses = []
        
        # Clause de définition des parties
        clauses.append({
            "title": "Définition des parties",
            "content": "Les parties mentionnées ci-dessus sont engagées par le présent contrat selon les termes et conditions définis dans les articles suivants."
        })
        
        # Clause d'objet du contrat
        if "vente" in contract_type or "bois" in contract_type:
            clauses.append({
                "title": "Objet du contrat",
                "content": "Le présent contrat a pour objet la vente de bois selon les conditions techniques et financières définies ci-après."
            })
        elif "travaux" in contract_type:
            clauses.append({
                "title": "Objet du contrat",
                "content": "Le présent contrat a pour objet la réalisation de travaux forestiers selon les conditions techniques et financières définies ci-après."
            })
        elif "bail" in contract_type or "location" in contract_type:
            clauses.append({
                "title": "Objet du contrat",
                "content": "Le présent contrat a pour objet la location de terrains forestiers selon les conditions définies ci-après."
            })
        elif "gestion" in contract_type:
            clauses.append({
                "title": "Objet du contrat",
                "content": "Le présent contrat a pour objet la gestion forestière des parcelles définies ci-après, selon les conditions techniques et financières convenues entre les parties."
            })
        else:
            clauses.append({
                "title": "Objet du contrat",
                "content": "Le présent contrat a pour objet la prestation de services forestiers définis ci-après, selon les conditions convenues entre les parties."
            })
        
        # Clause de durée
        clauses.append({
            "title": "Durée du contrat",
            "content": f"Le présent contrat est conclu pour une durée de {data.get('duration', '1 an')} à compter de sa date de signature."
        })
        
        # Clause de montant
        if "amount" in data or "contract_value" in data:
            amount = data.get("amount", data.get("contract_value", ""))
            clauses.append({
                "title": "Montant et conditions financières",
                "content": f"Le montant du présent contrat est fixé à {amount} euros. Les modalités de paiement sont définies comme suit: {data.get('payment_terms', 'paiement à 30 jours suivant la signature')}."
            })
        
        # Clause de résiliation
        clauses.append({
            "title": "Conditions de résiliation",
            "content": "Le présent contrat peut être résilié par l'une ou l'autre des parties en cas de manquement grave aux obligations définies dans le présent contrat, après mise en demeure restée sans effet pendant un délai de 30 jours."
        })
        
        # Clause de litiges
        clauses.append({
            "title": "Litiges",
            "content": "En cas de litige portant sur l'interprétation ou l'exécution du présent contrat, les parties conviennent de s'en remettre à l'appréciation des tribunaux compétents après épuisement des voies amiables."
        })
        
        return clauses
