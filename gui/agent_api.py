# gui/agent_api.py
"""
API pour interagir avec les agents.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable
import json
import requests
from PyQt6.QtCore import QObject, pyqtSignal

from forestai.core.utils.config import Config
from forestai.core.utils.logging_config import LoggingConfig
from forestai.agents.base_agent import BaseAgent


class AgentAPI(QObject):
    """
    API pour interagir avec les agents du système ForestAI.
    Supporte deux modes de fonctionnement :
    - Mode direct : interagit directement avec les agents en local
    - Mode API : interagit avec l'API REST du système
    """
    
    agents_updated = pyqtSignal(list)
    tasks_updated = pyqtSignal(list)
    agent_action_completed = pyqtSignal(str, str, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, use_api=True, api_url=None):
        """
        Initialise l'API agent.
        
        Args:
            use_api: Utiliser l'API REST (True) ou le mode direct (False)
            api_url: URL de l'API REST (utilisé uniquement si use_api=True)
        """
        super().__init__()
        self.logger = logging.getLogger("forestai.gui.agent_api")
        
        # Mode de fonctionnement
        self.use_api = use_api
        self.api_url = api_url or "http://localhost:8000"
        
        # Référence aux agents (mode direct uniquement)
        self.agents = {}
        
        # Configuration du polling
        self.polling_active = False
        self.polling_thread = None
        self.polling_interval = 2  # secondes
    
    def start_polling(self):
        """Démarre le polling des données des agents."""
        if self.polling_active:
            return
        
        self.polling_active = True
        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()
    
    def stop_polling(self):
        """Arrête le polling des données des agents."""
        self.polling_active = False
        if self.polling_thread:
            self.polling_thread.join(timeout=1)
    
    def _polling_loop(self):
        """Boucle de polling des données des agents."""
        while self.polling_active:
            try:
                # Récupération des données des agents
                agents_data = self.get_agents()
                self.agents_updated.emit(agents_data)
                
                # Récupération des données des tâches récentes
                tasks_data = self.get_recent_tasks()
                self.tasks_updated.emit(tasks_data)
                
            except Exception as e:
                self.logger.error(f"Erreur lors du polling: {e}", exc_info=True)
                self.error_occurred.emit(f"Erreur de communication avec les agents: {str(e)}")
            
            # Attendre avant la prochaine itération
            time.sleep(self.polling_interval)
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des agents disponibles.
        
        Returns:
            Liste des agents
        """
        if self.use_api:
            try:
                response = requests.get(f"{self.api_url}/agents")
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.error(f"Erreur lors de la récupération des agents: {e}", exc_info=True)
                return []
        else:
            result = []
            for name, agent in self.agents.items():
                result.append({
                    "name": name,
                    "type": agent.__class__.__name__,
                    **agent.get_status()
                })
            return result
    
    def get_recent_tasks(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des tâches récentes.
        
        Returns:
            Liste des tâches
        """
        if self.use_api:
            try:
                response = requests.get(f"{self.api_url}/tasks")
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.error(f"Erreur lors de la récupération des tâches: {e}", exc_info=True)
                return []
        else:
            # Dans le mode direct, il faudrait implémenter un système pour suivre les tâches
            # Pour le moment, on renvoie une liste vide
            return []
    
    def get_agent_actions(self, agent_name: str) -> List[str]:
        """
        Récupère la liste des actions disponibles pour un agent.
        
        Args:
            agent_name: Nom de l'agent
            
        Returns:
            Liste des actions
        """
        if self.use_api:
            try:
                response = requests.get(f"{self.api_url}/agents/{agent_name}/actions")
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.error(f"Erreur lors de la récupération des actions: {e}", exc_info=True)
                return []
        else:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                # Obtenir les méthodes publiques de l'agent qui ne commencent pas par "_"
                return [method for method in dir(agent) 
                        if callable(getattr(agent, method)) and not method.startswith("_")]
            return []
    
    def execute_action(self, agent_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une action sur un agent.
        
        Args:
            agent_name: Nom de l'agent
            action: Nom de l'action
            params: Paramètres de l'action
            
        Returns:
            Résultat de l'action
        """
        try:
            result = None
            
            if self.use_api:
                response = requests.post(
                    f"{self.api_url}/agents/{agent_name}/actions/{action}",
                    json=params
                )
                response.raise_for_status()
                result = response.json()
            else:
                if agent_name in self.agents:
                    agent = self.agents[agent_name]
                    if action == "start":
                        agent.run()
                        result = {"status": "success", "message": f"Agent {agent_name} démarré"}
                    elif action == "stop":
                        agent.stop()
                        result = {"status": "success", "message": f"Agent {agent_name} arrêté"}
                    elif hasattr(agent, action) and callable(getattr(agent, action)):
                        method = getattr(agent, action)
                        result = method(**params)
                    else:
                        raise ValueError(f"Action {action} non disponible pour l'agent {agent_name}")
                else:
                    raise ValueError(f"Agent {agent_name} non trouvé")
            
            self.agent_action_completed.emit(agent_name, action, result or {})
            return result or {}
        
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution de l'action: {e}", exc_info=True)
            self.error_occurred.emit(f"Erreur lors de l'exécution de l'action: {str(e)}")
            return {"status": "error", "error_message": str(e)}
    
    def register_agent(self, name: str, agent: BaseAgent):
        """
        Enregistre un agent pour le mode direct.
        
        Args:
            name: Nom de l'agent
            agent: Instance de l'agent
        """
        if not self.use_api:
            self.agents[name] = agent
            self.logger.info(f"Agent {name} enregistré")
            
    def unregister_agent(self, name: str):
        """
        Désenregistre un agent.
        
        Args:
            name: Nom de l'agent
        """
        if not self.use_api and name in self.agents:
            del self.agents[name]
            self.logger.info(f"Agent {name} désenregistré")
