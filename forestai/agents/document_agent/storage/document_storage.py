# -*- coding: utf-8 -*-
"""
Module de stockage des documents pour le DocumentAgent.

Ce module fournit les fonctionnalités pour stocker, récupérer et gérer
les documents générés par le DocumentAgent.
"""

import os
import logging
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentStorage:
    """
    Gestionnaire de stockage des documents générés.
    
    Cette classe s'occupe du stockage, de la récupération et de la gestion
    des documents générés par le DocumentAgent.
    """
    
    def __init__(self, base_dir: str, max_retention_days: int = 365):
        """
        Initialise le gestionnaire de stockage de documents.
        
        Args:
            base_dir: Répertoire de base pour le stockage
            max_retention_days: Nombre maximal de jours de rétention des documents
        """
        self.base_dir = Path(base_dir)
        self.max_retention_days = max_retention_days
        
        # Créer le répertoire de base s'il n'existe pas
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Définir les sous-répertoires par type de document
        self.contract_dir = self.base_dir / "contracts"
        self.specification_dir = self.base_dir / "specifications"
        self.management_plan_dir = self.base_dir / "management_plans"
        self.administrative_dir = self.base_dir / "administrative"
        self.reports_dir = self.base_dir / "reports"
        
        # Créer les sous-répertoires s'ils n'existent pas
        for directory in [self.contract_dir, self.specification_dir, 
                         self.management_plan_dir, self.administrative_dir,
                         self.reports_dir]:
            directory.mkdir(exist_ok=True)
        
        # Créer un sous-répertoire par année et mois
        current_date = datetime.now()
        self.year_dir = str(current_date.year)
        self.month_dir = f"{current_date.month:02d}"
        
        for directory in [self.contract_dir, self.specification_dir, 
                         self.management_plan_dir, self.administrative_dir,
                         self.reports_dir]:
            (directory / self.year_dir / self.month_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DocumentStorage initialisé avec répertoire de base: {self.base_dir}")
    
    def _get_storage_path(self, document_type: str) -> Path:
        """
        Détermine le chemin de stockage en fonction du type de document.
        
        Args:
            document_type: Type de document (contract, specification, management_plan, administrative, report)
            
        Returns:
            Chemin du répertoire de stockage
        """
        document_type = document_type.lower()
        
        if "contract" in document_type:
            return self.contract_dir / self.year_dir / self.month_dir
        elif "spec" in document_type:
            return self.specification_dir / self.year_dir / self.month_dir
        elif "management" in document_type or "plan" in document_type:
            return self.management_plan_dir / self.year_dir / self.month_dir
        elif "admin" in document_type:
            return self.administrative_dir / self.year_dir / self.month_dir
        elif "report" in document_type:
            return self.reports_dir / self.year_dir / self.month_dir
        else:
            # Par défaut, utiliser le répertoire de base
            return self.base_dir / self.year_dir / self.month_dir
    
    def store(self, content: Union[str, bytes], filename: str, 
              document_type: str = "custom") -> Path:
        """
        Stocke un document dans le système de fichiers.
        
        Args:
            content: Contenu du document (texte ou binaire)
            filename: Nom du fichier
            document_type: Type de document
            
        Returns:
            Chemin du fichier stocké
        """
        # Déterminer le répertoire de stockage
        storage_dir = self._get_storage_path(document_type)
        
        # S'assurer que le répertoire existe
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer un nom de fichier unique si nécessaire
        if not filename:
            # Utiliser un hachage du contenu + timestamp
            content_hash = hashlib.md5(content.encode() if isinstance(content, str) else content).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = "txt"  # extension par défaut
            filename = f"{document_type}_{timestamp}_{content_hash}.{extension}"
        
        # Chemin complet du fichier
        file_path = storage_dir / filename
        
        # Écrire le contenu dans le fichier
        try:
            if isinstance(content, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(file_path, 'wb') as f:
                    f.write(content)
            
            logger.info(f"Document stocké avec succès: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erreur lors du stockage du document {filename}: {str(e)}")
            raise
    
    def retrieve(self, file_path: Union[str, Path]) -> Union[str, bytes]:
        """
        Récupère un document du système de fichiers.
        
        Args:
            file_path: Chemin du fichier à récupérer
            
        Returns:
            Contenu du document (texte ou binaire)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Document non trouvé: {file_path}")
            raise FileNotFoundError(f"Document non trouvé: {file_path}")
        
        try:
            # Déterminer si le fichier est binaire ou texte
            is_binary = self._is_binary_file(file_path)
            
            if is_binary:
                with open(file_path, 'rb') as f:
                    return f.read()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du document {file_path}: {str(e)}")
            raise
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """
        Détermine si un fichier est binaire ou texte.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            True si le fichier est binaire, False sinon
        """
        # Vérifier l'extension du fichier
        binary_extensions = ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.zip']
        extension = file_path.suffix.lower()
        
        if extension in binary_extensions:
            return True
        
        # Si l'extension n'est pas dans la liste, vérifier le contenu
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Essayer de lire comme du texte
            return False  # Si pas d'erreur, c'est un fichier texte
        except UnicodeDecodeError:
            return True  # Si erreur de décodage, c'est un fichier binaire
    
    def list_documents(self, document_type: Optional[str] = None, 
                      max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Liste les documents stockés, éventuellement filtrés par type.
        
        Args:
            document_type: Type de document pour filtrer (optionnel)
            max_results: Nombre maximal de résultats à retourner
            
        Returns:
            Liste de dictionnaires avec les métadonnées des documents
        """
        results = []
        
        # Déterminer les répertoires à parcourir
        if document_type:
            # Filtrer par type de document
            base_dir = self._get_storage_path(document_type)
            directories = [base_dir]
        else:
            # Parcourir tous les répertoires
            directories = [
                self.contract_dir / self.year_dir / self.month_dir,
                self.specification_dir / self.year_dir / self.month_dir,
                self.management_plan_dir / self.year_dir / self.month_dir,
                self.administrative_dir / self.year_dir / self.month_dir,
                self.reports_dir / self.year_dir / self.month_dir
            ]
        
        # Parcourir les répertoires
        for directory in directories:
            if not directory.exists():
                continue
            
            for file_path in directory.glob("**/*"):
                if file_path.is_file():
                    # Extraire les métadonnées du fichier
                    stat = file_path.stat()
                    document_info = {
                        "path": str(file_path),
                        "filename": file_path.name,
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "document_type": self._guess_document_type(file_path),
                        "format": file_path.suffix.lstrip('.')
                    }
                    
                    results.append(document_info)
                    
                    # Limiter le nombre de résultats
                    if len(results) >= max_results:
                        break
            
            # Limiter le nombre de résultats
            if len(results) >= max_results:
                break
        
        return results
    
    def _guess_document_type(self, file_path: Path) -> str:
        """
        Devine le type de document en fonction de son emplacement.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Type de document deviné
        """
        path_str = str(file_path).lower()
        
        if "contract" in path_str:
            return "contract"
        elif "spec" in path_str:
            return "specification"
        elif "management" in path_str or "plan" in path_str:
            return "management_plan"
        elif "admin" in path_str:
            return "administrative"
        elif "report" in path_str:
            return "report"
        else:
            return "custom"
    
    def delete(self, file_path: Union[str, Path]) -> bool:
        """
        Supprime un document du système de fichiers.
        
        Args:
            file_path: Chemin du fichier à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"Document à supprimer non trouvé: {file_path}")
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Document supprimé avec succès: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document {file_path}: {str(e)}")
            return False
    
    def clean_old_documents(self, max_age_days: Optional[int] = None) -> int:
        """
        Nettoie les documents plus anciens qu'un certain âge.
        
        Args:
            max_age_days: Âge maximal en jours (par défaut: max_retention_days)
            
        Returns:
            Nombre de documents supprimés
        """
        if max_age_days is None:
            max_age_days = self.max_retention_days
        
        # Calcul de la date limite
        cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        deleted_count = 0
        
        # Parcourir tous les répertoires de documents
        for directory in [self.contract_dir, self.specification_dir, 
                         self.management_plan_dir, self.administrative_dir,
                         self.reports_dir]:
            
            if not directory.exists():
                continue
            
            for file_path in directory.glob("**/*"):
                if file_path.is_file():
                    # Vérifier la date de modification
                    mod_time = file_path.stat().st_mtime
                    
                    if mod_time < cutoff_date:
                        # Supprimer le fichier
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.error(f"Erreur lors de la suppression de {file_path}: {str(e)}")
        
        logger.info(f"Nettoyage terminé: {deleted_count} documents supprimés")
        return deleted_count
