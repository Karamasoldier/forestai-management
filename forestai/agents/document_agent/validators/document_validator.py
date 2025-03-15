# -*- coding: utf-8 -*-
"""
Module de validation de documents pour le DocumentAgent.

Ce module fournit des fonctionnalités pour valider les documents selon
différents critères et normes spécifiques aux documents forestiers.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime

from forestai.agents.document_agent.models.document_models import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult
)

logger = logging.getLogger(__name__)

class DocumentValidator:
    """
    Validateur de documents forestiers.
    
    Cette classe s'occupe de la validation des documents selon différents critères
    et normes spécifiques aux documents forestiers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le validateur de documents.
        
        Args:
            config: Configuration optionnelle du validateur
        """
        self.config = config or {}
        logger.info("DocumentValidator initialisé")
    
    def validate(self, content: Union[str, bytes], format: str, 
                document_type: str, strict_mode: bool = False) -> ValidationResult:
        """
        Valide un document selon les règles du type spécifié.
        
        Args:
            content: Contenu du document (texte ou binaire)
            format: Format du document (pdf, docx, html, etc.)
            document_type: Type du document
            strict_mode: Si True, applique des règles de validation plus strictes
            
        Returns:
            Résultat de la validation
        """
        logger.info(f"Validation du document {document_type} au format {format}")
        
        # Initialiser le résultat de validation
        validation_result = ValidationResult(
            is_valid=True,
            document_type=document_type,
            format=format,
            issues=[],
            warnings=[],
            metadata={}
        )
        
        # Effectuer des validations spécifiques au format
        format_validation = self._validate_format(content, format, validation_result)
        validation_result.issues.extend(format_validation.get("issues", []))
        validation_result.warnings.extend(format_validation.get("warnings", []))
        
        # Effectuer des validations spécifiques au type de document
        type_validation = self._validate_document_type(content, format, document_type, strict_mode, validation_result)
        validation_result.issues.extend(type_validation.get("issues", []))
        validation_result.warnings.extend(type_validation.get("warnings", []))
        
        # Collecter des métadonnées sur le document
        metadata = self._extract_metadata(content, format, document_type)
        validation_result.metadata.update(metadata)
        
        # Déterminer si le document est valide (aucune erreur critique)
        has_critical_issues = any(issue.severity == ValidationSeverity.CRITICAL for issue in validation_result.issues)
        validation_result.is_valid = not has_critical_issues
        
        return validation_result
    
    def _validate_format(self, content: Union[str, bytes], format: str, 
                        validation_result: ValidationResult) -> Dict[str, List[ValidationIssue]]:
        """
        Effectue des validations spécifiques au format du document.
        
        Args:
            content: Contenu du document
            format: Format du document
            validation_result: Résultat de validation en cours
            
        Returns:
            Dictionnaire contenant les problèmes et avertissements détectés
        """
        issues = []
        warnings = []
        
        if format == "pdf" and isinstance(content, bytes):
            # Vérifier la signature PDF
            if not content.startswith(b'%PDF-'):
                issues.append(ValidationIssue(
                    code="invalid_pdf_header",
                    message="Le fichier ne commence pas par une signature PDF valide",
                    severity=ValidationSeverity.CRITICAL,
                    section="header"
                ))
            
            # Vérifier la taille minimale
            if len(content) < 100:
                issues.append(ValidationIssue(
                    code="pdf_too_small",
                    message="Le fichier PDF est trop petit pour être valide",
                    severity=ValidationSeverity.ERROR,
                    section="content"
                ))
        
        elif format == "html" and isinstance(content, str):
            # Vérifier la présence de balises HTML de base
            if not re.search(r'<\s*html', content, re.IGNORECASE):
                issues.append(ValidationIssue(
                    code="missing_html_tag",
                    message="La balise <html> est manquante",
                    severity=ValidationSeverity.ERROR,
                    section="structure"
                ))
            
            if not re.search(r'<\s*body', content, re.IGNORECASE):
                issues.append(ValidationIssue(
                    code="missing_body_tag",
                    message="La balise <body> est manquante",
                    severity=ValidationSeverity.ERROR,
                    section="structure"
                ))
            
            # Vérifier la présence de balises non fermées
            opening_tags = re.findall(r'<\s*([a-zA-Z0-9]+)[^>]*(?<!/)>', content)
            closing_tags = re.findall(r'</\s*([a-zA-Z0-9]+)\s*>', content)
            
            # Compter les occurrences de chaque tag
            tag_counts = {}
            for tag in opening_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            for tag in closing_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) - 1
            
            # Vérifier les tags non fermés
            for tag, count in tag_counts.items():
                if count > 0 and tag not in ["img", "br", "hr", "meta", "input"]:
                    warnings.append(ValidationIssue(
                        code="unclosed_tag",
                        message=f"Balise <{tag}> non fermée",
                        severity=ValidationSeverity.WARNING,
                        section="structure",
                        context={"tag": tag, "count": count}
                    ))
        
        elif format == "docx" and isinstance(content, bytes):
            # Vérifier la signature DOCX (format ZIP)
            if not content.startswith(b'PK\x03\x04'):
                issues.append(ValidationIssue(
                    code="invalid_docx_header",
                    message="Le fichier ne commence pas par une signature DOCX/ZIP valide",
                    severity=ValidationSeverity.CRITICAL,
                    section="header"
                ))
        
        elif format == "txt" and isinstance(content, str):
            # Vérifier la présence de caractères non imprimables
            if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', content):
                warnings.append(ValidationIssue(
                    code="non_printable_chars",
                    message="Le fichier contient des caractères non imprimables",
                    severity=ValidationSeverity.WARNING,
                    section="content"
                ))
            
            # Vérifier la longueur minimale
            if len(content) < 10:
                warnings.append(ValidationIssue(
                    code="txt_too_short",
                    message="Le fichier texte est très court",
                    severity=ValidationSeverity.INFO,
                    section="content"
                ))
        
        return {"issues": issues, "warnings": warnings}
    
    def _validate_document_type(self, content: Union[str, bytes], format: str, 
                               document_type: str, strict_mode: bool,
                               validation_result: ValidationResult) -> Dict[str, List[ValidationIssue]]:
        """
        Effectue des validations spécifiques au type de document.
        
        Args:
            content: Contenu du document
            format: Format du document
            document_type: Type du document
            strict_mode: Si True, applique des règles de validation plus strictes
            validation_result: Résultat de validation en cours
            
        Returns:
            Dictionnaire contenant les problèmes et avertissements détectés
        """
        issues = []
        warnings = []
        
        content_str = content if isinstance(content, str) else ""
        if isinstance(content, bytes) and format in ["txt", "html"]:
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                pass
        
        # Vérifications communes à tous les documents
        if not content_str:
            # Pas de validations spécifiques pour le contenu binaire ici
            return {"issues": issues, "warnings": warnings}
        
        # Vérifier la présence de dates au format français
        dates_fr = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', content_str)
        if not dates_fr and strict_mode:
            warnings.append(ValidationIssue(
                code="missing_dates",
                message="Aucune date au format français n'a été détectée",
                severity=ValidationSeverity.INFO,
                section="content"
            ))
        
        # Vérifier la présence d'informations de contact
        has_contact_info = bool(re.search(r'\b(email|courriel|tel|téléphone|tél|contact|adresse)\b', content_str, re.IGNORECASE))
        if not has_contact_info and strict_mode:
            warnings.append(ValidationIssue(
                code="missing_contact_info",
                message="Aucune information de contact n'a été détectée",
                severity=ValidationSeverity.INFO,
                section="content"
            ))
        
        # Validations spécifiques par type de document
        if "contract" in document_type.lower():
            # Vérifier la présence de parties au contrat
            has_parties = bool(re.search(r'\b(parties|entre|soussigné|ci-après|représentant)\b', content_str, re.IGNORECASE))
            if not has_parties:
                issues.append(ValidationIssue(
                    code="missing_contract_parties",
                    message="Aucune mention des parties contractantes n'a été détectée",
                    severity=ValidationSeverity.ERROR if strict_mode else ValidationSeverity.WARNING,
                    section="content"
                ))
            
            # Vérifier la présence de clauses
            has_clauses = bool(re.search(r'\b(article|clause|conditions|obligation|engagement)\b', content_str, re.IGNORECASE))
            if not has_clauses:
                issues.append(ValidationIssue(
                    code="missing_contract_clauses",
                    message="Aucune clause contractuelle n'a été détectée",
                    severity=ValidationSeverity.ERROR if strict_mode else ValidationSeverity.WARNING,
                    section="content"
                ))
            
            # Vérifier la présence d'une date de signature
            has_signature_date = bool(re.search(r'\b(fait à|signé à|le \d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', content_str, re.IGNORECASE))
            if not has_signature_date and strict_mode:
                warnings.append(ValidationIssue(
                    code="missing_signature_date",
                    message="Aucune date de signature n'a été détectée",
                    severity=ValidationSeverity.WARNING,
                    section="content"
                ))
        
        elif "specification" in document_type.lower():
            # Vérifier la présence de spécifications techniques
            has_tech_specs = bool(re.search(r'\b(technique|spécification|exigence|cahier des charges|caractéristique)\b', content_str, re.IGNORECASE))
            if not has_tech_specs:
                issues.append(ValidationIssue(
                    code="missing_tech_specs",
                    message="Aucune spécification technique n'a été détectée",
                    severity=ValidationSeverity.ERROR if strict_mode else ValidationSeverity.WARNING,
                    section="content"
                ))
            
            # Vérifier la présence de travaux forestiers
            has_forestry_work = bool(re.search(r'\b(coupe|plantation|débardage|éclaircie|bois|arbre|forêt|forestier)\b', content_str, re.IGNORECASE))
            if not has_forestry_work:
                warnings.append(ValidationIssue(
                    code="missing_forestry_work",
                    message="Aucune mention de travaux forestiers n'a été détectée",
                    severity=ValidationSeverity.WARNING,
                    section="content"
                ))
        
        elif "management_plan" in document_type.lower() or "plan" in document_type.lower():
            # Vérifier la présence d'informations sur le peuplement
            has_stand_info = bool(re.search(r'\b(peuplement|essence|espèce|diamètre|hauteur|âge|densité)\b', content_str, re.IGNORECASE))
            if not has_stand_info:
                issues.append(ValidationIssue(
                    code="missing_stand_info",
                    message="Aucune information sur le peuplement forestier n'a été détectée",
                    severity=ValidationSeverity.ERROR if strict_mode else ValidationSeverity.WARNING,
                    section="content"
                ))
            
            # Vérifier la présence d'actions de gestion
            has_management_actions = bool(re.search(r'\b(intervention|gestion|action|planification|objectif|aménagement)\b', content_str, re.IGNORECASE))
            if not has_management_actions:
                issues.append(ValidationIssue(
                    code="missing_management_actions",
                    message="Aucune action de gestion n'a été détectée",
                    severity=ValidationSeverity.ERROR if strict_mode else ValidationSeverity.WARNING,
                    section="content"
                ))
            
            # Vérifier la présence de dates ou périodes
            has_periods = bool(re.search(r'\b(\d{4}[-–]\d{4}|période|durée)\b', content_str, re.IGNORECASE))
            if not has_periods and strict_mode:
                warnings.append(ValidationIssue(
                    code="missing_periods",
                    message="Aucune période de planification n'a été détectée",
                    severity=ValidationSeverity.WARNING,
                    section="content"
                ))
        
        elif "administrative" in document_type.lower():
            # Vérifier la présence d'une référence administrative
            has_admin_ref = bool(re.search(r'\b(référence|dossier|numéro|n°)\b', content_str, re.IGNORECASE))
            if not has_admin_ref and strict_mode:
                warnings.append(ValidationIssue(
                    code="missing_admin_ref",
                    message="Aucune référence administrative n'a été détectée",
                    severity=ValidationSeverity.WARNING,
                    section="content"
                ))
            
            # Vérifier la présence d'une autorité administrative
            has_authority = bool(re.search(r'\b(préfet|maire|administration|ministère|direction|département|région)\b', content_str, re.IGNORECASE))
            if not has_authority:
                issues.append(ValidationIssue(
                    code="missing_authority",
                    message="Aucune autorité administrative n'a été détectée",
                    severity=ValidationSeverity.ERROR if strict_mode else ValidationSeverity.WARNING,
                    section="content"
                ))
        
        return {"issues": issues, "warnings": warnings}
    
    def _extract_metadata(self, content: Union[str, bytes], format: str, 
                        document_type: str) -> Dict[str, Any]:
        """
        Extrait des métadonnées du document pour enrichir le résultat de validation.
        
        Args:
            content: Contenu du document
            format: Format du document
            document_type: Type du document
            
        Returns:
            Dictionnaire de métadonnées extraites
        """
        metadata = {
            "content_type": format,
            "document_type": document_type,
            "size_bytes": len(content),
            "analysis_date": datetime.now().isoformat()
        }
        
        content_str = content if isinstance(content, str) else ""
        if isinstance(content, bytes) and format in ["txt", "html"]:
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                pass
        
        if content_str:
            # Extraire des données structurées selon le type de document
            # et le contenu disponible
            
            # Extraire le titre (première ligne en majuscules ou ligne après un titre HTML)
            title_match = re.search(r'^([A-Z\s]+)$', content_str, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()
            else:
                title_h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content_str, re.IGNORECASE | re.DOTALL)
                if title_h1_match:
                    metadata["title"] = title_h1_match.group(1).strip()
            
            # Extraire les dates
            dates = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', content_str)
            if dates:
                metadata["dates"] = dates
            
            # Extraire des informations de contact (email, téléphone)
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content_str)
            if emails:
                metadata["emails"] = emails
            
            phones = re.findall(r'\b(?:0\d[\s.-]?){4,5}\d{2}\b', content_str)  # Format français
            if phones:
                metadata["phones"] = phones
            
            # Extraire des indications monétaires
            monetary = re.findall(r'\b\d+(?:\s?\d+)*(?:,\d+)?\s?(?:€|EUR|euros?)\b', content_str, re.IGNORECASE)
            if monetary:
                metadata["monetary_values"] = monetary
            
            # Extraire des surfaces (hectares)
            areas = re.findall(r'\b\d+(?:,\d+)?\s?(?:ha|hectares?)\b', content_str, re.IGNORECASE)
            if areas:
                metadata["areas"] = areas
            
            # Calculer des statistiques sur le contenu
            words = re.findall(r'\w+', content_str, re.UNICODE)
            metadata["word_count"] = len(words)
            metadata["character_count"] = len(content_str)
            
        return metadata
