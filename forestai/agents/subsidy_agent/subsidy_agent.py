"""
Implémentation de l'agent de subventions forestières.

Cet agent est responsable de la recherche, de l'analyse et de la génération
de dossiers de subventions pour des projets forestiers.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..base_agent import BaseAgent
from .scrapers.base_scraper import BaseSubsidyScraper
from .scrapers.france_relance_scraper import FranceRelanceScraper
from .document_generation.document_generator import SubsidyDocumentGenerator


class SubsidyAgent(BaseAgent):
    """
    Agent spécialisé dans la recherche et l'analyse des subventions forestières.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'agent de subventions.
        
        Args:
            config: Dictionnaire de configuration contenant:
                - data_dir: Chemin vers le répertoire de données
                - output_dir: Chemin vers le répertoire de sortie
                - cache_subsidies: Booléen indiquant si les subventions doivent être mises en cache
                - cache_duration: Durée de validité du cache en jours
        """
        super().__init__("SubsidyAgent", config)
        
        # Configuration des chemins
        self.data_dir = config.get("data_dir", "data")
        self.output_dir = config.get("output_dir", "outputs")
        self.cache_dir = os.path.join(self.data_dir, "cache", "subsidies")
        self.cache_duration = config.get("cache_duration", 7)  # 7 jours par défaut
        
        # S'assurer que les répertoires existent
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialisation du cache
        self.subsidies_cache = {}
        self.cache_timestamp = None
        self.use_cache = config.get("cache_subsidies", True)
        
        # Initialisation des scrapers
        self.scrapers = []
        self._initialize_scrapers()
        
        # Initialisation du générateur de documents
        self.document_generator = SubsidyDocumentGenerator(
            templates_dir=os.path.join(self.data_dir, "templates"),
            output_dir=self.output_dir
        )
        
        self.logger.info("SubsidyAgent initialisé")

    def _initialize_scrapers(self) -> None:
        """Initialise les scrapers de subventions."""
        self.scrapers = [
            FranceRelanceScraper()
        ]
        self.logger.info(f"Scrapers initialisés: {len(self.scrapers)} scrapers disponibles")
    
    def _execute(self) -> None:
        """
        Implémentation de la logique d'exécution de l'agent.
        """
        self.logger.info("Exécution de l'agent de subventions")
        
        # Traitement des tâches en attente
        while self.is_running and self.tasks_queue:
            task = self.tasks_queue.pop(0)
            self.logger.info(f"Traitement de la tâche: {task.get('type', 'unknown')}")
            
            try:
                self._process_task(task)
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de la tâche: {e}", exc_info=True)
    
    def _process_task(self, task: Dict[str, Any]) -> None:
        """
        Traite une tâche spécifique.
        
        Args:
            task: Dictionnaire contenant les informations de la tâche
        """
        task_type = task.get("type")
        
        if task_type == "search_subsidies":
            self._handle_search_subsidies(task)
        elif task_type == "analyze_eligibility":
            self._handle_analyze_eligibility(task)
        elif task_type == "generate_documents":
            self._handle_generate_documents(task)
        elif task_type == "refresh_cache":
            self._handle_refresh_cache()
        else:
            self.logger.warning(f"Type de tâche inconnu: {task_type}")
    
    def _handle_search_subsidies(self, task: Dict[str, Any]) -> None:
        """
        Recherche les subventions selon les critères spécifiés.
        
        Args:
            task: Tâche contenant les critères de recherche
        """
        project_type = task.get("project_type")
        region = task.get("region")
        owner_type = task.get("owner_type", "all")
        
        self.logger.info(f"Recherche de subventions pour: projet={project_type}, région={region}, propriétaire={owner_type}")
        
        # Récupérer les subventions (du cache ou via les scrapers)
        subsidies = self.search_subsidies(
            project_type=project_type,
            region=region,
            owner_type=owner_type
        )
        
        # Stocker les résultats dans le dictionnaire de résultats de la tâche
        task["results"] = {
            "subsidies": subsidies,
            "count": len(subsidies),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Recherche terminée: {len(subsidies)} subventions trouvées")
    
    def _handle_analyze_eligibility(self, task: Dict[str, Any]) -> None:
        """
        Analyse l'éligibilité d'un projet aux subventions.
        
        Args:
            task: Tâche contenant les informations du projet
        """
        project = task.get("project", {})
        subsidy_id = task.get("subsidy_id")
        
        self.logger.info(f"Analyse d'éligibilité pour le projet: {project.get('type')} (subvention {subsidy_id})")
        
        # Analyser l'éligibilité du projet
        eligibility = self.analyze_eligibility(project, subsidy_id)
        
        # Stocker les résultats
        task["results"] = eligibility
        
        self.logger.info(f"Analyse d'éligibilité terminée: {'éligible' if eligibility['eligible'] else 'non éligible'}")
    
    def _handle_generate_documents(self, task: Dict[str, Any]) -> None:
        """
        Génère les documents de demande de subvention.
        
        Args:
            task: Tâche contenant les informations pour la génération de documents
        """
        project = task.get("project", {})
        subsidy_id = task.get("subsidy_id")
        applicant = task.get("applicant", {})
        output_formats = task.get("output_formats", ["pdf"])
        
        self.logger.info(f"Génération de documents pour le projet: {project.get('type')} (subvention {subsidy_id})")
        
        # Générer les documents
        document_paths = self.generate_application_documents(
            project=project,
            subsidy_id=subsidy_id,
            applicant=applicant,
            output_formats=output_formats
        )
        
        # Stocker les résultats
        task["results"] = {
            "document_paths": document_paths,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Génération de documents terminée: {len(document_paths)} documents générés")
    
    def _handle_refresh_cache(self) -> None:
        """Rafraîchit le cache de subventions."""
        self.logger.info("Rafraîchissement du cache de subventions")
        
        # Forcer le rechargement des subventions en ignorant le cache
        all_subsidies = self._fetch_all_subsidies(ignore_cache=True)
        
        self.logger.info(f"Cache rafraîchi: {len(all_subsidies)} subventions mises en cache")
    
    def search_subsidies(
        self, 
        project_type: Optional[str] = None, 
        region: Optional[str] = None, 
        owner_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche des subventions selon les critères spécifiés.
        
        Args:
            project_type: Type de projet forestier (reboisement, boisement, etc.)
            region: Région administrative
            owner_type: Type de propriétaire (privé, public, etc.)
            
        Returns:
            Liste des subventions correspondant aux critères
        """
        # Récupérer toutes les subventions
        all_subsidies = self._get_subsidies_from_cache_or_fetch()
        
        # Filtrer selon les critères
        filtered_subsidies = all_subsidies
        
        if project_type:
            filtered_subsidies = [
                s for s in filtered_subsidies 
                if project_type.lower() in [p.lower() for p in s.get("eligible_projects", [])]
            ]
        
        if region:
            filtered_subsidies = [
                s for s in filtered_subsidies 
                if (not s.get("regions") or 
                    region.lower() in [r.lower() for r in s.get("regions", [])] or
                    "national" in [r.lower() for r in s.get("regions", [])])
            ]
        
        if owner_type and owner_type != "all":
            filtered_subsidies = [
                s for s in filtered_subsidies 
                if (not s.get("eligible_owners") or 
                    owner_type.lower() in [o.lower() for o in s.get("eligible_owners", [])] or
                    "all" in [o.lower() for o in s.get("eligible_owners", [])])
            ]
        
        return filtered_subsidies
    
    def _get_subsidies_from_cache_or_fetch(self) -> List[Dict[str, Any]]:
        """
        Récupère les subventions du cache ou à partir des scrapers.
        
        Returns:
            Liste des subventions
        """
        # Vérifier si le cache est valide
        cache_file = os.path.join(self.cache_dir, "subsidies.json")
        
        if self.use_cache and os.path.exists(cache_file):
            cache_time = os.path.getmtime(cache_file)
            cache_age_days = (datetime.now().timestamp() - cache_time) / (60 * 60 * 24)
            
            if cache_age_days < self.cache_duration:
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        self.logger.info(f"Utilisation du cache de subventions (âge: {cache_age_days:.1f} jours)")
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.warning(f"Erreur lors de la lecture du cache: {e}")
        
        # Si on arrive ici, il faut rafraîchir le cache
        return self._fetch_all_subsidies()
    
    def _fetch_all_subsidies(self, ignore_cache: bool = False) -> List[Dict[str, Any]]:
        """
        Récupère toutes les subventions à partir des scrapers et met à jour le cache.
        
        Args:
            ignore_cache: Forcer le rechargement même si le cache est valide
            
        Returns:
            Liste des subventions
        """
        self.logger.info("Récupération des subventions à partir des scrapers")
        
        all_subsidies = []
        
        # Récupérer les subventions de chaque scraper
        for scraper in self.scrapers:
            try:
                self.logger.info(f"Exécution du scraper: {scraper.name}")
                subsidies = scraper.fetch_subsidies()
                all_subsidies.extend(subsidies)
                self.logger.info(f"Scraper {scraper.name}: {len(subsidies)} subventions récupérées")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution du scraper {scraper.name}: {e}", exc_info=True)
        
        # Mettre à jour le cache
        if self.use_cache:
            cache_file = os.path.join(self.cache_dir, "subsidies.json")
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(all_subsidies, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Cache de subventions mis à jour: {len(all_subsidies)} subventions")
            except IOError as e:
                self.logger.error(f"Erreur lors de l'écriture du cache: {e}", exc_info=True)
        
        return all_subsidies
    
    def analyze_eligibility(
        self, 
        project: Dict[str, Any], 
        subsidy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyse l'éligibilité d'un projet à une ou plusieurs subventions.
        
        Args:
            project: Informations sur le projet
            subsidy_id: Identifiant de la subvention à analyser (optionnel)
            
        Returns:
            Résultat de l'analyse d'éligibilité
        """
        self.logger.info(f"Analyse d'éligibilité pour le projet de type {project.get('type', 'inconnu')}")
        
        # Récupérer les subventions
        all_subsidies = self._get_subsidies_from_cache_or_fetch()
        
        # Si un subsidy_id est fourni, filtrer la liste
        if subsidy_id:
            subsidies = [s for s in all_subsidies if s.get("id") == subsidy_id]
            if not subsidies:
                return {
                    "eligible": False,
                    "error": f"Subvention introuvable: {subsidy_id}",
                    "timestamp": datetime.now().isoformat()
                }
            subsidy = subsidies[0]
            result = self._analyze_single_eligibility(project, subsidy)
            return result
        
        # Sinon, analyser toutes les subventions
        results = []
        for subsidy in all_subsidies:
            result = self._analyze_single_eligibility(project, subsidy)
            if result["eligible"]:
                results.append({
                    "subsidy_id": subsidy.get("id"),
                    "subsidy_title": subsidy.get("title"),
                    "eligibility": result
                })
        
        return {
            "eligible_count": len(results),
            "eligible_subsidies": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_single_eligibility(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyse l'éligibilité d'un projet pour une subvention spécifique.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse d'éligibilité
        """
        self.logger.debug(f"Analyse de l'éligibilité pour la subvention {subsidy.get('id')}")
        
        eligibility_conditions = []
        is_eligible = True
        
        # Vérification du type de projet
        project_type = project.get("type", "").lower()
        eligible_projects = [p.lower() for p in subsidy.get("eligible_projects", [])]
        
        project_eligible = (
            not eligible_projects or 
            project_type in eligible_projects or 
            "all" in eligible_projects
        )
        
        eligibility_conditions.append({
            "condition": "Type de projet éligible",
            "satisfied": project_eligible,
            "details": f"Type de projet: {project_type}"
        })
        
        if not project_eligible:
            is_eligible = False
        
        # Vérification de la localisation
        location = project.get("location", "")
        region = project.get("region", "")
        eligible_regions = [r.lower() for r in subsidy.get("regions", [])]
        
        region_eligible = (
            not eligible_regions or 
            region.lower() in eligible_regions or 
            "national" in eligible_regions
        )
        
        eligibility_conditions.append({
            "condition": "Région éligible",
            "satisfied": region_eligible,
            "details": f"Région: {region}"
        })
        
        if not region_eligible:
            is_eligible = False
        
        # Vérification de la superficie
        area_ha = project.get("area_ha", 0)
        min_area = subsidy.get("min_area_ha", 0)
        max_area = subsidy.get("max_area_ha", float("inf"))
        
        area_eligible = area_ha >= min_area and (max_area == float("inf") or area_ha <= max_area)
        
        eligibility_conditions.append({
            "condition": "Superficie éligible",
            "satisfied": area_eligible,
            "details": f"Superficie: {area_ha} ha (min: {min_area} ha, max: {max_area if max_area != float('inf') else 'non spécifié'} ha)"
        })
        
        if not area_eligible:
            is_eligible = False
        
        # Vérification des espèces
        species = project.get("species", [])
        eligible_species = subsidy.get("eligible_species", [])
        
        species_eligible = (
            not eligible_species or 
            any(s in eligible_species for s in species) or 
            "all" in eligible_species
        )
        
        eligibility_conditions.append({
            "condition": "Espèces éligibles",
            "satisfied": species_eligible,
            "details": f"Espèces: {', '.join(species)}"
        })
        
        if not species_eligible:
            is_eligible = False
        
        # Vérification de la date limite
        deadline = subsidy.get("deadline")
        if deadline:
            deadline_date = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            current_date = datetime.now()
            deadline_eligible = current_date <= deadline_date
            
            eligibility_conditions.append({
                "condition": "Date limite respectée",
                "satisfied": deadline_eligible,
                "details": f"Date limite: {deadline_date.strftime('%d/%m/%Y')}"
            })
            
            if not deadline_eligible:
                is_eligible = False
        
        # Résultat final
        return {
            "eligible": is_eligible,
            "subsidy_id": subsidy.get("id"),
            "subsidy_title": subsidy.get("title"),
            "conditions": eligibility_conditions,
            "next_steps": subsidy.get("application_process", []) if is_eligible else [],
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_application_documents(
        self,
        project: Dict[str, Any],
        subsidy_id: str,
        applicant: Dict[str, Any],
        output_formats: List[str] = ["pdf"]
    ) -> Dict[str, str]:
        """
        Génère les documents de demande de subvention.
        
        Args:
            project: Informations sur le projet
            subsidy_id: Identifiant de la subvention
            applicant: Informations sur le demandeur
            output_formats: Formats de sortie souhaités (pdf, html, docx)
            
        Returns:
            Dictionnaire des chemins des documents générés par format
        """
        self.logger.info(f"Génération de documents de demande pour la subvention {subsidy_id}")
        
        # Récupérer les informations de la subvention
        all_subsidies = self._get_subsidies_from_cache_or_fetch()
        subsidies = [s for s in all_subsidies if s.get("id") == subsidy_id]
        
        if not subsidies:
            self.logger.error(f"Subvention introuvable: {subsidy_id}")
            return {}
        
        subsidy = subsidies[0]
        
        # Vérifier l'éligibilité
        eligibility = self._analyze_single_eligibility(project, subsidy)
        
        if not eligibility["eligible"]:
            self.logger.warning(f"Le projet n'est pas éligible à la subvention {subsidy_id}")
            return {}
        
        # Préparer les données pour les documents
        document_data = {
            "subsidy": subsidy,
            "project": project,
            "applicant": applicant,
            "application_date": datetime.now().strftime("%d/%m/%Y"),
            "eligibility": eligibility
        }
        
        # Générer les documents dans les formats demandés
        output_paths = {}
        
        for format_type in output_formats:
            try:
                if format_type.lower() == "pdf":
                    output_path = self.document_generator.generate_pdf(document_data, subsidy_id)
                    output_paths["pdf"] = output_path
                elif format_type.lower() == "html":
                    output_path = self.document_generator.generate_html(document_data, subsidy_id)
                    output_paths["html"] = output_path
                elif format_type.lower() == "docx":
                    output_path = self.document_generator.generate_docx(document_data, subsidy_id)
                    output_paths["docx"] = output_path
                else:
                    self.logger.warning(f"Format non supporté: {format_type}")
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération du document {format_type}: {e}", exc_info=True)
        
        return output_paths
    
    def get_subsidy_by_id(self, subsidy_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'une subvention par son identifiant.
        
        Args:
            subsidy_id: Identifiant de la subvention
            
        Returns:
            Informations sur la subvention ou None si non trouvée
        """
        all_subsidies = self._get_subsidies_from_cache_or_fetch()
        subsidies = [s for s in all_subsidies if s.get("id") == subsidy_id]
        
        if not subsidies:
            return None
        
        return subsidies[0]
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Génère un rapport sur l'état de l'agent.
        
        Returns:
            Dictionnaire contenant les informations d'état
        """
        status = super().get_status()
        
        # Ajouter des informations spécifiques
        all_subsidies = self._get_subsidies_from_cache_or_fetch()
        
        # Statistiques sur les subventions
        status.update({
            "subsidies_count": len(all_subsidies),
            "cache_status": "actif" if self.use_cache else "inactif",
            "scrapers_count": len(self.scrapers),
            "scrapers": [scraper.name for scraper in self.scrapers]
        })
        
        return status
