"""
Module de calcul des scores de recommandation d'espèces.

Ce module contient les fonctions de calcul de scores utilisées par le système 
de recommandation d'espèces forestières.
"""

import logging
from typing import Dict, Any, Optional

from forestai.core.utils.logging_utils import get_logger
from forestai.domain.services.species_recommender.models import (
    SpeciesData,
    SoilType,
    MoistureRegime,
    DroughtResistance,
    FrostResistance,
    GrowthRate,
    WoodUse
)

logger = get_logger(__name__)


def calculate_climate_score(species: SpeciesData, climate_data: Dict[str, Any]) -> float:
    """
    Calcule le score de compatibilité climatique d'une espèce.
    
    Args:
        species: Données de l'espèce
        climate_data: Données climatiques de la parcelle
        
    Returns:
        Score de compatibilité climatique (0-1)
    """
    # Initialiser les sous-scores
    temperature_score = 0.0
    precipitation_score = 0.0
    frost_score = 0.0
    drought_score = 0.0
    
    # Calculer le score de température
    if species.optimal_temperature_range and 'mean_annual_temperature' in climate_data:
        mean_temp = climate_data['mean_annual_temperature']
        min_temp, max_temp = species.optimal_temperature_range
        
        if min_temp <= mean_temp <= max_temp:
            temperature_score = 1.0
        elif mean_temp < min_temp:
            # Pénalité proportionnelle à l'écart
            temperature_score = max(0, 1 - (min_temp - mean_temp) / 5)
        else:  # mean_temp > max_temp
            # Pénalité proportionnelle à l'écart
            temperature_score = max(0, 1 - (mean_temp - max_temp) / 5)
    else:
        # Si les données ne sont pas disponibles, score moyen
        temperature_score = 0.5
    
    # Calculer le score de précipitations
    if species.annual_rainfall_range and 'annual_precipitation' in climate_data:
        annual_precip = climate_data['annual_precipitation']
        min_precip, max_precip = species.annual_rainfall_range
        
        if min_precip <= annual_precip <= max_precip:
            precipitation_score = 1.0
        elif annual_precip < min_precip:
            # Pénalité proportionnelle à l'écart relatif
            precipitation_score = max(0, 1 - (min_precip - annual_precip) / min_precip)
        else:  # annual_precip > max_precip
            # Pénalité proportionnelle à l'écart relatif
            precipitation_score = max(0, 1 - (annual_precip - max_precip) / max_precip)
    else:
        # Si les données ne sont pas disponibles, score moyen
        precipitation_score = 0.5
    
    # Calculer le score de résistance au gel
    if species.frost_resistance and 'min_temperature' in climate_data:
        min_temp = climate_data['min_temperature']
        
        # Correspondance entre résistance au gel et températures minimales supportées
        frost_thresholds = {
            FrostResistance.VERY_LOW: -5,
            FrostResistance.LOW: -10,
            FrostResistance.MEDIUM: -15,
            FrostResistance.HIGH: -25,
            FrostResistance.VERY_HIGH: -40
        }
        
        threshold = frost_thresholds[species.frost_resistance]
        
        if min_temp >= threshold:
            frost_score = 1.0
        else:
            # Pénalité proportionnelle à l'écart
            frost_score = max(0, 1 - (threshold - min_temp) / 10)
    else:
        # Si les données ne sont pas disponibles, score moyen
        frost_score = 0.5
    
    # Calculer le score de résistance à la sécheresse
    if species.drought_resistance and 'drought_index' in climate_data:
        drought_index = climate_data['drought_index']  # Index de 0 (pas de sécheresse) à 10 (sécheresse extrême)
        
        # Correspondance entre résistance à la sécheresse et index supporté
        drought_thresholds = {
            DroughtResistance.VERY_LOW: 2,
            DroughtResistance.LOW: 4,
            DroughtResistance.MEDIUM: 6,
            DroughtResistance.HIGH: 8,
            DroughtResistance.VERY_HIGH: 10
        }
        
        threshold = drought_thresholds[species.drought_resistance]
        
        if drought_index <= threshold:
            drought_score = 1.0
        else:
            # Pénalité proportionnelle à l'écart
            drought_score = max(0, 1 - (drought_index - threshold) / 10)
    else:
        # Si les données ne sont pas disponibles, score moyen
        drought_score = 0.5
    
    # Combiner les sous-scores en pondérant selon l'importance
    weights = {
        'temperature': 0.35,
        'precipitation': 0.25,
        'frost': 0.2,
        'drought': 0.2
    }
    
    climate_score = (
        weights['temperature'] * temperature_score +
        weights['precipitation'] * precipitation_score +
        weights['frost'] * frost_score +
        weights['drought'] * drought_score
    )
    
    # Arrondir le score à 3 décimales
    return round(climate_score, 3)


