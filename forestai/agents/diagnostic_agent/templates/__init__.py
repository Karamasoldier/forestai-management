# -*- coding: utf-8 -*-
"""Module contenant les templates par défaut pour les rapports."""

from forestai.agents.diagnostic_agent.templates.diagnostic_template import create_default_diagnostic_template
from forestai.agents.diagnostic_agent.templates.management_plan_template import create_default_management_plan_template

__all__ = ['create_default_diagnostic_template', 'create_default_management_plan_template']
