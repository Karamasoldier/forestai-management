# forestai/core/utils/logging.py

import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
import traceback

class ForestAILogger:
    """
    Gestionnaire de logging avancé pour le projet ForestAI.
    
    Cette classe fournit des fonctionnalités de logging avancées:
    - Logging multi-niveaux (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Logs vers la console et les fichiers simultanément
    - Rotation des fichiers de logs par taille et par date
    - Format personnalisable avec des informations contextuelles
    - Support pour le contexte d'exécution (id de tâche, agent, etc.)
    - Intégration avec les métriques et tableau de bord (à venir)
    """
    
    # Formatage par défaut des messages de log
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Niveaux de log
    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_dir: Optional[str] = None,
        log_to_console: bool = True,
        log_to_file: bool = True,
        rotation_size_mb: int = 10,
        max_log_files: int = 5,
        format_string: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialise le logger ForestAI.
        
        Args:
            name: Nom du logger (généralement le nom du module ou de l'agent)
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Répertoire où stocker les fichiers de log
            log_to_console: Activer la sortie console
            log_to_file: Activer la sortie fichier
            rotation_size_mb: Taille max des fichiers de log en Mo
            max_log_files: Nombre max de fichiers de log à conserver
            format_string: Format personnalisé des messages de log
            context: Dictionnaire de contexte additionnel pour les logs
        """
        self.name = name
        self.context = context or {}
        
        # Récupérer le niveau de log
        self.level = self.LEVELS.get(level.upper(), logging.INFO)
        
        # Définir le répertoire de logs
        if log_dir is None:
            self.log_dir = Path(os.getenv("LOG_DIR", "logs"))
        else:
            self.log_dir = Path(log_dir)
        
        # Créer le répertoire de logs s'il n'existe pas
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurer le format de log
        self.format_string = format_string or self.DEFAULT_FORMAT
        self.formatter = logging.Formatter(self.format_string)
        
        # Créer le logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Supprimer les handlers existants pour éviter les doublons
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Configurer les handlers
        if log_to_console:
            self._setup_console_handler()
        
        if log_to_file:
            self._setup_file_handler(rotation_size_mb, max_log_files)
    
    def _setup_console_handler(self):
        """Configure le handler pour la sortie console."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self, rotation_size_mb: int, max_log_files: int):
        """Configure le handler pour la sortie fichier avec rotation."""
        try:
            # Utiliser RotatingFileHandler pour gérer la rotation des logs
            from logging.handlers import RotatingFileHandler
            
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{self.name}_{today}.log"
            
            # Conversion Mo en octets
            max_bytes = rotation_size_mb * 1024 * 1024
            
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=max_log_files,
                encoding='utf-8'
            )
            
            file_handler.setLevel(self.level)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            # En cas d'erreur, on ajoute un handler de secours sur stderr
            sys.stderr.write(f"Erreur lors de la configuration du fichier de log: {str(e)}\n")
            error_handler = logging.StreamHandler(sys.stderr)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(self.formatter)
            self.logger.addHandler(error_handler)
    
    def _format_context(self) -> str:
        """Formate le contexte pour l'inclure dans les messages de log."""
        if not self.context:
            return ""
        
        try:
            return f" | Context: {json.dumps(self.context)}"
        except:
            return f" | Context: {str(self.context)}"
    
    def update_context(self, new_context: Dict[str, Any]):
        """
        Met à jour le contexte du logger.
        
        Args:
            new_context: Nouvelles valeurs de contexte à ajouter/mettre à jour
        """
        self.context.update(new_context)
    
    def debug(self, message: str, exc_info: bool = False, extra: Dict[str, Any] = None):
        """Enregistre un message de niveau DEBUG."""
        context_msg = self._format_context() if extra is None else ""
        self.logger.debug(f"{message}{context_msg}", exc_info=exc_info, extra=extra)
    
    def info(self, message: str, exc_info: bool = False, extra: Dict[str, Any] = None):
        """Enregistre un message de niveau INFO."""
        context_msg = self._format_context() if extra is None else ""
        self.logger.info(f"{message}{context_msg}", exc_info=exc_info, extra=extra)
    
    def warning(self, message: str, exc_info: bool = False, extra: Dict[str, Any] = None):
        """Enregistre un message de niveau WARNING."""
        context_msg = self._format_context() if extra is None else ""
        self.logger.warning(f"{message}{context_msg}", exc_info=exc_info, extra=extra)
    
    def error(self, message: str, exc_info: bool = True, extra: Dict[str, Any] = None):
        """Enregistre un message de niveau ERROR avec traceback par défaut."""
        context_msg = self._format_context() if extra is None else ""
        self.logger.error(f"{message}{context_msg}", exc_info=exc_info, extra=extra)
    
    def critical(self, message: str, exc_info: bool = True, extra: Dict[str, Any] = None):
        """Enregistre un message de niveau CRITICAL avec traceback par défaut."""
        context_msg = self._format_context() if extra is None else ""
        self.logger.critical(f"{message}{context_msg}", exc_info=exc_info, extra=extra)
    
    def exception(self, message: str, exc_info: bool = True, extra: Dict[str, Any] = None):
        """Enregistre une exception."""
        context_msg = self._format_context() if extra is None else ""
        self.logger.exception(f"{message}{context_msg}", exc_info=exc_info, extra=extra)

    def log_api_call(self, 
                   api_name: str, 
                   endpoint: str, 
                   params: Dict[str, Any] = None, 
                   success: bool = True,
                   response_time: float = None,
                   error: Exception = None):
        """
        Enregistre les détails d'un appel API.
        
        Args:
            api_name: Nom de l'API (ex: "IGN Geoportail")
            endpoint: Point d'accès (ex: "/cadastre")
            params: Paramètres de la requête
            success: Si l'appel a réussi
            response_time: Temps de réponse en secondes
            error: Exception en cas d'échec
        """
        log_data = {
            "type": "api_call",
            "api": api_name,
            "endpoint": endpoint,
            "params": params or {},
            "success": success,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if response_time is not None:
            log_data["response_time"] = f"{response_time:.4f}s"
        
        if error:
            log_data["error"] = str(error)
            log_data["traceback"] = traceback.format_exc()
            self.error(f"API Call: {api_name} {endpoint}", extra={"api_data": log_data})
        elif success:
            self.info(f"API Call: {api_name} {endpoint}", extra={"api_data": log_data})
        else:
            self.warning(f"API Call: {api_name} {endpoint} (failed but no exception)", 
                      extra={"api_data": log_data})

    def log_task(self, 
                task_id: str, 
                task_type: str, 
                agent_name: str,
                status: str, 
                details: Dict[str, Any] = None):
        """
        Enregistre des informations sur une tâche.
        
        Args:
            task_id: Identifiant unique de la tâche
            task_type: Type de tâche (ex: "analyze_parcel")
            agent_name: Nom de l'agent exécutant la tâche
            status: Statut de la tâche (started, completed, failed)
            details: Détails additionnels de la tâche
        """
        log_data = {
            "type": "task",
            "task_id": task_id,
            "task_type": task_type,
            "agent": agent_name,
            "status": status,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if details:
            log_data.update(details)
        
        if status == "failed":
            self.error(f"Task {task_id} ({task_type}) {status}", extra={"task_data": log_data})
        elif status == "completed":
            self.info(f"Task {task_id} ({task_type}) {status}", extra={"task_data": log_data})
        else:
            self.debug(f"Task {task_id} ({task_type}) {status}", extra={"task_data": log_data})


# Fonction pour obtenir un logger configuré
def get_logger(
    name: str,
    level: str = None,
    log_dir: str = None,
    context: Dict[str, Any] = None
) -> ForestAILogger:
    """
    Crée et retourne un logger ForestAI configuré.
    
    Args:
        name: Nom du logger
        level: Niveau de log (si None, utilise la variable d'environnement LOG_LEVEL)
        log_dir: Répertoire des logs (si None, utilise la variable d'environnement LOG_DIR)
        context: Contexte initial du logger
        
    Returns:
        Une instance configurée de ForestAILogger
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    return ForestAILogger(
        name=name,
        level=level,
        log_dir=log_dir,
        context=context
    )
