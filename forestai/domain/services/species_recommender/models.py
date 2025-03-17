"""
Modèles pour le système de recommandation d'espèces.

Ce module définit les structures de données utilisées par le système
de recommandation d'espèces forestières.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime


class SoilType(Enum):
    """Types de sols pour la recommandation d'espèces."""
    SANDY = "sableux"
    CLAY = "argileux"
    LOAM = "limoneux"
    CHALKY = "calcaire"
    ACIDIC = "acide"
    PEATY = "tourbeux"
    SILTY = "silteux"
    ROCKY = "rocailleux"


class MoistureRegime(Enum):
    """Régimes d'humidité du sol."""
    VERY_DRY = "très sec"
    DRY = "sec"
    MEDIUM = "moyen"
    MOIST = "humide"
    WET = "très humide"
    WATERLOGGED = "hydromorphe"


class DroughtResistance(Enum):
    """Niveaux de résistance à la sécheresse."""
    VERY_LOW = "très faible"
    LOW = "faible"
    MEDIUM = "moyenne"
    HIGH = "élevée"
    VERY_HIGH = "très élevée"


class FrostResistance(Enum):
    """Niveaux de résistance au gel."""
    VERY_LOW = "très faible"
    LOW = "faible"
    MEDIUM = "moyenne"
    HIGH = "élevée"
    VERY_HIGH = "très élevée"


class GrowthRate(Enum):
    """Taux de croissance des espèces."""
    VERY_SLOW = "très lent"
    SLOW = "lent"
    MEDIUM = "moyen"
    FAST = "rapide"
    VERY_FAST = "très rapide"


class EconomicValue(Enum):
    """Valeur économique des espèces."""
    VERY_LOW = "très faible"
    LOW = "faible"
    MEDIUM = "moyenne"
    HIGH = "élevée"
    VERY_HIGH = "très élevée"


class EcologicalValue(Enum):
    """Valeur écologique des espèces."""
    VERY_LOW = "très faible"
    LOW = "faible"
    MEDIUM = "moyenne"
    HIGH = "élevée"
    VERY_HIGH = "très élevée"


class WoodUse(Enum):
    """Utilisations possibles du bois."""
    CONSTRUCTION = "construction"
    FURNITURE = "ameublement"
    PULP = "pâte à papier"
    ENERGY = "énergie/chauffage"
    VENEER = "placage"
    ARTISANAL = "artisanat"
    MULTIPURPOSE = "multiple"


