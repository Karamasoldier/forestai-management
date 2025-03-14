"""
Module d'analyse d'éligibilité pour les subventions forestières.

Ce module fournit des outils pour analyser l'éligibilité des projets
forestiers aux différents programmes de subventions disponibles.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional


class EligibilityAnalyzer:
    """
    Analyseur d'éligibilité pour les projets forestiers.
    
    Cette classe fournit des méthodes pour évaluer si un projet forestier
    est éligible à une subvention spécifique selon divers critères.
    """
    
    def __init__(self):
        """Initialise l'analyseur d'éligibilité."""
        self.condition_checkers = {
            "project_type": self._check_project_type,
            "region": self._check_region,
            "area": self._check_area,
            "species": self._check_species,
            "owner_type": self._check_owner_type,
            "deadline": self._check_deadline,
            "min_density": self._check_min_density,
            "slope": self._check_slope,
            "protected_area": self._check_protected_area
        }
    
    def analyze(
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
        eligibility_conditions = []
        is_eligible = True
        
        # Exécuter tous les contrôles d'éligibilité
        for condition_type, checker in self.condition_checkers.items():
            condition_result = checker(project, subsidy)
            
            if condition_result:
                eligibility_conditions.append(condition_result)
                if not condition_result["satisfied"]:
                    is_eligible = False
        
        # Résultat final
        return {
            "eligible": is_eligible,
            "subsidy_id": subsidy.get("id"),
            "subsidy_title": subsidy.get("title"),
            "conditions": eligibility_conditions,
            "next_steps": subsidy.get("application_process", []) if is_eligible else [],
            "funding_details": self._get_funding_details(project, subsidy) if is_eligible else None,
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_project_type(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si le type de projet est éligible pour la subvention.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "eligible_projects" not in subsidy:
            return None
        
        project_type = project.get("type", "").lower()
        eligible_projects = [p.lower() for p in subsidy.get("eligible_projects", [])]
        
        project_eligible = (
            not eligible_projects or 
            project_type in eligible_projects or 
            "all" in eligible_projects
        )
        
        return {
            "condition": "Type de projet éligible",
            "satisfied": project_eligible,
            "details": f"Type de projet: {project_type}"
        }
    
    def _check_region(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si la région du projet est éligible pour la subvention.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "regions" not in subsidy:
            return None
        
        region = project.get("region", "").lower()
        eligible_regions = [r.lower() for r in subsidy.get("regions", [])]
        
        region_eligible = (
            not eligible_regions or 
            region in eligible_regions or 
            "national" in eligible_regions
        )
        
        return {
            "condition": "Région éligible",
            "satisfied": region_eligible,
            "details": f"Région: {region}"
        }
    
    def _check_area(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si la superficie du projet est dans les limites de la subvention.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "min_area_ha" not in subsidy and "max_area_ha" not in subsidy:
            return None
        
        area_ha = project.get("area_ha", 0)
        min_area = subsidy.get("min_area_ha", 0)
        max_area = subsidy.get("max_area_ha", float("inf"))
        
        area_eligible = area_ha >= min_area and (max_area == float("inf") or area_ha <= max_area)
        
        return {
            "condition": "Superficie éligible",
            "satisfied": area_eligible,
            "details": f"Superficie: {area_ha} ha (min: {min_area} ha, max: {max_area if max_area != float('inf') else 'non spécifié'} ha)"
        }
    
    def _check_species(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si les espèces du projet sont éligibles pour la subvention.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "eligible_species" not in subsidy:
            return None
        
        species = project.get("species", [])
        eligible_species = subsidy.get("eligible_species", [])
        
        species_eligible = (
            not eligible_species or 
            any(s in eligible_species for s in species) or 
            "all" in eligible_species
        )
        
        return {
            "condition": "Espèces éligibles",
            "satisfied": species_eligible,
            "details": f"Espèces: {', '.join(species)}"
        }
    
    def _check_owner_type(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si le type de propriétaire est éligible pour la subvention.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "eligible_owners" not in subsidy:
            return None
        
        owner_type = project.get("owner_type", "").lower()
        eligible_owners = [o.lower() for o in subsidy.get("eligible_owners", [])]
        
        owner_eligible = (
            not eligible_owners or 
            owner_type in eligible_owners or 
            "all" in eligible_owners
        )
        
        return {
            "condition": "Type de propriétaire éligible",
            "satisfied": owner_eligible,
            "details": f"Type de propriétaire: {owner_type}"
        }
    
    def _check_deadline(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si la date limite de la subvention n'est pas dépassée.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "deadline" not in subsidy:
            return None
        
        deadline = subsidy.get("deadline")
        if not deadline:
            return None
            
        try:
            deadline_date = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            current_date = datetime.now()
            deadline_eligible = current_date <= deadline_date
            
            return {
                "condition": "Date limite respectée",
                "satisfied": deadline_eligible,
                "details": f"Date limite: {deadline_date.strftime('%d/%m/%Y')}"
            }
        except (ValueError, TypeError):
            return None
    
    def _check_min_density(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si la densité de plantation du projet est suffisante.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "min_planting_density" not in subsidy:
            return None
        
        min_density = subsidy.get("min_planting_density", 0)
        project_density = project.get("planting_density", 0)
        
        density_eligible = project_density >= min_density
        
        return {
            "condition": "Densité de plantation suffisante",
            "satisfied": density_eligible,
            "details": f"Densité: {project_density} plants/ha (min: {min_density} plants/ha)"
        }
    
    def _check_slope(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si la pente du terrain est dans les limites acceptables.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "max_slope" not in subsidy:
            return None
        
        max_slope = subsidy.get("max_slope", float("inf"))
        project_slope = project.get("slope", 0)
        
        slope_eligible = project_slope <= max_slope
        
        return {
            "condition": "Pente du terrain acceptable",
            "satisfied": slope_eligible,
            "details": f"Pente: {project_slope}% (max: {max_slope}%)"
        }
    
    def _check_protected_area(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie la compatibilité avec les zones protégées.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'analyse ou None si non applicable
        """
        if "excluded_zones" not in subsidy:
            return None
        
        excluded_zones = subsidy.get("excluded_zones", [])
        project_zones = project.get("protected_areas", [])
        
        zones_eligible = not any(zone in excluded_zones for zone in project_zones)
        
        return {
            "condition": "Zones protégées compatibles",
            "satisfied": zones_eligible,
            "details": f"Zones protégées: {', '.join(project_zones) if project_zones else 'aucune'}"
        }
    
    def _get_funding_details(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcule les détails de financement pour un projet éligible.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Détails de financement
        """
        area_ha = project.get("area_ha", 0)
        funding_rate = subsidy.get("funding_rate", 0)
        max_funding = subsidy.get("max_funding", float("inf"))
        base_amount_per_ha = subsidy.get("amount_per_ha", 0)
        
        # Montant de base
        estimated_amount = area_ha * base_amount_per_ha
        
        # Application du taux de financement si spécifié
        if funding_rate > 0:
            estimated_amount = estimated_amount * (funding_rate / 100)
        
        # Plafonnement au montant maximum
        if max_funding < float("inf") and estimated_amount > max_funding:
            estimated_amount = max_funding
        
        # Application des bonus éventuels
        bonus_amount = 0
        bonus_details = []
        
        if subsidy.get("bonus") and project.get("certifications"):
            for certification in project.get("certifications", []):
                if certification in subsidy.get("bonus_certifications", {}):
                    bonus_rate = subsidy["bonus_certifications"][certification]
                    cert_bonus = estimated_amount * (bonus_rate / 100)
                    bonus_amount += cert_bonus
                    bonus_details.append({
                        "type": f"Certification {certification}",
                        "rate": f"{bonus_rate}%",
                        "amount": cert_bonus
                    })
        
        # Résultat final
        return {
            "base_amount": estimated_amount,
            "bonus_amount": bonus_amount,
            "total_amount": estimated_amount + bonus_amount,
            "details": {
                "area_ha": area_ha,
                "amount_per_ha": base_amount_per_ha,
                "funding_rate": funding_rate,
                "max_funding": max_funding if max_funding < float("inf") else "Non plafonné",
                "bonus_details": bonus_details
            }
        }


class EligibilityRuleEngine:
    """
    Moteur de règles d'éligibilité pour les subventions forestières.
    
    Permet d'évaluer l'éligibilité selon des règles complexes et personnalisées
    pour chaque type de subvention.
    """
    
    def __init__(self):
        """Initialise le moteur de règles d'éligibilité."""
        self.rule_handlers = {
            "france_relance": self._apply_france_relance_rules,
            "feader": self._apply_feader_rules,
            "region_standard": self._apply_region_standard_rules
        }
    
    def evaluate(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Évalue l'éligibilité d'un projet selon les règles spécifiques à la subvention.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            
        Returns:
            Résultat de l'évaluation
        """
        # Utiliser l'analyseur standard pour les vérifications de base
        analyzer = EligibilityAnalyzer()
        base_result = analyzer.analyze(project, subsidy)
        
        # Si déjà non éligible selon les critères de base, inutile d'aller plus loin
        if not base_result["eligible"]:
            return base_result
        
        # Appliquer les règles spécifiques au type de subvention
        subsidy_type = subsidy.get("subsidy_type", "standard")
        
        if subsidy_type in self.rule_handlers:
            return self.rule_handlers[subsidy_type](project, subsidy, base_result)
        
        # Par défaut, retourner le résultat de l'analyse de base
        return base_result
    
    def _apply_france_relance_rules(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any], 
        base_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applique les règles spécifiques aux subventions France Relance.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            base_result: Résultat de l'analyse de base
            
        Returns:
            Résultat de l'évaluation
        """
        conditions = base_result["conditions"].copy()
        still_eligible = base_result["eligible"]
        
        # Vérifier si le projet est en zone prioritaire France Relance
        is_priority_zone = self._check_priority_zone(project)
        conditions.append({
            "condition": "Zone prioritaire France Relance",
            "satisfied": is_priority_zone,
            "details": "Le projet est situé dans une zone prioritaire France Relance" if is_priority_zone else "Le projet n'est pas situé dans une zone prioritaire France Relance (critère non éliminatoire)"
        })
        
        # Si c'est une zone prioritaire, ajuster le financement
        if is_priority_zone and "funding_details" in base_result and base_result["funding_details"]:
            funding_details = base_result["funding_details"].copy()
            priority_bonus = funding_details["base_amount"] * 0.10  # 10% de bonus
            
            funding_details["bonus_amount"] += priority_bonus
            funding_details["total_amount"] += priority_bonus
            funding_details["details"]["bonus_details"].append({
                "type": "Zone prioritaire France Relance",
                "rate": "10%",
                "amount": priority_bonus
            })
            
            base_result["funding_details"] = funding_details
        
        # Vérifier les surfaces minimales par îlot pour France Relance
        min_island_area = subsidy.get("min_island_area_ha", 0)
        if min_island_area > 0:
            islands = project.get("islands", [])
            if islands:
                all_islands_compliant = all(island.get("area_ha", 0) >= min_island_area for island in islands)
                conditions.append({
                    "condition": f"Surface minimale par îlot ({min_island_area} ha)",
                    "satisfied": all_islands_compliant,
                    "details": f"Tous les îlots ont une surface d'au moins {min_island_area} ha" if all_islands_compliant else f"Certains îlots ont une surface inférieure à {min_island_area} ha"
                })
                
                if not all_islands_compliant:
                    still_eligible = False
            else:
                # Si pas d'information sur les îlots, on considère que c'est OK
                conditions.append({
                    "condition": f"Surface minimale par îlot ({min_island_area} ha)",
                    "satisfied": True,
                    "details": "Information sur les îlots non disponible - critère ignoré"
                })
        
        # Mettre à jour le résultat
        base_result["eligible"] = still_eligible
        base_result["conditions"] = conditions
        
        return base_result
    
    def _apply_feader_rules(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any], 
        base_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applique les règles spécifiques aux subventions FEADER.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            base_result: Résultat de l'analyse de base
            
        Returns:
            Résultat de l'évaluation
        """
        conditions = base_result["conditions"].copy()
        still_eligible = base_result["eligible"]
        
        # Vérifier la présence d'un document de gestion durable
        has_management_doc = project.get("has_management_document", False)
        conditions.append({
            "condition": "Document de gestion durable",
            "satisfied": has_management_doc,
            "details": "Le projet dispose d'un document de gestion durable" if has_management_doc else "Le projet ne dispose pas de document de gestion durable"
        })
        
        if not has_management_doc:
            still_eligible = False
        
        # Vérifier l'engagement de maintien 5 ans
        has_maintenance_commitment = project.get("maintenance_commitment_years", 0) >= 5
        conditions.append({
            "condition": "Engagement d'entretien sur 5 ans",
            "satisfied": has_maintenance_commitment,
            "details": "Le projet inclut un engagement d'entretien sur au moins 5 ans" if has_maintenance_commitment else "Le projet n'inclut pas d'engagement d'entretien sur au moins 5 ans"
        })
        
        if not has_maintenance_commitment:
            still_eligible = False
        
        # Mettre à jour le résultat
        base_result["eligible"] = still_eligible
        base_result["conditions"] = conditions
        
        return base_result
    
    def _apply_region_standard_rules(
        self, 
        project: Dict[str, Any], 
        subsidy: Dict[str, Any], 
        base_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applique les règles standard des subventions régionales.
        
        Args:
            project: Informations sur le projet
            subsidy: Informations sur la subvention
            base_result: Résultat de l'analyse de base
            
        Returns:
            Résultat de l'évaluation
        """
        # Pour l'instant, pas de règles supplémentaires pour les subventions régionales standard
        return base_result
    
    def _check_priority_zone(self, project: Dict[str, Any]) -> bool:
        """
        Vérifie si le projet est situé dans une zone prioritaire France Relance.
        
        Args:
            project: Informations sur le projet
            
        Returns:
            True si le projet est en zone prioritaire, False sinon
        """
        priority_zones = project.get("priority_zones", [])
        return "france_relance" in priority_zones