def calculate_soil_score(species: SpeciesData, soil_data: Dict[str, Any]) -> float:
    """
    Calcule le score de compatibilité pédologique d'une espèce.
    
    Args:
        species: Données de l'espèce
        soil_data: Données pédologiques de la parcelle
        
    Returns:
        Score de compatibilité pédologique (0-1)
    """
    # Initialiser les sous-scores
    soil_type_score = 0.0
    moisture_score = 0.0
    ph_score = 0.0
    
    # Calculer le score de type de sol
    if species.suitable_soil_types and 'soil_type' in soil_data:
        # Convertir le type de sol en objet SoilType s'il s'agit d'une chaîne
        if isinstance(soil_data['soil_type'], str):
            try:
                parcel_soil_type = SoilType(soil_data['soil_type'])
            except ValueError:
                parcel_soil_type = None
        else:
            parcel_soil_type = soil_data['soil_type']
        
        if parcel_soil_type in species.suitable_soil_types:
            soil_type_score = 1.0
        else:
            # Si le sol n'est pas idéal mais pas incompatible, score intermédiaire
            # Basé sur des affinités entre types de sols (simplifié)
            compatible_combinations = {
                SoilType.SANDY: [SoilType.LOAM, SoilType.SILTY],
                SoilType.CLAY: [SoilType.LOAM, SoilType.SILTY],
                SoilType.LOAM: [SoilType.SANDY, SoilType.CLAY, SoilType.SILTY],
                SoilType.CHALKY: [SoilType.ROCKY, SoilType.LOAM],
                SoilType.ACIDIC: [SoilType.SANDY, SoilType.PEATY],
                SoilType.PEATY: [SoilType.ACIDIC, SoilType.WET],
                SoilType.SILTY: [SoilType.LOAM, SoilType.CLAY],
                SoilType.ROCKY: [SoilType.CHALKY, SoilType.SANDY]
            }
            
            if parcel_soil_type and parcel_soil_type in compatible_combinations:
                for species_soil in species.suitable_soil_types:
                    if species_soil in compatible_combinations[parcel_soil_type]:
                        soil_type_score = 0.5
                        break
    else:
        # Si les données ne sont pas disponibles, score moyen
        soil_type_score = 0.5
    
    # Calculer le score d'humidité du sol
    if species.suitable_moisture_regimes and 'moisture_regime' in soil_data:
        # Convertir le régime d'humidité en objet MoistureRegime s'il s'agit d'une chaîne
        if isinstance(soil_data['moisture_regime'], str):
            try:
                parcel_moisture = MoistureRegime(soil_data['moisture_regime'])
            except ValueError:
                parcel_moisture = None
        else:
            parcel_moisture = soil_data['moisture_regime']
        
        if parcel_moisture in species.suitable_moisture_regimes:
            moisture_score = 1.0
        else:
            # Évaluer la proximité des régimes d'humidité
            moisture_values = [mr.value for mr in MoistureRegime]
            
            if parcel_moisture:
                parcel_index = moisture_values.index(parcel_moisture.value)
                closest_distance = float('inf')
                
                for species_moisture in species.suitable_moisture_regimes:
                    species_index = moisture_values.index(species_moisture.value)
                    distance = abs(parcel_index - species_index)
                    closest_distance = min(closest_distance, distance)
                
                # Normaliser la distance sur une échelle de 0 à 1
                moisture_score = max(0, 1 - closest_distance / len(moisture_values))
    else:
        # Si les données ne sont pas disponibles, score moyen
        moisture_score = 0.5
    
    # Calculer le score de pH du sol
    if 'pH' in soil_data:
        soil_ph = soil_data['pH']
        
        # Définir les plages optimales de pH par type de sol préféré
        ph_ranges = {
            SoilType.ACIDIC: (4.0, 5.5),
            SoilType.SANDY: (5.0, 7.0),
            SoilType.LOAM: (5.5, 7.5),
            SoilType.CLAY: (6.0, 8.0),
            SoilType.CHALKY: (7.0, 8.5),
            SoilType.SILTY: (5.5, 7.0),
            SoilType.PEATY: (3.5, 5.0),
            SoilType.ROCKY: (5.0, 7.5)
        }
        
        # Trouver la plage de pH optimale pour l'espèce
        if species.suitable_soil_types:
            # Calculer le score pour chaque type de sol adapté à l'espèce
            ph_scores = []
            
            for soil_type in species.suitable_soil_types:
                if soil_type in ph_ranges:
                    min_ph, max_ph = ph_ranges[soil_type]
                    
                    if min_ph <= soil_ph <= max_ph:
                        ph_scores.append(1.0)
                    elif soil_ph < min_ph:
                        # Pénalité proportionnelle à l'écart
                        ph_scores.append(max(0, 1 - (min_ph - soil_ph) / 2))
                    else:  # soil_ph > max_ph
                        # Pénalité proportionnelle à l'écart
                        ph_scores.append(max(0, 1 - (soil_ph - max_ph) / 2))
            
            if ph_scores:
                # Utiliser le meilleur score de pH parmi les types de sol adaptés
                ph_score = max(ph_scores)
            else:
                ph_score = 0.5
        else:
            # Si aucun type de sol n'est spécifié, utiliser une plage générique
            if 5.0 <= soil_ph <= 7.5:
                ph_score = 1.0
            elif soil_ph < 5.0:
                ph_score = max(0, 1 - (5.0 - soil_ph) / 2)
            else:  # soil_ph > 7.5
                ph_score = max(0, 1 - (soil_ph - 7.5) / 2)
    else:
        # Si les données de pH ne sont pas disponibles, score moyen
        ph_score = 0.5
    
    # Combiner les sous-scores en pondérant selon l'importance
    weights = {
        'soil_type': 0.4,
        'moisture': 0.4,
        'ph': 0.2
    }
    
    soil_score = (
        weights['soil_type'] * soil_type_score +
        weights['moisture'] * moisture_score +
        weights['ph'] * ph_score
    )
    
    # Arrondir le score à 3 décimales
    return round(soil_score, 3)


