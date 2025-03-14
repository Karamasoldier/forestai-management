"""
Service de détection automatique des zones prioritaires pour subventions.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class PriorityZoneService:
    """
    Service spécialisé dans la détection automatique des zones prioritaires
    pour les subventions forestières.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le service de détection des zones prioritaires.
        
        Args:
            config: Configuration du service
        """
        self.config = config
        self.data_path = config.get('DATA_PATH', os.path.join(os.getcwd(), 'data'))
        self.zones_path = os.path.join(self.data_path, 'zones_prioritaires')
        
        # Créer le répertoire des zones prioritaires s'il n'existe pas
        os.makedirs(self.zones_path, exist_ok=True)
        
        logger.info(f"PriorityZoneService initialized with zones_path={self.zones_path}")
    
    def detect_priority_zones(self, geometry: Dict[str, Any], region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Détecte automatiquement les zones prioritaires selon la géométrie fournie.
        
        Args:
            geometry: Géométrie de la parcelle (GeoJSON)
            region: Région administrative (optionnel)
            
        Returns:
            Liste des zones prioritaires détectées avec leur couverture
        """
        logger.info(f"Detecting priority zones for geometry in region={region}")
        
        # Dans une implémentation réelle, cela ferait une analyse SIG des intersections
        # Pour l'exemple, nous utilisons des données simulées
        
        # Types de zones prioritaires à vérifier
        zone_types = [
            "Natura 2000",
            "Zone humide",
            "Réserve naturelle",
            "Parc national",
            "Parc naturel régional",
            "Zone de captage d'eau",
            "Territoire à risque incendie élevé",
            "Corridor écologique"
        ]
        
        # Simuler une détection basée sur la région
        detected_zones = []
        
        if region == "Provence-Alpes-Côte d'Azur":
            detected_zones = [
                {
                    "zone_type": "Natura 2000",
                    "code": "FR9301595",
                    "name": "Crau centrale - Crau sèche",
                    "coverage_percentage": 15.3,
                    "priority_level": "high"
                },
                {
                    "zone_type": "Zone humide",
                    "code": "13CREN0136",
                    "name": "Marais des Baux",
                    "coverage_percentage": 5.8,
                    "priority_level": "medium"
                },
                {
                    "zone_type": "Territoire à risque incendie élevé",
                    "code": "DFCI-13-04",
                    "name": "Zone DFCI Sud Alpilles",
                    "coverage_percentage": 100.0,
                    "priority_level": "high"
                }
            ]
        elif region == "Occitanie":
            detected_zones = [
                {
                    "zone_type": "Natura 2000",
                    "code": "FR9101410",
                    "name": "Étang de Capestang",
                    "coverage_percentage": 22.7,
                    "priority_level": "high"
                },
                {
                    "zone_type": "Parc naturel régional",
                    "code": "FR8000016",
                    "name": "Parc naturel régional du Haut-Languedoc",
                    "coverage_percentage": 78.5,
                    "priority_level": "medium"
                }
            ]
        else:
            # Pour les autres régions, générer des zones fictives
            # Dans une implémentation réelle, cela se baserait sur des données SIG
            detected_zones = [
                {
                    "zone_type": "Natura 2000",
                    "code": "FR9300000",
                    "name": "Zone Natura 2000 générique",
                    "coverage_percentage": 12.0,
                    "priority_level": "medium"
                }
            ]
        
        logger.info(f"Detected {len(detected_zones)} priority zones")
        return detected_zones
    
    def get_subsidy_impact(self, priority_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule l'impact des zones prioritaires sur les subventions potentielles.
        
        Args:
            priority_zones: Liste des zones prioritaires détectées
            
        Returns:
            Informations sur l'impact des zones prioritaires sur les subventions
        """
        logger.info(f"Calculating subsidy impact for {len(priority_zones)} priority zones")
        
        # Calculer le potentiel d'obtention de subventions
        impact = {
            "total_bonus_potential": 0.0,
            "zone_impacts": [],
            "recommended_subsidies": []
        }
        
        # Table de correspondance des types de zones avec les potentiels de bonus
        zone_bonus_map = {
            "Natura 2000": 15.0,
            "Zone humide": 20.0,
            "Réserve naturelle": 25.0,
            "Parc national": 20.0,
            "Parc naturel régional": 10.0,
            "Zone de captage d'eau": 15.0,
            "Territoire à risque incendie élevé": 20.0,
            "Corridor écologique": 15.0
        }
        
        for zone in priority_zones:
            zone_type = zone["zone_type"]
            coverage = zone.get("coverage_percentage", 100.0) / 100.0
            
            # Déterminer le bonus potentiel
            base_bonus = zone_bonus_map.get(zone_type, 5.0)
            weighted_bonus = base_bonus * coverage
            
            impact["total_bonus_potential"] += weighted_bonus
            
            impact["zone_impacts"].append({
                "zone_type": zone_type,
                "name": zone.get("name", ""),
                "coverage_percentage": zone.get("coverage_percentage", 100.0),
                "base_bonus": base_bonus,
                "weighted_bonus": round(weighted_bonus, 1)
            })
        
        # Recommander des types de subventions selon les zones
        if any(zone["zone_type"] == "Natura 2000" for zone in priority_zones):
            impact["recommended_subsidies"].append("biodiversité")
        
        if any(zone["zone_type"] == "Zone humide" for zone in priority_zones):
            impact["recommended_subsidies"].append("restauration_ecologique")
        
        if any(zone["zone_type"] == "Territoire à risque incendie élevé" for zone in priority_zones):
            impact["recommended_subsidies"].append("prevention_incendie")
        
        if any(zone["zone_type"] in ["Parc national", "Parc naturel régional"] for zone in priority_zones):
            impact["recommended_subsidies"].append("aires_protegees")
        
        # Arrondir le total
        impact["total_bonus_potential"] = round(impact["total_bonus_potential"], 1)
        
        logger.info(f"Total bonus potential: {impact['total_bonus_potential']}%")
        return impact
