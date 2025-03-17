#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de gestion des modèles de prédiction pour l'analyse de croissance forestière.

Ce module fournit des services pour la gestion des modèles SARIMA et autres modèles
de séries temporelles utilisés dans la prédiction de croissance forestière.
"""

import os
import logging
import pickle
import json
import hashlib
from typing import Dict, List, Tuple, Any, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

# Configuration du logger
logger = logging.getLogger(__name__)

class ModelManager:
    """Gestionnaire des modèles de prédiction pour l'analyse de croissance forestière."""
    
    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialise le gestionnaire de modèles.
        
        Args:
            models_dir: Répertoire pour stocker les modèles persistants
                        (si None, utilise le répertoire par défaut)
        """
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if models_dir is None:
            # Utiliser un répertoire par défaut
            base_dir = os.environ.get('FORESTAI_DATA_DIR', os.path.expanduser('~/.forestai'))
            self.models_dir = os.path.join(base_dir, 'models', 'growth_prediction')
        else:
            self.models_dir = models_dir
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(self.models_dir, exist_ok=True)
        
        self._logger.debug(f"Utilisation du répertoire de modèles: {self.models_dir}")
    
    def generate_model_id(self, parcel_id: str, target_metric: str, params: Dict[str, Any]) -> str:
        """
        Génère un identifiant unique pour un modèle basé sur ses paramètres.
        
        Args:
            parcel_id: Identifiant de la parcelle
            target_metric: Métrique cible du modèle
            params: Paramètres du modèle
            
        Returns:
            Identifiant unique du modèle
        """
        # Créer une chaîne représentant les paramètres
        param_str = json.dumps(params, sort_keys=True)
        model_info = f"{parcel_id}_{target_metric}_{param_str}"
        
        # Générer un hash pour l'identifiant du modèle
        model_id = hashlib.md5(model_info.encode()).hexdigest()
        
        return model_id
    
    def get_model_path(self, model_id: str) -> str:
        """
        Obtient le chemin d'accès complet pour un modèle.
        
        Args:
            model_id: Identifiant du modèle
            
        Returns:
            Chemin d'accès complet au fichier du modèle
        """
        return os.path.join(self.models_dir, f"{model_id}.pkl")
    
    def save_model(self, model: Any, parcel_id: str, target_metric: str, 
                  params: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Sauvegarde un modèle entraîné avec ses métadonnées.
        
        Args:
            model: Modèle entraîné à sauvegarder
            parcel_id: Identifiant de la parcelle
            target_metric: Métrique cible du modèle
            params: Paramètres du modèle
            metadata: Métadonnées supplémentaires à stocker avec le modèle
            
        Returns:
            Identifiant du modèle sauvegardé
        """
        # Générer l'identifiant du modèle
        model_id = self.generate_model_id(parcel_id, target_metric, params)
        model_path = self.get_model_path(model_id)
        
        # Préparer les métadonnées
        if metadata is None:
            metadata = {}
        
        metadata.update({
            'parcel_id': parcel_id,
            'target_metric': target_metric,
            'params': params,
            'saved_at': datetime.now().isoformat(),
            'model_id': model_id
        })
        
        # Créer un bundle avec le modèle et ses métadonnées
        model_bundle = {
            'model': model,
            'metadata': metadata
        }
        
        # Sauvegarder le bundle
        with open(model_path, 'wb') as f:
            pickle.dump(model_bundle, f)
        
        self._logger.info(f"Modèle sauvegardé: {model_id} ({target_metric} pour parcelle {parcel_id})")
        
        return model_id
    
    @cached(data_type=CacheType.MODEL, policy=CachePolicy.DAILY)
    def load_model(self, model_id: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Charge un modèle sauvegardé et ses métadonnées.
        
        Args:
            model_id: Identifiant du modèle à charger
            
        Returns:
            Tuple contenant (modèle, métadonnées)
            
        Raises:
            FileNotFoundError: Si le modèle n'existe pas
        """
        model_path = self.get_model_path(model_id)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modèle non trouvé: {model_id}")
        
        # Charger le bundle
        with open(model_path, 'rb') as f:
            model_bundle = pickle.load(f)
        
        model = model_bundle['model']
        metadata = model_bundle['metadata']
        
        self._logger.debug(f"Modèle chargé: {model_id} ({metadata.get('target_metric', 'inconnu')} "
                          f"pour parcelle {metadata.get('parcel_id', 'inconnue')})")
        
        return model, metadata
    
    def find_best_model(self, parcel_id: str, target_metric: str) -> Optional[str]:
        """
        Trouve le meilleur modèle existant pour une parcelle et une métrique.
        
        Args:
            parcel_id: Identifiant de la parcelle
            target_metric: Métrique cible
            
        Returns:
            Identifiant du meilleur modèle trouvé, ou None si aucun modèle n'est disponible
        """
        best_model_id = None
        best_score = float('-inf')
        
        # Parcourir tous les fichiers de modèles
        for filename in os.listdir(self.models_dir):
            if not filename.endswith('.pkl'):
                continue
            
            try:
                # Extraire l'identifiant du modèle
                model_id = filename[:-4]  # Enlever l'extension .pkl
                
                # Charger les métadonnées du modèle
                _, metadata = self.load_model(model_id)
                
                # Vérifier si le modèle correspond à la parcelle et à la métrique
                if (metadata.get('parcel_id') == parcel_id and 
                    metadata.get('target_metric') == target_metric):
                    
                    # Vérifier s'il y a un score dans les métadonnées
                    model_score = metadata.get('validation_score', float('-inf'))
                    
                    # Mettre à jour le meilleur modèle si nécessaire
                    if model_score > best_score:
                        best_score = model_score
                        best_model_id = model_id
            
            except Exception as e:
                self._logger.warning(f"Erreur lors du chargement du modèle {filename}: {str(e)}")
        
        if best_model_id:
            self._logger.info(f"Meilleur modèle trouvé pour {target_metric} (parcelle {parcel_id}): {best_model_id}")
        else:
            self._logger.info(f"Aucun modèle trouvé pour {target_metric} (parcelle {parcel_id})")
        
        return best_model_id
    
    def delete_model(self, model_id: str) -> bool:
        """
        Supprime un modèle sauvegardé.
        
        Args:
            model_id: Identifiant du modèle à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        model_path = self.get_model_path(model_id)
        
        if not os.path.exists(model_path):
            self._logger.warning(f"Tentative de suppression d'un modèle inexistant: {model_id}")
            return False
        
        try:
            os.remove(model_path)
            self._logger.info(f"Modèle supprimé: {model_id}")
            return True
        except Exception as e:
            self._logger.error(f"Erreur lors de la suppression du modèle {model_id}: {str(e)}")
            return False
    
    def list_models(self, parcel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste tous les modèles disponibles, éventuellement filtrés par parcelle.
        
        Args:
            parcel_id: Identifiant de parcelle pour filtrer les modèles (optionnel)
            
        Returns:
            Liste des métadonnées des modèles disponibles
        """
        models_info = []
        
        # Parcourir tous les fichiers de modèles
        for filename in os.listdir(self.models_dir):
            if not filename.endswith('.pkl'):
                continue
            
            try:
                # Extraire l'identifiant du modèle
                model_id = filename[:-4]  # Enlever l'extension .pkl
                
                # Charger les métadonnées du modèle
                _, metadata = self.load_model(model_id)
                
                # Filtrer par parcelle si nécessaire
                if parcel_id is None or metadata.get('parcel_id') == parcel_id:
                    models_info.append(metadata)
            
            except Exception as e:
                self._logger.warning(f"Erreur lors du chargement du modèle {filename}: {str(e)}")
        
        return models_info