def calculate_economic_score(species: SpeciesData, context: Dict[str, Any]) -> float:
    """
    Calcule le score de valeur économique d'une espèce.
    
    Args:
        species: Données de l'espèce
        context: Contexte de la recommandation (objectifs, contraintes)
        
    Returns:
        Score économique (0-1)
    """
    # Initialiser le score et les sous-scores
    value_score = 0.0
    growth_score = 0.0
    purpose_score = 0.0
    
    # Calculer le score de valeur économique
    if species.economic_value:
        # Convertir l'énumération en valeur numérique
        value_map = {
            "très faible": 0.1,
            "faible": 0.3,
            "moyenne": 0.5,
            "élevée": 0.8,
            "très élevée": 1.0
        }
        value_score = value_map.get(species.economic_value.value, 0.5)
    else:
        value_score = 0.5
    
    # Calculer le score de croissance
    if species.growth_rate:
        # Convertir l'énumération en valeur numérique
        growth_map = {
            "très lent": 0.1,
            "lent": 0.3,
            "moyen": 0.5,
            "rapide": 0.8,
            "très rapide": 1.0
        }
        
        # Si l'objectif est la production rapide, favoriser les espèces à croissance rapide
        if context.get("objective") == "production_rapide":
            growth_score = growth_map.get(species.growth_rate.value, 0.5)
        # Si l'objectif est la qualité du bois, ne pas trop pénaliser les espèces à croissance lente
        elif context.get("objective") == "qualite_bois":
            # Inverser le score de croissance pour les espèces à croissance lente ou moyenne
            if species.growth_rate in [GrowthRate.VERY_SLOW, GrowthRate.SLOW, GrowthRate.MEDIUM]:
                growth_score = 0.8
            else:
                growth_score = 0.5
        else:
            # Pour les autres objectifs, score moyen pour la croissance
            growth_score = 0.6
    else:
        growth_score = 0.5
    
    # Calculer le score d'adéquation à l'usage prévu
    if species.wood_uses and "wood_use" in context:
        target_use = context["wood_use"]
        
        # Convertir la chaîne en objet WoodUse si nécessaire
        if isinstance(target_use, str):
            try:
                target_use = WoodUse(target_use)
            except ValueError:
                target_use = None
        
        if target_use and target_use in species.wood_uses:
            purpose_score = 1.0
        elif WoodUse.MULTIPURPOSE in species.wood_uses:
            purpose_score = 0.7
        else:
            purpose_score = 0.3
    else:
        purpose_score = 0.5
    
    # Combiner les sous-scores en pondérant selon l'importance et l'objectif
    if context.get("objective") == "production_rapide":
        weights = {
            'value': 0.2,
            'growth': 0.5,
            'purpose': 0.3
        }
    elif context.get("objective") == "qualite_bois":
        weights = {
            'value': 0.5,
            'growth': 0.1,
            'purpose': 0.4
        }
    else:
        weights = {
            'value': 0.4,
            'growth': 0.3,
            'purpose': 0.3
        }
    
    economic_score = (
        weights['value'] * value_score +
        weights['growth'] * growth_score +
        weights['purpose'] * purpose_score
    )
    
    # Arrondir le score à 3 décimales
    return round(economic_score, 3)


