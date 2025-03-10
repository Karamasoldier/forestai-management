# forestai/agents/base_agent.py

import logging
from typing import Dict, Any, List

class BaseAgent:
    """
    Classe de base pour tous les agents du système ForestAI.
    Définit l'interface commune et les fonctionnalités partagées.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialise un agent.
        
        Args:
            name: Nom identifiant l'agent
            config: Dictionnaire de configuration
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"forestai.agents.{name.lower()}")
        
        # État de l'agent
        self.is_running = False
        self.tasks_queue = []
        
    def run(self) -> None:
        """
        Démarre l'exécution de l'agent.
        Cette méthode doit être surchargée par les classes filles.
        """
        self.is_running = True
        self.logger.info(f"Agent {self.name} démarré")
        
        try:
            self._execute()
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution de l'agent {self.name}: {e}", exc_info=True)
        finally:
            self.is_running = False
            self.logger.info(f"Agent {self.name} arrêté")
    
    def _execute(self) -> None:
        """
        Implémentation de la logique d'exécution.
        Cette méthode doit être surchargée par les classes filles.
        """
        raise NotImplementedError("Les classes dérivées doivent implémenter cette méthode")
    
    def stop(self) -> None:
        """Arrête l'exécution de l'agent."""
        if self.is_running:
            self.is_running = False
            self.logger.info(f"Arrêt de l'agent {self.name} demandé")
        
    def add_task(self, task: Dict[str, Any]) -> None:
        """
        Ajoute une tâche à la file d'attente de l'agent.
        
        Args:
            task: Dictionnaire contenant les informations de la tâche
        """
        self.tasks_queue.append(task)
        self.logger.debug(f"Tâche ajoutée à l'agent {self.name}: {task}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Récupère l'état actuel de l'agent.
        
        Returns:
            Dictionnaire contenant les informations d'état
        """
        return {
            "name": self.name,
            "running": self.is_running,
            "tasks_pending": len(self.tasks_queue)
        }
