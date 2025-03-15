# -*- coding: utf-8 -*-
"""
Modèles de données pour le DocumentAgent.

Ce module définit les classes de modèles et énumérations utilisées pour
la génération et la manipulation de documents par le DocumentAgent.
"""

from enum import Enum, auto
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentType(str, Enum):
    """Types de documents supportés par le DocumentAgent."""
    CONTRACT = "contract"
    SPECIFICATION = "specification"
    MANAGEMENT_PLAN = "management_plan"
    ADMINISTRATIVE = "administrative"
    REPORT = "report"
    CUSTOM = "custom"

class DocumentFormat(str, Enum):
    """Formats de sortie supportés pour les documents."""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    TXT = "txt"
    JSON = "json"
    XML = "xml"

class ValidationSeverity(str, Enum):
    """Niveaux de sévérité pour les problèmes de validation de documents."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationIssue(BaseModel):
    """Représente un problème détecté lors de la validation d'un document."""
    code: str
    message: str
    severity: ValidationSeverity
    section: Optional[str] = None
    element_id: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    """Résultat complet d'une validation de document."""
    is_valid: bool
    document_type: str
    format: str
    issues: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []
    metadata: Dict[str, Any] = {}
    validation_date: datetime = Field(default_factory=datetime.now)

class DocumentRequest(BaseModel):
    """Requête de génération de document."""
    document_type: DocumentType
    data: Dict[str, Any]
    formats: List[DocumentFormat]
    options: Dict[str, Any] = {}
    template_name: Optional[str] = None
    request_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))

class DocumentResult(BaseModel):
    """Résultat d'une génération de document."""
    request_id: str
    document_type: DocumentType
    documents: Dict[str, Union[str, bytes]]  # Format -> Contenu
    metadata: Dict[str, Any] = {}
    generation_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

class DocumentMetadata(BaseModel):
    """Métadonnées associées à un document généré."""
    document_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    document_type: DocumentType
    title: str
    author: Optional[str] = None
    creation_date: datetime = Field(default_factory=datetime.now)
    version: str = "1.0"
    keywords: List[str] = []
    language: str = "fr"
    description: Optional[str] = None
    additional_properties: Dict[str, Any] = {}

class TemplateVariable(BaseModel):
    """Définition d'une variable de template."""
    name: str
    description: str
    type: str
    required: bool = False
    default: Optional[Any] = None
    example: Optional[Any] = None
    constraints: Dict[str, Any] = {}

class TemplateDefinition(BaseModel):
    """Définition d'un template de document."""
    template_id: str
    name: str
    document_type: DocumentType
    description: str
    variables: List[TemplateVariable] = []
    supported_formats: List[DocumentFormat] = []
    version: str = "1.0"
    author: Optional[str] = None
    creation_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
