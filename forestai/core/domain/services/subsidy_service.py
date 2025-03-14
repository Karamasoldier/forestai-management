"""
Service de gestion des subventions pour ForestAI.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class SubsidyService:
    """
    Service de gestion des subventions pour l'analyse d'éligibilité et la recherche de financements.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le service de subventions.
        
        Args:
            config: Configuration du service
        """
        self.config = config
        
        # Configure les chemins
        self.data_path = config.get('DATA_PATH', os.path.join(os.getcwd(), 'data'))
        self.cache_path = os.path.join(self.data_path, 'cache', 'subsidies')
        self.templates_path = config.get('SUBSIDY_TEMPLATES_DIR', 
                                         os.path.join(self.data_path, 'templates'))
        self.output_path = config.get('OUTPUT_PATH', os.path.join(self.data_path, 'outputs'))
        
        # Durée de validité du cache en jours
        self.cache_duration = int(config.get('SUBSIDY_CACHE_DURATION', 7))
        
        # Crée les répertoires nécessaires s'ils n'existent pas
        os.makedirs(self.cache_path, exist_ok=True)
        os.makedirs(self.templates_path, exist_ok=True)
        os.makedirs(os.path.join(self.output_path, 'subsidies'), exist_ok=True)
        
        logger.info(f"SubsidyService initialized with cache_path={self.cache_path}, "
                   f"templates_path={self.templates_path}, cache_duration={self.cache_duration} days")
    
    def search_subsidies(self, project_type: str, region: Optional[str] = None, 
                         owner_type: Optional[str] = None, priority_zones: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Recherche des subventions adaptées à un projet forestier.
        
        Args:
            project_type: Type de projet (reboisement, boisement, etc.)
            region: Région administrative (optionnel)
            owner_type: Type de propriétaire (privé, public, etc.) (optionnel)
            priority_zones: Liste des zones prioritaires identifiées (optionnel)
            
        Returns:
            Liste des subventions disponibles
        """
        logger.info(f"Searching subsidies for project_type={project_type}, region={region}, "
                   f"owner_type={owner_type}, priority_zones={priority_zones is not None}")
        
        # Charge les subventions depuis le cache
        subsidies = self._load_subsidies_from_cache()
        
        # Filtre les subventions selon les critères
        filtered_subsidies = []
        for subsidy in subsidies:
            # Vérifie le type de projet
            if project_type not in subsidy.get("project_types", []):
                continue
            
            # Vérifie la région si spécifiée
            if region and region not in subsidy.get("regions", ["*"]) and "*" not in subsidy.get("regions", []):
                continue
            
            # Vérifie le type de propriétaire si spécifié
            if owner_type and owner_type not in subsidy.get("owner_types", ["*"]) and "*" not in subsidy.get("owner_types", []):
                continue
            
            # Vérifie si la subvention est encore valide
            deadline = subsidy.get("deadline")
            if deadline:
                deadline_date = datetime.datetime.strptime(deadline, "%Y-%m-%d")
                if deadline_date < datetime.datetime.now():
                    continue
            
            # Ajoute des informations sur la priorité si des zones prioritaires sont fournies
            if priority_zones:
                subsidy["priority_match"] = self._check_priority_match(subsidy, priority_zones)
            
            filtered_subsidies.append(subsidy)
        
        # Trie les subventions par pertinence
        if priority_zones:
            filtered_subsidies.sort(key=lambda s: s.get("priority_match", {}).get("score", 0), reverse=True)
        
        return filtered_subsidies
    
    def analyze_eligibility(self, project: Dict[str, Any], subsidy_id: str) -> Dict[str, Any]:
        """
        Analyse l'éligibilité d'un projet à une subvention.
        
        Args:
            project: Données du projet forestier
            subsidy_id: Identifiant de la subvention
            
        Returns:
            Résultat de l'analyse d'éligibilité
        """
        logger.info(f"Analyzing eligibility for project={project}, subsidy_id={subsidy_id}")
        
        # Charge les données de la subvention
        subsidies = self._load_subsidies_from_cache()
        subsidy = next((s for s in subsidies if s["id"] == subsidy_id), None)
        
        if not subsidy:
            return {
                "eligible": False,
                "error": f"Subsidy with ID {subsidy_id} not found"
            }
        
        # Vérifie les critères d'éligibilité de base
        basic_eligibility, reasons = self._check_basic_eligibility(project, subsidy)
        
        if not basic_eligibility:
            return {
                "eligible": False,
                "reasons": reasons
            }
        
        # Vérifie les critères spécifiques
        specific_eligibility, details = self._check_specific_eligibility(project, subsidy)
        
        # Calcule le score d'éligibilité (0-100)
        eligibility_score = self._calculate_eligibility_score(project, subsidy, details)
        
        # Vérifie si des zones prioritaires sont concernées
        priority_bonus = self._calculate_priority_bonus(project, subsidy)
        
        result = {
            "eligible": specific_eligibility,
            "eligibility_score": eligibility_score,
            "details": details
        }
        
        if priority_bonus > 0:
            result["priority_bonus"] = priority_bonus
        
        return result
    
    def generate_application(self, project: Dict[str, Any], subsidy_id: str, 
                             applicant: Dict[str, Any], output_formats: List[str]) -> Dict[str, str]:
        """
        Génère les documents de demande de subvention.
        
        Args:
            project: Données du projet forestier
            subsidy_id: Identifiant de la subvention
            applicant: Données du demandeur
            output_formats: Formats de sortie (pdf, html, docx)
            
        Returns:
            Chemins vers les documents générés par format
        """
        logger.info(f"Generating application for project={project}, subsidy_id={subsidy_id}, "
                   f"applicant={applicant}, formats={output_formats}")
        
        # Charge les données de la subvention
        subsidies = self._load_subsidies_from_cache()
        subsidy = next((s for s in subsidies if s["id"] == subsidy_id), None)
        
        if not subsidy:
            raise ValueError(f"Subsidy with ID {subsidy_id} not found")
        
        # Prépare les données pour le modèle
        template_data = {
            "project": project,
            "subsidy": subsidy,
            "applicant": applicant,
            "generated_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "application_id": f"APP-{subsidy_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Génère les documents dans les formats demandés
        output_files = {}
        
        for output_format in output_formats:
            if output_format.lower() == "pdf":
                output_path = self._generate_pdf(template_data, subsidy)
                output_files["pdf"] = output_path
            
            elif output_format.lower() == "html":
                output_path = self._generate_html(template_data, subsidy)
                output_files["html"] = output_path
            
            elif output_format.lower() == "docx":
                output_path = self._generate_docx(template_data, subsidy)
                output_files["docx"] = output_path
            
            else:
                logger.warning(f"Unsupported output format: {output_format}")
        
        return output_files
    
    def _load_subsidies_from_cache(self) -> List[Dict[str, Any]]:
        """
        Charge les subventions depuis le cache.
        
        Returns:
            Liste des subventions
        """
        cache_file = os.path.join(self.cache_path, "subsidies.json")
        
        # Vérifie si le fichier de cache existe et est récent
        if os.path.exists(cache_file):
            file_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
            
            if file_age.days < self.cache_duration:
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error loading subsidies from cache: {str(e)}")
        
        # Si le cache n'existe pas ou est périmé, retourne des données fictives pour cette démonstration
        # Dans une vraie implémentation, cela appellerait les scrapers de subventions
        subsidies = [
            {
                "id": "FR-2023-12",
                "title": "Plan de relance - Renouvellement forestier",
                "description": "Aide au renouvellement forestier dans le cadre du plan de relance",
                "funding_agency": "Ministère de l'Agriculture",
                "amount": "2500€/ha",
                "project_types": ["reboisement", "boisement"],
                "regions": ["*"],  # Toutes les régions
                "owner_types": ["private", "public"],
                "deadline": "2025-12-31",
                "eligibility_criteria": [
                    {"type": "min_area", "value": 1.0, "unit": "ha"},
                    {"type": "species", "values": ["pinus_halepensis", "quercus_ilex", "quercus_pubescens"]}
                ],
                "priority_zones": [
                    {"zone_type": "Natura 2000", "bonus": 10},
                    {"zone_type": "Zone humide", "bonus": 15}
                ]
            },
            {
                "id": "OCC-2024-05",
                "title": "Reboisement post-incendie Occitanie",
                "description": "Aide au reboisement des parcelles touchées par les incendies en Occitanie",
                "funding_agency": "Région Occitanie",
                "amount": "3500€/ha",
                "project_types": ["reboisement"],
                "regions": ["Occitanie"],
                "owner_types": ["private"],
                "deadline": "2025-06-30",
                "eligibility_criteria": [
                    {"type": "min_area", "value": 0.5, "unit": "ha"},
                    {"type": "max_area", "value": 20.0, "unit": "ha"},
                    {"type": "fire_damage", "value": true}
                ],
                "priority_zones": []
            },
            {
                "id": "PACA-2024-08",
                "title": "Diversification forestière PACA",
                "description": "Aide à la diversification des essences dans les forêts de PACA",
                "funding_agency": "Région Provence-Alpes-Côte d'Azur",
                "amount": "2000€/ha",
                "project_types": ["reboisement", "diversification"],
                "regions": ["Provence-Alpes-Côte d'Azur"],
                "owner_types": ["private", "public"],
                "deadline": "2025-09-15",
                "eligibility_criteria": [
                    {"type": "min_area", "value": 1.0, "unit": "ha"},
                    {"type": "min_species_count", "value": 3}
                ],
                "priority_zones": [
                    {"zone_type": "Natura 2000", "bonus": 5}
                ]
            }
        ]
        
        # Enregistre les données dans le cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(subsidies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving subsidies to cache: {str(e)}")
        
        return subsidies
    
    def _check_priority_match(self, subsidy: Dict[str, Any], priority_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Vérifie si des zones prioritaires correspondent à la subvention.
        
        Args:
            subsidy: Données de la subvention
            priority_zones: Zones prioritaires identifiées
            
        Returns:
            Informations sur la correspondance des zones prioritaires
        """
        priority_match = {"matching_zones": [], "score": 0}
        
        subsidy_priority_zones = subsidy.get("priority_zones", [])
        if not subsidy_priority_zones:
            return priority_match
        
        for zone in priority_zones:
            for subsidy_zone in subsidy_priority_zones:
                if zone["zone_type"] == subsidy_zone["zone_type"]:
                    priority_match["matching_zones"].append({
                        "zone_type": zone["zone_type"],
                        "bonus": subsidy_zone["bonus"],
                        "coverage_percentage": zone.get("coverage_percentage", 100)
                    })
                    
                    # Ajuste le score en fonction du pourcentage de couverture
                    coverage_factor = zone.get("coverage_percentage", 100) / 100.0
                    priority_match["score"] += subsidy_zone["bonus"] * coverage_factor
        
        return priority_match
    
    def _check_basic_eligibility(self, project: Dict[str, Any], subsidy: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Vérifie les critères d'éligibilité de base.
        
        Args:
            project: Données du projet
            subsidy: Données de la subvention
            
        Returns:
            Tuple (éligibilité, raisons)
        """
        reasons = []
        
        # Vérifie le type de projet
        if project.get("type") not in subsidy.get("project_types", []):
            reasons.append(f"Project type '{project.get('type')}' not eligible (accepted: {', '.join(subsidy.get('project_types', []))})")
        
        # Vérifie la région
        if project.get("region") and subsidy.get("regions") and "*" not in subsidy.get("regions", []):
            if project.get("region") not in subsidy.get("regions", []):
                reasons.append(f"Region '{project.get('region')}' not eligible (accepted: {', '.join(subsidy.get('regions', []))})")
        
        # Vérifie le type de propriétaire
        if project.get("owner_type") and subsidy.get("owner_types") and "*" not in subsidy.get("owner_types", []):
            if project.get("owner_type") not in subsidy.get("owner_types", []):
                reasons.append(f"Owner type '{project.get('owner_type')}' not eligible (accepted: {', '.join(subsidy.get('owner_types', []))})")
        
        return len(reasons) == 0, reasons
    
    def _check_specific_eligibility(self, project: Dict[str, Any], subsidy: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Vérifie les critères d'éligibilité spécifiques.
        
        Args:
            project: Données du projet
            subsidy: Données de la subvention
            
        Returns:
            Tuple (éligibilité, détails)
        """
        details = []
        is_eligible = True
        
        for criterion in subsidy.get("eligibility_criteria", []):
            criterion_type = criterion.get("type")
            criterion_result = {"type": criterion_type, "eligible": True, "description": ""}
            
            # Vérifie la superficie minimale
            if criterion_type == "min_area":
                min_area = criterion.get("value", 0)
                project_area = project.get("area_ha", 0)
                criterion_result["eligible"] = project_area >= min_area
                criterion_result["description"] = f"Minimum area: {min_area} ha (Project: {project_area} ha)"
            
            # Vérifie la superficie maximale
            elif criterion_type == "max_area":
                max_area = criterion.get("value", float("inf"))
                project_area = project.get("area_ha", 0)
                criterion_result["eligible"] = project_area <= max_area
                criterion_result["description"] = f"Maximum area: {max_area} ha (Project: {project_area} ha)"
            
            # Vérifie les espèces
            elif criterion_type == "species":
                accepted_species = criterion.get("values", [])
                project_species = project.get("species", [])
                
                # Vérifie si au moins une espèce du projet est dans la liste des espèces acceptées
                has_valid_species = any(species in accepted_species for species in project_species)
                criterion_result["eligible"] = has_valid_species
                criterion_result["description"] = f"Accepted species: {', '.join(accepted_species)} (Project: {', '.join(project_species)})"
            
            # Vérifie le nombre minimum d'espèces
            elif criterion_type == "min_species_count":
                min_count = criterion.get("value", 1)
                project_species = project.get("species", [])
                criterion_result["eligible"] = len(project_species) >= min_count
                criterion_result["description"] = f"Minimum species count: {min_count} (Project: {len(project_species)})"
            
            # Vérifie les dommages d'incendie
            elif criterion_type == "fire_damage":
                required_value = criterion.get("value", True)
                project_value = project.get("fire_damage", False)
                criterion_result["eligible"] = project_value == required_value
                criterion_result["description"] = f"Fire damage required: {required_value} (Project: {project_value})"
            
            # Autres critères spécifiques peuvent être ajoutés ici
            
            details.append(criterion_result)
            
            # Si un critère n'est pas satisfait, le projet n'est pas éligible
            if not criterion_result["eligible"]:
                is_eligible = False
        
        return is_eligible, details
    
    def _calculate_eligibility_score(self, project: Dict[str, Any], subsidy: Dict[str, Any], 
                                    details: List[Dict[str, Any]]) -> float:
        """
        Calcule un score d'éligibilité (0-100).
        
        Args:
            project: Données du projet
            subsidy: Données de la subvention
            details: Détails de l'éligibilité
            
        Returns:
            Score d'éligibilité
        """
        # Si aucun critère n'est satisfait, le score est 0
        if not details:
            return 0.0
        
        # Calcule le pourcentage de critères satisfaits
        satisfied_criteria = sum(1 for detail in details if detail["eligible"])
        score = (satisfied_criteria / len(details)) * 100.0
        
        return round(score, 1)
    
    def _calculate_priority_bonus(self, project: Dict[str, Any], subsidy: Dict[str, Any]) -> float:
        """
        Calcule le bonus de priorité en pourcentage.
        
        Args:
            project: Données du projet
            subsidy: Données de la subvention
            
        Returns:
            Bonus de priorité en pourcentage
        """
        priority_bonus = 0.0
        
        # Vérifie s'il y a des zones prioritaires dans le projet
        if "priority_zones" not in project:
            return priority_bonus
        
        # Récupère les zones prioritaires du projet et de la subvention
        project_zones = project.get("priority_zones", [])
        subsidy_zones = subsidy.get("priority_zones", [])
        
        for project_zone in project_zones:
            zone_type = project_zone.get("zone_type")
            coverage = project_zone.get("coverage_percentage", 100) / 100.0
            
            # Trouve le bonus correspondant dans la subvention
            for subsidy_zone in subsidy_zones:
                if subsidy_zone.get("zone_type") == zone_type:
                    priority_bonus += subsidy_zone.get("bonus", 0) * coverage
        
        return round(priority_bonus, 1)
    
    def _generate_pdf(self, template_data: Dict[str, Any], subsidy: Dict[str, Any]) -> str:
        """
        Génère un document PDF pour la demande de subvention.
        
        Args:
            template_data: Données pour le modèle
            subsidy: Données de la subvention
            
        Returns:
            Chemin vers le fichier PDF généré
        """
        # Dans une vraie implémentation, cela générerait un PDF
        subsidy_id = subsidy["id"]
        output_file = os.path.join(self.output_path, "subsidies", f"application_{subsidy_id}.pdf")
        
        logger.info(f"PDF would be generated at: {output_file}")
        
        # Simulation de la génération de PDF
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Simulated PDF file for subsidy application {subsidy_id}\n")
            f.write(f"Generated on {template_data['generated_date']}\n")
            f.write(f"Application ID: {template_data['application_id']}\n")
        
        return output_file
    
    def _generate_html(self, template_data: Dict[str, Any], subsidy: Dict[str, Any]) -> str:
        """
        Génère un document HTML pour la demande de subvention.
        
        Args:
            template_data: Données pour le modèle
            subsidy: Données de la subvention
            
        Returns:
            Chemin vers le fichier HTML généré
        """
        # Dans une vraie implémentation, cela générerait un HTML
        subsidy_id = subsidy["id"]
        output_file = os.path.join(self.output_path, "subsidies", f"application_{subsidy_id}.html")
        
        logger.info(f"HTML would be generated at: {output_file}")
        
        # Simulation de la génération de HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Demande de subvention - {subsidy['title']}</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Demande de subvention - {subsidy['title']}</h1>
    <p>ID de demande: {template_data['application_id']}</p>
    <p>Date de génération: {template_data['generated_date']}</p>
    <!-- Le reste du contenu HTML serait généré ici -->
</body>
</html>
"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return output_file
    
    def _generate_docx(self, template_data: Dict[str, Any], subsidy: Dict[str, Any]) -> str:
        """
        Génère un document DOCX pour la demande de subvention.
        
        Args:
            template_data: Données pour le modèle
            subsidy: Données de la subvention
            
        Returns:
            Chemin vers le fichier DOCX généré
        """
        # Dans une vraie implémentation, cela générerait un DOCX
        subsidy_id = subsidy["id"]
        output_file = os.path.join(self.output_path, "subsidies", f"application_{subsidy_id}.docx")
        
        logger.info(f"DOCX would be generated at: {output_file}")
        
        # Simulation de la génération de DOCX
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Simulated DOCX file for subsidy application {subsidy_id}\n")
            f.write(f"Generated on {template_data['generated_date']}\n")
            f.write(f"Application ID: {template_data['application_id']}\n")
        
        return output_file