def calculate_ecological_score(species: SpeciesData, context: Dict[str, Any]) -> float:
    """
    Calcule le score de valeur écologique d'une espèce.
    
    Args:
        species: Données de l'espèce
        context: Contexte de la recommandation (objectifs, contraintes)
        
    Returns:
        Score écologique (0-1)
    """
    # Initialiser le score et les sous-scores
    eco_value_score = 0.0
    carbon_score = 0.0
    wildlife_score = 0.0
    erosion_score = 0.0
    native_score = 0.0
    
    # Calculer le score de valeur écologique
    if species.ecological_value:
        # Convertir l'énumération en valeur numérique
        value_map = {
            "très faible": 0.1,
            "faible": 0.3,
            "moyenne": 0.5,
            "élevée": 0.8,
            "très élevée": 1.0
        }
        eco_value_score = value_map.get(species.ecological_value.value, 0.5)
    else:
        eco_value_score = 0.5
    
    # Calculer le score de séquestration carbone
    if species.carbon_sequestration_rate is not None:
        # Normaliser le taux de séquestration carbone (hypothèse: max 20 tonnes CO2/ha/an)
        carbon_score = min(1.0, species.carbon_sequestration_rate / 20.0)
    else:
        carbon_score = 0.5
    
    # Calculer le score de valeur pour la faune
    if species.wildlife_value is not None:
        # Normaliser la valeur pour la faune (échelle de 0 à 10)
        wildlife_score = species.wildlife_value / 10.0
    else:
        wildlife_score = 0.5
    
    # Calculer le score de contrôle de l'érosion
    if species.erosion_control is not None:
        # Normaliser la valeur de contrôle de l'érosion (échelle de 0 à 10)
        erosion_score = species.erosion_control / 10.0
    else:
        erosion_score = 0.5
    
    # Calculer le score pour les espèces natives (bonus pour la biodiversité locale)
    native_score = 1.0 if species.native else 0.4
    
    # Combiner les sous-scores en pondérant selon l'importance et l'objectif
    if context.get("objective") == "biodiversite":
        weights = {
            'eco_value': 0.3,
            'carbon': 0.1,
            'wildlife': 0.3,
            'erosion': 0.1,
            'native': 0.2
        }
    elif context.get("objective") == "carbon_sequestration":
        weights = {
            'eco_value': 0.1,
            'carbon': 0.6,
            'wildlife': 0.1,
            'erosion': 0.1,
            'native': 0.1
        }
    elif context.get("objective") == "erosion_control":
        weights = {
            'eco_value': 0.1,
            'carbon': 0.1,
            'wildlife': 0.1,
            'erosion': 0.6,
            'native': 0.1
        }
    else:
        weights = {
            'eco_value': 0.2,
            'carbon': 0.2,
            'wildlife': 0.2,
            'erosion': 0.2,
            'native': 0.2
        }
    
    ecological_score = (
        weights['eco_value'] * eco_value_score +
        weights['carbon'] * carbon_score +
        weights['wildlife'] * wildlife_score +
        weights['erosion'] * erosion_score +
        weights['native'] * native_score
    )
    
    # Arrondir le score à 3 décimales
    return round(ecological_score, 3)


