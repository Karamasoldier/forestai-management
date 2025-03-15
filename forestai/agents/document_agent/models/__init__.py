# -*- coding: utf-8 -*-
"""
Module de modèles pour le DocumentAgent.

Ce package contient les définitions des modèles de données utilisés par le
DocumentAgent pour représenter et manipuler les documents.
"""

from forestai.agents.document_agent.models.document_models import (
    DocumentType, 
    DocumentFormat, 
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    DocumentRequest,
    DocumentResult,
    DocumentMetadata,
    TemplateVariable,
    TemplateDefinition
)

__all__ = [
    'DocumentType',
    'DocumentFormat',
    'ValidationSeverity',
    'ValidationIssue',
    'ValidationResult',
    'DocumentRequest',
    'DocumentResult',
    'DocumentMetadata',
    'TemplateVariable',
    'TemplateDefinition'
]
