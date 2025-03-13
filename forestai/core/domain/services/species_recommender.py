"""
Module de recommandation d'espèces forestières.

Ce module est responsable de la recommandation d'espèces adaptées
au climat actuel et futur pour une zone climatique donnée.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd

class SpeciesRecommender:
    """
    Recommandeur d'espèces forestières adaptées aux zones climatiques.
    
    Responsabilités:
    - Filtrer les espèces compatibles avec une zone et un scénario
    - Calculer les scores pour prioriser les recommandations
    - Filtrer les espèces en fonction des risques
    """
    
    def __init__(self, species_compatibility: Dict[str, Dict[str, Any]]):
        """
        Initialise le recommandeur d'espèces.
        
        Args:
            species_compatibility: Dictionnaire des espèces et leur compatibilité avec les zones climatiques
                                  Format: {"Species name": {"common_name": "Nom commun", "climate_compatibility": {...}, "risks": {...}, ...}}
        """
        self.logger = logging.getLogger(__name__)
        self.species_compatibility = species_compatibility
        
        # Constantes pour le calcul des scores
        self.COMPATIBILITY_SCORES = {
            "optimal": 1.0,   # Compatibilité optimale
            "suitable": 0.7,  # Compatibilité bonne
            "marginal": 0.4,  # Compatibilité marginale
            "unsuitable": 0.0 # Compatibilité nulle
        }
        
        self.RISK_SCORES = {
            "low": 0.9,     # Risque faible
            "medium": 0.6,  # Risque moyen
            "high": 0.3     # Risque élevé
        }
        
        self.VALUE_SCORES = {
            "low": 0.3,     # Valeur faible
            "medium": 0.6,  # Valeur moyenne
            "high": 0.9     # Valeur élevée
        }
        
        self.GROWTH_RATE_SCORES = {
            "slow": 0.5,    # Croissance lente
            "medium": 0.7,  # Croissance moyenne
            "fast": 0.9     # Croissance rapide
        }
        
        # Poids par défaut pour les critères
        self.DEFAULT_CRITERIA = {
            "compatibility": 1.0,      # Compatibilité climatique
            "economic_value": 0.7,     # Valeur économique
            "ecological_value": 0.7,   # Valeur écologique
            "growth_rate": 0.6,        # Vitesse de croissance
            "risk_drought": 0.8,       # Résistance à la sécheresse
            "risk_frost": 0.7,         # Résistance au gel
            "risk_fire": 0.6,          # Résistance au feu
            "risk_pests": 0.5          # Résistance aux parasites
        }
        
        self.logger.info(f"SpeciesRecommender initialisé avec {len(species_compatibility)} espèces")
    
    def get_compatible_species(self, zone_id: str, scenario: str = "current") -> Dict[str, Dict[str, Any]]:
        """
        Retourne les espèces compatibles avec une zone climatique et un scénario donnés.
        
        Args:
            zone_id: Identifiant de la zone climatique
            scenario: Scénario climatique à utiliser (défaut: climat actuel)
            
        Returns:
            Dictionnaire des espèces avec leur compatibilité pour la zone et le scénario
        """
        compatible_species = {}
        
        for species_name, species_data in self.species_compatibility.items():
            # Vérifier si l'espèce a des données pour cette zone et ce scénario
            if zone_id in species_data.get("climate_compatibility", {}) and \
               scenario in species_data["climate_compatibility"][zone_id]:
                
                # Récupérer la compatibilité
                compatibility = species_data["climate_compatibility"][zone_id][scenario]
                
                if compatibility != "unsuitable":
                    # Copier les données de base
                    compatible_species[species_name] = {
                        "species_name": species_name,
                        "common_name": species_data.get("common_name", ""),
                        "compatibility": compatibility,
                        "economic_value": species_data.get("economic_value", "medium"),
                        "ecological_value": species_data.get("ecological_value", "medium"),
                        "growth_rate": species_data.get("growth_rate", "medium"),
                        "risks": species_data.get("risks", {})
                    }
        
        self.logger.info(f"Trouvé {len(compatible_species)} espèces compatibles avec la zone {zone_id} pour le scénario {scenario}")
        return compatible_species
    
    def recommend_species(self, zone_id: str, scenario: str = "current",
                         min_compatibility: str = "suitable",
                         criteria: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Recommande des espèces adaptées pour une zone climatique et un scénario donnés.
        
        Args:
            zone_id: Identifiant de la zone climatique
            scenario: Scénario climatique à utiliser
            min_compatibility: Niveau minimal de compatibilité (optimal, suitable, marginal)
            criteria: Poids des critères pour le classement (défaut: self.DEFAULT_CRITERIA)
            
        Returns:
            Liste des espèces recommandées avec leurs scores, triée par score décroissant
        """
        try:
            # Utiliser les critères par défaut si non spécifiés
            if criteria is None:
                criteria = self.DEFAULT_CRITERIA
            
            # Obtenir les espèces compatibles
            compatible_species = self.get_compatible_species(zone_id, scenario)
            
            # Filtrer par niveau minimal de compatibilité
            compatibility_levels = ["optimal", "suitable", "marginal"]
            min_level_index = compatibility_levels.index(min_compatibility)
            accepted_levels = compatibility_levels[:min_level_index + 1]
            
            filtered_species = {
                name: data for name, data in compatible_species.items()
                if data["compatibility"] in accepted_levels
            }
            
            # Calculer les scores pour chaque espèce
            scored_species = []
            for species_name, species_data in filtered_species.items():
                score = self._calculate_score(species_data, criteria)
                
                # Ajouter le score au dictionnaire
                species_data["global_score"] = round(score, 2)
                
                # Ajouter l'espèce à la liste
                scored_species.append(species_data)
            
            # Trier par score décroissant
            sorted_species = sorted(scored_species, key=lambda x: x["global_score"], reverse=True)
            
            self.logger.info(f"Généré {len(sorted_species)} recommandations pour la zone {zone_id}, scénario {scenario}")
            return sorted_species
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recommandation d'espèces: {str(e)}")
            return []
    
    def filter_recommendations_by_risks(self, recommendations: List[Dict[str, Any]], 
                                      excluded_risks: List[str] = None) -> List[Dict[str, Any]]:
        """
        Filtre les recommandations en fonction des risques à éviter.
        
        Args:
            recommendations: Liste des recommandations à filtrer
            excluded_risks: Liste des risques à éviter ("drought", "frost", "fire")
            
        Returns:
            Liste filtrée des recommandations
        """
        if not excluded_risks:
            return recommendations
        
        filtered_recommendations = []
        
        for recommendation in recommendations:
            exclude = False
            risks = recommendation.get("risks", {})
            
            for risk in excluded_risks:
                if risk in risks and risks[risk] == "high":
                    exclude = True
                    break
            
            if not exclude:
                filtered_recommendations.append(recommendation)
        
        self.logger.info(f"Filtré {len(recommendations) - len(filtered_recommendations)} espèces à risque élevé pour: {', '.join(excluded_risks)}")
        return filtered_recommendations
    
    def get_species_details(self, species_name: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une espèce spécifique.
        
        Args:
            species_name: Nom de l'espèce
            
        Returns:
            Détails de l'espèce ou dictionnaire vide si non trouvée
        """
        if species_name in self.species_compatibility:
            return self.species_compatibility[species_name]
        else:
            self.logger.warning(f"Espèce non trouvée: {species_name}")
            return {}
    
    def get_all_species_names(self) -> List[str]:
        """
        Récupère la liste de toutes les espèces disponibles.
        
        Returns:
            Liste des noms d'espèces
        """
        return list(self.species_compatibility.keys())
    
    def get_tolerance_ranking(self, risk_type: str, zone_id: str = None, 
                            scenario: str = "current") -> List[Dict[str, Any]]:
        """
        Classe les espèces selon leur tolérance à un risque spécifique.
        
        Args:
            risk_type: Type de risque ("drought", "frost", "fire", "pests")
            zone_id: Identifiant de la zone climatique (optionnel)
            scenario: Scénario climatique (si zone_id est spécifié)
            
        Returns:
            Liste des espèces classées par tolérance décroissante au risque
        """
        try:
            species_list = []
            
            # Filtrer par compatibilité si zone_id est spécifié
            if zone_id:
                species_data = self.get_compatible_species(zone_id, scenario)
            else:
                species_data = {
                    name: {"species_name": name, "common_name": data.get("common_name", ""), "risks": data.get("risks", {})}
                    for name, data in self.species_compatibility.items()
                }
            
            # Préparer la liste avec les scores de tolérance
            for name, data in species_data.items():
                risk_score = 0.0
                
                if "risks" in data and risk_type in data["risks"]:
                    risk_level = data["risks"][risk_type]
                    if isinstance(risk_level, str):  # Si c'est un niveau (low, medium, high)
                        risk_score = self.RISK_SCORES.get(risk_level, 0.0)
                
                species_list.append({
                    "species_name": name,
                    "common_name": data.get("common_name", ""),
                    "risk_level": data.get("risks", {}).get(risk_type, "unknown"),
                    "tolerance_score": risk_score
                })
            
            # Trier par score de tolérance décroissant
            sorted_species = sorted(species_list, key=lambda x: x["tolerance_score"], reverse=True)
            
            return sorted_species
            
        except Exception as e:
            self.logger.error(f"Erreur lors du classement par tolérance aux risques: {str(e)}")
            return []
    
    def _calculate_score(self, species_data: Dict[str, Any], criteria: Dict[str, float]) -> float:
        """
        Calcule le score global pour une espèce en fonction des critères.
        
        Args:
            species_data: Données de l'espèce
            criteria: Poids des critères pour le calcul du score
            
        Returns:
            Score global entre 0 et 1
        """
        score = 0.0
        total_weight = 0.0
        
        # Score de compatibilité climatique
        compatibility = species_data.get("compatibility", "unsuitable")
        compatibility_score = self.COMPATIBILITY_SCORES.get(compatibility, 0.0)
        compatibility_weight = criteria.get("compatibility", 1.0)
        
        score += compatibility_score * compatibility_weight
        total_weight += compatibility_weight
        
        # Score économique
        economic_value = species_data.get("economic_value", "medium")
        economic_score = self.VALUE_SCORES.get(economic_value, 0.5)
        economic_weight = criteria.get("economic_value", 0.7)
        
        score += economic_score * economic_weight
        total_weight += economic_weight
        
        # Score écologique
        ecological_value = species_data.get("ecological_value", "medium")
        ecological_score = self.VALUE_SCORES.get(ecological_value, 0.5)
        ecological_weight = criteria.get("ecological_value", 0.7)
        
        score += ecological_score * ecological_weight
        total_weight += ecological_weight
        
        # Score de croissance
        growth_rate = species_data.get("growth_rate", "medium")
        growth_score = self.GROWTH_RATE_SCORES.get(growth_rate, 0.5)
        growth_weight = criteria.get("growth_rate", 0.6)
        
        score += growth_score * growth_weight
        total_weight += growth_weight
        
        # Scores de risques
        risks = species_data.get("risks", {})
        
        # Sécheresse
        if "drought" in risks:
            drought_score = self.RISK_SCORES.get(risks["drought"], 0.5)
            drought_weight = criteria.get("risk_drought", 0.8)
            
            score += drought_score * drought_weight
            total_weight += drought_weight
        
        # Gel
        if "frost" in risks:
            frost_score = self.RISK_SCORES.get(risks["frost"], 0.5)
            frost_weight = criteria.get("risk_frost", 0.7)
            
            score += frost_score * frost_weight
            total_weight += frost_weight
        
        # Feu
        if "fire" in risks:
            fire_score = self.RISK_SCORES.get(risks["fire"], 0.5)
            fire_weight = criteria.get("risk_fire", 0.6)
            
            score += fire_score * fire_weight
            total_weight += fire_weight
        
        # Normaliser le score
        if total_weight > 0:
            return score / total_weight
        else:
            return 0.0
