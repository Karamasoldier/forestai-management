"""
Module de configuration de la journalisation pour ForestAI.
"""

import os
import logging
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime
import functools

class LoggingConfig:
    """Classe de configuration de la journalisation."""
    
    _instance = None
    
    def __new__(cls):
        """Implémentation du pattern Singleton."""
        if cls._instance is None:
            cls._instance = super(LoggingConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de LoggingConfig."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialise la configuration si ce n'est pas déjà fait."""
        if not getattr(self, '_initialized', False):
            self._initialized = True
            self._default_format = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
            self._default_level = "INFO"
            self._default_log_dir = "logs"
            self._metrics = {}
    
    def init(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialise la configuration de journalisation.
        
        Args:
            config: Dictionnaire de configuration (optionnel)
        """
        if config is None:
            config = {}
        
        # Paramètres de configuration
        log_level = config.get('level', self._default_level)
        log_format = config.get('format_string', self._default_format)
        log_dir = config.get('log_dir', self._default_log_dir)
        
        # Créer le répertoire de logs s'il n'existe pas
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Définir le niveau de log
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            numeric_level = getattr(logging, self._default_level, logging.INFO)
        
        # Configurer le formateur
        formatter = logging.Formatter(log_format)
        
        # Configurer le logger root
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Supprimer les handlers existants
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Ajouter un handler pour la console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Ajouter un handler pour le fichier avec rotation
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"forestai_{current_date}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10 Mo
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Journaliser l'initialisation
        logging.info(f"Logging initialized with level {log_level}")
    
    def log_function(self, func):
        """
        Décorateur pour journaliser les appels de fonction
        
        Args:
            func: Fonction à décorer
            
        Returns:
            Fonction décorée
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Function {func.__name__} completed in {execution_time:.4f} seconds")
                
                # Collecter des métriques
                if func.__name__ not in self._metrics:
                    self._metrics[func.__name__] = []
                self._metrics[func.__name__].append(execution_time)
                
                return result
            except Exception as e:
                logger.exception(f"Error in {func.__name__}: {str(e)}")
                raise
        
        return wrapper
    
    def get_metrics(self, function_name=None):
        """
        Retourne les métriques collectées
        
        Args:
            function_name: Nom de la fonction (optionnel)
            
        Returns:
            Métriques
        """
        if function_name:
            return self._metrics.get(function_name, [])
        return self._metrics.copy()

# Définir un décorateur plus simple à utiliser
def log_function(func):
    """Décorateur pour journaliser les appels de fonction."""
    return LoggingConfig.get_instance().log_function(func)
