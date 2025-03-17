"""
Module principal du système de recommandation d'espèces forestières.

Ce module implémente le moteur de recommandation qui analyse les conditions
environnementales d'une parcelle et recommande les espèces forestières les plus adaptées.
"""

import os
import uuid
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from forestai.core.utils.logging_utils import get_logger
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached
from forestai.domain.services.species_recommender.data_loader import SpeciesDataLoader
from forestai.domain.services.species_recommender.score_calculator import (
    calculate_climate_score,
    calculate_soil_score,
    calculate_economic_score,
    calculate_ecological_score,
    calculate_risk_score,
    calculate_overall_score
)
from forestai.domain.services.species_recommender.models import (
    SpeciesData, 
    SpeciesRecommendation, 
    RecommendationScore
)

logger = get_logger(__name__)


class SpeciesRecommender:
    """
    Système de recommandation d'espèces forestières basé sur ML.
    
    Cette classe fournit des méthodes pour recommander des espèces forestières
    adaptées aux conditions environnementales d'une parcelle.
    """
    
    def __init__(self, data_dir: Optional[Path] = None, climate_analyzer=None, geo_agent=None):
        """
        Initialise le système de recommandation d'espèces.
        
        Args:
            data_dir: Répertoire de stockage des données (facultatif)
            climate_analyzer: Instance du ClimateAnalyzer (facultatif)
            geo_agent: Instance du GeoAgent (facultatif)
        """
        # Si aucun répertoire n'est spécifié, utiliser le dossier par défaut
        if data_dir is None:
            data_dir = Path(os.environ.get("FORESTAI_DATA_DIR", ".")) / "data" / "species"
        
        self.data_dir = data_dir
        self.recommendations_dir = self.data_dir / "recommendations"
        
        # Créer les répertoires si nécessaires
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.recommendations_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser le chargeur de données
        self.data_loader = SpeciesDataLoader(data_dir)
        
        # Références aux autres services
        self.climate_analyzer = climate_analyzer
        self.geo_agent = geo_agent
        
        # Charger les modèles ML si disponibles
        self._load_ml_models()
        
        logger.info("SpeciesRecommender initialisé")
    
    def _load_ml_models(self):
        """Charge les modèles ML utilisés pour les recommandations."""
        # TODO: Implémenter le chargement des modèles ML
        self.models_loaded = False
        logger.info("Modèles ML non chargés (à implémenter)")
    
    def get_species_data(self) -> Dict[str, SpeciesData]:
        """
        Récupère toutes les données d'espèces disponibles.
        
        Returns:
            Dictionnaire des données d'espèces indexées par ID
        """
        return self.data_loader.load_species_data()
    
    def get_species(self, species_id: str) -> Optional[SpeciesData]:
        """
        Récupère les données d'une espèce spécifique.
        
        Args:
            species_id: Identifiant de l'espèce à récupérer
            
        Returns:
            Données de l'espèce ou None si non trouvée
        """
        return self.data_loader.get_species(species_id)
    
    def recommend_species(self, parcel_id: str, climate_data: Dict[str, Any], 
                        soil_data: Dict[str, Any], context: Dict[str, Any] = None) -> SpeciesRecommendation:
        """
        Recommande des espèces forestières adaptées aux conditions d'une parcelle.
        
        Args:
            parcel_id: Identifiant de la parcelle
            climate_data: Données climatiques de la parcelle
            soil_data: Données pédologiques de la parcelle
            context: Contexte de la recommandation (objectifs, contraintes)
            
        Returns:
            Recommandation d'espèces avec scores
        """
        # Initialiser le contexte si non fourni
        if context is None:
            context = {"objective": "balanced"}
        
        # Charger les données d'espèces
        species_data = self.get_species_data()
        
        # Calculer les scores pour chaque espèce
        scores = []
        
        for species_id, species in species_data.items():
            # Calculer les scores individuels
            climate_score = calculate_climate_score(species, climate_data)
            soil_score = calculate_soil_score(species, soil_data)
            economic_score = calculate_economic_score(species, context)
            ecological_score = calculate_ecological_score(species, context)
            risk_score = calculate_risk_score(species, climate_data, soil_data, context)
            
            # Calculer le score global
            overall_score = calculate_overall_score(
                climate_score, soil_score, economic_score, ecological_score, risk_score, context
            )
            
            # Créer l'objet de score
            score = RecommendationScore(
                species_id=species_id,
                overall_score=overall_score,
                climate_score=climate_score,
                soil_score=soil_score,
                economic_score=economic_score,
                ecological_score=ecological_score,
                risk_score=risk_score,
                score_details={
                    "climate": climate_score,
                    "soil": soil_score,
                    "economic": economic_score,
                    "ecological": ecological_score,
                    "risk": risk_score
                }
            )
            
            scores.append(score)
        
        # Trier les scores par score global décroissant
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        
        # Convertir les scores en dictionnaires et enrichir avec les infos des espèces
        recommendations = []
        
        for i, score in enumerate(scores[:10]):  # Limiter aux 10 meilleures espèces
            species = species_data[score.species_id]
            
            recommendation = {
                "rank": i + 1,
                "species_id": score.species_id,
                "latin_name": species.latin_name,
                "common_name": species.common_name,
                "family": species.family,
                "native": species.native,
                "scores": score.to_dict()
            }
            
            recommendations.append(recommendation)
        
        # Créer l'objet de recommandation
        recommendation_id = f"rec-{uuid.uuid4().hex[:8]}"
        location = self._extract_location_data(parcel_id)
        
        # Préparer les métadonnées
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "model_version": "ML model not used"
        }
        
        # Créer l'objet de recommandation
        recommendation = SpeciesRecommendation(
            id=recommendation_id,
            parcel_id=parcel_id,
            location=location,
            climate_data=climate_data,
            soil_data=soil_data,
            recommendations=recommendations,
            context=context,
            metadata=metadata
        )
        
        # Sauvegarder la recommandation
        self._save_recommendation(recommendation)
        
        return recommendation
    
    def _extract_location_data(self, parcel_id: str) -> Dict[str, Any]:
        """
        Extrait les données de localisation d'une parcelle.
        
        Args:
            parcel_id: Identifiant de la parcelle
            
        Returns:
            Données de localisation
        """
        # Si un GeoAgent est disponible, l'utiliser pour obtenir les infos
        if self.geo_agent:
            try:
                parcel_info = self.geo_agent.get_parcel_info({"parcel_id": parcel_id})
                if parcel_info["status"] == "success":
                    return parcel_info["result"]["location"]
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des infos de la parcelle: {str(e)}")
        
        # Par défaut, retourner un objet avec l'ID de la parcelle
        return {"parcel_id": parcel_id}
    
    def _save_recommendation(self, recommendation: SpeciesRecommendation) -> bool:
        """
        Sauvegarde une recommandation d'espèces.
        
        Args:
            recommendation: Recommandation à sauvegarder
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            filename = f"{recommendation.id}.json"
            file_path = self.recommendations_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recommendation.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"Recommandation sauvegardée: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la recommandation: {str(e)}")
            return False
    
    def get_recommendation(self, recommendation_id: str) -> Optional[SpeciesRecommendation]:
        """
        Récupère une recommandation d'espèces par son identifiant.
        
        Args:
            recommendation_id: Identifiant de la recommandation
            
        Returns:
            Recommandation d'espèces ou None si non trouvée
        """
        try:
            filename = f"{recommendation_id}.json"
            file_path = self.recommendations_dir / filename
            
            if not file_path.exists():
                logger.warning(f"Recommandation non trouvée: {recommendation_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return SpeciesRecommendation.from_dict(data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la recommandation: {str(e)}")
            return None
    
    def get_recommendations_for_parcel(self, parcel_id: str) -> List[SpeciesRecommendation]:
        """
        Récupère toutes les recommandations pour une parcelle spécifique.
        
        Args:
            parcel_id: Identifiant de la parcelle
            
        Returns:
            Liste des recommandations pour la parcelle
        """
        recommendations = []
        
        try:
            for file_path in self.recommendations_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data.get("parcel_id") == parcel_id:
                        recommendation = SpeciesRecommendation.from_dict(data)
                        recommendations.append(recommendation)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")
            
            # Trier par date de génération (la plus récente en premier)
            recommendations.sort(
                key=lambda r: r.metadata.get("generated_at", ""),
                reverse=True
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des recommandations pour la parcelle {parcel_id}: {str(e)}")
        
        return recommendations
    
    @cached(data_type=CacheType.FORESTRY_DATA, policy=CachePolicy.WEEKLY)
    def get_species_by_climate_zone(self, climate_zone: str) -> List[str]:
        """
        Récupère les espèces recommandées pour une zone climatique spécifique.
        
        Args:
            climate_zone: Identifiant de la zone climatique
            
        Returns:
            Liste des identifiants d'espèces recommandées
        """
        # TODO: Implémenter l'analyse des zones climatiques
        # Ceci est une implémentation simplifiée
        
        species_data = self.get_species_data()
        recommended_species = []
        
        for species_id, species in species_data.items():
            # Logique simplifiée - à remplacer par un vrai modèle de compatibilité
            if climate_zone in species.tags:
                recommended_species.append(species_id)
        
        return recommended_species
    
    def add_or_update_species(self, species_data: Dict[str, Any]) -> bool:
        """
        Ajoute ou met à jour une espèce dans la base de données.
        
        Args:
            species_data: Données de l'espèce
            
        Returns:
            True si l'opération a réussi, False sinon
        """
        try:
            species_id = species_data.get("id")
            
            if not species_id:
                # Générer un nouvel identifiant pour les nouvelles espèces
                species_id = f"sp-{uuid.uuid4().hex[:8]}"
                species_data["id"] = species_id
                
                # Ajouter une nouvelle espèce
                species = SpeciesData.from_dict(species_data)
                return self.data_loader.add_species(species)
            else:
                # Mettre à jour une espèce existante
                species = SpeciesData.from_dict(species_data)
                return self.data_loader.update_species(species)
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout/mise à jour de l'espèce: {str(e)}")
            return False
