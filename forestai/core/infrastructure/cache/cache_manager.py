"""
Gestionnaire de cache pour les données externes.

Ce module fournit un système de cache avancé pour optimiser l'accès aux données
externes et réduire les appels redondants aux sources de données.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable, Union

from forestai.core.infrastructure.memory.agent_memory import get_agent_memory
from forestai.core.infrastructure.cache.base import (
    CacheType, CachePolicy, CacheLevel, CacheKey, CacheEntry, 
    CacheValidator, DiskCacheBackend
)


class CacheManager:
    """
    Gestionnaire de cache pour les données externes.
    Fournit une interface unifiée pour le cache mémoire, disque et base de données.
    """
    
    def __init__(self):
        """Initialise le gestionnaire de cache."""
        self.logger = logging.getLogger(__name__)
        
        # Backends de cache
        self.memory_cache = get_agent_memory()
        self.disk_cache = DiskCacheBackend()
        
        # Statistiques d'utilisation
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0,
            "db_hits": 0,
            "cache_saves": 0,
            "cache_updates": 0,
            "cache_errors": 0
        }
        
        # Cache de préchargement
        self.preload_cache = {}
        
        # Verrou pour les opérations thread-safe
        self.lock = threading.RLock()
        
        # Démarrer le thread de nettoyage
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get(
        self,
        data_type: CacheType,
        identifier: str,
        params: Optional[Dict[str, Any]] = None,
        policy: Optional[CachePolicy] = None,
        max_age: Optional[int] = None,
        force_refresh: bool = False,
        default_value: Any = None,
        refresh_callback: Optional[Callable[[], Any]] = None,
        level: Optional[CacheLevel] = None
    ) -> Any:
        """
        Récupère des données du cache ou les rafraîchit si nécessaire.
        
        Args:
            data_type: Type de données
            identifier: Identifiant principal
            params: Paramètres additionnels
            policy: Politique de mise à jour à appliquer
            max_age: Âge maximum en secondes
            force_refresh: Forcer le rafraîchissement des données
            default_value: Valeur par défaut si non trouvée
            refresh_callback: Fonction à appeler pour rafraîchir les données
            level: Niveau de cache à utiliser
            
        Returns:
            Données du cache ou valeur par défaut
        """
        # Générer la clé de cache
        key = CacheKey.generate(data_type, identifier, params)
        
        # Si rafraîchissement forcé, supprimer d'abord
        if force_refresh:
            self.delete(data_type, identifier, params)
        
        # Essayer de récupérer du cache
        entry = self._get_entry(key, level)
        
        if entry is not None:
            # Vérifier la validité selon la politique
            if CacheValidator.is_valid(entry, policy, max_age):
                with self.lock:
                    self.stats["hits"] += 1
                return entry.data
        
        # Cache miss ou données périmées
        with self.lock:
            self.stats["misses"] += 1
        
        # Rafraîchir les données si callback fourni
        if refresh_callback is not None:
            try:
                fresh_data = refresh_callback()
                if fresh_data is not None:
                    # Mettre en cache les nouvelles données
                    self.set(
                        data_type=data_type,
                        identifier=identifier,
                        data=fresh_data,
                        params=params,
                        policy=policy,
                        level=level
                    )
                    return fresh_data
            except Exception as e:
                self.logger.error(f"Erreur lors du rafraîchissement des données: {str(e)}", exc_info=True)
                with self.lock:
                    self.stats["cache_errors"] += 1
        
        # Retourner les données périmées si disponibles ou la valeur par défaut
        return entry.data if entry is not None else default_value
    
    def set(
        self,
        data_type: CacheType,
        identifier: str,
        data: Any,
        params: Optional[Dict[str, Any]] = None,
        policy: Optional[CachePolicy] = CachePolicy.DAILY,
        ttl: Optional[int] = None,
        source: Optional[str] = None,
        level: Optional[CacheLevel] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Stocke des données dans le cache.
        
        Args:
            data_type: Type de données
            identifier: Identifiant principal
            data: Données à stocker
            params: Paramètres additionnels
            policy: Politique de mise à jour
            ttl: Durée de vie en secondes (remplace policy si spécifié)
            source: Source des données
            level: Niveau de cache à utiliser
            metadata: Métadonnées additionnelles
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        # Générer la clé de cache
        key = CacheKey.generate(data_type, identifier, params)
        
        # Calculer l'expiration
        if ttl is None and policy is not None:
            ttl = CacheValidator.get_ttl_from_policy(policy)
        
        expires_at = time.time() + ttl if ttl is not None else None
        
        # Créer l'entrée de cache
        entry = CacheEntry(
            data=data,
            expires_at=expires_at,
            source=source,
            data_type=data_type,
            policy=policy,
            level=level,
            metadata=metadata
        )
        
        # Stocker dans les niveaux appropriés
        success = self._set_entry(key, entry, level)
        
        if success:
            with self.lock:
                self.stats["cache_saves"] += 1
        
        return success
    
    def delete(
        self,
        data_type: CacheType,
        identifier: str,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Supprime des données du cache.
        
        Args:
            data_type: Type de données
            identifier: Identifiant principal
            params: Paramètres additionnels
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        # Générer la clé de cache
        key = CacheKey.generate(data_type, identifier, params)
        
        # Supprimer de tous les niveaux
        memory_success = self.memory_cache.remove(key)
        disk_success = self.disk_cache.delete(key)
        
        return memory_success or disk_success
    
    def clear(
        self,
        data_type: Optional[CacheType] = None,
        older_than: Optional[int] = None
    ) -> int:
        """
        Nettoie le cache selon des critères.
        
        Args:
            data_type: Type de données à nettoyer (None pour tous)
            older_than: Âge minimum en secondes pour suppression
            
        Returns:
            Nombre d'entrées supprimées
        """
        count = 0
        
        # Nettoyer le cache mémoire
        if data_type is None:
            # Tout nettoyer
            if self.memory_cache.clear_all():
                count += 1
        else:
            # Nettoyer par préfixe
            pattern = f"cache:{data_type.value}:*"
            keys = self.memory_cache.list_keys(pattern)
            
            for key in keys:
                entry = self._get_entry_from_memory(key)
                
                if entry is not None and (older_than is None or entry.get_age() > older_than):
                    if self.memory_cache.remove(key):
                        count += 1
        
        # Nettoyer le cache disque
        # Le cache disque est nettoyé automatiquement par le thread de nettoyage
        
        return count
    
    def preload(
        self,
        data_type: CacheType,
        data_loader: Callable[[], Dict[str, Any]],
        policy: CachePolicy = CachePolicy.DAILY
    ) -> int:
        """
        Précharge des données dans le cache.
        
        Args:
            data_type: Type de données
            data_loader: Fonction de chargement des données
            policy: Politique de mise à jour
            
        Returns:
            Nombre d'entrées préchargées
        """
        try:
            # Charger les données
            data_dict = data_loader()
            
            if not data_dict:
                return 0
            
            count = 0
            # Stocker chaque entrée dans le cache
            for identifier, data in data_dict.items():
                if self.set(
                    data_type=data_type,
                    identifier=identifier,
                    data=data,
                    policy=policy,
                    metadata={"preloaded": True}
                ):
                    count += 1
            
            return count
        except Exception as e:
            self.logger.error(f"Erreur lors du préchargement du cache: {str(e)}", exc_info=True)
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques d'utilisation du cache.
        
        Returns:
            Dictionnaire des statistiques
        """
        with self.lock:
            stats = self.stats.copy()
            
            # Calculer les ratios
            total_requests = stats["hits"] + stats["misses"]
            if total_requests > 0:
                stats["hit_ratio"] = stats["hits"] / total_requests
            else:
                stats["hit_ratio"] = 0.0
            
            return stats
    
    def warmup(self, common_data_types: Optional[List[CacheType]] = None):
        """
        Précharge des données communes pour améliorer les performances initiales.
        
        Cette méthode peut être appelée au démarrage de l'application pour
        charger les données fréquemment utilisées dans le cache.
        
        Args:
            common_data_types: Liste des types de données à précharger
                (par défaut: toutes les données configurées pour le préchargement)
        """
        if common_data_types is None:
            common_data_types = [
                CacheType.REGULATION,  # Données réglementaires (rarement modifiées)
                CacheType.CLIMATE      # Données climatiques (mises à jour périodiques)
            ]
        
        self.logger.info(f"Démarrage du préchargement du cache pour {len(common_data_types)} types de données")
        
        total_entries = 0
        for data_type in common_data_types:
            try:
                # Vérifie si un chargeur est disponible pour ce type
                loader_method = getattr(self, f"_load_{data_type.value}_data", None)
                if loader_method is None:
                    self.logger.warning(f"Pas de chargeur disponible pour {data_type.value}")
                    continue
                
                # Déterminer la politique appropriée selon le type
                policy = self._get_default_policy_for_type(data_type)
                
                # Charger et mettre en cache
                entries_count = self.preload(data_type, loader_method, policy)
                total_entries += entries_count
                
                self.logger.info(f"Préchargé {entries_count} entrées pour {data_type.value}")
            except Exception as e:
                self.logger.error(f"Erreur lors du préchargement de {data_type.value}: {str(e)}", exc_info=True)
        
        self.logger.info(f"Préchargement terminé: {total_entries} entrées au total")
        return total_entries
    
    def _get_default_policy_for_type(self, data_type: CacheType) -> CachePolicy:
        """
        Détermine la politique de cache par défaut selon le type de données.
        
        Args:
            data_type: Type de données
            
        Returns:
            Politique de cache recommandée
        """
        # Politiques recommandées par type
        policies = {
            CacheType.GEODATA: CachePolicy.WEEKLY,      # Données géographiques (mises à jour peu fréquentes)
            CacheType.REGULATION: CachePolicy.MONTHLY,  # Données réglementaires (mises à jour lentes)
            CacheType.SUBSIDY: CachePolicy.DAILY,       # Données de subventions (mises à jour régulières)
            CacheType.CLIMATE: CachePolicy.WEEKLY,      # Données climatiques (mise à jour hebdomadaire)
            CacheType.EXTERNAL_API: CachePolicy.DAILY,  # Données d'API externes (fraîcheur importante)
            CacheType.GENERIC: CachePolicy.DAILY        # Données génériques (cas par défaut)
        }
        
        return policies.get(data_type, CachePolicy.DAILY)
    
    def _get_entry(self, key: str, level: Optional[CacheLevel] = None) -> Optional[CacheEntry]:
        """
        Récupère une entrée du cache à partir de la clé.
        
        Args:
            key: Clé de cache
            level: Niveau de cache à utiliser
            
        Returns:
            Entrée de cache ou None si non trouvée
        """
        entry = None
        
        # Essayer d'abord en mémoire, sauf si niveau spécifique demandé
        if level is None or level == CacheLevel.MEMORY:
            entry = self._get_entry_from_memory(key)
            if entry is not None:
                with self.lock:
                    self.stats["memory_hits"] += 1
                return entry
        
        # Ensuite sur disque
        if level is None or level == CacheLevel.DISK:
            entry = self.disk_cache.get(key)
            if entry is not None:
                with self.lock:
                    self.stats["disk_hits"] += 1
                
                # Promouvoir l'entrée en mémoire pour les prochains accès
                if level is None and entry.level != CacheLevel.DISK:
                    self._set_entry_in_memory(key, entry)
                
                return entry
        
        # Niveau base de données (pour l'instant, non implémenté)
        # TODO: Implémenter le backend de base de données
        
        return entry
    
    def _get_entry_from_memory(self, key: str) -> Optional[CacheEntry]:
        """
        Récupère une entrée du cache mémoire.
        
        Args:
            key: Clé de cache
            
        Returns:
            Entrée de cache ou None si non trouvée
        """
        data = self.memory_cache.retrieve(key)
        if data is None:
            return None
        
        try:
            if isinstance(data, dict):
                return CacheEntry.from_dict(data)
            return data
        except Exception as e:
            self.logger.warning(f"Erreur lors de la désérialisation de l'entrée de cache: {str(e)}")
            return None
    
    def _set_entry(
        self,
        key: str,
        entry: CacheEntry,
        level: Optional[CacheLevel] = None
    ) -> bool:
        """
        Stocke une entrée dans le cache.
        
        Args:
            key: Clé de cache
            entry: Entrée de cache
            level: Niveau de cache à utiliser
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        success = False
        
        # Définir le niveau utilisé
        if entry.level is None:
            entry.level = level or CacheLevel.MEMORY
        
        # Stocker selon le niveau spécifié
        if level is None or level == CacheLevel.MEMORY:
            success = self._set_entry_in_memory(key, entry) or success
        
        if level is None or level == CacheLevel.DISK:
            # Stocker sur disque seulement si TTL > 5 minutes ou politique non "ALWAYS_FRESH"
            if (entry.expires_at is None or 
                entry.expires_at - time.time() > 300 or 
                entry.policy != CachePolicy.ALWAYS_FRESH):
                success = self.disk_cache.set(key, entry) or success
        
        # Niveau base de données (pour l'instant, non implémenté)
        # TODO: Implémenter le backend de base de données
        
        return success
    
    def _set_entry_in_memory(self, key: str, entry: CacheEntry) -> bool:
        """
        Stocke une entrée dans le cache mémoire.
        
        Args:
            key: Clé de cache
            entry: Entrée de cache
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        try:
            if isinstance(entry, CacheEntry):
                # Calculer le TTL restant si l'entrée a une expiration
                ttl = None
                if entry.expires_at is not None:
                    ttl = max(0, int(entry.expires_at - time.time()))
                
                return self.memory_cache.store(key, entry, ttl)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Erreur lors du stockage dans le cache mémoire: {str(e)}")
            return False
    
    def _cleanup_loop(self):
        """Boucle de nettoyage périodique des caches."""
        while True:
            try:
                # Nettoyer le cache disque
                count_disk = self.disk_cache.cleanup_expired()
                if count_disk > 0:
                    self.logger.debug(f"Nettoyé {count_disk} entrées expirées du cache disque")
                
                # Attendre 15 minutes avant le prochain nettoyage
                time.sleep(900)
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de nettoyage: {str(e)}", exc_info=True)
                time.sleep(60)  # Attendre 1 minute avant de réessayer
    
    # Méthodes de chargement de données pour différents types
    # Ces méthodes seront implémentées par les sous-classes ou remplacées
    
    def _load_regulation_data(self) -> Dict[str, Any]:
        """
        Charge les données réglementaires pour le préchargement.
        Par défaut, cette méthode renvoie un dictionnaire vide.
        Elle devrait être surchargée par les implémentations spécifiques.
        
        Returns:
            Dictionnaire de données réglementaires
        """
        self.logger.warning("Méthode _load_regulation_data non implémentée")
        return {}
    
    def _load_climate_data(self) -> Dict[str, Any]:
        """
        Charge les données climatiques pour le préchargement.
        Par défaut, cette méthode renvoie un dictionnaire vide.
        Elle devrait être surchargée par les implémentations spécifiques.
        
        Returns:
            Dictionnaire de données climatiques
        """
        self.logger.warning("Méthode _load_climate_data non implémentée")
        return {}
    
    def _load_geodata_data(self) -> Dict[str, Any]:
        """
        Charge les données géographiques pour le préchargement.
        Par défaut, cette méthode renvoie un dictionnaire vide.
        Elle devrait être surchargée par les implémentations spécifiques.
        
        Returns:
            Dictionnaire de données géographiques
        """
        self.logger.warning("Méthode _load_geodata_data non implémentée")
        return {}
    
    def _load_subsidy_data(self) -> Dict[str, Any]:
        """
        Charge les données de subventions pour le préchargement.
        Par défaut, cette méthode renvoie un dictionnaire vide.
        Elle devrait être surchargée par les implémentations spécifiques.
        
        Returns:
            Dictionnaire de données de subventions
        """
        self.logger.warning("Méthode _load_subsidy_data non implémentée")
        return {}


# Singleton pour l'accès global au cache
_cache_manager_instance = None

def get_cache_manager() -> CacheManager:
    """
    Récupère l'instance unique du gestionnaire de cache (pattern Singleton).
    
    Returns:
        Instance de CacheManager
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    
    return _cache_manager_instance
