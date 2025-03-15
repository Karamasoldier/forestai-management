# -*- coding: utf-8 -*-
"""
Implémentation principale du DocumentAgent.

Ce module fournit la classe DocumentAgent qui gère la génération de documents
administratifs pour la gestion forestière.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from forestai.core.infrastructure.agent_base import Agent
from forestai.core.infrastructure.cache.cache_utils import cached
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.utils.config import Config
from forestai.agents.document_agent.generators.contract_generator import ContractGenerator
from forestai.agents.document_agent.generators.spec_generator import SpecificationGenerator
from forestai.agents.document_agent.generators.management_plan_generator import ManagementPlanGenerator
from forestai.agents.document_agent.generators.administrative_generator import AdministrativeDocumentGenerator
from forestai.agents.document_agent.templates.template_manager import TemplateManager
from forestai.agents.document_agent.validators.document_validator import DocumentValidator
from forestai.agents.document_agent.storage.document_storage import DocumentStorage
from forestai.agents.document_agent.models.document_models import DocumentType, DocumentFormat, DocumentRequest

logger = logging.getLogger(__name__)

class DocumentAgent(Agent):
    """
    Agent responsable de la génération de documents administratifs pour la gestion forestière.
    
    Cette classe orchestre la création de différents types de documents comme des contrats,
    cahiers des charges, plans de gestion, et autres documents administratifs liés
    à la foresterie.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le DocumentAgent.
        
        Args:
            config: Configuration optionnelle du DocumentAgent.
        """
        super().__init__(name="document_agent", config=config)
        
        # Charger la configuration
        self.config = Config.get_instance().get("document_agent", {}) if config is None else config
        
        # Chemin pour le stockage des documents
        self.output_dir = Path(self.config.get("output_dir", "outputs/documents"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser les générateurs de documents
        self.template_manager = TemplateManager(self.config.get("templates_dir"))
        self.document_validator = DocumentValidator()
        self.document_storage = DocumentStorage(str(self.output_dir))
        
        # Initialiser les générateurs spécifiques
        self.contract_generator = ContractGenerator(self.template_manager)
        self.spec_generator = SpecificationGenerator(self.template_manager)
        self.management_plan_generator = ManagementPlanGenerator(self.template_manager)
        self.admin_generator = AdministrativeDocumentGenerator(self.template_manager)
        
        # Registre des actions disponibles
        self._register_actions()
        
        logger.info(f"DocumentAgent initialisé avec répertoire de sortie: {self.output_dir}")
    
    def _register_actions(self):
        """Enregistre les actions disponibles pour cet agent."""
        self.actions = {
            "generate_contract": self.generate_contract,
            "generate_specifications": self.generate_specifications,
            "generate_management_plan_doc": self.generate_management_plan_doc,
            "generate_administrative_doc": self.generate_administrative_doc,
            "get_document_types": self.get_document_types,
            "validate_document": self.validate_document
        }
    
    @cached(data_type=CacheType.DOCUMENT, policy=CachePolicy.WEEKLY)
    def generate_contract(self, contract_data: Dict[str, Any], 
                          formats: List[str] = ["pdf"], 
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère un contrat forestier à partir des données fournies.
        
        Args:
            contract_data: Données du contrat (parties, clauses, etc.)
            formats: Formats de sortie souhaités (pdf, docx, html)
            options: Options supplémentaires de génération
            
        Returns:
            Dictionnaire contenant les chemins vers les fichiers générés et métadonnées
        """
        logger.info(f"Génération d'un contrat forestier")
        
        options = options or {}
        request = DocumentRequest(
            document_type=DocumentType.CONTRACT,
            data=contract_data,
            formats=[DocumentFormat(f) for f in formats],
            options=options
        )
        
        # Générer le contrat dans tous les formats demandés
        result = self.contract_generator.generate(request)
        
        # Stocker les documents générés
        stored_files = {}
        for fmt, content in result.documents.items():
            filename = f"contrat_{contract_data.get('reference', datetime.now().strftime('%Y%m%d_%H%M%S'))}.{fmt}"
            file_path = self.document_storage.store(content, filename, fmt)
            stored_files[fmt] = str(file_path)
        
        return {
            "status": "success",
            "files": stored_files,
            "metadata": {
                "document_type": "contrat_forestier",
                "timestamp": datetime.now().isoformat(),
                "contract_reference": contract_data.get("reference"),
                "parties": [p.get("name") for p in contract_data.get("parties", [])]
            }
        }
    
    @cached(data_type=CacheType.DOCUMENT, policy=CachePolicy.WEEKLY)
    def generate_specifications(self, spec_data: Dict[str, Any], 
                               formats: List[str] = ["pdf"], 
                               options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère un cahier des charges pour des travaux forestiers.
        
        Args:
            spec_data: Données du cahier des charges (lots, conditions, etc.)
            formats: Formats de sortie souhaités (pdf, docx, html)
            options: Options supplémentaires de génération
            
        Returns:
            Dictionnaire contenant les chemins vers les fichiers générés et métadonnées
        """
        logger.info(f"Génération d'un cahier des charges forestier")
        
        options = options or {}
        request = DocumentRequest(
            document_type=DocumentType.SPECIFICATION,
            data=spec_data,
            formats=[DocumentFormat(f) for f in formats],
            options=options
        )
        
        # Générer le cahier des charges dans tous les formats demandés
        result = self.spec_generator.generate(request)
        
        # Stocker les documents générés
        stored_files = {}
        for fmt, content in result.documents.items():
            filename = f"cahier_charges_{spec_data.get('reference', datetime.now().strftime('%Y%m%d_%H%M%S'))}.{fmt}"
            file_path = self.document_storage.store(content, filename, fmt)
            stored_files[fmt] = str(file_path)
        
        return {
            "status": "success",
            "files": stored_files,
            "metadata": {
                "document_type": "cahier_charges",
                "timestamp": datetime.now().isoformat(),
                "spec_reference": spec_data.get("reference"),
                "work_types": spec_data.get("work_types", [])
            }
        }
    
    @cached(data_type=CacheType.DOCUMENT, policy=CachePolicy.WEEKLY)
    def generate_management_plan_doc(self, plan_data: Dict[str, Any], 
                                    formats: List[str] = ["pdf"], 
                                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère un document de plan de gestion forestière.
        
        Args:
            plan_data: Données du plan de gestion
            formats: Formats de sortie souhaités (pdf, docx, html)
            options: Options supplémentaires de génération
            
        Returns:
            Dictionnaire contenant les chemins vers les fichiers générés et métadonnées
        """
        logger.info(f"Génération d'un document de plan de gestion forestière")
        
        options = options or {}
        request = DocumentRequest(
            document_type=DocumentType.MANAGEMENT_PLAN,
            data=plan_data,
            formats=[DocumentFormat(f) for f in formats],
            options=options
        )
        
        # Générer le plan de gestion dans tous les formats demandés
        result = self.management_plan_generator.generate(request)
        
        # Stocker les documents générés
        stored_files = {}
        for fmt, content in result.documents.items():
            filename = f"plan_gestion_{plan_data.get('reference', datetime.now().strftime('%Y%m%d_%H%M%S'))}.{fmt}"
            file_path = self.document_storage.store(content, filename, fmt)
            stored_files[fmt] = str(file_path)
        
        return {
            "status": "success",
            "files": stored_files,
            "metadata": {
                "document_type": "plan_gestion",
                "timestamp": datetime.now().isoformat(),
                "plan_reference": plan_data.get("reference"),
                "property_name": plan_data.get("property_name"),
                "duration_years": plan_data.get("duration_years"),
                "parcels": len(plan_data.get("parcels", []))
            }
        }
    
    @cached(data_type=CacheType.DOCUMENT, policy=CachePolicy.WEEKLY)
    def generate_administrative_doc(self, admin_data: Dict[str, Any], 
                                  doc_type: str,
                                  formats: List[str] = ["pdf"], 
                                  options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère un document administratif de type spécifié.
        
        Args:
            admin_data: Données pour le document administratif
            doc_type: Type de document (autorisation_coupe, declaration_fiscale, etc.)
            formats: Formats de sortie souhaités (pdf, docx, html)
            options: Options supplémentaires de génération
            
        Returns:
            Dictionnaire contenant les chemins vers les fichiers générés et métadonnées
        """
        logger.info(f"Génération d'un document administratif de type {doc_type}")
        
        options = options or {}
        options["administrative_type"] = doc_type
        
        request = DocumentRequest(
            document_type=DocumentType.ADMINISTRATIVE,
            data=admin_data,
            formats=[DocumentFormat(f) for f in formats],
            options=options
        )
        
        # Générer le document administratif dans tous les formats demandés
        result = self.admin_generator.generate(request)
        
        # Stocker les documents générés
        stored_files = {}
        for fmt, content in result.documents.items():
            filename = f"{doc_type}_{admin_data.get('reference', datetime.now().strftime('%Y%m%d_%H%M%S'))}.{fmt}"
            file_path = self.document_storage.store(content, filename, fmt)
            stored_files[fmt] = str(file_path)
        
        return {
            "status": "success",
            "files": stored_files,
            "metadata": {
                "document_type": doc_type,
                "timestamp": datetime.now().isoformat(),
                "document_reference": admin_data.get("reference"),
                "authority": admin_data.get("authority")
            }
        }
    
    def get_document_types(self) -> Dict[str, Any]:
        """
        Récupère la liste des types de documents disponibles.
        
        Returns:
            Dictionnaire contenant les types de documents et leur description
        """
        return {
            "contract_types": {
                "vente_bois": "Contrat de vente de bois",
                "travaux_forestiers": "Contrat de travaux forestiers",
                "bail_forestier": "Bail forestier",
                "gestion_deleguee": "Contrat de gestion déléguée"
            },
            "specification_types": {
                "cahier_charges_travaux": "Cahier des charges pour travaux forestiers",
                "cahier_charges_coupe": "Cahier des charges pour coupe de bois",
                "cahier_charges_plantation": "Cahier des charges pour plantation"
            },
            "management_plan_types": {
                "plan_simple_gestion": "Plan simple de gestion (PSG)",
                "document_amenagement": "Document d'aménagement",
                "plan_gestion_durable": "Plan de gestion durable"
            },
            "administrative_types": {
                "autorisation_coupe": "Autorisation de coupe",
                "declaration_fiscale": "Déclaration fiscale forestière",
                "demande_aide": "Demande d'aide forestière",
                "notice_impact": "Notice d'impact environnemental",
                "certification": "Document de certification forestière"
            }
        }
    
    def validate_document(self, document_path: str, 
                        document_type: str, 
                        strict_mode: bool = False) -> Dict[str, Any]:
        """
        Valide un document existant selon les règles du type spécifié.
        
        Args:
            document_path: Chemin vers le document à valider
            document_type: Type du document
            strict_mode: Si True, applique des règles de validation plus strictes
            
        Returns:
            Résultats de la validation
        """
        logger.info(f"Validation du document {document_path} de type {document_type}")
        
        try:
            # Charger le document depuis le stockage
            document_content = self.document_storage.retrieve(document_path)
            
            # Identifier le format
            format_ext = Path(document_path).suffix.lstrip('.')
            
            # Effectuer la validation
            validation_result = self.document_validator.validate(
                document_content, 
                format_ext, 
                document_type, 
                strict_mode
            )
            
            return {
                "status": "success",
                "is_valid": validation_result.is_valid,
                "issues": validation_result.issues,
                "warnings": validation_result.warnings,
                "metadata": validation_result.metadata
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du document: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "is_valid": False
            }
