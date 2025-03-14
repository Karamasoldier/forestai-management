"""
Bus de messages pour la communication entre agents ForestAI.
"""

import logging
import threading
import uuid
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class Message:
    """Classe représentant un message dans le bus."""
    
    def __init__(self, topic: str, data: Dict[str, Any], sender: str = None):
        """
        Initialise un message.
        
        Args:
            topic: Sujet du message
            data: Données du message
            sender: Identifiant de l'expéditeur (optionnel)
        """
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.data = data
        self.sender = sender
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le message en dictionnaire."""
        return {
            'id': self.id,
            'topic': self.topic,
            'data': self.data,
            'sender': self.sender,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        """Retourne une représentation textuelle du message."""
        return f"Message(id={self.id}, topic={self.topic}, sender={self.sender})"


class Subscription:
    """Classe représentant un abonnement à un sujet."""
    
    def __init__(self, topic: str, callback: Callable[[Message], None], subscriber_id: str):
        """
        Initialise un abonnement.
        
        Args:
            topic: Sujet de l'abonnement
            callback: Fonction de rappel qui sera appelée lorsqu'un message est publié sur ce sujet
            subscriber_id: Identifiant de l'abonné
        """
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.callback = callback
        self.subscriber_id = subscriber_id
        self.created_at = datetime.now()
    
    def __str__(self) -> str:
        """Retourne une représentation textuelle de l'abonnement."""
        return f"Subscription(id={self.id}, topic={self.topic}, subscriber={self.subscriber_id})"


class MessageBus:
    """
    Bus de messages pour la communication entre agents.
    Implémente le pattern Singleton et Publish-Subscribe.
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """Implémentation du pattern Singleton."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MessageBus, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de MessageBus."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialise le bus de messages si ce n'est pas déjà fait."""
        with self._lock:
            if not getattr(self, '_initialized', False):
                self._subscriptions: Dict[str, List[Subscription]] = {}
                self._message_history: Dict[str, List[Message]] = {}
                self._history_max_size = 100
                self._initialized = True
                logger.info("MessageBus initialized")
    
    def publish(self, topic: str, data: Dict[str, Any], sender: str = None) -> str:
        """
        Publie un message sur un sujet.
        
        Args:
            topic: Sujet du message
            data: Données du message
            sender: Identifiant de l'expéditeur (optionnel)
            
        Returns:
            Identifiant du message
        """
        with self._lock:
            # Créer le message
            message = Message(topic, data, sender)
            logger.debug(f"Publishing message: {message}")
            
            # Stocker le message dans l'historique
            if topic not in self._message_history:
                self._message_history[topic] = []
            
            self._message_history[topic].append(message)
            
            # Limiter la taille de l'historique
            if len(self._message_history[topic]) > self._history_max_size:
                self._message_history[topic] = self._message_history[topic][-self._history_max_size:]
            
            # Transmettre le message aux abonnés
            if topic in self._subscriptions:
                for subscription in self._subscriptions[topic]:
                    try:
                        # Execute callbacks in a separate thread
                        threading.Thread(
                            target=subscription.callback,
                            args=(message,),
                            daemon=True
                        ).start()
                    except Exception as e:
                        logger.error(f"Error delivering message to subscriber {subscription.subscriber_id}: {str(e)}")
            
            # Transmettre également aux abonnés du caractère générique "*"
            if "*" in self._subscriptions:
                for subscription in self._subscriptions["*"]:
                    try:
                        threading.Thread(
                            target=subscription.callback,
                            args=(message,),
                            daemon=True
                        ).start()
                    except Exception as e:
                        logger.error(f"Error delivering message to wildcard subscriber {subscription.subscriber_id}: {str(e)}")
            
            return message.id
    
    def subscribe(self, topic: str, callback: Callable[[Message], None], subscriber_id: str) -> str:
        """
        S'abonne à un sujet.
        
        Args:
            topic: Sujet de l'abonnement
            callback: Fonction de rappel qui sera appelée lorsqu'un message est publié sur ce sujet
            subscriber_id: Identifiant de l'abonné
            
        Returns:
            Identifiant de l'abonnement
        """
        with self._lock:
            subscription = Subscription(topic, callback, subscriber_id)
            logger.debug(f"New subscription: {subscription}")
            
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            
            self._subscriptions[topic].append(subscription)
            return subscription.id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Désabonne un abonnement.
        
        Args:
            subscription_id: Identifiant de l'abonnement
            
        Returns:
            True si l'abonnement a été trouvé et supprimé, False sinon
        """
        with self._lock:
            for topic, subscriptions in self._subscriptions.items():
                for idx, subscription in enumerate(subscriptions):
                    if subscription.id == subscription_id:
                        logger.debug(f"Removing subscription: {subscription}")
                        subscriptions.pop(idx)
                        
                        # Supprimer le sujet s'il n'y a plus d'abonnés
                        if not subscriptions:
                            del self._subscriptions[topic]
                        
                        return True
            return False
    
    def unsubscribe_all(self, subscriber_id: str) -> int:
        """
        Désabonne tous les abonnements d'un abonné.
        
        Args:
            subscriber_id: Identifiant de l'abonné
            
        Returns:
            Nombre d'abonnements supprimés
        """
        with self._lock:
            count = 0
            topics_to_check = list(self._subscriptions.keys())
            
            for topic in topics_to_check:
                subscriptions = self._subscriptions[topic]
                original_count = len(subscriptions)
                
                # Filtrer les abonnements de cet abonné
                subscriptions = [s for s in subscriptions if s.subscriber_id != subscriber_id]
                count += original_count - len(subscriptions)
                
                if subscriptions:
                    self._subscriptions[topic] = subscriptions
                else:
                    del self._subscriptions[topic]
            
            logger.debug(f"Removed {count} subscriptions for subscriber {subscriber_id}")
            return count
    
    def get_message_history(self, topic: Optional[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des messages.
        
        Args:
            topic: Sujet des messages (optionnel)
            limit: Nombre maximum de messages à retourner (optionnel)
            
        Returns:
            Liste des messages
        """
        with self._lock:
            result = []
            
            if topic:
                # Historique pour un sujet spécifique
                if topic in self._message_history:
                    history = self._message_history[topic]
                    if limit:
                        history = history[-limit:]
                    result = [msg.to_dict() for msg in history]
            else:
                # Historique pour tous les sujets
                all_messages = []
                for topic_history in self._message_history.values():
                    all_messages.extend(topic_history)
                
                # Trier par horodatage
                all_messages.sort(key=lambda msg: msg.timestamp)
                
                if limit:
                    all_messages = all_messages[-limit:]
                
                result = [msg.to_dict() for msg in all_messages]
            
            return result
    
    def clear_history(self, topic: Optional[str] = None) -> None:
        """
        Efface l'historique des messages.
        
        Args:
            topic: Sujet des messages à effacer (optionnel, tous les sujets si non spécifié)
        """
        with self._lock:
            if topic:
                if topic in self._message_history:
                    del self._message_history[topic]
                    logger.debug(f"Cleared message history for topic {topic}")
            else:
                self._message_history.clear()
                logger.debug("Cleared all message history")
