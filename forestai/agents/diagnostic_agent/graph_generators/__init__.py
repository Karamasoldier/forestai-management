# -*- coding: utf-8 -*-
"""
Module contenant les générateurs de graphiques pour les rapports.
"""

from forestai.agents.diagnostic_agent.graph_generators.diagnostic_graphs import generate_diagnostic_graphs
from forestai.agents.diagnostic_agent.graph_generators.management_plan_graphs import generate_management_plan_graphs

__all__ = ['generate_diagnostic_graphs', 'generate_management_plan_graphs']
