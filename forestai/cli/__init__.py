"""
Module CLI pour ForestAI.

Ce module fournit les points d'entrée en ligne de commande unifiés pour ForestAI.
"""

from .commands import (
    run_api,
    run_web,
    run_complete,
    run_agent,
    run_diagnostics
)

__all__ = [
    "run_api",
    "run_web",
    "run_complete",
    "run_agent",
    "run_diagnostics"
]
