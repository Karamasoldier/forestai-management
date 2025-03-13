"""
Module de recommandation d'espèces forestières adaptées au climat.

S'occupe de calculer les scores des espèces et de les recommander
selon différents critères.
"""

import logging
from typing import Dict, List, Any, Optional

class SpeciesRecommender:
    """
    Recommandeur d'espèces forestières adaptées au changement climatique.
    
    Fonctionnalités:
    - Calcul des scores de compatibilité
    - Recommandation d'espèces selon critères multiples
    - Tri et classement des recommandations
    """
    
    def __init__(self, species_compatibility: Dict[str, Any]):
        """
        Initialise le recommandeur d'espèces.
        
        Args:
            species_compatibility: Dictionnaire contenant les données de compatibilité des espèces
        """
        self.logger = logging.getLogger(__name__)
        self.species_compatibility = species_compatibility
    
    def get_compatible_species(self, zone_id: str, 
                              scenario: str = "current") -> Dict[str, Dict[str, Any]]:
        """
        Retourne la compatibilité des espèces pour une zone climatique et un scénario donnés.
        
        Args:
            zone_id: Identifiant de la zone climatique
            scenario: Scénario climatique à utiliser (défaut: climat actuel)
            
        Returns:
            Dictionnaire des espèces avec leur compatibilité
        """
        try:
            compatible_species = {}
            
            for species_name, species_data in self.species_compatibility.items():
                if zone_id in species_data["climate_compatibility"]:
                    zone_compat = species_data["climate_compatibility"][zone_id]
                    
                    if scenario in zone_compat:
                        compatibility = zone_compat[scenario]
                        
                        # Ajouter l'espèce au dictionnaire résultat
                        compatible_species[species_name] = {
                            "common_name": species_data["common_name"],
                            "compatibility": compatibility,
                            "compatibility_score": self._compatibility_to_score(compatibility),
                            "growth_rate": species_data["growth_rate"],
                            "economic_value": species_data["economic_value"],
                            "ecological_value": species_data["ecological_value"],
                            "risks": species_data["risks"]
                        }
            
            return compatible_species
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la compatibilité des espèces: {str(e)}")
            return {}
    
    def recommend_species(self, zone_id: str, 
                         scenario: str = "current",
                         min_compatibility: str = "suitable",
                         criteria: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Recommande des espèces adaptées pour une zone climatique et un scénario.
        
        Args:
            zone_id: Identifiant de la zone climatique
            scenario: Scénario climatique à utiliser
            min_compatibility: Niveau minimal de compatibilité ("optimal", "suitable", "marginal")
            criteria: Poids des critères pour le classement (economic_value, ecological_value, growth_rate)
            
        Returns:
            Liste des espèces recommandées avec leurs scores et détails
        """
        try:
            # Obtenir la compatibilité des espèces
            compatible_species = self.get_compatible_species(zone_id, scenario)
            
            # Filtrer par niveau minimal de compatibilité
            min_score = self._compatibility_to_score(min_compatibility)
            filtered_species = {
                name: data for name, data in compatible_species.items()
                if data["compatibility_score"] >= min_score
            }
            
            # Définir les critères de pondération par défaut
            default_criteria = {
                "economic_value": 0.4,
                "ecological_value": 0.4,
                "growth_rate": 0.2
            }
            
            # Utiliser les critères fournis ou les critères par défaut
            criteria = criteria or default_criteria
            
            # Calculer le score global pour chaque espèce
            recommendations = []
            
            for species_name, data in filtered_species.items():
                # Convertir les valeurs textuelles en scores numériques
                value_scores = {
                    "economic_value": self._value_to_score(data["economic_value"]),
                    "ecological_value": self._value_to_score(data["ecological_value"]),
                    "growth_rate": self._value_to_score(data["growth_rate"])
                }
                
                # Calculer le score global pondéré
                global_score = (
                    data["compatibility_score"] * 0.6 +
                    value_scores["economic_value"] * criteria.get("economic_value", 0.4) * 0.4 +
                    value_scores["ecological_value"] * criteria.get("ecological_value", 0.4) * 0.4 +
                    value_scores["growth_rate"] * criteria.get("growth_rate", 0.2) * 0.4
                )
                
                # Créer l'objet de recommandation
                recommendation = {
                    "species_name": species_name,
                    "common_name": data["common_name"],
                    "global_score": round(global_score, 2),
                    "compatibility": data["compatibility"],
                    "compatibility_score": data["compatibility_score"],
                    "economic_value": data["economic_value"],
                    "ecological_value": data["ecological_value"],
                    "growth_rate": data["growth_rate"],
                    "risks": data["risks"]
                }
                
                recommendations.append(recommendation)
            
            # Trier par score global décroissant
            sorted_recommendations = sorted(recommendations, key=lambda x: x["global_score"], reverse=True)
            
            return sorted_recommendations
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recommandation d'espèces: {str(e)}")
            return []
    
    def filter_recommendations_by_risks(self, recommendations: List[Dict[str, Any]], 
                                      excluded_risks: List[str] = None) -> List[Dict[str, Any]]:
        """
        Filtre les recommandations en fonction des risques à éviter.
        
        Args:
            recommendations: Liste des recommandations à filtrer
            excluded_risks: Liste des risques à éviter (drought, frost, fire)
            
        Returns:
            Liste filtrée des recommandations
        """
        if not excluded_risks:
            return recommendations
        
        filtered = []
        for rec in recommendations:
            risks = rec.get("risks", {})
            
            # Vérifier si l'espèce a des risques élevés parmi ceux à éviter
            exclude = False
            for risk in excluded_risks:
                if risk in risks and risks[risk] in ["high", "very high"]:
                    exclude = True
                    break
            
            if not exclude:
                filtered.append(rec)
        
        return filtered
    
    def _compatibility_to_score(self, compatibility: str) -> float:
        """
        Convertit un niveau de compatibilité textuel en score numérique.
        
        Args:
            compatibility: Niveau de compatibilité ("optimal", "suitable", "marginal", "unsuitable")
            
        Returns:
            Score de compatibilité entre 0 et 1
        """
        compatibility_scores = {
            "optimal": 1.0,
            "suitable": 0.7,
            "marginal": 0.3,
            "unsuitable": 0.0
        }
        
        return compatibility_scores.get(compatibility.lower(), 0.0)
    
    def _value_to_score(self, value: str) -> float:
        """
        Convertit une valeur textuelle en score numérique.
        
        Args:
            value: Valeur textuelle ("very low", "low", "medium", "high", "very high" ou équivalents)
            
        Returns:
            Score entre 0 et 1
        """
        value_scores = {
            "very low": 0.1,
            "low": 0.3,
            "medium": 0.5,
            "high": 0.8,
            "very high": 1.0,
            "slow": 0.3,  # Pour growth_rate
            "medium": 0.5,  # Pour growth_rate
            "fast": 0.8    # Pour growth_rate
        }
        
        return value_scores.get(value.lower(), 0.5)
