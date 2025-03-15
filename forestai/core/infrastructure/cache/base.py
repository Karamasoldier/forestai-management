"""
Classes de base pour le système de cache.

Ce module fournit les classes et enums fondamentales utilisées par le système de cache.
"""

import time
import json
import hashlib
import logging
import os
import pickle
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


class CacheType(str, Enum):
    """Types de données pouvant être mises en cache."""
    GEODATA = "geodata"        # Données géographiques (parcelles, zones)
    REGULATION = "regulation"  # Données réglementaires (Code forestier)
    SUBSIDY = "subsidy"        # Données de subventions
    CLIMATE = "climate"        # Données climatiques
    EXTERNAL_API = "external_api"  # Données d'API externes
    GENERIC = "generic"        # Données génériques


class CachePolicy(str, Enum):
    """Politiques de mise à jour du cache."""
    ALWAYS_FRESH = "always_fresh"  # Toujours vérifier la fraîcheur (données très volatiles)
    DAILY = "daily"                # Mise à jour quotidienne
    WEEKLY = "weekly"              # Mise à jour hebdomadaire
    MONTHLY = "monthly"            # Mise à jour mensuelle
    STATIC = "static"              # Données statiques (pas de mise à jour automatique)
    CUSTOM = "custom"              # Politique de mise à jour personnalisée


class CacheLevel(str, Enum):
    """Niveaux de stockage du cache."""
    MEMORY = "memory"      # Cache en mémoire (plus rapide, volatile)
    DISK = "disk"          # Cache sur disque (persistant, plus lent)
    DATABASE = "database"  # Cache en base de données (persistant, requêtes possibles)


