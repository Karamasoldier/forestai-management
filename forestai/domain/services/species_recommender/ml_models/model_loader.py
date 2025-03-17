#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module pour le chargement et la sauvegarde des modèles ML du recommandeur d'espèces.

Ce module fournit les classes et fonctions nécessaires pour gérer les modèles
d'apprentissage automatique utilisés par le système de recommandation d'espèces.
"""

import os
import pickle
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from forestai.core.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ModelLoader:
    """
    Classe pour charger et sauvegarder les modèles ML utilisés par le recommandeur d'espèces.
    """
    
    def __init__(self, models_dir: Path):
        """
        Initialise le chargeur de modèles.
        
        Args:
            models_dir: Répertoire de stockage des modèles entraînés
        """
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Définir les chemins vers les modèles
        self.model_paths = {
            "climate": self.models_dir / "climate_model.pkl",
            "soil": self.models_dir / "soil_model.pkl",
            "economic": self.models_dir / "economic_model.pkl",
            "ecological": self.models_dir / "ecological_model.pkl",
            "risk": self.models_dir / "risk_model.pkl",
            "overall": self.models_dir / "overall_model.pkl"
        }
        
        # Définir les chemins vers les transformateurs
        self.transformer_paths = {
            "climate": self.models_dir / "climate_transformer.pkl",
            "soil": self.models_dir / "soil_transformer.pkl",
            "context": self.models_dir / "context_transformer.pkl",
            "species": self.models_dir / "species_transformer.pkl"
        }
    
    def load_models(self) -> Dict[str, Any]:
        """
        Charge les modèles ML entraînés.
        
        Returns:
            Dictionnaire des modèles chargés
        """
        models = {}
        transformers = {}
        
        try:
            # Charger les modèles individuels
            for name, path in self.model_paths.items():
                if path.exists():
                    with open(path, 'rb') as f:
                        models[name] = pickle.load(f)
                    logger.info(f"Modèle {name} chargé")
                else:
                    models[name] = None
                    logger.warning(f"Modèle {name} non trouvé")
            
            # Charger les transformateurs
            for name, path in self.transformer_paths.items():
                if path.exists():
                    with open(path, 'rb') as f:
                        transformers[name] = pickle.load(f)
                    logger.info(f"Transformateur {name} chargé")
                else:
                    transformers[name] = None
                    logger.warning(f"Transformateur {name} non trouvé")
            
            # Ajouter les transformateurs aux modèles
            models["transformers"] = transformers
            
            return models
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {str(e)}")
            return {}
    
    def save_models(self, models: Dict[str, Any], transformers: Dict[str, Any]) -> bool:
        """
        Sauvegarde les modèles ML entraînés.
        
        Args:
            models: Dictionnaire des modèles à sauvegarder
            transformers: Dictionnaire des transformateurs à sauvegarder
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Sauvegarder les modèles individuels
            for name, model in models.items():
                if model and name in self.model_paths:
                    with open(self.model_paths[name], 'wb') as f:
                        pickle.dump(model, f)
                    logger.info(f"Modèle {name} sauvegardé")
            
            # Sauvegarder les transformateurs
            for name, transformer in transformers.items():
                if transformer and name in self.transformer_paths:
                    with open(self.transformer_paths[name], 'wb') as f:
                        pickle.dump(transformer, f)
                    logger.info(f"Transformateur {name} sauvegardé")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des modèles: {str(e)}")
            return False
