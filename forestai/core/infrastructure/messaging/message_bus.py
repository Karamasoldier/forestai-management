"""
Implémentation d'un message bus pour la communication entre agents.

Ce module fournit un bus de messages simple permettant aux agents 
de communiquer de manière découplée à travers des événements publiés et souscrits.
"""

import logging
import json
import time
import threading
import uuid
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from queue import Queue


class MessagePriority(Enum):
    """Priorité des messages dans le bus."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Message:
    """Représente un message dans le système."""
    message_id: str
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    sender: str
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    
    @classmethod
    def create(cls, topic: str, payload: Dict[str, Any], sender: str, 
               priority: MessagePriority = MessagePriority.NORMAL,
               correlation_id: Optional[str] = None) -> 'Message':
        """
        Crée une nouvelle instance de Message avec un ID unique et l'horodatage actuel.
        """
        return cls(
            message_id=str(uuid.uuid4()),
            topic=topic,
            payload=payload,
            timestamp=datetime.now(),
            sender=sender,
            priority=priority,
            correlation_id=correlation_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le message en dictionnaire."""
        return {
            "message_id": self.message_id,
            "topic": self.topic,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "priority": self.priority.name,
            "correlation_id": self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Crée un message à partir d'un dictionnaire."""
        return cls(
            message_id=data["message_id"],
            topic=data["topic"],
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sender=data["sender"],
            priority=MessagePriority[data["priority"]],
            correlation_id=data.get("correlation_id")
        )


class MessageBus:
    """
    Bus de messages permettant la communication entre agents via 
    un modèle publish/subscribe.
    """
    
    def __init__(self):
        """Initialise le bus de messages."""
        self.logger = logging.getLogger(__name__)
        self.subscribers: Dict[str, List[Callable[[Message], None]]] = {}
        self.message_queue: Queue = Queue()
        self.is_running = False
        self.worker_thread = None
        self.message_history: List[Message] = []
        self.max_history_size = 1000  # Nombre maximum de messages à conserver dans l'historique
    
    def start(self):
        """Démarre le traitement asynchrone des messages."""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.worker_thread.start()
        self.logger.info("Message bus started")
    
    def stop(self):
        """Arrête le traitement des messages."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        self.logger.info("Message bus stopped")
    
    def subscribe(self, topic: str, handler: Callable[[Message], None]):
        """
        Souscrit à un topic en enregistrant un gestionnaire qui sera appelé 
        lorsqu'un message sur ce topic est publié.
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        
        if handler not in self.subscribers[topic]:
            self.subscribers[topic].append(handler)
            self.logger.debug(f"Subscribed handler to topic: {topic}")
    
    def unsubscribe(self, topic: str, handler: Callable[[Message], None]):
        """Désinscrit un gestionnaire d'un topic."""
        if topic in self.subscribers and handler in self.subscribers[topic]:
            self.subscribers[topic].remove(handler)
            self.logger.debug(f"Unsubscribed handler from topic: {topic}")
            
            # Nettoyer les topics sans abonnés
            if not self.subscribers[topic]:
                del self.subscribers[topic]
    
    def publish(self, message: Message):
        """
        Publie un message sur le bus.
        Le message sera traité de manière asynchrone.
        """
        self.message_queue.put(message)
        self.logger.debug(f"Message queued for topic: {message.topic}, id: {message.message_id}")
    
    def publish_sync(self, message: Message):
        """
        Publie un message et le traite immédiatement de manière synchrone.
        Utile pour les messages urgents ou lors des tests.
        """
        self._dispatch_message(message)
    
    def create_and_publish(self, topic: str, payload: Dict[str, Any], sender: str,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          correlation_id: Optional[str] = None):
        """
        Crée un nouveau message et le publie sur le bus.
        """
        message = Message.create(
            topic=topic,
            payload=payload,
            sender=sender,
            priority=priority,
            correlation_id=correlation_id
        )
        self.publish(message)
        return message.message_id
    
    def _process_messages(self):
        """
        Traite les messages de la file d'attente.
        Cette méthode est exécutée dans un thread séparé.
        """
        while self.is_running:
            try:
                # Récupérer un message de la file d'attente (avec un timeout pour pouvoir arrêter proprement)
                try:
                    message = self.message_queue.get(block=True, timeout=0.5)
                except:
                    continue
                
                # Traiter le message
                self._dispatch_message(message)
                
                # Marquer la tâche comme terminée
                self.message_queue.task_done()
            
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}", exc_info=True)
    
    def _dispatch_message(self, message: Message):
        """
        Distribue un message à tous les gestionnaires abonnés au topic.
        Ajoute également le message à l'historique.
        """
        # Ajouter à l'historique
        self._add_to_history(message)
        
        # Distribuer aux abonnés directs du topic
        if message.topic in self.subscribers:
            for handler in self.subscribers[message.topic]:
                try:
                    handler(message)
                except Exception as e:
                    self.logger.error(f"Error in handler for topic {message.topic}: {str(e)}", exc_info=True)
        
        # Distribuer aux abonnés des wildcards (par exemple: "parcel.*")
        for topic, handlers in self.subscribers.items():
            if '*' in topic:
                pattern = topic.replace('*', '')
                if message.topic.startswith(pattern) or message.topic.endswith(pattern):
                    for handler in handlers:
                        try:
                            handler(message)
                        except Exception as e:
                            self.logger.error(f"Error in wildcard handler for {topic}: {str(e)}", exc_info=True)
    
    def _add_to_history(self, message: Message):
        """Ajoute un message à l'historique, en limitant la taille."""
        self.message_history.append(message)
        
        # Limiter la taille de l'historique
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
    
    def get_history(self, topic: Optional[str] = None, limit: int = 100) -> List[Message]:
        """
        Récupère l'historique des messages, filtré par topic si spécifié.
        
        Args:
            topic: Filtre optionnel par topic
            limit: Nombre maximum de messages à retourner
            
        Returns:
            Liste des messages, du plus récent au plus ancien
        """
        result = []
        
        # Parcourir l'historique du plus récent au plus ancien
        for message in reversed(self.message_history):
            if topic is None or message.topic == topic:
                result.append(message)
                
                if len(result) >= limit:
                    break
        
        return result
    
    def clear_history(self):
        """Efface l'historique des messages."""
        self.message_history = []
        self.logger.debug("Message history cleared")


# Singleton pour l'accès global au message bus
_message_bus_instance = None

def get_message_bus() -> MessageBus:
    """
    Récupère l'instance unique du message bus (pattern Singleton).
    """
    global _message_bus_instance
    if _message_bus_instance is None:
        _message_bus_instance = MessageBus()
    return _message_bus_instance
