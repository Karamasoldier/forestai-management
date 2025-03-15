# -*- coding: utf-8 -*-
"""
Module de calcul d'indicateurs sanitaires forestiers.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HealthIndicatorCalculator:
    """Calculateur d'indicateurs sanitaires forestiers."""
    
    def __init__(self, thresholds: Dict[str, float]):
        """
        Initialise le calculateur d'indicateurs sanitaires.
        
        Args:
            thresholds: Seuils pour différentes analyses
        """
        self.thresholds = thresholds
    
    def calculate_indicators(self, trees: List[Dict[str, Any]], 
                            additional_symptoms: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calcule les indicateurs globaux de santé de la forêt.
        
        Args:
            trees: Liste des arbres de l'inventaire
            additional_symptoms: Observations supplémentaires
            
        Returns:
            Indicateurs de santé forestière globaux
        """
        # Initialisation des compteurs
        total_trees = len(trees)
        if total_trees == 0:
            return {
                "defoliation_rate": None,
                "discoloration_rate": None,
                "pest_presence_rate": None,
                "bark_damage_rate": None,
                "crown_transparency": None,
                "mortality_rate": None,
                "health_thresholds": self.thresholds
            }
        
        defoliation_count = 0
        discoloration_count = 0
        pest_presence_count = 0
        bark_damage_count = 0
        crown_transparency_sum = 0
        crown_transparency_count = 0
        mortality_count = 0
        
        # Comptage à partir des données d'arbres
        for tree in trees:
            # Vérifier la mortalité
            if tree.get("status") == "dead" or tree.get("health_status") == "dead":
                mortality_count += 1
            
            # Comptabiliser les symptômes
            if "symptoms" in tree and isinstance(tree["symptoms"], list):
                for symptom in tree["symptoms"]:
                    if isinstance(symptom, str):
                        sympt_name = symptom.lower()
                    else:
                        sympt_name = symptom.get("name", "").lower()
                    
                    if "defoli" in sympt_name or "leaf loss" in sympt_name:
                        defoliation_count += 1
                    if "discol" in sympt_name or "yellow" in sympt_name or "chloro" in sympt_name:
                        discoloration_count += 1
                    if "pest" in sympt_name or "insect" in sympt_name or "larv" in sympt_name:
                        pest_presence_count += 1
                    if "bark" in sympt_name and ("damage" in sympt_name or "lesion" in sympt_name):
                        bark_damage_count += 1
            
            # Transparence du houppier
            if "crown_transparency" in tree and isinstance(tree["crown_transparency"], (int, float)):
                crown_transparency_sum += tree["crown_transparency"]
                crown_transparency_count += 1
        
        # Intégrer les observations supplémentaires si fournies
        if additional_symptoms:
            # Exemple: {"defoliation_observed": true, "defoliation_rate": 0.4, "pest_species": ["bark beetle"]}
            if additional_symptoms.get("defoliation_observed", False) and "defoliation_rate" in additional_symptoms:
                defoliation_count = max(defoliation_count, int(total_trees * additional_symptoms["defoliation_rate"]))
            
            if additional_symptoms.get("discoloration_observed", False) and "discoloration_rate" in additional_symptoms:
                discoloration_count = max(discoloration_count, int(total_trees * additional_symptoms["discoloration_rate"]))
            
            if additional_symptoms.get("bark_damage_observed", False) and "bark_damage_rate" in additional_symptoms:
                bark_damage_count = max(bark_damage_count, int(total_trees * additional_symptoms["bark_damage_rate"]))
            
            if "pest_presence_rate" in additional_symptoms:
                pest_presence_count = max(pest_presence_count, int(total_trees * additional_symptoms["pest_presence_rate"]))
            
            if "mortality_rate" in additional_symptoms:
                mortality_count = max(mortality_count, int(total_trees * additional_symptoms["mortality_rate"]))
        
        # Calcul des indicateurs
        indicators = {
            "defoliation_rate": round(defoliation_count / total_trees, 3) if total_trees > 0 else None,
            "discoloration_rate": round(discoloration_count / total_trees, 3) if total_trees > 0 else None,
            "pest_presence_rate": round(pest_presence_count / total_trees, 3) if total_trees > 0 else None,
            "bark_damage_rate": round(bark_damage_count / total_trees, 3) if total_trees > 0 else None,
            "crown_transparency": round(crown_transparency_sum / crown_transparency_count, 3) if crown_transparency_count > 0 else None,
            "mortality_rate": round(mortality_count / total_trees, 3) if total_trees > 0 else None,
            "health_thresholds": self.thresholds
        }
        
        # Ajouter des flags pour les valeurs critiques
        indicators["critical_flags"] = {
            "critical_defoliation": indicators["defoliation_rate"] is not None and indicators["defoliation_rate"] > self.thresholds.get("defoliation_critical", 0.25),
            "critical_discoloration": indicators["discoloration_rate"] is not None and indicators["discoloration_rate"] > self.thresholds.get("discoloration_critical", 0.2),
            "critical_pest_presence": indicators["pest_presence_rate"] is not None and indicators["pest_presence_rate"] > self.thresholds.get("pest_presence_critical", 0.1),
            "critical_bark_damage": indicators["bark_damage_rate"] is not None and indicators["bark_damage_rate"] > self.thresholds.get("bark_damage_critical", 0.15),
            "critical_crown_transparency": indicators["crown_transparency"] is not None and indicators["crown_transparency"] > self.thresholds.get("crown_transparency_critical", 0.35),
            "critical_mortality": indicators["mortality_rate"] is not None and indicators["mortality_rate"] > 0.1  # Plus de 10% de mortalité est considéré critique
        }
        
        # Calculer un score global de santé
        critical_count = sum(1 for flag, value in indicators["critical_flags"].items() if value)
        indicators["global_health_index"] = max(0, 10 - critical_count * 2)  # Réduction de 2 points par indicateur critique
        
        return indicators