@dataclass
class SpeciesData:
    """Données de base sur une espèce forestière."""
    id: str
    latin_name: str
    common_name: str
    family: str
    growth_form: str  # Arbre, arbuste, etc.
    native: bool
    description: str = ""
    
    # Caractéristiques environnementales
    min_temperature: float = None  # °C
    max_temperature: float = None  # °C
    optimal_temperature_range: tuple = None  # (min, max) en °C
    annual_rainfall_range: tuple = None  # (min, max) en mm
    altitude_range: tuple = None  # (min, max) en m
    
    # Tolérance et exigences
    suitable_soil_types: List[SoilType] = field(default_factory=list)
    suitable_moisture_regimes: List[MoistureRegime] = field(default_factory=list)
    drought_resistance: DroughtResistance = None
    frost_resistance: FrostResistance = None
    shade_tolerance: int = None  # 0-10
    wind_resistance: int = None  # 0-10
    fire_resistance: int = None  # 0-10
    
    # Caractéristiques de croissance
    growth_rate: GrowthRate = None
    max_height: float = None  # mètres
    max_dbh: float = None  # diamètre à hauteur de poitrine en cm
    longevity: int = None  # années
    root_system_type: str = ""
    
    # Caractéristiques économiques
    economic_value: EconomicValue = None
    rotation_age: int = None  # années
    wood_density: float = None  # kg/m³
    wood_uses: List[WoodUse] = field(default_factory=list)
    
    # Caractéristiques écologiques
    ecological_value: EcologicalValue = None
    carbon_sequestration_rate: float = None  # tonnes CO2/ha/an
    wildlife_value: int = None  # 0-10
    erosion_control: int = None  # 0-10
    
    # Sensibilité aux pathogènes
    pest_vulnerability: Dict[str, int] = field(default_factory=dict)  # nom: niveau (0-10)
    disease_vulnerability: Dict[str, int] = field(default_factory=dict)  # nom: niveau (0-10)
    
    # Métadonnées
    tags: List[str] = field(default_factory=list)
    data_source: str = ""
    last_updated: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        result = {
            "id": self.id,
            "latin_name": self.latin_name,
            "common_name": self.common_name,
            "family": self.family,
            "growth_form": self.growth_form,
            "native": self.native,
            "description": self.description,
        }
        
        # Ajouter les caractéristiques non nulles
        if self.min_temperature is not None:
            result["min_temperature"] = self.min_temperature
        if self.max_temperature is not None:
            result["max_temperature"] = self.max_temperature
        if self.optimal_temperature_range is not None:
            result["optimal_temperature_range"] = {
                "min": self.optimal_temperature_range[0],
                "max": self.optimal_temperature_range[1]
            }
        if self.annual_rainfall_range is not None:
            result["annual_rainfall_range"] = {
                "min": self.annual_rainfall_range[0],
                "max": self.annual_rainfall_range[1]
            }
        if self.altitude_range is not None:
            result["altitude_range"] = {
                "min": self.altitude_range[0],
                "max": self.altitude_range[1]
            }
        
        # Sols et humidité
        if self.suitable_soil_types:
            result["suitable_soil_types"] = [st.value for st in self.suitable_soil_types]
        if self.suitable_moisture_regimes:
            result["suitable_moisture_regimes"] = [mr.value for mr in self.suitable_moisture_regimes]
        
        # Résistances
        if self.drought_resistance:
            result["drought_resistance"] = self.drought_resistance.value
        if self.frost_resistance:
            result["frost_resistance"] = self.frost_resistance.value
        if self.shade_tolerance is not None:
            result["shade_tolerance"] = self.shade_tolerance
        if self.wind_resistance is not None:
            result["wind_resistance"] = self.wind_resistance
        if self.fire_resistance is not None:
            result["fire_resistance"] = self.fire_resistance
        
        # Croissance
        if self.growth_rate:
            result["growth_rate"] = self.growth_rate.value
        if self.max_height is not None:
            result["max_height"] = self.max_height
        if self.max_dbh is not None:
            result["max_dbh"] = self.max_dbh
        if self.longevity is not None:
            result["longevity"] = self.longevity
        if self.root_system_type:
            result["root_system_type"] = self.root_system_type
        
        # Valeur économique
        if self.economic_value:
            result["economic_value"] = self.economic_value.value
        if self.rotation_age is not None:
            result["rotation_age"] = self.rotation_age
        if self.wood_density is not None:
            result["wood_density"] = self.wood_density
        if self.wood_uses:
            result["wood_uses"] = [wu.value for wu in self.wood_uses]
        
        # Valeur écologique
        if self.ecological_value:
            result["ecological_value"] = self.ecological_value.value
        if self.carbon_sequestration_rate is not None:
            result["carbon_sequestration_rate"] = self.carbon_sequestration_rate
        if self.wildlife_value is not None:
            result["wildlife_value"] = self.wildlife_value
        if self.erosion_control is not None:
            result["erosion_control"] = self.erosion_control
        
        # Vulnérabilités
        if self.pest_vulnerability:
            result["pest_vulnerability"] = self.pest_vulnerability
        if self.disease_vulnerability:
            result["disease_vulnerability"] = self.disease_vulnerability
        
        # Métadonnées
        if self.tags:
            result["tags"] = self.tags
        if self.data_source:
            result["data_source"] = self.data_source
        if self.last_updated:
            result["last_updated"] = self.last_updated.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpeciesData':
        """Crée une instance à partir d'un dictionnaire."""
        species_data = cls(
            id=data["id"],
            latin_name=data["latin_name"],
            common_name=data["common_name"],
            family=data["family"],
            growth_form=data["growth_form"],
            native=data["native"],
            description=data.get("description", "")
        )
        
        # Ajouter les caractéristiques si présentes
        if "min_temperature" in data:
            species_data.min_temperature = data["min_temperature"]
        if "max_temperature" in data:
            species_data.max_temperature = data["max_temperature"]
        if "optimal_temperature_range" in data:
            temp_range = data["optimal_temperature_range"]
            species_data.optimal_temperature_range = (temp_range["min"], temp_range["max"])
        if "annual_rainfall_range" in data:
            rain_range = data["annual_rainfall_range"]
            species_data.annual_rainfall_range = (rain_range["min"], rain_range["max"])
        if "altitude_range" in data:
            alt_range = data["altitude_range"]
            species_data.altitude_range = (alt_range["min"], alt_range["max"])
        
        # Sols et humidité
        if "suitable_soil_types" in data:
            species_data.suitable_soil_types = [
                SoilType(st) for st in data["suitable_soil_types"]
                if st and any(st == soil_type.value for soil_type in SoilType)
            ]
        if "suitable_moisture_regimes" in data:
            species_data.suitable_moisture_regimes = [
                MoistureRegime(mr) for mr in data["suitable_moisture_regimes"]
                if mr and any(mr == moisture.value for moisture in MoistureRegime)
            ]
        
        # Résistances
        if "drought_resistance" in data and data["drought_resistance"]:
            try:
                species_data.drought_resistance = DroughtResistance(data["drought_resistance"])
            except ValueError:
                pass
        if "frost_resistance" in data and data["frost_resistance"]:
            try:
                species_data.frost_resistance = FrostResistance(data["frost_resistance"])
            except ValueError:
                pass
        if "shade_tolerance" in data:
            species_data.shade_tolerance = data["shade_tolerance"]
        if "wind_resistance" in data:
            species_data.wind_resistance = data["wind_resistance"]
        if "fire_resistance" in data:
            species_data.fire_resistance = data["fire_resistance"]
        
        # Croissance
        if "growth_rate" in data and data["growth_rate"]:
            try:
                species_data.growth_rate = GrowthRate(data["growth_rate"])
            except ValueError:
                pass
        if "max_height" in data:
            species_data.max_height = data["max_height"]
        if "max_dbh" in data:
            species_data.max_dbh = data["max_dbh"]
        if "longevity" in data:
            species_data.longevity = data["longevity"]
        if "root_system_type" in data:
            species_data.root_system_type = data["root_system_type"]
        
        # Valeur économique
        if "economic_value" in data and data["economic_value"]:
            try:
                species_data.economic_value = EconomicValue(data["economic_value"])
            except ValueError:
                pass
        if "rotation_age" in data:
            species_data.rotation_age = data["rotation_age"]
        if "wood_density" in data:
            species_data.wood_density = data["wood_density"]
        if "wood_uses" in data:
            species_data.wood_uses = [
                WoodUse(wu) for wu in data["wood_uses"]
                if wu and any(wu == use.value for use in WoodUse)
            ]
        
        # Valeur écologique
        if "ecological_value" in data and data["ecological_value"]:
            try:
                species_data.ecological_value = EcologicalValue(data["ecological_value"])
            except ValueError:
                pass
        if "carbon_sequestration_rate" in data:
            species_data.carbon_sequestration_rate = data["carbon_sequestration_rate"]
        if "wildlife_value" in data:
            species_data.wildlife_value = data["wildlife_value"]
        if "erosion_control" in data:
            species_data.erosion_control = data["erosion_control"]
        
        # Vulnérabilités
        if "pest_vulnerability" in data:
            species_data.pest_vulnerability = data["pest_vulnerability"]
        if "disease_vulnerability" in data:
            species_data.disease_vulnerability = data["disease_vulnerability"]
        
        # Métadonnées
        if "tags" in data:
            species_data.tags = data["tags"]
        if "data_source" in data:
            species_data.data_source = data["data_source"]
        if "last_updated" in data and data["last_updated"]:
            try:
                species_data.last_updated = datetime.fromisoformat(data["last_updated"])
            except (ValueError, TypeError):
                pass
        
        return species_data


