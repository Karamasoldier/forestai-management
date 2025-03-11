"""
Service d'analyse du potentiel forestier des parcelles.

Ce service encapsule la logique métier pour évaluer le potentiel forestier
des parcelles en fonction de leurs caractéristiques géographiques, topographiques,
et environnementales.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from ...domain.models.parcel import Parcel, ForestPotential, TerrainCharacteristics


class ForestPotentialService:
    """
    Service responsable de l'analyse du potentiel forestier des parcelles.
    """
    
    def __init__(self, climate_repository=None, species_repository=None):
        """
        Initialise le service d'analyse du potentiel forestier.
        
        Args:
            climate_repository: Repository pour accéder aux données climatiques
            species_repository: Repository pour accéder aux informations sur les espèces forestières
        """
        self.logger = logging.getLogger(__name__)
        self.climate_repository = climate_repository
        self.species_repository = species_repository
        
        # Paramètres d'analyse par défaut
        self.analysis_parameters = {
            "slope_weight": 0.3,  # Poids de la pente dans le score final
            "soil_weight": 0.3,   # Poids du type de sol dans le score final
            "climate_weight": 0.4, # Poids du climat dans le score final
            "max_viable_slope": 30.0,  # Pente maximale en degrés pour une plantation viable
            "min_soil_depth": 30.0,  # Profondeur minimale de sol en cm
            "wetland_penalty": 0.5,  # Pénalité pour les zones humides
            "drought_risk_factor": 0.2,  # Facteur de risque lié à la sécheresse
        }
        
        # Correspondance des types de sol avec leur potentiel forestier (0-1)
        self.soil_potential_mapping = {
            "argile": 0.8,
            "limon": 0.9,
            "sable": 0.5,
            "calcaire": 0.6,
            "grès": 0.7,
            "alluvion": 0.8,
            "tourbe": 0.3,
            "caillouteux": 0.4,
            "rocheux": 0.2,
        }
        
        # Correspondance des orientations avec leur potentiel forestier (0-1)
        self.aspect_potential_mapping = {
            "N": 0.7,   # Nord - moins d'ensoleillement
            "NE": 0.75,
            "E": 0.85,
            "SE": 0.9,
            "S": 0.95,  # Sud - ensoleillement maximal
            "SW": 0.9,
            "W": 0.85,
            "NW": 0.75,
        }
    
    def analyze_parcel_potential(self, parcel: Parcel) -> ForestPotential:
        """
        Analyse le potentiel forestier d'une parcelle.
        
        Args:
            parcel: Parcelle à analyser
            
        Returns:
            ForestPotential contenant le score et les caractéristiques du potentiel forestier
        """
        self.logger.info(f"Analysing forest potential for parcel {parcel.identifier.to_string()}")
        
        # S'assurer que la parcelle a des caractéristiques de terrain
        if parcel.terrain is None:
            self.logger.warning(f"Parcelle {parcel.identifier.to_string()} sans caractéristiques de terrain")
            # Créer un terrain par défaut pour éviter les erreurs
            parcel.terrain = TerrainCharacteristics()
        
        # Analyser les différents facteurs
        slope_score = self._analyze_slope(parcel.terrain)
        soil_score = self._analyze_soil(parcel.terrain)
        climate_score = self._analyze_climate(parcel)
        
        # Calculer le score global
        overall_score = (
            self.analysis_parameters["slope_weight"] * slope_score +
            self.analysis_parameters["soil_weight"] * soil_score +
            self.analysis_parameters["climate_weight"] * climate_score
        )
        
        # Limiter le score entre 0 et 1
        overall_score = max(0.0, min(1.0, overall_score))
        
        # Déterminer les espèces adaptées
        suitable_species = self._find_suitable_species(parcel, overall_score)
        
        # Identifier les limitations et opportunités
        limitations, opportunities = self._identify_factors(parcel, slope_score, soil_score, climate_score)
        
        # Calculer les potentiels spécifiques
        carbon_potential = self._calculate_carbon_potential(parcel, overall_score)
        timber_potential = self._calculate_timber_potential(parcel, overall_score, suitable_species)
        biodiversity_score = self._calculate_biodiversity_score(parcel)
        
        # Créer et retourner l'objet ForestPotential
        return ForestPotential(
            score=overall_score,
            suitable_species=suitable_species,
            limitations=limitations,
            opportunities=opportunities,
            carbon_potential=carbon_potential,
            timber_potential=timber_potential,
            biodiversity_score=biodiversity_score
        )
    
    def _analyze_slope(self, terrain: TerrainCharacteristics) -> float:
        """
        Analyse la pente du terrain et calcule un score.
        
        Args:
            terrain: Caractéristiques du terrain
            
        Returns:
            Score de pente entre 0 et 1
        """
        # Une pente trop forte est défavorable pour la plantation
        max_viable_slope = self.analysis_parameters["max_viable_slope"]
        
        if terrain.avg_slope >= max_viable_slope:
            return 0.0
        
        # Score décroissant avec la pente
        return 1.0 - (terrain.avg_slope / max_viable_slope)
    
    def _analyze_soil(self, terrain: TerrainCharacteristics) -> float:
        """
        Analyse le sol et calcule un score.
        
        Args:
            terrain: Caractéristiques du terrain
            
        Returns:
            Score de sol entre 0 et 1
        """
        # Score de base selon le type de sol
        base_score = self.soil_potential_mapping.get(terrain.soil_type.lower(), 0.5)
        
        # Réduction pour les zones humides
        if terrain.water_presence or terrain.wetland_area_pct > 0:
            wetland_factor = terrain.wetland_area_pct / 100 if terrain.wetland_area_pct > 0 else 0.5
            base_score *= (1 - self.analysis_parameters["wetland_penalty"] * wetland_factor)
        
        return max(0.0, min(1.0, base_score))
    
    def _analyze_climate(self, parcel: Parcel) -> float:
        """
        Analyse le climat et calcule un score.
        
        Args:
            parcel: Parcelle à analyser
            
        Returns:
            Score climatique entre 0 et 1
        """
        # Score de base selon l'orientation (aspect)
        aspect_score = self.aspect_potential_mapping.get(
            parcel.terrain.aspect, 0.8  # Valeur par défaut si l'orientation n'est pas spécifiée
        )
        
        # Si nous avons un repository climat, récupérer des données plus précises
        climate_factor = 1.0
        if self.climate_repository:
            try:
                climate_data = self.climate_repository.get_climate_data(
                    parcel.geometry.centroid_x, 
                    parcel.geometry.centroid_y
                )
                
                # Calculer un facteur climatique basé sur les précipitations et températures
                if climate_data:
                    precipitation = climate_data.get("annual_precipitation", 800)  # mm/an
                    avg_temperature = climate_data.get("avg_temperature", 12)  # °C
                    
                    # Formule simplifiée: plus de précipitations et température modérée sont favorables
                    precipitation_factor = min(1.0, precipitation / 1000)
                    temperature_factor = 1.0 - abs(avg_temperature - 12) / 20
                    
                    climate_factor = 0.6 * precipitation_factor + 0.4 * temperature_factor
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des données climatiques: {str(e)}")
        
        return aspect_score * climate_factor
    
    def _find_suitable_species(self, parcel: Parcel, overall_score: float) -> List[str]:
        """
        Détermine les espèces forestières adaptées à la parcelle.
        
        Args:
            parcel: Parcelle à analyser
            overall_score: Score global de potentiel forestier
            
        Returns:
            Liste des espèces adaptées
        """
        suitable_species = []
        
        # Si nous avons un repository d'espèces, l'utiliser pour une recommandation précise
        if self.species_repository:
            try:
                # Récupérer les caractéristiques clés pour la sélection d'espèces
                characteristics = {
                    "soil_type": parcel.terrain.soil_type,
                    "avg_slope": parcel.terrain.avg_slope,
                    "aspect": parcel.terrain.aspect,
                    "avg_elevation": parcel.terrain.avg_elevation,
                    "water_presence": parcel.terrain.water_presence,
                }
                
                suitable_species = self.species_repository.find_suitable_species(characteristics)
            except Exception as e:
                self.logger.error(f"Erreur lors de la recherche d'espèces adaptées: {str(e)}")
        
        # Si pas de species repository ou pas de résultats, utiliser une liste par défaut
        if not suitable_species:
            # Liste simplifiée basée sur le score global
            if overall_score > 0.8:
                suitable_species = ["chêne sessile", "hêtre", "châtaignier", "douglas"]
            elif overall_score > 0.6:
                suitable_species = ["pin sylvestre", "pin maritime", "érable sycomore", "mélèze"]
            elif overall_score > 0.4:
                suitable_species = ["bouleau", "robinier", "aulne", "peuplier"]
            else:
                suitable_species = ["pin noir", "genévrier", "bouleau"]
        
        return suitable_species
    
    def _identify_factors(self, parcel: Parcel, slope_score: float, 
                         soil_score: float, climate_score: float) -> Tuple[List[str], List[str]]:
        """
        Identifie les limitations et opportunités pour la parcelle.
        
        Args:
            parcel: Parcelle à analyser
            slope_score: Score de la pente
            soil_score: Score du sol
            climate_score: Score du climat
            
        Returns:
            Tuple (limitations, opportunités)
        """
        limitations = []
        opportunities = []
        
        # Analyser les limitations
        if slope_score < 0.4:
            limitations.append(f"Pente importante ({parcel.terrain.avg_slope:.1f}°) limitant l'accès et augmentant l'érosion")
        
        if soil_score < 0.4:
            if parcel.terrain.soil_type.lower() in ["rocheux", "caillouteux"]:
                limitations.append(f"Sol {parcel.terrain.soil_type} peu propice à la croissance des arbres")
            elif parcel.terrain.wetland_area_pct > 30:
                limitations.append(f"Zone humide importante ({parcel.terrain.wetland_area_pct}% de la surface)")
        
        if climate_score < 0.4:
            if parcel.terrain.aspect in ["N", "NE", "NW"]:
                limitations.append(f"Exposition {parcel.terrain.aspect} limitant l'ensoleillement")
        
        # Analyser les opportunités
        if slope_score > 0.7:
            opportunities.append("Terrain peu pentu facilitant les interventions sylvicoles")
        
        if soil_score > 0.7:
            opportunities.append(f"Sol {parcel.terrain.soil_type} favorable à la croissance forestière")
        
        if climate_score > 0.7:
            if parcel.terrain.aspect in ["S", "SE", "SW"]:
                opportunities.append(f"Bonne exposition {parcel.terrain.aspect} favorisant la croissance")
        
        if parcel.terrain.water_presence:
            opportunities.append("Présence d'eau favorable à certaines essences adaptées")
        
        return limitations, opportunities
    
    def _calculate_carbon_potential(self, parcel: Parcel, overall_score: float) -> float:
        """
        Calcule le potentiel de séquestration carbone.
        
        Args:
            parcel: Parcelle à analyser
            overall_score: Score global de potentiel forestier
            
        Returns:
            Potentiel de séquestration carbone en tonnes CO2/ha/an
        """
        # Valeurs moyennes de séquestration pour différents types de forêts
        # Entre 5 et 15 tonnes de CO2 par hectare et par an pour une forêt productive
        base_sequestration = 10.0  # tonnes CO2/ha/an
        
        # Ajuster selon le score global
        adjusted_sequestration = base_sequestration * overall_score
        
        # Ajuster selon la surface
        total_potential = adjusted_sequestration * parcel.geometry.area_ha
        
        return total_potential
    
    def _calculate_timber_potential(self, parcel: Parcel, overall_score: float, 
                                   species: List[str]) -> float:
        """
        Calcule le potentiel de production de bois.
        
        Args:
            parcel: Parcelle à analyser
            overall_score: Score global de potentiel forestier
            species: Espèces forestières adaptées
            
        Returns:
            Potentiel de production de bois en m³/ha/an
        """
        # Valeurs moyennes de production selon les espèces
        species_production = {
            "douglas": 15.0,
            "pin maritime": 12.0,
            "pin sylvestre": 8.0,
            "mélèze": 10.0,
            "chêne sessile": 6.0,
            "hêtre": 7.0,
            "châtaignier": 9.0,
            "érable sycomore": 8.0,
            "peuplier": 15.0,
            "robinier": 10.0,
            "aulne": 8.0,
            "bouleau": 6.0,
            "pin noir": 7.0,
            "genévrier": 3.0,
        }
        
        # Calculer la production moyenne pour les espèces recommandées
        if species:
            avg_production = sum(species_production.get(s.lower(), 8.0) for s in species) / len(species)
        else:
            avg_production = 8.0  # Valeur par défaut
        
        # Ajuster selon le score global
        adjusted_production = avg_production * overall_score
        
        # Calculer pour la surface totale
        total_potential = adjusted_production * parcel.geometry.area_ha
        
        return total_potential
    
    def _calculate_biodiversity_score(self, parcel: Parcel) -> float:
        """
        Calcule un score de potentiel de biodiversité.
        
        Args:
            parcel: Parcelle à analyser
            
        Returns:
            Score de biodiversité entre 0 et 1
        """
        # Éléments favorables à la biodiversité
        factors = []
        
        # Présence d'eau
        if parcel.terrain.water_presence:
            factors.append(0.2)
        
        # Zones humides (en proportion modérée)
        if 0 < parcel.terrain.wetland_area_pct < 50:
            factors.append(0.15 * (parcel.terrain.wetland_area_pct / 50))
        
        # Variation d'altitude
        elevation_range = parcel.terrain.max_elevation - parcel.terrain.min_elevation
        if elevation_range > 20:
            factors.append(min(0.15, 0.15 * (elevation_range / 100)))
        
        # Type de sol favorable
        if parcel.terrain.soil_type.lower() in ["limon", "alluvion"]:
            factors.append(0.1)
        
        # Score de base pour toute parcelle forestière
        base_score = 0.5
        
        # Calculer le score final
        biodiversity_score = base_score + sum(factors)
        
        # Limiter entre 0 et 1
        return max(0.0, min(1.0, biodiversity_score))
