"""
Système de mémoire partagée pour les agents.

Ce module implémente un système de mémoire qui permet aux agents de partager 
des données et du contexte entre eux. Il fournit une interface simple pour 
stocker et récupérer des informations avec des options de durée de vie.
"""

import json
import logging
import os
import time
import threading
from typing import Dict, Any, Optional, List, Set, Tuple
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import sqlite3


class MemoryBackend(ABC):
    """Interface abstraite pour les backends de stockage de mémoire."""
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Stocke une valeur dans la mémoire.
        
        Args:
            key: Clé pour l'accès ultérieur
            value: Valeur à stocker (doit être sérialisable)
            ttl: Durée de vie en secondes (None pour une durée illimitée)
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur par sa clé.
        
        Args:
            key: Clé de la valeur
            
        Returns:
            Valeur stockée ou None si la clé n'existe pas ou est expirée
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Supprime une valeur de la mémoire.
        
        Args:
            key: Clé de la valeur à supprimer
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Vérifie si une clé existe et n'est pas expirée.
        
        Args:
            key: Clé à vérifier
            
        Returns:
            True si la clé existe et n'est pas expirée, False sinon
        """
        pass
    
    @abstractmethod
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Récupère les clés correspondant à un motif.
        
        Args:
            pattern: Motif de filtre (peut utiliser * comme wildcard)
            
        Returns:
            Liste des clés correspondantes
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Efface toutes les valeurs de la mémoire.
        
        Returns:
            True si l'opération a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Nettoie les valeurs expirées.
        
        Returns:
            Nombre de valeurs supprimées
        """
        pass


class InMemoryBackend(MemoryBackend):
    """
    Implémentation du backend de mémoire en mémoire (volatile).
    Utilise un dictionnaire en mémoire pour stocker les données.
    """
    
    def __init__(self):
        """Initialise le backend en mémoire."""
        self.data: Dict[str, Tuple[Any, Optional[float]]] = {}  # (value, expiration_timestamp)
        self.lock = threading.RLock()  # Lock réentrant pour thread safety
        self.logger = logging.getLogger(__name__)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur avec une durée de vie optionnelle."""
        expiration = time.time() + ttl if ttl is not None else None
        
        with self.lock:
            self.data[key] = (value, expiration)
        
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur si elle existe et n'est pas expirée."""
        with self.lock:
            if key not in self.data:
                return None
            
            value, expiration = self.data[key]
            
            # Vérifier si la valeur a expiré
            if expiration is not None and time.time() > expiration:
                del self.data[key]
                return None
            
            return value
    
    def delete(self, key: str) -> bool:
        """Supprime une valeur."""
        with self.lock:
            if key in self.data:
                del self.data[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe et n'est pas expirée."""
        return self.get(key) is not None
    
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Récupère les clés correspondant à un motif."""
        with self.lock:
            if pattern is None:
                return list(self.data.keys())
            
            # Filtrage simple avec wildcard
            if '*' not in pattern:
                return [key for key in self.data.keys() if key == pattern]
            
            prefix = pattern.split('*')[0]
            suffix = pattern.split('*')[-1]
            
            return [
                key for key in self.data.keys() 
                if key.startswith(prefix) and key.endswith(suffix)
            ]
    
    def clear(self) -> bool:
        """Efface toutes les valeurs."""
        with self.lock:
            self.data.clear()
        return True
    
    def cleanup_expired(self) -> int:
        """Nettoie les valeurs expirées."""
        count = 0
        current_time = time.time()
        
        with self.lock:
            expired_keys = [
                key for key, (_, expiration) in self.data.items()
                if expiration is not None and current_time > expiration
            ]
            
            for key in expired_keys:
                del self.data[key]
                count += 1
        
        return count


class SQLiteBackend(MemoryBackend):
    """
    Implémentation du backend de mémoire utilisant SQLite.
    Persistant avec de meilleures performances pour de grandes quantités de données.
    """
    
    def __init__(self, db_path: str = "agent_memory.db"):
        """
        Initialise le backend SQLite.
        
        Args:
            db_path: Chemin vers le fichier de base de données SQLite
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialiser la base de données
        self._init_db()
    
    def _init_db(self):
        """Initialise la base de données et les tables."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Créer la table si elle n'existe pas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_memory (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expiration REAL NULL
                )
            ''')
            
            # Créer un index sur l'expiration pour optimiser le nettoyage
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_expiration ON agent_memory(expiration)
            ''')
            
            conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur avec une durée de vie optionnelle."""
        conn = None
        try:
            # Sérialiser la valeur
            serialized_value = json.dumps(value)
            
            # Calculer l'expiration
            expiration = time.time() + ttl if ttl is not None else None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insérer ou mettre à jour
            cursor.execute(
                "INSERT OR REPLACE INTO agent_memory (key, value, expiration) VALUES (?, ?, ?)",
                (key, serialized_value, expiration)
            )
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur si elle existe et n'est pas expirée."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer la valeur et vérifier l'expiration
            cursor.execute(
                "SELECT value, expiration FROM agent_memory WHERE key = ?",
                (key,)
            )
            
            result = cursor.fetchone()
            if not result:
                return None
            
            serialized_value, expiration = result
            
            # Vérifier si la valeur a expiré
            if expiration is not None and time.time() > expiration:
                cursor.execute("DELETE FROM agent_memory WHERE key = ?", (key,))
                conn.commit()
                return None
            
            # Désérialiser la valeur
            return json.loads(serialized_value)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def delete(self, key: str) -> bool:
        """Supprime une valeur."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM agent_memory WHERE key = ?", (key,))
            conn.commit()
            
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe et n'est pas expirée."""
        return self.get(key) is not None
    
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Récupère les clés correspondant à un motif."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if pattern is None:
                cursor.execute(
                    "SELECT key FROM agent_memory WHERE expiration IS NULL OR expiration > ?",
                    (time.time(),)
                )
            else:
                # Convertir le motif avec wildcard en LIKE SQL
                sql_pattern = pattern.replace('*', '%')
                cursor.execute(
                    "SELECT key FROM agent_memory WHERE (expiration IS NULL OR expiration > ?) AND key LIKE ?",
                    (time.time(), sql_pattern)
                )
            
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def clear(self) -> bool:
        """Efface toutes les valeurs."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM agent_memory")
            conn.commit()
            
            return True
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def cleanup_expired(self) -> int:
        """Nettoie les valeurs expirées."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM agent_memory WHERE expiration IS NOT NULL AND expiration <= ?",
                (time.time(),)
            )
            
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {str(e)}")
            return 0
        finally:
            if conn:
                conn.close()


