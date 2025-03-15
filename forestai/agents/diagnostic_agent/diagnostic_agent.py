# -*- coding: utf-8 -*-
"""
DiagnosticAgent: Analyse des données terrain pour générer des diagnostics forestiers
et des plans de gestion.

Cet agent permet de:
- Analyser les données terrain importées
- Générer des rapports de diagnostic forestier
- Créer des plans de gestion adaptés aux parcelles
- Intégrer des données climatiques pour les recommandations
- Effectuer des analyses d'inventaire forestier
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

from forestai.agents.base_agent import BaseAgent
from forestai.core.domain.services.climate_analyzer import ClimateAnalyzer
from forestai.core.domain.services.species_recommender import SpeciesRecommender
from forestai.core.domain.services.forest_potential_service import ForestPotentialService
from forestai.core.infrastructure.cache.cache_utils import cached
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy

logger = logging.getLogger(__name__)

class DiagnosticAgent(BaseAgent):
    """Agent spécialisé dans l'analyse des données terrain et la génération
    de diagnostics forestiers et plans de gestion."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialise le DiagnosticAgent.

        Args:
            config: Configuration de l'agent avec les clés:
                - data_dir: Répertoire des données
                - templates_dir: Répertoire des modèles de documents
                - output_dir: Répertoire pour les sorties générées
        """
        super().__init__("diagnostic", config)
        self.config = config or {}
        
        # Répertoires par défaut si non spécifiés
        self.data_dir = Path(self.config.get("data_dir", "./data/diagnostic"))
        self.templates_dir = Path(self.config.get("templates_dir", "./templates/diagnostic"))
        self.output_dir = Path(self.config.get("output_dir", "./output/diagnostic"))
        
        # Création des répertoires s'ils n'existent pas
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Services utilisés par l'agent
        self.climate_analyzer = ClimateAnalyzer()
        self.species_recommender = SpeciesRecommender()
        self.forest_potential_service = None  # Initialisé à la demande
        
        logger.info(f"DiagnosticAgent initialisé avec data_dir={self.data_dir}")

    def initialize_services(self):
        """Initialise les services auxiliaires au besoin."""
        if self.forest_potential_service is None:
            # Initialisé à la demande pour éviter de charger inutilement les données géospatiales
            from forestai.core.infrastructure.repositories.geo_data_repository import GeoDataRepository
            from forestai.core.infrastructure.repositories.climate_repository import ClimateRepository
            
            geo_data_repo = GeoDataRepository()
            climate_repo = ClimateRepository()
            self.forest_potential_service = ForestPotentialService(geo_data_repo, climate_repo)
            logger.info("Services auxiliaires initialisés pour le DiagnosticAgent")
    
    @cached(data_type=CacheType.DIAGNOSTIC, policy=CachePolicy.DAILY)
    def generate_diagnostic(self, parcel_id: str, inventory_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Génère un diagnostic forestier pour une parcelle donnée.
        
        Args:
            parcel_id: Identifiant de la parcelle
            inventory_data: Données d'inventaire forestier (optionnel)
            
        Returns:
            Dictionnaire contenant le diagnostic forestier
        """
        self.initialize_services()
        
        # Récupération des données de la parcelle
        logger.info(f"Génération du diagnostic pour la parcelle {parcel_id}")
        
        try:
            # Obtention des caractéristiques de la parcelle via le ForestPotentialService
            parcel_data = self.forest_potential_service.get_parcel_info(parcel_id)
            
            if not parcel_data:
                logger.error(f"Parcelle {parcel_id} non trouvée")
                return {"error": f"Parcelle {parcel_id} non trouvée"}
                
            # Analyse du potentiel forestier
            potential_data = self.forest_potential_service.analyze_parcel_potential(parcel_id)
            
            # Recommandations climatiques
            parcel_geometry = parcel_data.get("geometry")
            climate_data = self.climate_analyzer.analyze_climate(parcel_geometry)
            
            # Recommandation d'espèces
            species_recommendations = self.species_recommender.recommend_species(
                parcel_geometry, 
                climate_scenario="current",
                soil_data=parcel_data.get("soil"),
                slope=parcel_data.get("slope")
            )
            
            # Future climate considerations
            future_recommendations = self.species_recommender.recommend_species(
                parcel_geometry, 
                climate_scenario="2050_rcp45",
                soil_data=parcel_data.get("soil"),
                slope=parcel_data.get("slope")
            )
            
            # Construction du diagnostic
            diagnostic = {
                "parcel_id": parcel_id,
                "parcel_data": parcel_data,
                "potential": potential_data,
                "climate": climate_data,
                "species_recommendations": species_recommendations,
                "future_climate": {
                    "scenario": "2050_rcp45",
                    "recommendations": future_recommendations
                },
                "timestamp": pd.Timestamp.now().isoformat()
            }
            
            # Intégration des données d'inventaire si fournies
            if inventory_data:
                diagnostic["inventory"] = self.analyze_inventory(inventory_data)
            
            logger.info(f"Diagnostic généré pour la parcelle {parcel_id}")
            return diagnostic
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du diagnostic pour {parcel_id}: {str(e)}")
            return {"error": str(e)}
    
    def analyze_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les données d'inventaire forestier.
        
        Args:
            inventory_data: Données d'inventaire à analyser
            
        Returns:
            Résultats de l'analyse d'inventaire
        """
        # Conversion en DataFrame pour faciliter l'analyse
        try:
            if isinstance(inventory_data, Dict) and "items" in inventory_data:
                df = pd.DataFrame(inventory_data["items"])
            elif isinstance(inventory_data, List):
                df = pd.DataFrame(inventory_data)
            else:
                raise ValueError("Format d'inventaire non reconnu")
            
            # Statistiques de base par espèce
            species_stats = df.groupby("species").agg({
                "diameter": ["count", "mean", "std", "min", "max"],
                "height": ["mean", "std", "min", "max"]
            }).reset_index()
            
            # Calcul du volume total (exemple simplifié)
            if "diameter" in df.columns and "height" in df.columns:
                # Formule simplifiée: volume = pi * (diameter/2)^2 * height * 0.5 (facteur de forme)
                import numpy as np
                df["volume"] = np.pi * ((df["diameter"]/100)/2)**2 * df["height"] * 0.5
                volume_by_species = df.groupby("species")["volume"].sum().to_dict()
                total_volume = df["volume"].sum()
            else:
                volume_by_species = {}
                total_volume = 0
            
            # Calcul de la densité si surface disponible
            density = None
            if "area" in inventory_data:
                trees_count = len(df)
                density = trees_count / inventory_data["area"]
            
            # Construction du résultat
            analysis = {
                "species_distribution": df["species"].value_counts().to_dict(),
                "species_stats": json.loads(species_stats.to_json()),
                "volume": {
                    "total": total_volume,
                    "by_species": volume_by_species
                }
            }
            
            if density is not None:
                analysis["density"] = density
                
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'inventaire: {str(e)}")
            return {"error": str(e)}
    
    def generate_management_plan(self, parcel_id: str, diagnostic: Optional[Dict[str, Any]] = None, 
                               goals: List[str] = None, horizon_years: int = 10) -> Dict[str, Any]:
        """Génère un plan de gestion forestière basé sur un diagnostic.
        
        Args:
            parcel_id: Identifiant de la parcelle
            diagnostic: Diagnostic existant (si non fourni, sera généré)
            goals: Objectifs de gestion (production, biodiversité, résilience...)
            horizon_years: Horizon temporel du plan en années
            
        Returns:
            Plan de gestion forestière
        """
        # Utiliser le diagnostic fourni ou en générer un nouveau
        if diagnostic is None:
            diagnostic = self.generate_diagnostic(parcel_id)
        
        # Objectifs par défaut si non spécifiés
        if goals is None:
            goals = ["production", "resilience"]
            
        logger.info(f"Génération d'un plan de gestion pour {parcel_id} avec objectifs: {goals}")
        
        try:
            # Extraction des données utiles du diagnostic
            parcel_data = diagnostic.get("parcel_data", {})
            potential = diagnostic.get("potential", {})
            recommendations = diagnostic.get("species_recommendations", {}).get("recommended_species", [])
            climate_data = diagnostic.get("climate", {})
            future_climate = diagnostic.get("future_climate", {})
            
            # Calcul de l'année cible
            from datetime import datetime
            current_year = datetime.now().year
            target_year = current_year + horizon_years
            
            # Définition des phases de gestion en fonction des objectifs
            phases = []
            
            # Exemple: Phase initiale
            phases.append({
                "name": "Diagnostic et préparation",
                "year": current_year,
                "actions": [
                    "Analyse complète du terrain",
                    "Définition des zones d'intervention",
                    "Planification des accès"
                ],
                "expected_outcomes": "Plan détaillé d'intervention"
            })
            
            # Phases ultérieures dépendant des objectifs
            if "production" in goals:
                species_for_production = [s for s in recommendations if s.get("suitability", {}).get("production", 0) > 0.7]
                if species_for_production:
                    best_production = species_for_production[0]["species_name"]
                    phases.append({
                        "name": "Plantation productive",
                        "year": current_year + 1,
                        "actions": [
                            f"Plantation de {best_production}",
                            "Mise en place de protections",
                            "Planification des éclaircies"
                        ],
                        "expected_outcomes": "Établissement d'un peuplement productif"
                    })
            
            if "resilience" in goals:
                resilient_species = [s for s in recommendations if s.get("suitability", {}).get("resilience", 0) > 0.7]
                if resilient_species:
                    phases.append({
                        "name": "Renforcement de la résilience",
                        "year": current_year + 2,
                        "actions": [
                            "Introduction d'essences mixtes",
                            "Création de structures forestières variées",
                            "Mise en place d'un suivi de l'adaptation au changement climatique"
                        ],
                        "expected_outcomes": "Peuplement plus résilient aux stress environnementaux"
                    })
            
            # Génération du plan complet
            management_plan = {
                "parcel_id": parcel_id,
                "created_at": pd.Timestamp.now().isoformat(),
                "horizon": {
                    "start_year": current_year,
                    "end_year": target_year,
                    "duration_years": horizon_years
                },
                "goals": goals,
                "summary": f"Plan de gestion forestière sur {horizon_years} ans avec focus sur {', '.join(goals)}",
                "phases": phases,
                "recommended_species": recommendations[:5],  # Top 5 recommendations
                "climate_considerations": {
                    "current": climate_data.get("summary", {}),
                    "future": future_climate.get("summary", {})
                },
                "monitoring_plan": {
                    "frequency": "annual",
                    "indicators": [
                        "Taux de survie des plantations",
                        "Croissance en hauteur et diamètre",
                        "Biodiversité associée",
                        "Résilience aux événements climatiques"
                    ]
                }
            }
            
            # Ajout de l'estimation des coûts
            estimated_area = parcel_data.get("area", 0)  # en hectares
            management_plan["estimated_costs"] = self._estimate_costs(estimated_area, goals, len(phases))
            
            logger.info(f"Plan de gestion généré pour {parcel_id}")
            return management_plan
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du plan de gestion pour {parcel_id}: {str(e)}")
            return {"error": str(e)}
    
    def _estimate_costs(self, area: float, goals: List[str], phases_count: int) -> Dict[str, Any]:
        """Estime les coûts de gestion en fonction de la surface et des objectifs.
        
        Args:
            area: Surface en hectares
            goals: Objectifs de gestion
            phases_count: Nombre de phases du plan
            
        Returns:
            Estimation des coûts
        """
        # Coûts par hectare pour différentes opérations (euros)
        cost_rates = {
            "diagnostic": 200,  # €/ha
            "plantation": 3000,  # €/ha
            "maintenance_annual": 300,  # €/ha/an
            "protection": 800,  # €/ha
            "thinning": 1200,  # €/ha
            "monitoring": 100  # €/ha/an
        }
        
        # Ajustement des coûts en fonction des objectifs
        if "biodiversity" in goals:
            cost_rates["plantation"] *= 1.2  # +20% pour la diversité des essences
            
        if "resilience" in goals:
            cost_rates["plantation"] *= 1.15  # +15% pour des essences plus adaptées
            
        # Calcul des coûts par phase
        phase_costs = []
        total_cost = 0
        
        # Phase initiale (diagnostic)
        initial_cost = cost_rates["diagnostic"] * area
        phase_costs.append({
            "phase": "Diagnostic initial",
            "cost": initial_cost,
            "details": f"Diagnostic complet à {cost_rates['diagnostic']}€/ha sur {area} ha"
        })
        total_cost += initial_cost
        
        # Phase de plantation (si applicable)
        if "production" in goals or "restoration" in goals:
            plantation_cost = cost_rates["plantation"] * area
            protection_cost = cost_rates["protection"] * area
            phase_costs.append({
                "phase": "Plantation et protection",
                "cost": plantation_cost + protection_cost,
                "details": f"Plantation à {cost_rates['plantation']}€/ha et protection à {cost_rates['protection']}€/ha sur {area} ha"
            })
            total_cost += plantation_cost + protection_cost
        
        # Maintenance annuelle
        maintenance_annual = cost_rates["maintenance_annual"] * area
        maintenance_total = maintenance_annual * 5  # 5 premières années
        phase_costs.append({
            "phase": "Maintenance (5 ans)",
            "cost": maintenance_total,
            "details": f"Maintenance annuelle à {cost_rates['maintenance_annual']}€/ha/an sur {area} ha pendant 5 ans"
        })
        total_cost += maintenance_total
        
        # Éclaircies (si applicable pour production)
        if "production" in goals:
            thinning_cost = cost_rates["thinning"] * area
            phase_costs.append({
                "phase": "Éclaircies",
                "cost": thinning_cost,
                "details": f"Éclaircies à {cost_rates['thinning']}€/ha sur {area} ha"
            })
            total_cost += thinning_cost
        
        # Monitoring
        monitoring_cost = cost_rates["monitoring"] * area * 10  # sur 10 ans
        phase_costs.append({
            "phase": "Monitoring (10 ans)",
            "cost": monitoring_cost,
            "details": f"Suivi annuel à {cost_rates['monitoring']}€/ha/an sur {area} ha pendant 10 ans"
        })
        total_cost += monitoring_cost
        
        return {
            "total": total_cost,
            "per_hectare": total_cost / area if area > 0 else 0,
            "phase_breakdown": phase_costs,
            "disclaimer": "Estimation indicative susceptible de varier selon les conditions du terrain et du marché"
        }
    
    def export_diagnostic_json(self, diagnostic: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """Exporte un diagnostic au format JSON.
        
        Args:
            diagnostic: Diagnostic à exporter
            output_path: Chemin d'export (optionnel)
            
        Returns:
            Chemin du fichier exporté
        """
        if output_path is None:
            parcel_id = diagnostic.get("parcel_id", "unknown")
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"diagnostic_{parcel_id}_{timestamp}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(diagnostic, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Diagnostic exporté vers {output_path}")
        return output_path
    
    def export_management_plan_json(self, plan: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """Exporte un plan de gestion au format JSON.
        
        Args:
            plan: Plan de gestion à exporter
            output_path: Chemin d'export (optionnel)
            
        Returns:
            Chemin du fichier exporté
        """
        if output_path is None:
            parcel_id = plan.get("parcel_id", "unknown")
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"management_plan_{parcel_id}_{timestamp}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Plan de gestion exporté vers {output_path}")
        return output_path
    
    def available_actions(self) -> List[Dict[str, Any]]:
        """Liste les actions disponibles pour cet agent.
        
        Returns:
            Liste des actions disponibles avec leur description
        """
        return [
            {
                "name": "generate_diagnostic",
                "description": "Génère un diagnostic forestier pour une parcelle",
                "parameters": {
                    "parcel_id": "Identifiant de la parcelle",
                    "inventory_data": "Données d'inventaire forestier (optionnel)"
                }
            },
            {
                "name": "generate_management_plan",
                "description": "Génère un plan de gestion forestière",
                "parameters": {
                    "parcel_id": "Identifiant de la parcelle",
                    "diagnostic": "Diagnostic existant (optionnel)",
                    "goals": "Objectifs de gestion (liste)",
                    "horizon_years": "Horizon temporel en années"
                }
            },
            {
                "name": "analyze_inventory",
                "description": "Analyse des données d'inventaire forestier",
                "parameters": {
                    "inventory_data": "Données d'inventaire à analyser"
                }
            },
            {
                "name": "export_diagnostic_json",
                "description": "Exporte un diagnostic au format JSON",
                "parameters": {
                    "diagnostic": "Diagnostic à exporter",
                    "output_path": "Chemin d'export (optionnel)"
                }
            },
            {
                "name": "export_management_plan_json",
                "description": "Exporte un plan de gestion au format JSON",
                "parameters": {
                    "plan": "Plan de gestion à exporter",
                    "output_path": "Chemin d'export (optionnel)"
                }
            }
        ]
