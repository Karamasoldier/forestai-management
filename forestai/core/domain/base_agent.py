"""
Classe de base pour tous les agents du système ForestAI.
"""

import logging
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set

from forestai.core.utils.config import Config
from forestai.core.communication.message_bus import MessageBus, Message
from forestai.core.utils.logging_config import log_function

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Classe abstraite de base pour tous les agents ForestAI.
    
    Cette classe fournit une infrastructure commune pour tous les agents,
    incluant la gestion de la configuration, la communication entre agents
    via le bus de messages, et la journalisation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, agent_id: Optional[str] = None,
                 subscribe_topics: Optional[List[str]] = None):
        """
        Initialise un agent avec une configuration.
        
        Args:
            config: Dictionnaire de configuration ou instance Config (optionnel)
            agent_id: Identifiant unique de l'agent (généré automatiquement si non fourni)
            subscribe_topics: Liste des sujets auxquels l'agent doit s'abonner (optionnel)
        """
        # Identifiant de l'agent
        self.agent_id = agent_id or f"{self.__class__.__name__}_{str(uuid.uuid4())[:8]}"
        logger.info(f"Initializing agent: {self.agent_id}")
        
        # Configuration
        if isinstance(config, dict):
            self.config = Config.get_instance()
            for key, value in config.items():
                self.config.set(key, value)
        elif config is None:
            self.config = Config.get_instance()
        else:
            self.config = config
        
        # Bus de messages
        self.message_bus = MessageBus.get_instance()
        
        # Abonnements
        self.subscription_ids: Set[str] = set()
        
        # S'abonner aux sujets spécifiés
        if subscribe_topics:
            for topic in subscribe_topics:
                self.subscribe_to_topic(topic)
    
    @log_function
    def subscribe_to_topic(self, topic: str) -> str:
        """
        S'abonne à un sujet sur le bus de messages.
        
        Args:
            topic: Sujet auquel s'abonner
            
        Returns:
            Identifiant de l'abonnement
        """
        logger.debug(f"Agent {self.agent_id} subscribing to topic: {topic}")
        subscription_id = self.message_bus.subscribe(topic, self._message_handler, self.agent_id)
        self.subscription_ids.add(subscription_id)
        return subscription_id
    
    @log_function
    def unsubscribe_from_topic(self, subscription_id: str) -> bool:
        """
        Se désabonne d'un sujet.
        
        Args:
            subscription_id: Identifiant de l'abonnement
            
        Returns:
            True si l'abonnement a été trouvé et supprimé, False sinon
        """
        result = self.message_bus.unsubscribe(subscription_id)
        if result:
            self.subscription_ids.remove(subscription_id)
        return result
    
    @log_function
    def unsubscribe_all(self) -> int:
        """
        Se désabonne de tous les sujets.
        
        Returns:
            Nombre d'abonnements supprimés
        """
        count = self.message_bus.unsubscribe_all(self.agent_id)
        self.subscription_ids.clear()
        return count
    
    @log_function
    def publish_message(self, topic: str, data: Dict[str, Any]) -> str:
        """
        Publie un message sur le bus de messages.
        
        Args:
            topic: Sujet du message
            data: Données du message
            
        Returns:
            Identifiant du message
        """
        logger.debug(f"Agent {self.agent_id} publishing message to topic: {topic}")
        message_id = self.message_bus.publish(topic, data, self.agent_id)
        return message_id
    
    def _message_handler(self, message: Message) -> None:
        """
        Gestionnaire de messages par défaut.
        Cette méthode est appelée lorsqu'un message est reçu.
        
        Args:
            message: Message reçu
        """
        try:
            logger.debug(f"Agent {self.agent_id} received message: {message}")
            self.handle_message(message)
        except Exception as e:
            logger.exception(f"Error handling message in agent {self.agent_id}: {str(e)}")
    
    @abstractmethod
    def handle_message(self, message: Message) -> None:
        """
        Méthode abstraite à implémenter par les sous-classes pour gérer les messages reçus.
        
        Args:
            message: Message reçu
        """
        pass
    
    @abstractmethod
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode abstraite à implémenter par les sous-classes pour exécuter une action.
        
        Args:
            action: Action à exécuter
            params: Paramètres de l'action
            
        Returns:
            Résultat de l'action
        """
        pass
    
    def __del__(self):
        """
        Destructeur appelé lorsque l'agent est détruit.
        """
        try:
            self.unsubscribe_all()
            logger.info(f"Agent {self.agent_id} unsubscribed from all topics")
        except:
            pass  # Ignorer les erreurs lors de la destruction
