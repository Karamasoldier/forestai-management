"""
Module de configuration pour ForestAI.
Gère le chargement et l'accès aux paramètres de configuration.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Classe de gestion de la configuration de ForestAI."""
    
    _instance = None
    
    def __new__(cls):
        """Implémentation du pattern Singleton."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de Config."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialise la configuration si ce n'est pas déjà fait."""
        if not getattr(self, '_initialized', False):
            self._config = {}
            self._initialized = True
    
    def load_config(self, env_file: Optional[str] = None) -> 'Config':
        """
        Charge la configuration depuis un fichier .env
        
        Args:
            env_file: Chemin vers le fichier .env (optionnel)
            
        Returns:
            L'instance Config (self)
        """
        # Recherche du fichier .env
        if env_file is None:
            env_file = '.env'
        
        # Charger les variables d'environnement du fichier .env
        env_path = Path(env_file)
        if env_path.exists():
            logger.info(f"Chargement de la configuration depuis {env_path}")
            load_dotenv(dotenv_path=env_path)
        else:
            logger.warning(f"Fichier de configuration {env_path} non trouvé. Utilisation des variables d'environnement.")
        
        # Charger toutes les variables d'environnement dans le dictionnaire de configuration
        for key, value in os.environ.items():
            self._config[key] = value
        
        # Configurer les chemins de base
        self._setup_paths()
        
        logger.info("Configuration chargée avec succès")
        return self
    
    def _setup_paths(self):
        """Configure les chemins de base si non spécifiés."""
        # Chemin des données
        if 'DATA_PATH' not in self._config:
            self._config['DATA_PATH'] = os.path.join(os.getcwd(), 'data')
            logger.info(f"DATA_PATH non spécifié, utilisation de la valeur par défaut: {self._config['DATA_PATH']}")
        
        # Chemin des sorties
        if 'OUTPUT_PATH' not in self._config:
            self._config['OUTPUT_PATH'] = os.path.join(self._config['DATA_PATH'], 'outputs')
            logger.info(f"OUTPUT_PATH non spécifié, utilisation de la valeur par défaut: {self._config['OUTPUT_PATH']}")
            
        # Créer les répertoires s'ils n'existent pas
        for path_key in ['DATA_PATH', 'OUTPUT_PATH']:
            path = self._config[path_key]
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                logger.info(f"Création du répertoire: {path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration
        
        Args:
            key: Clé de configuration
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            La valeur de configuration ou la valeur par défaut
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Définit une valeur de configuration
        
        Args:
            key: Clé de configuration
            value: Valeur à définir
        """
        self._config[key] = value
        
    def as_dict(self) -> Dict[str, Any]:
        """
        Retourne une copie du dictionnaire de configuration
        
        Returns:
            Dictionnaire de configuration
        """
        return self._config.copy()
