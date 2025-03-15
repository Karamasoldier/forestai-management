"""
Utilitaires de cache pour simplifier l'utilisation du système de cache.

Ce module fournit des décorateurs et des fonctions auxiliaires pour 
faciliter l'utilisation du cache dans différents contextes.
"""

import functools
import inspect
import logging
import json
import hashlib
from typing import Callable, Dict, Any, Optional, Type, List, Union

from forestai.core.infrastructure.cache.base import CacheType, CachePolicy, CacheLevel
from forestai.core.infrastructure.cache.cache_manager import get_cache_manager


logger = logging.getLogger(__name__)


def cached(
    data_type: CacheType,
    identifier_key: Optional[str] = None,
    policy: CachePolicy = CachePolicy.DAILY,
    level: Optional[CacheLevel] = None,
    max_age: Optional[int] = None,
    key_prefix: Optional[str] = None,
    ignore_args: Optional[List[str]] = None
):
    """
    Décorateur pour mettre en cache les résultats de fonctions ou méthodes.
    
    Args:
        data_type: Type de données
        identifier_key: Nom du paramètre à utiliser comme identifiant (par défaut: premier argument)
        policy: Politique de mise à jour
        level: Niveau de cache à utiliser
        max_age: Âge maximum en secondes (remplace policy si spécifié)
        key_prefix: Préfixe optionnel pour l'identifiant
        ignore_args: Liste des noms de paramètres à ignorer pour le cache
        
    Returns:
        Décorateur de fonction
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Récupérer les informations sur les paramètres de la fonction
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Déterminer l'identifiant
            identifier = None
            if identifier_key is not None:
                # Utiliser le paramètre spécifié comme identifiant
                if identifier_key in bound_args.arguments:
                    identifier = str(bound_args.arguments[identifier_key])
            else:
                # Utiliser le premier argument comme identifiant
                if len(bound_args.arguments) > 0:
                    first_arg_name = list(bound_args.arguments.keys())[0]
                    # Ignorer 'self' pour les méthodes de classe
                    if first_arg_name == 'self':
                        if len(bound_args.arguments) > 1:
                            second_arg_name = list(bound_args.arguments.keys())[1]
                            identifier = str(bound_args.arguments[second_arg_name])
                    else:
                        identifier = str(bound_args.arguments[first_arg_name])
            
            # Si aucun identifiant n'a pu être déterminé, utiliser le nom de la fonction
            if identifier is None:
                identifier = func.__name__
            
            # Appliquer le préfixe si spécifié
            if key_prefix is not None:
                identifier = f"{key_prefix}:{identifier}"
            
            # Créer un dictionnaire de paramètres pour le cache
            cache_params = {}
            for name, value in bound_args.arguments.items():
                # Ignorer les paramètres spécifiés
                if ignore_args and name in ignore_args:
                    continue
                
                # Ignorer 'self' pour les méthodes de classe
                if name == 'self':
                    continue
                
                # Ignorer le paramètre utilisé comme identifiant
                if identifier_key is not None and name == identifier_key:
                    continue
                
                # Essayer de sérialiser la valeur
                try:
                    # Pour les objets non-sérialisables, utiliser leur représentation en chaîne
                    if isinstance(value, (int, float, bool, str, type(None))):
                        cache_params[name] = value
                    else:
                        # Pour les objets complexes, utiliser un hash de leur représentation
                        obj_str = str(value)
                        cache_params[name] = hashlib.md5(obj_str.encode('utf-8')).hexdigest()
                except (TypeError, ValueError) as e:
                    logger.warning(f"Impossible de sérialiser le paramètre '{name}': {str(e)}")
            
            # Essayer de récupérer depuis le cache
            result = cache_manager.get(
                data_type=data_type,
                identifier=identifier,
                params=cache_params,
                policy=policy,
                max_age=max_age,
                level=level,
                refresh_callback=lambda: func(*args, **kwargs)
            )
            
            return result
        
        return wrapper
    
    return decorator


def invalidate_cache(
    data_type: CacheType,
    identifier: str,
    params: Optional[Dict[str, Any]] = None
):
    """
    Invalide manuellement une entrée de cache.
    
    Args:
        data_type: Type de données
        identifier: Identifiant principal
        params: Paramètres additionnels
    """
    cache_manager = get_cache_manager()
    return cache_manager.delete(data_type, identifier, params)


def clear_cache_type(data_type: CacheType, older_than: Optional[int] = None):
    """
    Nettoie un type de données spécifique du cache.
    
    Args:
        data_type: Type de données à nettoyer
        older_than: Âge minimum en secondes pour suppression
    """
    cache_manager = get_cache_manager()
    return cache_manager.clear(data_type, older_than)


def preload_cache(data_type: CacheType, data_loader: Callable[[], Dict[str, Any]], policy: CachePolicy = CachePolicy.DAILY):
    """
    Précharge des données dans le cache.
    
    Args:
        data_type: Type de données
        data_loader: Fonction de chargement des données
        policy: Politique de mise à jour
    """
    cache_manager = get_cache_manager()
    return cache_manager.preload(data_type, data_loader, policy)


def get_cache_stats():
    """
    Récupère les statistiques d'utilisation du cache.
    
    Returns:
        Dictionnaire des statistiques
    """
    cache_manager = get_cache_manager()
    return cache_manager.get_stats()


class CachedProperty:
    """
    Décorateur similar à @property mais avec mise en cache du résultat.
    
    Exemple:
        class MyClass:
            @CachedProperty(CacheType.GENERIC, CachePolicy.DAILY)
            def expensive_computation(self):
                # Calcul coûteux...
                return result
    """
    
    def __init__(
        self,
        data_type: CacheType,
        policy: CachePolicy = CachePolicy.DAILY,
        level: Optional[CacheLevel] = None
    ):
        """
        Initialise le décorateur.
        
        Args:
            data_type: Type de données
            policy: Politique de mise à jour
            level: Niveau de cache à utiliser
        """
        self.data_type = data_type
        self.policy = policy
        self.level = level
        self.func = None
        self.name = None
    
    def __set_name__(self, owner, name):
        """
        Appelé automatiquement par Python quand la propriété est assignée à une classe.
        
        Args:
            owner: Classe propriétaire
            name: Nom de l'attribut
        """
        self.name = name
        self.func_name = name
    
    def __get__(self, instance, owner=None):
        """
        Appelé quand la propriété est accédée.
        
        Args:
            instance: Instance de l'objet
            owner: Classe propriétaire
            
        Returns:
            Résultat de la fonction mise en cache
        """
        if instance is None:
            return self
        
        # Générer un identifiant unique pour cette propriété sur cette instance
        identifier = f"{instance.__class__.__name__}:{id(instance)}:{self.name}"
        
        # Récupérer ou calculer la valeur
        cache_manager = get_cache_manager()
        return cache_manager.get(
            data_type=self.data_type,
            identifier=identifier,
            policy=self.policy,
            level=self.level,
            refresh_callback=lambda: self.func(instance)
        )
    
    def __call__(self, func):
        """
        Appelé quand le décorateur est utilisé.
        
        Args:
            func: Fonction à décorer
            
        Returns:
            Self pour le comportement de descripteur
        """
        self.func = func
        functools.update_wrapper(self, func)
        self.func_name = func.__name__
        return self


def cache_key_from_args(*args, **kwargs) -> str:
    """
    Génère une clé de cache à partir des arguments.
    
    Args:
        *args: Arguments positionnels
        **kwargs: Arguments nommés
        
    Returns:
        Clé de cache sous forme de chaîne
    """
    # Convertir tous les arguments en une chaîne JSON triée
    key_parts = []
    
    # Ajouter les arguments positionnels
    for arg in args:
        try:
            if isinstance(arg, (int, float, bool, str, type(None))):
                key_parts.append(str(arg))
            else:
                # Pour les objets complexes, utiliser un hash
                obj_str = str(arg)
                key_parts.append(hashlib.md5(obj_str.encode('utf-8')).hexdigest())
        except Exception:
            key_parts.append("non_serializable")
    
    # Ajouter les arguments nommés (triés par nom)
    sorted_kwargs = sorted(kwargs.items())
    for name, value in sorted_kwargs:
        try:
            if isinstance(value, (int, float, bool, str, type(None))):
                key_parts.append(f"{name}={value}")
            else:
                # Pour les objets complexes, utiliser un hash
                obj_str = str(value)
                key_parts.append(f"{name}={hashlib.md5(obj_str.encode('utf-8')).hexdigest()}")
        except Exception:
            key_parts.append(f"{name}=non_serializable")
    
    # Joindre toutes les parties avec un séparateur
    return ":".join(key_parts)


def memoize(func):
    """
    Décorateur qui met en cache les résultats d'une fonction en mémoire.
    Ne persiste pas entre les redémarrages.
    
    Args:
        func: Fonction à décorer
        
    Returns:
        Fonction décorée
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Générer une clé de cache
        key = cache_key_from_args(*args, **kwargs)
        
        # Vérifier si le résultat est déjà en cache
        if key in cache:
            return cache[key]
        
        # Calculer et mettre en cache
        result = func(*args, **kwargs)
        cache[key] = result
        return result
    
    # Ajouter une méthode pour vider le cache
    wrapper.clear_cache = lambda: cache.clear()
    
    return wrapper


