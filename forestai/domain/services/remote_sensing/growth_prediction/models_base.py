#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classe de base pour les modèles de prédiction de croissance forestière.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class GrowthPredictionModel(ABC):
    """
    Classe abstraite définissant l'interface pour tous les modèles de prédiction de croissance.
    
    Tous les modèles concrets doivent implémenter les méthodes définies ici.
    """
    
    def __init__(self, model_params: Dict[str, Any] = None):
        """
        Initialise le modèle de prédiction avec des paramètres optionnels.
        
        Args:
            model_params: Paramètres du modèle (optionnel)
        """
        self.model_params = model_params or {}
        self.model = None
        self.metrics = {}
        self.trained = False
    
    @abstractmethod
    def fit(self, train_data: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """
        Entraîne le modèle sur les données fournies.
        
        Args:
            train_data: Données d'entraînement en DataFrame (index = date)
            target_column: Nom de la colonne cible à prédire
            
        Returns:
            Dictionnaire contenant le modèle entraîné et des métriques de performance
        """
        pass
    
    @abstractmethod
    def predict(self, 
               horizon: int,
               confidence_level: float = 0.95) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Génère des prédictions pour un horizon donné.
        
        Args:
            horizon: Nombre de pas de temps à prédire
            confidence_level: Niveau de confiance pour les intervalles
            
        Returns:
            Tuple contenant (prédictions, intervalles de confiance)
        """
        pass
    
    @abstractmethod
    def evaluate(self, test_data: pd.DataFrame, target_column: str) -> Dict[str, float]:
        """
        Évalue le modèle sur un ensemble de test.
        
        Args:
            test_data: Données de test (index = date)
            target_column: Nom de la colonne cible
            
        Returns:
            Dictionnaire des métriques d'évaluation
        """
        pass
    
    @abstractmethod
    def analyze_features(self) -> Dict[str, Any]:
        """
        Analyse les caractéristiques du modèle pour comprendre les facteurs d'influence.
        
        Returns:
            Dictionnaire contenant l'analyse des facteurs d'influence
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Fournit des informations sur le modèle entraîné.
        
        Returns:
            Dictionnaire contenant des métadonnées et caractéristiques du modèle
        """
        pass
    
    def save(self, path: str) -> None:
        """
        Sauvegarde le modèle sur le disque.
        
        Args:
            path: Chemin où sauvegarder le modèle
        """
        raise NotImplementedError("La méthode save() doit être implémentée par les sous-classes")
    
    def load(self, path: str) -> None:
        """
        Charge un modèle depuis le disque.
        
        Args:
            path: Chemin d'où charger le modèle
        """
        raise NotImplementedError("La méthode load() doit être implémentée par les sous-classes")
