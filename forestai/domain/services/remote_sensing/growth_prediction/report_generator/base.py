#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de base pour la génération de rapports forestiers.

Fournit la classe de base abstraite pour tous les générateurs de rapports.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime

from forestai.domain.services.remote_sensing.models import ForestMetrics
from forestai.domain.services.remote_sensing.growth_prediction.models_base import GrowthPredictionResult

class BaseReportGenerator(ABC):
    """
    Classe de base abstraite pour tous les générateurs de rapports.
    
    Cette classe définit l'interface commune que tous les générateurs 
    de rapports doivent implémenter.
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialise le générateur de rapports.
        
        Args:
            template_dir: Répertoire contenant les templates de rapports.
                         Si None, utilise le répertoire par défaut.
        """
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if template_dir is None:
            # Utiliser le répertoire de templates par défaut
            package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(package_dir, 'templates')
            
            # Si le répertoire n'existe pas, utiliser un répertoire temporaire
            if not os.path.exists(template_dir):
                template_dir = os.path.join(os.path.expanduser('~'), '.forestai', 'templates')
                os.makedirs(template_dir, exist_ok=True)
        
        self.template_dir = template_dir
        self._ensure_templates_exist()
    
    def _ensure_templates_exist(self) -> None:
        """
        S'assure que les templates nécessaires existent dans le répertoire de templates.
        Si non, crée les templates par défaut.
        """
        self._create_default_templates_if_needed()
    
    @abstractmethod
    def _create_default_templates_if_needed(self) -> None:
        """
        Crée les templates par défaut si nécessaire.
        À implémenter par chaque classe dérivée.
        """
        pass
    
    @abstractmethod
    def generate_report(self, prediction_result: GrowthPredictionResult, 
                        additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Génère un rapport à partir des résultats de prédiction.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            additional_context: Contexte supplémentaire à inclure dans le rapport
            
        Returns:
            Contenu du rapport au format spécifié
        """
        pass
    
    def _create_prediction_summary(self, prediction_result: GrowthPredictionResult) -> Dict[str, Dict[str, Any]]:
        """
        Crée un résumé des prédictions pour inclusion dans le rapport.
        
        Args:
            prediction_result: Résultat de la prédiction de croissance
            
        Returns:
            Dictionnaire contenant le résumé des prédictions
        """
        summary = {}
        
        # S'assurer que nous avons des prédictions
        if not prediction_result.predictions:
            return summary
        
        # Obtenir la première et la dernière prédiction
        first_date, first_metrics, _ = prediction_result.predictions[0]
        last_date, last_metrics, _ = prediction_result.predictions[-1]
        
        # Pour chaque attribut de ForestMetrics
        for attr in dir(first_metrics):
            # Ignorer les attributs spéciaux et les méthodes
            if attr.startswith('_') or callable(getattr(first_metrics, attr)):
                continue
            
            # Obtenir les valeurs initiale et finale
            initial_value = getattr(first_metrics, attr)
            final_value = getattr(last_metrics, attr)
            
            # S'assurer que les deux valeurs sont numériques
            if not (isinstance(initial_value, (int, float)) and isinstance(final_value, (int, float))):
                continue
            
            # Calculer le changement
            change = final_value - initial_value
            change_percent = (change / initial_value * 100) if initial_value != 0 else 0
            
            # Formater les valeurs pour affichage
            summary[attr] = {
                'initial': f"{initial_value:.2f}" if isinstance(initial_value, float) else initial_value,
                'final': f"{final_value:.2f}" if isinstance(final_value, float) else final_value,
                'change': f"{change:.2f}" if isinstance(change, float) else change,
                'change_percent': f"{change_percent:.1f}"
            }
        
        return summary
