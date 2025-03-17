"""
Module de chargement des données pour le système de recommandation d'espèces.

Ce module fournit des fonctions pour charger les données d'espèces forestières
à partir de différentes sources.
"""

import os
import json
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from forestai.core.utils.logging_utils import get_logger
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached
from forestai.domain.services.species_recommender.models import SpeciesData

logger = get_logger(__name__)


class SpeciesDataLoader:
    """
    Classe pour charger les données d'espèces forestières.
    
    Cette classe fournit des méthodes pour charger les données d'espèces forestières
    à partir de fichiers JSON, CSV ou d'autres sources.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialise le chargeur de données d'espèces.
        
        Args:
            data_dir: Répertoire de stockage des données (facultatif)
        """
        # Si aucun répertoire n'est spécifié, utiliser le dossier par défaut
        if data_dir is None:
            data_dir = Path(os.environ.get("FORESTAI_DATA_DIR", ".")) / "data" / "species"
        
        self.data_dir = data_dir
        
        # Créer le répertoire si nécessaire
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Chemin vers les fichiers de données
        self.species_json_file = self.data_dir / "species_data.json"
        self.species_csv_file = self.data_dir / "species_data.csv"
        
        logger.info(f"SpeciesDataLoader initialisé avec le répertoire: {self.data_dir}")
    
    @cached(data_type=CacheType.FORESTRY_DATA, policy=CachePolicy.DAILY)
    def load_species_data(self) -> Dict[str, SpeciesData]:
        """
        Charge toutes les données d'espèces disponibles.
        
        Returns:
            Dictionnaire des données d'espèces indexées par ID
        """
        species_data = {}
        
        # Essayer de charger à partir du JSON
        if self.species_json_file.exists():
            try:
                species_data = self._load_from_json()
                logger.info(f"Données d'espèces chargées à partir du JSON: {len(species_data)} espèces")
            except Exception as e:
                logger.error(f"Erreur lors du chargement des données d'espèces depuis JSON: {str(e)}")
        
        # Si aucune donnée n'a été chargée du JSON, essayer le CSV
        if not species_data and self.species_csv_file.exists():
            try:
                species_data = self._load_from_csv()
                logger.info(f"Données d'espèces chargées à partir du CSV: {len(species_data)} espèces")
            except Exception as e:
                logger.error(f"Erreur lors du chargement des données d'espèces depuis CSV: {str(e)}")
        
        return species_data
    
    def _load_from_json(self) -> Dict[str, SpeciesData]:
        """
        Charge les données d'espèces à partir du fichier JSON.
        
        Returns:
            Dictionnaire des données d'espèces indexées par ID
        """
        species_data = {}
        
        try:
            with open(self.species_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                try:
                    species = SpeciesData.from_dict(item)
                    species_data[species.id] = species
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de l'espèce {item.get('id', 'inconnu')}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier JSON: {str(e)}")
            raise
        
        return species_data
    
    def _load_from_csv(self) -> Dict[str, SpeciesData]:
        """
        Charge les données d'espèces à partir du fichier CSV.
        
        Returns:
            Dictionnaire des données d'espèces indexées par ID
        """
        species_data = {}
        
        try:
            with open(self.species_csv_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                
                for row in csv_reader:
                    try:
                        # Convertir les valeurs booléennes
                        if 'native' in row:
                            row['native'] = row['native'].lower() in ('true', 'yes', '1', 'oui')
                        
                        # Convertir les valeurs numériques
                        for key in ['min_temperature', 'max_temperature', 'max_height', 'max_dbh', 
                                    'longevity', 'rotation_age', 'wood_density',
                                    'carbon_sequestration_rate', 'wildlife_value',
                                    'erosion_control', 'shade_tolerance', 'wind_resistance', 
                                    'fire_resistance']:
                            if key in row and row[key]:
                                try:
                                    row[key] = float(row[key])
                                except ValueError:
                                    row[key] = None
                        
                        # Convertir les listes
                        for key in ['suitable_soil_types', 'suitable_moisture_regimes', 
                                    'wood_uses', 'tags']:
                            if key in row and row[key]:
                                row[key] = [item.strip() for item in row[key].split(',')]
                            else:
                                row[key] = []
                        
                        # Convertir les dictionnaires
                        for key in ['pest_vulnerability', 'disease_vulnerability']:
                            if key in row and row[key]:
                                parts = [item.strip() for item in row[key].split(',')]
                                row[key] = {}
                                for part in parts:
                                    if ':' in part:
                                        name, value = part.split(':', 1)
                                        try:
                                            row[key][name.strip()] = int(value.strip())
                                        except ValueError:
                                            row[key][name.strip()] = 0
                            else:
                                row[key] = {}
                        
                        # Convertir les plages de valeurs
                        for key in ['optimal_temperature_range', 'annual_rainfall_range', 'altitude_range']:
                            min_key = f"{key.split('_')[0]}_min_{key.split('_')[1]}"
                            max_key = f"{key.split('_')[0]}_max_{key.split('_')[1]}"
                            
                            if min_key in row and max_key in row and row[min_key] and row[max_key]:
                                try:
                                    min_val = float(row[min_key])
                                    max_val = float(row[max_key])
                                    row[key] = (min_val, max_val)
                                except ValueError:
                                    row[key] = None
                            else:
                                row[key] = None
                        
                        species = SpeciesData.from_dict(row)
                        species_data[species.id] = species
                    
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement de la ligne {row.get('id', 'inconnue')}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier CSV: {str(e)}")
            raise
        
        return species_data
    
    def save_species_data(self, species_data: Dict[str, SpeciesData]) -> bool:
        """
        Sauvegarde les données d'espèces dans le fichier JSON.
        
        Args:
            species_data: Dictionnaire des données d'espèces à sauvegarder
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Convertir les objets en dictionnaires
            data = [species.to_dict() for species in species_data.values()]
            
            # Sauvegarder au format JSON
            with open(self.species_json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Données d'espèces sauvegardées: {len(species_data)} espèces")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des données d'espèces: {str(e)}")
            return False
    
    def add_species(self, species_data: SpeciesData) -> bool:
        """
        Ajoute une nouvelle espèce au jeu de données.
        
        Args:
            species_data: Données de l'espèce à ajouter
            
        Returns:
            True si l'ajout a réussi, False sinon
        """
        try:
            # Charger les données existantes
            current_data = self.load_species_data()
            
            # Vérifier si l'ID existe déjà
            if species_data.id in current_data:
                logger.warning(f"Une espèce avec l'ID {species_data.id} existe déjà")
                return False
            
            # Ajouter la nouvelle espèce
            current_data[species_data.id] = species_data
            
            # Sauvegarder les données mises à jour
            return self.save_species_data(current_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'espèce: {str(e)}")
            return False
    
    def update_species(self, species_data: SpeciesData) -> bool:
        """
        Met à jour une espèce existante dans le jeu de données.
        
        Args:
            species_data: Données de l'espèce à mettre à jour
            
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        try:
            # Charger les données existantes
            current_data = self.load_species_data()
            
            # Vérifier si l'ID existe
            if species_data.id not in current_data:
                logger.warning(f"Aucune espèce avec l'ID {species_data.id} n'a été trouvée")
                return False
            
            # Mettre à jour l'espèce
            current_data[species_data.id] = species_data
            
            # Sauvegarder les données mises à jour
            return self.save_species_data(current_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'espèce: {str(e)}")
            return False
    
    def get_species(self, species_id: str) -> Optional[SpeciesData]:
        """
        Récupère les données d'une espèce spécifique.
        
        Args:
            species_id: Identifiant de l'espèce à récupérer
            
        Returns:
            Données de l'espèce ou None si non trouvée
        """
        try:
            species_data = self.load_species_data()
            return species_data.get(species_id)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'espèce {species_id}: {str(e)}")
            return None