def calculate_risk_score(species: SpeciesData, climate_data: Dict[str, Any], 
                         soil_data: Dict[str, Any], context: Dict[str, Any]) -> float:
    """
    Calcule le score de risque pour une espèce.
    
    Args:
        species: Données de l'espèce
        climate_data: Données climatiques de la parcelle
        soil_data: Données pédologiques de la parcelle
        context: Contexte de la recommandation (objectifs, contraintes)
        
    Returns:
        Score de risque (0-1, plus élevé = moins risqué)
    """
    # Initialiser le score et les sous-scores
    pest_score = 0.0
    disease_score = 0.0
    climate_risk_score = 0.0
    
    # Calculer le score de vulnérabilité aux ravageurs
    if species.pest_vulnerability:
        # Calculer la moyenne des vulnérabilités (échelle inversée : plus élevé = moins vulnérable)
        avg_vulnerability = sum(species.pest_vulnerability.values()) / len(species.pest_vulnerability)
        pest_score = 1.0 - (avg_vulnerability / 10.0)
    else:
        pest_score = 0.7  # Score par défaut modéré
    
    # Calculer le score de vulnérabilité aux maladies
    if species.disease_vulnerability:
        # Calculer la moyenne des vulnérabilités (échelle inversée : plus élevé = moins vulnérable)
        avg_vulnerability = sum(species.disease_vulnerability.values()) / len(species.disease_vulnerability)
        disease_score = 1.0 - (avg_vulnerability / 10.0)
    else:
        disease_score = 0.7  # Score par défaut modéré
    
    # Calculer le score de risque climatique
    if 'climate_change_scenario' in context and context['climate_change_scenario'] != 'none':
        # Risque plus élevé pour les espèces moins résistantes à la sécheresse
        if species.drought_resistance:
            drought_values = {
                DroughtResistance.VERY_LOW: 0.2,
                DroughtResistance.LOW: 0.4,
                DroughtResistance.MEDIUM: 0.6,
                DroughtResistance.HIGH: 0.8,
                DroughtResistance.VERY_HIGH: 1.0
            }
            
            # Plus le scénario est extrême, plus la résistance à la sécheresse est importante
            scenario_factor = {
                'moderate': 0.5,
                'high': 0.7,
                'extreme': 0.9
            }
            
            drought_weight = scenario_factor.get(context['climate_change_scenario'], 0.5)
            climate_risk_score = drought_values.get(species.drought_resistance, 0.5)
        else:
            climate_risk_score = 0.5
    else:
        climate_risk_score = 0.8  # Risque climatique faible si pas de scénario de changement
    
    # Combiner les sous-scores en pondérant selon l'importance et le contexte
    weights = {
        'pest': 0.3,
        'disease': 0.3,
        'climate': 0.4
    }
    
    # Ajuster les poids selon le contexte
    if 'climate_change_scenario' in context and context['climate_change_scenario'] != 'none':
        scenario_intensity = {
            'moderate': 0.6,
            'high': 0.7,
            'extreme': 0.8
        }
        weights['climate'] = scenario_intensity.get(context['climate_change_scenario'], 0.4)
        weights['pest'] = (1.0 - weights['climate']) / 2
        weights['disease'] = (1.0 - weights['climate']) / 2
    
    risk_score = (
        weights['pest'] * pest_score +
        weights['disease'] * disease_score +
        weights['climate'] * climate_risk_score
    )
    
    # Arrondir le score à 3 décimales
    return round(risk_score, 3)