class BatchCacheLoader:
    """
    Utilitaire pour charger des données en batch dans le cache.
    Utile pour précharger des données volumineuses de manière contrôlée.
    """
    
    def __init__(
        self, 
        data_type: CacheType,
        policy: CachePolicy = CachePolicy.DAILY,
        level: Optional[CacheLevel] = None,
        batch_size: int = 100
    ):
        """
        Initialise le chargeur de cache par batch.
        
        Args:
            data_type: Type de données
            policy: Politique de mise à jour
            level: Niveau de cache à utiliser
            batch_size: Taille des batches pour le chargement
        """
        self.data_type = data_type
        self.policy = policy
        self.level = level
        self.batch_size = batch_size
        self.cache_manager = get_cache_manager()
        self.total_loaded = 0
    
    def load_batch(self, data_dict: Dict[str, Any]) -> int:
        """
        Charge un batch de données dans le cache.
        
        Args:
            data_dict: Dictionnaire de données (identifiant -> données)
            
        Returns:
            Nombre d'entrées chargées
        """
        count = 0
        
        # Charger chaque entrée
        for identifier, data in data_dict.items():
            if self.cache_manager.set(
                data_type=self.data_type,
                identifier=str(identifier),
                data=data,
                policy=self.policy,
                level=self.level,
                metadata={"batch_loaded": True}
            ):
                count += 1
        
        self.total_loaded += count
        return count
    
    def load_from_generator(self, data_generator: Callable[[], Dict[str, Any]]) -> int:
        """
        Charge des données depuis un générateur en plusieurs batches.
        
        Args:
            data_generator: Générateur produisant des dictionnaires de données
            
        Returns:
            Nombre total d'entrées chargées
        """
        total = 0
        batch = {}
        batch_count = 0
        
        for identifier, data in data_generator():
            batch[str(identifier)] = data
            batch_count += 1
            
            # Charger le batch quand il atteint la taille limite
            if batch_count >= self.batch_size:
                total += self.load_batch(batch)
                batch = {}
                batch_count = 0
        
        # Charger le dernier batch partiellement rempli
        if batch_count > 0:
            total += self.load_batch(batch)
        
        return total


def force_refresh(
    data_type: CacheType,
    identifier: str,
    params: Optional[Dict[str, Any]] = None,
    refresh_func: Callable[[], Any],
    policy: CachePolicy = CachePolicy.DAILY,
    level: Optional[CacheLevel] = None
) -> Any:
    """
    Force le rafraîchissement d'une entrée de cache.
    
    Args:
        data_type: Type de données
        identifier: Identifiant principal
        params: Paramètres additionnels
        refresh_func: Fonction pour générer les nouvelles données
        policy: Politique de mise à jour
        level: Niveau de cache à utiliser
        
    Returns:
        Données fraîchement chargées
    """
    cache_manager = get_cache_manager()
    
    # Supprimer l'entrée existante
    cache_manager.delete(data_type, identifier, params)
    
    # Générer de nouvelles données
    fresh_data = refresh_func()
    
    # Mettre en cache et retourner
    cache_manager.set(
        data_type=data_type,
        identifier=identifier,
        data=fresh_data,
        params=params,
        policy=policy,
        level=level,
        metadata={"forced_refresh": True}
    )
    
    return fresh_data
