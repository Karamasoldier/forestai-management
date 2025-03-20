"""
Module de commandes CLI pour ForestAI.

Ce module contient les implémentations des différentes commandes
utilisables en ligne de commande.
"""

from .api_command import run_api
from .web_command import run_web
from .complete_command import run_complete
from .agent_command import run_agent
from .diagnostics_command import run_diagnostics

__all__ = [
    "run_api",
    "run_web",
    "run_complete",
    "run_agent",
    "run_diagnostics"
]