def calculate_overall_score(climate_score: float, soil_score: float, 
                           economic_score: Optional[float], ecological_score: Optional[float],
                           risk_score: Optional[float], context: Dict[str, Any]) -> float:
    """
    Calcule le score global de recommandation pour une espèce.
    
    Args:
        climate_score: Score climatique
        soil_score: Score pédologique
        economic_score: Score économique (optionnel)
        ecological_score: Score écologique (optionnel)
        risk_score: Score de risque (optionnel)
        context: Contexte de la recommandation
        
    Returns:
        Score global de recommandation (0-1)
    """
    # Déterminer les poids des scores selon l'objectif
    weights = {
        'climate': 0.3,
        'soil': 0.3,
        'economic': 0.15,
        'ecological': 0.15,
        'risk': 0.1
    }
    
    # Ajuster les poids selon l'objectif
    objective = context.get("objective", "balanced")
    
    if objective == "production_rapide" or objective == "qualite_bois":
        weights = {
            'climate': 0.25,
            'soil': 0.25,
            'economic': 0.35,
            'ecological': 0.05,
            'risk': 0.1
        }
    elif objective == "biodiversite" or objective == "carbon_sequestration":
        weights = {
            'climate': 0.25,
            'soil': 0.25,
            'economic': 0.05,
            'ecological': 0.35,
            'risk': 0.1
        }
    elif objective == "erosion_control":
        weights = {
            'climate': 0.2,
            'soil': 0.3,
            'economic': 0.05,
            'ecological': 0.35,
            'risk': 0.1
        }
    
    # Calculer le score global en combinant les scores individuels
    overall_score = 0.0
    
    # Ajouter les scores toujours présents
    overall_score += weights['climate'] * climate_score
    overall_score += weights['soil'] * soil_score
    
    # Ajouter les scores optionnels
    if economic_score is not None:
        overall_score += weights['economic'] * economic_score
    
    if ecological_score is not None:
        overall_score += weights['ecological'] * ecological_score
    
    if risk_score is not None:
        overall_score += weights['risk'] * risk_score
    
    # Ajuster les poids si certains scores sont manquants
    total_weight = weights['climate'] + weights['soil']
    if economic_score is not None:
        total_weight += weights['economic']
    if ecological_score is not None:
        total_weight += weights['ecological']
    if risk_score is not None:
        total_weight += weights['risk']
    
    # Normaliser le score si le poids total n'est pas 1
    if total_weight != 1.0 and total_weight > 0:
        overall_score /= total_weight
    
    # Arrondir le score à 3 décimales
    return round(overall_score, 3)
