# -*- coding: utf-8 -*-
"""
Module de génération de documents pour le DocumentAgent.

Ce package contient les classes et utilitaires responsables de la génération
des différents types de documents forestiers.
"""

from forestai.agents.document_agent.generators.contract_generator import ContractGenerator
from forestai.agents.document_agent.generators.spec_generator import SpecificationGenerator
from forestai.agents.document_agent.generators.management_plan_generator import ManagementPlanGenerator
from forestai.agents.document_agent.generators.administrative_generator import AdministrativeDocumentGenerator

__all__ = [
    'ContractGenerator',
    'SpecificationGenerator',
    'ManagementPlanGenerator',
    'AdministrativeDocumentGenerator'
]