class AgentMemory:
    """
    Système de mémoire partagée pour les agents.
    Fournit une interface simple pour le stockage et la récupération de données.
    """
    
    def __init__(self, backend: MemoryBackend = None):
        """
        Initialise la mémoire de l'agent.
        
        Args:
            backend: Backend de stockage à utiliser (par défaut, InMemoryBackend)
        """
        self.backend = backend or InMemoryBackend()
        self.logger = logging.getLogger(__name__)
        
        # Démarrer un thread pour nettoyer périodiquement les valeurs expirées
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Stocke une valeur dans la mémoire.
        
        Args:
            key: Clé pour l'accès ultérieur
            value: Valeur à stocker
            ttl: Durée de vie en secondes (None pour une durée illimitée)
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        return self.backend.set(key, value, ttl)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur par sa clé.
        
        Args:
            key: Clé de la valeur
            
        Returns:
            Valeur stockée ou None si la clé n'existe pas ou est expirée
        """
        return self.backend.get(key)
    
    def remove(self, key: str) -> bool:
        """
        Supprime une valeur de la mémoire.
        
        Args:
            key: Clé de la valeur à supprimer
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        return self.backend.delete(key)
    
    def has_key(self, key: str) -> bool:
        """
        Vérifie si une clé existe dans la mémoire.
        
        Args:
            key: Clé à vérifier
            
        Returns:
            True si la clé existe et n'est pas expirée, False sinon
        """
        return self.backend.exists(key)
    
    def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Liste les clés correspondant à un motif.
        
        Args:
            pattern: Motif de filtre (peut utiliser * comme wildcard)
            
        Returns:
            Liste des clés correspondantes
        """
        return self.backend.keys(pattern)
    
    def clear_all(self) -> bool:
        """
        Efface toutes les valeurs de la mémoire.
        
        Returns:
            True si l'opération a réussi, False sinon
        """
        return self.backend.clear()
    
    def store_context(self, context_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Stocke un contexte complet (ensemble de données liées).
        
        Args:
            context_id: Identifiant du contexte
            data: Dictionnaire de données
            ttl: Durée de vie en secondes
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        context_key = f"context:{context_id}"
        return self.store(context_key, data, ttl)
    
    def retrieve_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un contexte complet.
        
        Args:
            context_id: Identifiant du contexte
            
        Returns:
            Dictionnaire de données ou None si le contexte n'existe pas
        """
        context_key = f"context:{context_id}"
        return self.retrieve(context_key)
    
    def _cleanup_loop(self):
        """Boucle de nettoyage périodique des valeurs expirées."""
        while True:
            try:
                count = self.backend.cleanup_expired()
                if count > 0:
                    self.logger.debug(f"Cleaned up {count} expired memory entries")
                
                # Attendre 5 minutes avant le prochain nettoyage
                time.sleep(300)
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}", exc_info=True)
                time.sleep(60)  # Attendre une minute avant de réessayer


# Singleton pour l'accès global à la mémoire
_agent_memory_instance = None

def get_agent_memory() -> AgentMemory:
    """
    Récupère l'instance unique de la mémoire (pattern Singleton).
    
    Returns:
        Instance de AgentMemory
    """
    global _agent_memory_instance
    if _agent_memory_instance is None:
        # Créer un backend SQLite si possible, sinon en mémoire
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "agent_memory.db")
            backend = SQLiteBackend(db_path)
            _agent_memory_instance = AgentMemory(backend)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to create SQLite backend: {str(e)}")
            _agent_memory_instance = AgentMemory(InMemoryBackend())
    
    return _agent_memory_instance
