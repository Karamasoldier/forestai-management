"""
Service de gestion du cadre réglementaire forestier.

Ce service est responsable de la gestion des réglementations forestières,
notamment le chargement, la recherche et le filtrage des réglementations
applicables à différents types de projets forestiers.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Any, Union
import re

from forestai.core.domain.models.regulation import Regulation, RegulatoryRequirement
from forestai.core.utils.logging_config import LoggingConfig

# Configuration du logger
logger = LoggingConfig.get_instance().get_logger(__name__)

class RegulatoryFrameworkService:
    """
    Service de gestion du cadre réglementaire forestier.
    
    Ce service permet de:
    - Charger les réglementations depuis les fichiers
    - Rechercher des réglementations par critères
    - Récupérer des réglementations spécifiques
    - Filtrer les réglementations applicables à un contexte donné
    """
    
    def __init__(self, data_path: str, preload: bool = True):
        """
        Initialise le service de gestion du cadre réglementaire.
        
        Args:
            data_path: Chemin vers le dossier contenant les données réglementaires
            preload: Si True, charge automatiquement les réglementations à l'initialisation
        """
        self.data_path = data_path
        self.regulations: List[Regulation] = []
        
        if preload:
            self.regulations = self._load_regulations()
            logger.info(f"Service de cadre réglementaire initialisé avec {len(self.regulations)} réglementations")
    
    def _load_regulations(self) -> List[Regulation]:
        """
        Charge les réglementations depuis les fichiers JSON.
        
        Returns:
            Liste des réglementations
        """
        regulations = []
        regulations_path = os.path.join(self.data_path, "regulations.json")
        
        if os.path.exists(regulations_path):
            try:
                with open(regulations_path, 'r', encoding='utf-8') as f:
                    regulations_data = json.load(f)
                
                for reg_data in regulations_data:
                    requirements = []
                    for req_data in reg_data.get("requirements", []):
                        requirement = RegulatoryRequirement(
                            id=req_data.get("id"),
                            description=req_data.get("description"),
                            condition=req_data.get("condition"),
                            threshold=req_data.get("threshold"),
                            category=req_data.get("category"),
                            reference=req_data.get("reference"),
                            severity=req_data.get("severity", "normal")
                        )
                        requirements.append(requirement)
                    
                    regulation = Regulation(
                        id=reg_data.get("id"),
                        name=reg_data.get("name"),
                        description=reg_data.get("description"),
                        applicable_regions=reg_data.get("applicable_regions", []),
                        project_types=reg_data.get("project_types", []),
                        effective_date=datetime.datetime.fromisoformat(reg_data.get("effective_date", "2000-01-01")),
                        requirements=requirements,
                        reference_text=reg_data.get("reference_text"),
                        authority=reg_data.get("authority")
                    )
                    regulations.append(regulation)
                
                logger.info(f"Chargé {len(regulations)} réglementations depuis {regulations_path}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement des réglementations: {e}")
        else:
            logger.warning(f"Fichier de réglementations non trouvé: {regulations_path}")
            # Créer un exemple de fichier de réglementations
            self._create_example_regulations()
            # Recharger les réglementations
            return self._load_regulations()
        
        return regulations
    
    def _create_example_regulations(self):
        """Crée un exemple de fichier de réglementations."""
        example_regulations = [
            {
                "id": "CF-ART-L341-1",
                "name": "Défrichement - Autorisation préalable",
                "description": "Nul ne peut défricher sans autorisation préalable.",
                "applicable_regions": ["*"],
                "project_types": ["defrichement"],
                "effective_date": "2001-07-11",
                "requirements": [
                    {
                        "id": "CF-ART-L341-1-R1",
                        "description": "Tout défrichement nécessite une autorisation préalable",
                        "condition": "project_type == 'defrichement'",
                        "category": "autorisation",
                        "reference": "Article L341-1 du Code Forestier",
                        "severity": "high"
                    }
                ],
                "reference_text": "Article L341-1 du Code Forestier",
                "authority": "DDT/DDTM"
            },
            {
                "id": "CF-ART-L341-6",
                "name": "Défrichement - Compensation obligatoire",
                "description": "L'autorité administrative compétente peut subordonner son autorisation à certaines conditions de compensation.",
                "applicable_regions": ["*"],
                "project_types": ["defrichement"],
                "effective_date": "2014-10-14",
                "requirements": [
                    {
                        "id": "CF-ART-L341-6-R1",
                        "description": "Compensation par reboisement d'une surface au moins équivalente",
                        "condition": "project_type == 'defrichement'",
                        "category": "compensation",
                        "reference": "Article L341-6 du Code Forestier",
                        "severity": "medium"
                    }
                ],
                "reference_text": "Article L341-6 du Code Forestier",
                "authority": "DDT/DDTM"
            },
            {
                "id": "CF-ART-L122-1",
                "name": "Boisement - Document de gestion durable",
                "description": "Les bois et forêts font l'objet d'un document de gestion durable dans certaines conditions.",
                "applicable_regions": ["*"],
                "project_types": ["boisement", "reboisement"],
                "effective_date": "2001-07-11",
                "requirements": [
                    {
                        "id": "CF-ART-L122-1-R1",
                        "description": "Document de gestion durable obligatoire pour les forêts > 25 ha",
                        "condition": "area > 25",
                        "threshold": 25,
                        "category": "document",
                        "reference": "Article L122-1 du Code Forestier",
                        "severity": "medium"
                    }
                ],
                "reference_text": "Article L122-1 du Code Forestier",
                "authority": "CNPF"
            },
            {
                "id": "CF-ART-L124-5",
                "name": "Coupe - Déclaration préalable",
                "description": "Dans les forêts ne présentant pas de garantie de gestion durable, les coupes d'un seul tenant supérieures à un seuil fixé par département doivent faire l'objet d'une déclaration préalable.",
                "applicable_regions": ["*"],
                "project_types": ["coupe"],
                "effective_date": "2001-07-11",
                "requirements": [
                    {
                        "id": "CF-ART-L124-5-R1",
                        "description": "Déclaration préalable pour les coupes > 4 ha",
                        "condition": "area > 4",
                        "threshold": 4,
                        "category": "notification",
                        "reference": "Article L124-5 du Code Forestier",
                        "severity": "medium"
                    }
                ],
                "reference_text": "Article L124-5 du Code Forestier",
                "authority": "DDT/DDTM"
            },
            {
                "id": "CF-ART-L214-13",
                "name": "Forêt publique - Vente de coupes",
                "description": "Les coupes et produits des coupes dans les bois et forêts relevant du régime forestier ne peuvent être vendus que par l'ONF.",
                "applicable_regions": ["*"],
                "project_types": ["coupe", "vente"],
                "effective_date": "2012-07-01",
                "requirements": [
                    {
                        "id": "CF-ART-L214-13-R1",
                        "description": "Commercialisation par l'ONF obligatoire pour les forêts publiques",
                        "condition": "parameters.get('regime_forestier', False) == True",
                        "category": "notification",
                        "reference": "Article L214-13 du Code Forestier",
                        "severity": "high"
                    }
                ],
                "reference_text": "Article L214-13 du Code Forestier",
                "authority": "ONF"
            },
            {
                "id": "CE-ART-L211-1",
                "name": "Protection des eaux - Zone humide",
                "description": "Les zones humides sont protégées en raison de leur rôle dans la préservation de la ressource en eau.",
                "applicable_regions": ["*"],
                "project_types": ["defrichement", "boisement", "reboisement", "coupe"],
                "effective_date": "2006-12-30",
                "requirements": [
                    {
                        "id": "CE-ART-L211-1-R1",
                        "description": "Autorisation spéciale pour les travaux en zone humide",
                        "condition": "parameters.get('zone_humide', False) == True",
                        "category": "autorisation",
                        "reference": "Article L211-1 du Code de l'Environnement",
                        "severity": "high"
                    }
                ],
                "reference_text": "Article L211-1 du Code de l'Environnement",
                "authority": "DREAL"
            },
            {
                "id": "CE-ART-L414-4",
                "name": "Natura 2000 - Évaluation des incidences",
                "description": "Les projets susceptibles d'affecter un site Natura 2000 doivent faire l'objet d'une évaluation des incidences.",
                "applicable_regions": ["*"],
                "project_types": ["defrichement", "boisement", "reboisement"],
                "effective_date": "2010-07-13",
                "requirements": [
                    {
                        "id": "CE-ART-L414-4-R1",
                        "description": "Évaluation des incidences Natura 2000 obligatoire",
                        "condition": "parameters.get('natura_2000', False) == True",
                        "category": "evaluation",
                        "reference": "Article L414-4 du Code de l'Environnement",
                        "severity": "high"
                    }
                ],
                "reference_text": "Article L414-4 du Code de l'Environnement",
                "authority": "DREAL"
            }
        ]
        
        regulations_path = os.path.join(self.data_path, "regulations.json")
        os.makedirs(os.path.dirname(regulations_path), exist_ok=True)
        with open(regulations_path, 'w', encoding='utf-8') as f:
            json.dump(example_regulations, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Créé un exemple de fichier de réglementations à {regulations_path}")
    
    def get_all_regulations(self) -> List[Regulation]:
        """
        Récupère toutes les réglementations disponibles.
        
        Returns:
            Liste de toutes les réglementations
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        return self.regulations
    
    def get_regulation_by_id(self, regulation_id: str) -> Optional[Regulation]:
        """
        Récupère une réglementation par son identifiant.
        
        Args:
            regulation_id: Identifiant de la réglementation
        
        Returns:
            Réglementation trouvée ou None si non trouvée
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        for reg in self.regulations:
            if reg.id == regulation_id:
                return reg
        
        return None
    
    def get_regulations_by_project_type(self, project_type: str) -> List[Regulation]:
        """
        Récupère les réglementations applicables à un type de projet.
        
        Args:
            project_type: Type de projet (boisement, reboisement, defrichement, etc.)
        
        Returns:
            Liste des réglementations applicables
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        return [
            reg for reg in self.regulations
            if not reg.project_types or project_type in reg.project_types
        ]
    
    def get_regulations_by_region(self, region: str) -> List[Regulation]:
        """
        Récupère les réglementations applicables à une région administrative.
        
        Args:
            region: Code de la région administrative
        
        Returns:
            Liste des réglementations applicables
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        return [
            reg for reg in self.regulations
            if "*" in reg.applicable_regions or region in reg.applicable_regions
        ]
    
    def search_regulations(self, query: str) -> List[Regulation]:
        """
        Recherche des réglementations par mot-clé.
        
        Args:
            query: Terme de recherche
        
        Returns:
            Liste des réglementations correspondantes
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        query_lower = query.lower()
        results = []
        
        for reg in self.regulations:
            # Vérifier dans l'identifiant, le nom et la description
            if (query_lower in reg.id.lower() or
                query_lower in reg.name.lower() or
                query_lower in reg.description.lower() or
                (reg.reference_text and query_lower in reg.reference_text.lower()) or
                (reg.authority and query_lower in reg.authority.lower())):
                results.append(reg)
                continue
            
            # Vérifier dans les exigences
            for req in reg.requirements:
                if (req.description and query_lower in req.description.lower()) or \
                   (req.reference and query_lower in req.reference.lower()):
                    results.append(reg)
                    break
        
        return results
    
    def filter_applicable_regulations(self, project_type: str, regions: List[str], parameters: Dict[str, Any] = None) -> List[Regulation]:
        """
        Filtre les réglementations applicables à un projet avec des critères spécifiques.
        
        Args:
            project_type: Type de projet
            regions: Liste des régions concernées
            parameters: Paramètres additionnels du projet
        
        Returns:
            Liste des réglementations applicables
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        applicable = []
        
        # Si aucune région n'est spécifiée, utiliser le caractère générique
        if not regions:
            regions = ["*"]
        
        for reg in self.regulations:
            # Vérifier le type de projet
            project_type_match = not reg.project_types or project_type in reg.project_types
            
            # Vérifier la région
            region_match = False
            for region in regions:
                if "*" in reg.applicable_regions or region in reg.applicable_regions:
                    region_match = True
                    break
            
            if project_type_match and region_match:
                applicable.append(reg)
        
        return applicable
    
    def add_regulation(self, regulation: Regulation) -> bool:
        """
        Ajoute une nouvelle réglementation au système.
        
        Args:
            regulation: Objet réglementation à ajouter
        
        Returns:
            True si l'ajout a réussi, False sinon
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        # Vérifier si l'identifiant existe déjà
        for existing_reg in self.regulations:
            if existing_reg.id == regulation.id:
                logger.warning(f"Une réglementation avec l'identifiant {regulation.id} existe déjà")
                return False
        
        self.regulations.append(regulation)
        
        # Sauvegarder les modifications
        return self._save_regulations()
    
    def update_regulation(self, regulation: Regulation) -> bool:
        """
        Met à jour une réglementation existante.
        
        Args:
            regulation: Objet réglementation avec les modifications
        
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        # Rechercher la réglementation à mettre à jour
        for i, existing_reg in enumerate(self.regulations):
            if existing_reg.id == regulation.id:
                self.regulations[i] = regulation
                # Sauvegarder les modifications
                return self._save_regulations()
        
        logger.warning(f"Réglementation avec l'identifiant {regulation.id} non trouvée pour mise à jour")
        return False
    
    def delete_regulation(self, regulation_id: str) -> bool:
        """
        Supprime une réglementation existante.
        
        Args:
            regulation_id: Identifiant de la réglementation à supprimer
        
        Returns:
            True si la suppression a réussi, False sinon
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        # Rechercher la réglementation à supprimer
        original_length = len(self.regulations)
        self.regulations = [reg for reg in self.regulations if reg.id != regulation_id]
        
        if len(self.regulations) < original_length:
            # Sauvegarder les modifications
            return self._save_regulations()
        else:
            logger.warning(f"Réglementation avec l'identifiant {regulation_id} non trouvée pour suppression")
            return False
    
    def _save_regulations(self) -> bool:
        """
        Sauvegarde les réglementations dans le fichier JSON.
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            regulations_path = os.path.join(self.data_path, "regulations.json")
            
            # Convertir les objets en dictionnaires
            regulations_data = []
            for reg in self.regulations:
                requirements_data = []
                for req in reg.requirements:
                    requirements_data.append({
                        "id": req.id,
                        "description": req.description,
                        "condition": req.condition,
                        "threshold": req.threshold,
                        "category": req.category,
                        "reference": req.reference,
                        "severity": req.severity
                    })
                
                regulations_data.append({
                    "id": reg.id,
                    "name": reg.name,
                    "description": reg.description,
                    "applicable_regions": reg.applicable_regions,
                    "project_types": reg.project_types,
                    "effective_date": reg.effective_date.isoformat(),
                    "requirements": requirements_data,
                    "reference_text": reg.reference_text,
                    "authority": reg.authority
                })
            
            with open(regulations_path, 'w', encoding='utf-8') as f:
                json.dump(regulations_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Sauvegardé {len(self.regulations)} réglementations dans {regulations_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des réglementations: {e}")
            return False
    
    def get_water_protection_regulations(self) -> List[Regulation]:
        """
        Récupère les réglementations liées à la protection des eaux.
        
        Returns:
            Liste des réglementations liées à la protection des eaux
        """
        if not self.regulations:
            self.regulations = self._load_regulations()
        
        # Rechercher par mots-clés liés à l'eau
        water_keywords = ["eau", "water", "hydro", "aqua", "rivière", "cours d'eau", "captage", "zone humide", "humide"]
        
        water_regulations = []
        for reg in self.regulations:
            for keyword in water_keywords:
                if (keyword in reg.name.lower() or 
                    keyword in reg.description.lower() or 
                    (reg.reference_text and keyword in reg.reference_text.lower())):
                    water_regulations.append(reg)
                    break
        
        return water_regulations