@dataclass
class RecommendationScore:
    """Score de recommandation pour une espèce."""
    species_id: str
    overall_score: float  # Score global (0-1)
    climate_score: float  # Score climatique (0-1)
    soil_score: float  # Score pédologique (0-1)
    economic_score: float = None  # Score économique (0-1)
    ecological_score: float = None  # Score écologique (0-1)
    risk_score: float = None  # Score de risque (0-1)
    score_details: Dict[str, Any] = field(default_factory=dict)  # Détails du calcul de score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        result = {
            "species_id": self.species_id,
            "overall_score": round(self.overall_score, 3),
            "climate_score": round(self.climate_score, 3),
            "soil_score": round(self.soil_score, 3)
        }
        
        if self.economic_score is not None:
            result["economic_score"] = round(self.economic_score, 3)
        if self.ecological_score is not None:
            result["ecological_score"] = round(self.ecological_score, 3)
        if self.risk_score is not None:
            result["risk_score"] = round(self.risk_score, 3)
        if self.score_details:
            result["score_details"] = self.score_details
            
        return result


@dataclass
class SpeciesRecommendation:
    """Recommandation d'espèces pour une parcelle forestière."""
    id: str
    parcel_id: str
    location: Dict[str, Any]  # Informations de localisation
    climate_data: Dict[str, Any]  # Données climatiques utilisées
    soil_data: Dict[str, Any]  # Données pédologiques utilisées
    recommendations: List[Dict[str, Any]]  # Liste des recommandations avec scores
    context: Dict[str, Any]  # Contexte de la recommandation (objectifs, contraintes)
    metadata: Dict[str, Any]  # Métadonnées (date, version, etc.)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            "id": self.id,
            "parcel_id": self.parcel_id,
            "location": self.location,
            "climate_data": self.climate_data,
            "soil_data": self.soil_data,
            "recommendations": self.recommendations,
            "context": self.context,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpeciesRecommendation':
        """Crée une instance à partir d'un dictionnaire."""
        return cls(
            id=data["id"],
            parcel_id=data["parcel_id"],
            location=data["location"],
            climate_data=data["climate_data"],
            soil_data=data["soil_data"],
            recommendations=data["recommendations"],
            context=data["context"],
            metadata=data["metadata"]
        )
