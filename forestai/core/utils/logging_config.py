# forestai/core/utils/logging_config.py

import os
import sys
import logging
import functools
import datetime
import threading
import traceback
from typing import Dict, Any, Optional, Callable, Type, List, Union
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from forestai.core.utils.logging import ForestAILogger, get_logger

# Configuration globale de logging
class LoggingConfig:
    """
    Configuration centralisée du système de logging.
    
    Cette classe gère la configuration globale du système de logging,
    permettant de modifier la configuration de tous les loggers à la fois.
    """
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        "level": "INFO",
        "log_dir": "logs",
        "log_to_console": True,
        "log_to_file": True,
        "rotation_size_mb": 10,
        "max_log_files": 5,
        "format_string": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "capture_exceptions": True,
        "collect_metrics": True,
        "async_logging": False
    }
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'LoggingConfig':
        """Implémentation du pattern Singleton pour la configuration de logging."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self):
        """Initialise la configuration avec les valeurs par défaut ou environnementales."""
        self.config = self.DEFAULT_CONFIG.copy()
        self._initialized = False
        self._registered_loggers = []
        
        # Ne pas initialiser deux fois
        if LoggingConfig._instance is not None:
            return
        
        # Charger la configuration depuis les variables d'environnement
        self._load_from_env()
    
    def _load_from_env(self):
        """Charge la configuration depuis les variables d'environnement."""
        for key in self.config:
            env_key = f"LOG_{key.upper()}"
            if env_key in os.environ:
                # Conversion de type pour les valeurs numériques et booléennes
                value = os.environ[env_key]
                if key in ["rotation_size_mb", "max_log_files"]:
                    self.config[key] = int(value)
                elif key in ["log_to_console", "log_to_file", "capture_exceptions", 
                             "collect_metrics", "async_logging"]:
                    self.config[key] = value.lower() in ["true", "1", "yes", "y"]
                else:
                    self.config[key] = value
    
    def init(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise la configuration avec des valeurs personnalisées.
        
        Args:
            config: Dictionnaire de configuration personnalisée
        """
        if config:
            self.config.update(config)
        
        # Créer le répertoire de logs s'il n'existe pas
        log_dir = Path(self.config["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration de base du logging Python
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config["level"]))
        
        # Configurer le gestionnaire d'exceptions non gérées
        if self.config["capture_exceptions"]:
            self._setup_exception_handler()
        
        # Marquer comme initialisé
        self._initialized = True
        
        # Reconfigurer tous les loggers enregistrés
        for logger in self._registered_loggers:
            self._reconfigure_logger(logger)
    
    def _setup_exception_handler(self):
        """Configure un handler global pour les exceptions non gérées."""
        def exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Les interruptions clavier doivent être gérées normalement
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Logger l'exception
            logger = get_logger("system")
            logger.critical(
                "Uncaught exception:",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
        
        # Installer le handler
        sys.excepthook = exception_handler
    
    def register_logger(self, logger: ForestAILogger):
        """
        Enregistre un logger pour les mises à jour de configuration.
        
        Args:
            logger: L'instance de ForestAILogger à enregistrer
        """
        # Enregistrer uniquement si c'est une nouvelle instance
        if logger not in self._registered_loggers:
            self._registered_loggers.append(logger)
            
            # Si déjà initialisé, reconfigurer le logger
            if self._initialized:
                self._reconfigure_logger(logger)
    
    def _reconfigure_logger(self, logger: ForestAILogger):
        """Reconfigure un logger existant avec les paramètres actuels."""
        # Mettre à jour le niveau de log
        logger.level = getattr(logging, self.config["level"])
        logger.logger.setLevel(logger.level)
        
        # Mettre à jour les handlers
        for handler in logger.logger.handlers:
            handler.setLevel(logger.level)
            
            # Mettre à jour le formateur si c'est un handler connu
            if isinstance(handler, (logging.StreamHandler, RotatingFileHandler, TimedRotatingFileHandler)):
                formatter = logging.Formatter(
                    self.config["format_string"],
                    datefmt=self.config["date_format"]
                )
                handler.setFormatter(formatter)
    
    def update_config(self, config: Dict[str, Any]):
        """
        Met à jour la configuration et reconfigure tous les loggers.
        
        Args:
            config: Nouvelles valeurs de configuration
        """
        self.config.update(config)
        
        # Reconfigurer tous les loggers enregistrés
        for logger in self._registered_loggers:
            self._reconfigure_logger(logger)


# Décorateur pour logger automatiquement les entrées/sorties de fonction
def log_function(logger=None, level="DEBUG", log_args=True, log_result=True, 
                 log_exceptions=True, log_execution_time=True):
    """
    Décorateur pour logger automatiquement les entrées/sorties de fonction.
    
    Args:
        logger: Logger à utiliser (ou nom du logger à créer)
        level: Niveau de log pour les entrées/sorties
        log_args: Activer le logging des arguments
        log_result: Activer le logging du résultat
        log_exceptions: Activer le logging des exceptions
        log_execution_time: Activer le logging du temps d'exécution
    
    Returns:
        Décorateur configuré
    """
    def decorator(func):
        # Obtenir ou créer le logger
        nonlocal logger
        log = logger
        
        if logger is None:
            module_name = func.__module__
            log = get_logger(f"{module_name}.{func.__name__}")
        elif isinstance(logger, str):
            log = get_logger(logger)
        
        log_level = getattr(logging, level)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Logger l'entrée de fonction
            if log_args:
                # Filtrer les arguments trop volumineux
                safe_args = [arg if not hasattr(arg, '__len__') or len(arg) < 1000 
                            else f"{type(arg).__name__}(len={len(arg)})" 
                            for arg in args]
                
                safe_kwargs = {k: v if not hasattr(v, '__len__') or len(v) < 1000 
                              else f"{type(v).__name__}(len={len(v)})" 
                              for k, v in kwargs.items()}
                
                log.logger.log(log_level, 
                             f"Calling {func.__name__} with args={safe_args}, kwargs={safe_kwargs}")
            else:
                log.logger.log(log_level, f"Calling {func.__name__}")
            
            start_time = datetime.datetime.now()
            try:
                # Exécuter la fonction
                result = func(*args, **kwargs)
                
                # Calculer le temps d'exécution
                if log_execution_time:
                    execution_time = (datetime.datetime.now() - start_time).total_seconds()
                
                # Logger le résultat
                if log_result:
                    # Filtrer les résultats trop volumineux
                    if hasattr(result, '__len__') and len(result) > 1000:
                        safe_result = f"{type(result).__name__}(len={len(result)})"
                    else:
                        safe_result = result
                    
                    log_msg = f"{func.__name__} returned: {safe_result}"
                    if log_execution_time:
                        log_msg += f" (execution time: {execution_time:.4f}s)"
                    
                    log.logger.log(log_level, log_msg)
                elif log_execution_time:
                    log.logger.log(log_level, 
                                 f"{func.__name__} completed in {execution_time:.4f}s")
                
                return result
                
            except Exception as e:
                # Logger l'exception si activé
                if log_exceptions:
                    log.exception(f"Exception in {func.__name__}: {str(e)}")
                # Re-lever l'exception
                raise
        
        return wrapper
    
    return decorator


# Classe pour collecter des métriques de performance
class LoggingMetrics:
    """
    Collecte et gère les métriques de performance du système.
    
    Cette classe permet de collecter des statistiques sur les logs et 
    performances du système, utilisables pour le monitoring et les alertes.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'LoggingMetrics':
        """Implémentation du pattern Singleton pour les métriques."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self):
        """Initialise le collecteur de métriques."""
        self.metrics = {
            "errors": 0,
            "warnings": 0,
            "api_calls": 0,
            "api_errors": 0,
            "tasks": {"total": 0, "completed": 0, "failed": 0},
            "response_times": [],
            "start_time": datetime.datetime.now(),
            "last_reset": datetime.datetime.now(),
            "custom_metrics": {}
        }
        
        # Logger pour les métriques
        self.logger = get_logger("metrics", level="INFO")
    
    def increment(self, metric: str, value: int = 1):
        """
        Incrémente une métrique numérique.
        
        Args:
            metric: Nom de la métrique
            value: Valeur à ajouter (par défaut 1)
        """
        with self._lock:
            if metric in self.metrics:
                if isinstance(self.metrics[metric], int):
                    self.metrics[metric] += value
                elif isinstance(self.metrics[metric], dict) and "total" in self.metrics[metric]:
                    self.metrics[metric]["total"] += value
            elif metric in self.metrics["custom_metrics"]:
                self.metrics["custom_metrics"][metric] += value
            else:
                self.metrics["custom_metrics"][metric] = value
    
    def record_api_call(self, success: bool, response_time: float = None):
        """
        Enregistre un appel API dans les métriques.
        
        Args:
            success: Si l'appel a réussi
            response_time: Temps de réponse en secondes
        """
        with self._lock:
            self.metrics["api_calls"] += 1
            if not success:
                self.metrics["api_errors"] += 1
            
            if response_time is not None:
                self.metrics["response_times"].append(response_time)
                # Garder uniquement les 100 derniers temps de réponse
                if len(self.metrics["response_times"]) > 100:
                    self.metrics["response_times"].pop(0)
    
    def record_task(self, status: str):
        """
        Enregistre une tâche dans les métriques.
        
        Args:
            status: Statut de la tâche (completed, failed, etc.)
        """
        with self._lock:
            self.metrics["tasks"]["total"] += 1
            if status in self.metrics["tasks"]:
                self.metrics["tasks"][status] += 1
            else:
                self.metrics["tasks"][status] = 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques actuelles avec des statistiques.
        
        Returns:
            Dictionnaire des métriques et statistiques
        """
        with self._lock:
            metrics_copy = self.metrics.copy()
            
            # Calculer des statistiques supplémentaires
            uptime = (datetime.datetime.now() - metrics_copy["start_time"]).total_seconds()
            metrics_copy["uptime_seconds"] = uptime
            
            # Statistiques de temps de réponse
            response_times = metrics_copy["response_times"]
            if response_times:
                metrics_copy["avg_response_time"] = sum(response_times) / len(response_times)
                metrics_copy["max_response_time"] = max(response_times)
                metrics_copy["min_response_time"] = min(response_times)
            else:
                metrics_copy["avg_response_time"] = 0
                metrics_copy["max_response_time"] = 0
                metrics_copy["min_response_time"] = 0
            
            # Calcul du taux d'erreur API
            api_calls = metrics_copy["api_calls"]
            if api_calls > 0:
                metrics_copy["api_error_rate"] = metrics_copy["api_errors"] / api_calls
            else:
                metrics_copy["api_error_rate"] = 0
            
            # Taux de succès des tâches
            tasks_total = metrics_copy["tasks"]["total"]
            if tasks_total > 0:
                metrics_copy["task_success_rate"] = metrics_copy["tasks"].get("completed", 0) / tasks_total
                metrics_copy["task_failure_rate"] = metrics_copy["tasks"].get("failed", 0) / tasks_total
            else:
                metrics_copy["task_success_rate"] = 0
                metrics_copy["task_failure_rate"] = 0
            
            return metrics_copy
    
    def reset(self):
        """Réinitialise les métriques (sauf le temps de démarrage)."""
        with self._lock:
            start_time = self.metrics["start_time"]
            self.metrics = {
                "errors": 0,
                "warnings": 0,
                "api_calls": 0,
                "api_errors": 0,
                "tasks": {"total": 0, "completed": 0, "failed": 0},
                "response_times": [],
                "start_time": start_time,
                "last_reset": datetime.datetime.now(),
                "custom_metrics": {}
            }
    
    def log_current_metrics(self, level: str = "INFO"):
        """
        Enregistre les métriques actuelles dans le log.
        
        Args:
            level: Niveau de log à utiliser
        """
        metrics = self.get_metrics()
        log_level = getattr(logging, level)
        
        self.logger.logger.log(log_level, f"Current metrics: {json.dumps(metrics, default=str)}")
        
        return metrics


# Extensions pour faciliter l'intégration avec les agents
def setup_agent_logging(agent_name: str, level: str = None, context: Dict[str, Any] = None) -> ForestAILogger:
    """
    Configure un logger spécifique pour un agent avec les paramètres recommandés.
    
    Args:
        agent_name: Nom de l'agent (ex: "GeoAgent")
        level: Niveau de log spécifique à l'agent
        context: Contexte initial pour l'agent
    
    Returns:
        Logger configuré pour l'agent
    """
    # Utiliser la configuration globale
    config = LoggingConfig.get_instance()
    
    # Créer le contexte par défaut
    if context is None:
        context = {}
    
    context.update({
        "agent": agent_name,
        "agent_id": f"{agent_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    })
    
    # Niveau de log spécifique ou par défaut
    if level is None:
        level = config.config["level"]
    
    # Créer et configurer le logger
    logger = get_logger(
        name=f"agent.{agent_name.lower()}",
        level=level,
        log_dir=config.config["log_dir"],
        context=context
    )
    
    # Enregistrer le logger pour les mises à jour de configuration
    config.register_logger(logger)
    
    return logger


# Initialisation automatique de la configuration
# (peut être remplacé par un appel explicite à init() si nécessaire)
logging_config = LoggingConfig.get_instance()
metrics = LoggingMetrics.get_instance()

# Obtenir le logger racine du système
system_logger = get_logger("system")