class CacheKey:
    """Gestionnaire de clés de cache."""
    
    @staticmethod
    def generate(
        data_type: CacheType,
        identifier: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Génère une clé de cache unique.
        
        Args:
            data_type: Type de données
            identifier: Identifiant principal (ex: nom de commune, ID de parcelle)
            params: Paramètres additionnels influençant le résultat
            
        Returns:
            Clé unique pour le cache
        """
        # Préfixe pour le type de données
        key_parts = [f"cache:{data_type.value}:{identifier}"]
        
        # Ajouter les paramètres si présents
        if params:
            # Trier les paramètres pour assurer la cohérence
            param_str = json.dumps(params, sort_keys=True)
            # Créer un hash des paramètres pour limiter la taille de la clé
            param_hash = hashlib.md5(param_str.encode('utf-8')).hexdigest()[:10]
            key_parts.append(param_hash)
        
        return ":".join(key_parts)
    
    @staticmethod
    def parse(key: str) -> Tuple[CacheType, str, Optional[str]]:
        """
        Parse une clé de cache pour extraire ses composants.
        
        Args:
            key: Clé de cache générée par generate()
            
        Returns:
            Tuple (type de données, identifiant, hash de paramètres)
        """
        parts = key.split(":")
        if len(parts) < 3 or parts[0] != "cache":
            raise ValueError(f"Format de clé de cache invalide: {key}")
        
        data_type = CacheType(parts[1])
        identifier = parts[2]
        param_hash = parts[3] if len(parts) > 3 else None
        
        return data_type, identifier, param_hash


class CacheEntry:
    """Entrée de cache avec métadonnées."""
    
    def __init__(
        self,
        data: Any,
        created_at: Optional[float] = None,
        expires_at: Optional[float] = None,
        source: Optional[str] = None,
        data_type: Optional[CacheType] = None,
        policy: Optional[CachePolicy] = None,
        level: Optional[CacheLevel] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialise une entrée de cache.
        
        Args:
            data: Données à stocker
            created_at: Timestamp de création (par défaut: maintenant)
            expires_at: Timestamp d'expiration (optionnel)
            source: Source des données (ex: "INSEE", "IGN", "ADEME")
            data_type: Type de données
            policy: Politique de mise à jour
            level: Niveau de stockage
            metadata: Métadonnées additionnelles
        """
        self.data = data
        self.created_at = created_at or time.time()
        self.expires_at = expires_at
        self.source = source
        self.data_type = data_type
        self.policy = policy
        self.level = level
        self.metadata = metadata or {}
    
    def is_expired(self) -> bool:
        """
        Vérifie si l'entrée de cache a expiré.
        
        Returns:
            True si l'entrée a expiré, False sinon
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def get_age(self) -> float:
        """
        Calcule l'âge de l'entrée en secondes.
        
        Returns:
            Âge en secondes
        """
        return time.time() - self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entrée en dictionnaire pour la sérialisation.
        
        Returns:
            Dictionnaire représentant l'entrée
        """
        return {
            "data": self.data,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "source": self.source,
            "data_type": self.data_type.value if self.data_type else None,
            "policy": self.policy.value if self.policy else None,
            "level": self.level.value if self.level else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'CacheEntry':
        """
        Crée une entrée à partir d'un dictionnaire.
        
        Args:
            data_dict: Dictionnaire représentant l'entrée
            
        Returns:
            Instance de CacheEntry
        """
        # Convertir les valeurs d'énumération
        data_type = CacheType(data_dict["data_type"]) if data_dict.get("data_type") else None
        policy = CachePolicy(data_dict["policy"]) if data_dict.get("policy") else None
        level = CacheLevel(data_dict["level"]) if data_dict.get("level") else None
        
        return cls(
            data=data_dict["data"],
            created_at=data_dict.get("created_at"),
            expires_at=data_dict.get("expires_at"),
            source=data_dict.get("source"),
            data_type=data_type,
            policy=policy,
            level=level,
            metadata=data_dict.get("metadata", {})
        )


class CacheValidator:
    """Utilitaires pour valider et gérer la fraîcheur des données en cache."""
    
    @staticmethod
    def is_valid(
        entry: CacheEntry,
        policy: Optional[CachePolicy] = None,
        max_age: Optional[int] = None
    ) -> bool:
        """
        Vérifie si une entrée de cache est valide selon une politique.
        
        Args:
            entry: Entrée de cache à vérifier
            policy: Politique de fraîcheur à appliquer
            max_age: Âge maximum en secondes (remplace policy si spécifié)
            
        Returns:
            True si l'entrée est valide, False sinon
        """
        # Si l'entrée a une date d'expiration explicite
        if entry.expires_at is not None:
            return not entry.is_expired()
        
        # Si un âge maximum est spécifié
        if max_age is not None:
            return entry.get_age() <= max_age
        
        # Utiliser la politique spécifiée ou celle de l'entrée
        policy = policy or entry.policy
        if policy is None:
            # Sans politique, considérer valide
            return True
        
        # Appliquer la politique
        age = entry.get_age()
        if policy == CachePolicy.ALWAYS_FRESH:
            return False  # Toujours considérer comme périmé
        elif policy == CachePolicy.DAILY:
            return age <= 86400  # 24 heures
        elif policy == CachePolicy.WEEKLY:
            return age <= 604800  # 7 jours
        elif policy == CachePolicy.MONTHLY:
            return age <= 2592000  # 30 jours
        elif policy == CachePolicy.STATIC:
            return True  # Toujours considérer comme valide
        elif policy == CachePolicy.CUSTOM:
            # Vérifier les règles personnalisées dans les métadonnées
            if "max_age" in entry.metadata:
                return age <= entry.metadata["max_age"]
            return True
        
        return True
    
    @staticmethod
    def get_ttl_from_policy(policy: CachePolicy, custom_ttl: Optional[int] = None) -> Optional[int]:
        """
        Calcule le TTL en secondes à partir d'une politique.
        
        Args:
            policy: Politique de mise en cache
            custom_ttl: TTL personnalisé pour CachePolicy.CUSTOM
            
        Returns:
            TTL en secondes ou None pour pas d'expiration
        """
        if policy == CachePolicy.ALWAYS_FRESH:
            return 300  # 5 minutes
        elif policy == CachePolicy.DAILY:
            return 86400  # 24 heures
        elif policy == CachePolicy.WEEKLY:
            return 604800  # 7 jours
        elif policy == CachePolicy.MONTHLY:
            return 2592000  # 30 jours
        elif policy == CachePolicy.STATIC:
            return None  # Pas d'expiration
        elif policy == CachePolicy.CUSTOM:
            return custom_ttl
        
        return None


class DiskCacheBackend:
    """Backend de cache sur disque."""
    
    def __init__(self, cache_dir: str = None):
        """
        Initialise le backend de cache sur disque.
        
        Args:
            cache_dir: Répertoire de stockage du cache
        """
        if cache_dir is None:
            # Répertoire par défaut dans le dossier data
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            cache_dir = os.path.join(base_dir, "data", "cache")
        
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_file_path(self, key: str) -> str:
        """
        Obtient le chemin de fichier pour une clé.
        
        Args:
            key: Clé de cache
            
        Returns:
            Chemin de fichier
        """
        # Hasher la clé pour éviter les caractères spéciaux dans les noms de fichiers
        hashed_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.pickle")
    
    def set(self, key: str, entry: CacheEntry) -> bool:
        """
        Stocke une entrée dans le cache.
        
        Args:
            key: Clé de cache
            entry: Entrée de cache
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        try:
            file_path = self._get_file_path(key)
            
            # Stocker la clé originale dans les métadonnées
            entry.metadata["original_key"] = key
            
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'écriture dans le cache disque: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Récupère une entrée du cache.
        
        Args:
            key: Clé de cache
            
        Returns:
            Entrée de cache ou None si non trouvée ou expirée
        """
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'rb') as f:
                entry = pickle.load(f)
            
            # Vérifier si l'entrée a expiré
            if entry.is_expired():
                os.remove(file_path)
                return None
            
            return entry
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture du cache disque: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Supprime une entrée du cache.
        
        Args:
            key: Clé de cache
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        file_path = self._get_file_path(key)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors de la suppression du cache disque: {str(e)}")
        
        return False
    
    def cleanup_expired(self) -> int:
        """
        Nettoie les entrées expirées.
        
        Returns:
            Nombre d'entrées supprimées
        """
        count = 0
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.pickle'):
                continue
            
            file_path = os.path.join(self.cache_dir, filename)
            try:
                with open(file_path, 'rb') as f:
                    entry = pickle.load(f)
                
                if entry.is_expired():
                    os.remove(file_path)
                    count += 1
            except Exception as e:
                self.logger.warning(f"Erreur lors du nettoyage du cache disque: {str(e)}")
        
        return count
