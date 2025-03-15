# -*- coding: utf-8 -*-
"""
Module d'analyse d'inventaire forestier pour le DiagnosticAgent.

Ce module permet:
- L'analyse détaillée des inventaires forestiers
- Le calcul de métriques forestières avancées
- L'estimation de la valeur économique du peuplement
- L'analyse de la structure des âges et des diamètres
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from scipy import stats
import matplotlib.pyplot as plt
import io
import base64
from enum import Enum

from forestai.core.infrastructure.cache.cache_utils import cached
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy

logger = logging.getLogger(__name__)

class ForestType(Enum):
    """Énumération des types forestiers pour la classification."""
    PLANTATION = "Plantation"
    NATURAL_REGENERATION = "Régénération naturelle"
    MIXED = "Mixte"
    IRREGULAR = "Irrégulier"
    EVEN_AGED = "Équienne"
    UNEVEN_AGED = "Inéquienne"
    UNKNOWN = "Indéterminé"

class InventoryAnalyzer:
    """Classe spécialisée dans l'analyse des inventaires forestiers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialise l'analyseur d'inventaire.
        
        Args:
            config: Configuration optionnelle pour l'analyseur
        """
        self.config = config or {}
        self.volume_equations = {
            # Équations volumiques par défaut (coef a, b, c pour V = a + b*D^2*H)
            "default": (0, 0.42, 0),
            "Pinus": (0, 0.45, 0),
            "Quercus": (0, 0.39, 0),
            "Fagus": (0, 0.43, 0),
            "Betula": (0, 0.40, 0),
            "Populus": (0, 0.38, 0),
        }
        
        # Charger les équations volumiques spécifiques si fournies
        if "volume_equations" in self.config:
            self.volume_equations.update(self.config["volume_equations"])
            
        logger.info("InventoryAnalyzer initialisé")
    
    def load_inventory(self, inventory_data: Union[Dict[str, Any], List[Any], str, pd.DataFrame]) -> pd.DataFrame:
        """Charge et normalise les données d'inventaire dans un format standard.
        
        Args:
            inventory_data: Données d'inventaire sous diverses formes
            
        Returns:
            DataFrame normalisé contenant les données d'inventaire
        """
        try:
            if isinstance(inventory_data, pd.DataFrame):
                df = inventory_data.copy()
            elif isinstance(inventory_data, Dict) and "items" in inventory_data:
                df = pd.DataFrame(inventory_data["items"])
            elif isinstance(inventory_data, List):
                df = pd.DataFrame(inventory_data)
            elif isinstance(inventory_data, str):
                # Tente de charger à partir d'un chemin de fichier
                if inventory_data.endswith('.csv'):
                    df = pd.read_csv(inventory_data)
                elif inventory_data.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(inventory_data)
                else:
                    raise ValueError(f"Format de fichier non pris en charge: {inventory_data}")
            else:
                raise ValueError("Format d'inventaire non reconnu")
            
            # Normalisation des noms de colonnes
            column_mapping = {
                'espece': 'species', 'essence': 'species', 'nom_espece': 'species',
                'diametre': 'diameter', 'dbh': 'diameter', 'diam': 'diameter',
                'hauteur': 'height', 'h': 'height', 'ht': 'height',
                'age': 'age', 'classe_age': 'age_class',
                'qualite': 'quality', 'note_qualite': 'quality',
                'etat_sanitaire': 'health_status', 'sante': 'health_status', 'etat': 'health_status',
                'x': 'x_coord', 'y': 'y_coord', 'lon': 'longitude', 'lat': 'latitude'
            }
            
            # Normaliser les noms de colonnes
            df = df.rename(columns={col: column_mapping.get(col, col) for col in df.columns})
            
            # Vérifier les colonnes obligatoires
            required_columns = ['species', 'diameter']
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                raise ValueError(f"Colonnes obligatoires manquantes: {missing}")
            
            # Convertir les colonnes numériques
            numeric_columns = ['diameter', 'height', 'age', 'x_coord', 'y_coord', 'longitude', 'latitude']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Normaliser les noms d'espèces
            if 'species' in df.columns:
                df['species'] = df['species'].str.capitalize()
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'inventaire: {str(e)}")
            raise
    
    @cached(data_type=CacheType.DIAGNOSTIC, policy=CachePolicy.DAILY)
    def analyze(self, inventory_data: Union[Dict[str, Any], List[Any], str, pd.DataFrame], 
                area_ha: Optional[float] = None) -> Dict[str, Any]:
        """Analyse complète d'un inventaire forestier.
        
        Args:
            inventory_data: Données d'inventaire
            area_ha: Surface en hectares de la zone inventoriée
            
        Returns:
            Résultats de l'analyse d'inventaire
        """
        try:
            # Charger et normaliser les données
            df = self.load_inventory(inventory_data)
            
            # Récupérer la surface si fournie dans les données
            if area_ha is None and isinstance(inventory_data, Dict) and "area" in inventory_data:
                area_ha = inventory_data["area"]
            
            # Générer toutes les analyses
            basic_stats = self._calculate_basic_stats(df)
            species_analysis = self._analyze_species(df)
            diameter_structure = self._analyze_diameter_structure(df)
            spatial_metrics = self._calculate_spatial_metrics(df)
            economic_value = self._estimate_economic_value(df)
            
            # Calculer les métriques par hectare si surface disponible
            per_hectare_metrics = {}
            if area_ha is not None and area_ha > 0:
                per_hectare_metrics = self._calculate_per_hectare_metrics(df, species_analysis, area_ha)
            
            # Déterminer le type forestier
            forest_type = self._determine_forest_type(df)
            
            # Générer les visualisations
            visualizations = {}
            try:
                visualizations = self._generate_visualizations(df)
            except Exception as viz_error:
                logger.warning(f"Impossible de générer les visualisations: {str(viz_error)}")
            
            # Assembler le résultat final
            result = {
                "summary": basic_stats,
                "species_analysis": species_analysis,
                "diameter_structure": diameter_structure,
                "spatial_metrics": spatial_metrics,
                "economic_value": economic_value,
                "forest_type": forest_type.value,
                "forest_type_code": forest_type.name,
            }
            
            # Ajouter les métriques par hectare si disponibles
            if per_hectare_metrics:
                result["per_hectare"] = per_hectare_metrics
                
            # Ajouter les visualisations si disponibles
            if visualizations:
                result["visualizations"] = visualizations
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'inventaire: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcule les statistiques de base de l'inventaire."""
        total_trees = len(df)
        unique_species = df['species'].nunique()
        species_list = df['species'].unique().tolist()
        
        diameter_stats = {}
        height_stats = {}
        
        if 'diameter' in df.columns:
            diameter_stats = {
                "mean": df['diameter'].mean(),
                "median": df['diameter'].median(),
                "min": df['diameter'].min(),
                "max": df['diameter'].max(),
                "std": df['diameter'].std()
            }
            
        if 'height' in df.columns:
            height_stats = {
                "mean": df['height'].mean(),
                "median": df['height'].median(),
                "min": df['height'].min(),
                "max": df['height'].max(),
                "std": df['height'].std()
            }
            
        return {
            "total_trees": total_trees,
            "unique_species": unique_species,
            "species_list": species_list,
            "diameter_stats": diameter_stats,
            "height_stats": height_stats
        }
    
    def _analyze_species(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyse détaillée par espèce."""
        species_counts = df['species'].value_counts().to_dict()
        
        # Analyse par espèce
        species_analysis = {}
        for species in df['species'].unique():
            species_df = df[df['species'] == species]
            
            species_analysis[species] = {
                "count": len(species_df),
                "percentage": (len(species_df) / len(df)) * 100
            }
            
            # Ajouter les statistiques de diamètre si disponibles
            if 'diameter' in species_df.columns:
                species_analysis[species]["diameter"] = {
                    "mean": species_df['diameter'].mean(),
                    "median": species_df['diameter'].median(),
                    "min": species_df['diameter'].min(),
                    "max": species_df['diameter'].max(),
                    "std": species_df['diameter'].std()
                }
                
            # Ajouter les statistiques de hauteur si disponibles
            if 'height' in species_df.columns:
                species_analysis[species]["height"] = {
                    "mean": species_df['height'].mean(),
                    "median": species_df['height'].median(),
                    "min": species_df['height'].min(),
                    "max": species_df['height'].max(),
                    "std": species_df['height'].std()
                }
                
            # Calculer le volume si diamètre et hauteur disponibles
            if 'diameter' in species_df.columns and 'height' in species_df.columns:
                # Trouver l'équation de volume appropriée
                volume_eq = None
                for genus in self.volume_equations:
                    if species.startswith(genus):
                        volume_eq = self.volume_equations[genus]
                        break
                
                if volume_eq is None:
                    volume_eq = self.volume_equations["default"]
                
                # Calculer le volume pour chaque arbre
                a, b, c = volume_eq
                species_df['volume'] = a + b * ((species_df['diameter']/100) ** 2) * species_df['height']
                
                species_analysis[species]["volume"] = {
                    "total": species_df['volume'].sum(),
                    "mean": species_df['volume'].mean(),
                    "median": species_df['volume'].median(),
                    "min": species_df['volume'].min(),
                    "max": species_df['volume'].max()
                }
        
        return species_analysis
    
    def _analyze_diameter_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyse la structure des diamètres du peuplement."""
        if 'diameter' not in df.columns:
            return {"error": "Données de diamètre non disponibles"}
        
        # Définir les classes de diamètre (every 5cm)
        diameter_min = df['diameter'].min()
        diameter_max = df['diameter'].max()
        diameter_classes = np.arange(
            np.floor(diameter_min / 5) * 5,
            np.ceil(diameter_max / 5) * 5 + 5,
            5
        )
        
        # Ajouter une colonne pour la classe de diamètre
        df['diameter_class'] = pd.cut(
            df['diameter'],
            bins=diameter_classes,
            labels=[f"{int(c)}-{int(c+5)}" for c in diameter_classes[:-1]]
        )
        
        # Distribution globale des classes de diamètre
        diameter_distribution = df['diameter_class'].value_counts().sort_index().to_dict()
        
        # Distribution par espèce
        diameter_by_species = {}
        for species in df['species'].unique():
            species_df = df[df['species'] == species]
            diameter_by_species[species] = species_df['diameter_class'].value_counts().sort_index().to_dict()
        
        # Calculer les indicateurs de structure
        mean_diameter = df['diameter'].mean()
        median_diameter = df['diameter'].median()
        std_diameter = df['diameter'].std()
        
        # Coefficient de variation (indicateur d'hétérogénéité)
        cv_diameter = (std_diameter / mean_diameter) * 100 if mean_diameter > 0 else 0
        
        # Coefficient de Gini (mesure d'inégalité)
        sorted_diameters = np.sort(df['diameter'].values)
        n = len(sorted_diameters)
        index = np.arange(1, n + 1)
        gini = ((2 * np.sum(index * sorted_diameters)) / (n * np.sum(sorted_diameters))) - ((n + 1) / n)
        
        return {
            "diameter_classes": list(diameter_distribution.keys()),
            "diameter_distribution": diameter_distribution,
            "diameter_by_species": diameter_by_species,
            "structure_metrics": {
                "mean_diameter": mean_diameter,
                "median_diameter": median_diameter,
                "std_diameter": std_diameter,
                "cv_diameter": cv_diameter,
                "gini": gini,
                "interpretation": self._interpret_structure_metrics(cv_diameter, gini)
            }
        }
    
    def _interpret_structure_metrics(self, cv_diameter: float, gini: float) -> Dict[str, str]:
        """Interprète les métriques de structure."""
        cv_interpretation = ""
        if cv_diameter < 20:
            cv_interpretation = "Peuplement très homogène"
        elif cv_diameter < 40:
            cv_interpretation = "Peuplement relativement homogène"
        elif cv_diameter < 60:
            cv_interpretation = "Peuplement hétérogène"
        else:
            cv_interpretation = "Peuplement très hétérogène"
            
        gini_interpretation = ""
        if gini < 0.2:
            gini_interpretation = "Structure très équilibrée"
        elif gini < 0.4:
            gini_interpretation = "Structure relativement équilibrée"
        elif gini < 0.6:
            gini_interpretation = "Structure moyennement inégale"
        else:
            gini_interpretation = "Structure très inégale"
            
        structure_type = ""
        if cv_diameter < 30 and gini < 0.3:
            structure_type = "Peuplement régulier (probablement équienne)"
        elif cv_diameter > 50 or gini > 0.5:
            structure_type = "Peuplement irrégulier (probablement inéquienne)"
        else:
            structure_type = "Peuplement semi-régulier"
            
        return {
            "cv_interpretation": cv_interpretation,
            "gini_interpretation": gini_interpretation,
            "structure_type": structure_type
        }
    
    def _calculate_spatial_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcule les métriques spatiales si les données de position sont disponibles."""
        spatial_data_available = ('x_coord' in df.columns and 'y_coord' in df.columns) or \
                               ('longitude' in df.columns and 'latitude' in df.columns)
                               
        if not spatial_data_available:
            return {"spatial_data_available": False}
            
        # Utiliser x_coord/y_coord ou longitude/latitude
        position_columns = []
        if 'x_coord' in df.columns and 'y_coord' in df.columns:
            position_columns = ['x_coord', 'y_coord']
        else:
            position_columns = ['longitude', 'latitude']
            
        # Vérifier que les données sont numériques et non manquantes
        for col in position_columns:
            if df[col].isna().any() or not np.issubdtype(df[col].dtype, np.number):
                return {
                    "spatial_data_available": True,
                    "error": f"Données spatiales incomplètes ou non numériques dans la colonne {col}"
                }
        
        # Calculer la distance moyenne au plus proche voisin
        df_with_pos = df.dropna(subset=position_columns)
        
        if len(df_with_pos) < 2:
            return {
                "spatial_data_available": True,
                "error": "Trop peu d'arbres avec des coordonnées valides pour analyser la distribution spatiale"
            }
            
        # Calculer la distance minimale pour chaque arbre
        from scipy.spatial.distance import pdist, squareform
        
        positions = df_with_pos[position_columns].values
        distances = squareform(pdist(positions))
        
        # Remplacer les zéros diagonaux par l'infini pour ne pas les prendre en compte
        np.fill_diagonal(distances, np.inf)
        
        # Distance au plus proche voisin pour chaque arbre
        min_distances = np.min(distances, axis=1)
        
        # Métriques de distribution spatiale
        mean_min_distance = np.mean(min_distances)
        std_min_distance = np.std(min_distances)
        
        # Indice de Clark-Evans (R)
        # R = 1: distribution aléatoire, R < 1: agrégation, R > 1: régularité
        n = len(df_with_pos)
        
        # Calculer l'aire approximative du polygone convexe contenant les arbres
        from scipy.spatial import ConvexHull
        try:
            hull = ConvexHull(positions)
            area = hull.volume  # en 2D, volume = aire
        except Exception:
            # Fallback si le calcul de l'enveloppe convexe échoue (points alignés)
            x_range = np.max(positions[:, 0]) - np.min(positions[:, 0])
            y_range = np.max(positions[:, 1]) - np.min(positions[:, 1])
            area = x_range * y_range
            
        density = n / area if area > 0 else 0
        
        # Indice de Clark-Evans
        if density > 0:
            expected_mean_distance = 0.5 / np.sqrt(density)
            clark_evans_index = mean_min_distance / expected_mean_distance
        else:
            clark_evans_index = None
            
        # Interprétation
        if clark_evans_index is not None:
            if clark_evans_index < 0.8:
                distribution_type = "Agrégée"
            elif clark_evans_index > 1.2:
                distribution_type = "Régulière"
            else:
                distribution_type = "Aléatoire"
        else:
            distribution_type = "Indéterminée"
        
        return {
            "spatial_data_available": True,
            "nearest_neighbor": {
                "mean_distance": mean_min_distance,
                "std_distance": std_min_distance,
                "min_distance": np.min(min_distances),
                "max_distance": np.max(min_distances)
            },
            "spatial_pattern": {
                "clark_evans_index": clark_evans_index,
                "distribution_type": distribution_type,
                "tree_density": density
            }
        }
    
    def _estimate_economic_value(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Estime la valeur économique du peuplement."""
        if 'diameter' not in df.columns:
            return {"error": "Données de diamètre non disponibles pour l'estimation économique"}
            
        # Valeurs du bois par espèce et classe de diamètre (€/m³)
        default_values = {
            "small": 15,   # Petit bois (< 20 cm)
            "medium": 45,  # Bois moyen (20-35 cm)
            "large": 75    # Gros bois (> 35 cm)
        }
        
        species_values = {
            "Quercus": {"small": 20, "medium": 60, "large": 90},  # Chêne
            "Fagus": {"small": 15, "medium": 50, "large": 80},    # Hêtre
            "Pinus": {"small": 10, "medium": 40, "large": 70},    # Pin
            "Abies": {"small": 12, "medium": 45, "large": 75},    # Sapin
            "Picea": {"small": 12, "medium": 45, "large": 75},    # Épicéa
            "Pseudotsuga": {"small": 15, "medium": 55, "large": 85},  # Douglas
            "Larix": {"small": 15, "medium": 50, "large": 80},    # Mélèze
            "Fraxinus": {"small": 15, "medium": 55, "large": 85}, # Frêne
            "Acer": {"small": 15, "medium": 50, "large": 75},     # Érable
        }
        
        # Calculer le volume et la valeur pour chaque arbre
        total_value = 0
        total_volume = 0
        value_by_species = {}
        volume_by_species = {}
        
        for species in df['species'].unique():
            species_df = df[df['species'] == species]
            
            # Identifier le genre pour trouver les valeurs
            genus = species.split(' ')[0] if ' ' in species else species
            values = species_values.get(genus, default_values)
            
            species_value = 0
            species_volume = 0
            
            for _, tree in species_df.iterrows():
                # Calculer le volume de l'arbre
                diameter = tree['diameter']
                
                # Utiliser la hauteur si disponible, sinon estimer
                if 'height' in tree and not pd.isna(tree['height']):
                    height = tree['height']
                else:
                    # Équation hauteur-diamètre simplifiée
                    height = 1.3 + 0.25 * diameter
                
                # Calculer le volume avec l'équation appropriée
                volume_eq = None
                for g in self.volume_equations:
                    if genus.startswith(g):
                        volume_eq = self.volume_equations[g]
                        break
                
                if volume_eq is None:
                    volume_eq = self.volume_equations["default"]
                    
                a, b, c = volume_eq
                volume = a + b * ((diameter/100) ** 2) * height
                
                # Déterminer la catégorie de diamètre
                if diameter < 20:
                    category = "small"
                elif diameter < 35:
                    category = "medium"
                else:
                    category = "large"
                    
                # Calculer la valeur
                value = volume * values[category]
                
                species_volume += volume
                species_value += value
                
            total_volume += species_volume
            total_value += species_value
            
            volume_by_species[species] = species_volume
            value_by_species[species] = species_value
        
        # Calculer la valeur moyenne par m³
        mean_value_per_m3 = total_value / total_volume if total_volume > 0 else 0
        
        return {
            "total_value": total_value,
            "total_volume": total_volume,
            "mean_value_per_m3": mean_value_per_m3,
            "value_by_species": value_by_species,
            "volume_by_species": volume_by_species,
            "disclaimer": "Estimation basée sur des valeurs génériques"
        }
    
    def _calculate_per_hectare_metrics(self, df: pd.DataFrame, species_analysis: Dict[str, Any], area_ha: float) -> Dict[str, Any]:
        """Calcule les métriques par hectare."""
        density = len(df) / area_ha  # arbres/ha
        
        # Calculer la surface terrière (m²/ha)
        if 'diameter' in df.columns:
            # Formule: π * (d/2)^2 (en m²) pour chaque arbre
            basal_areas = np.pi * ((df['diameter']/100) / 2) ** 2
            total_basal_area = basal_areas.sum()
            basal_area_per_ha = total_basal_area / area_ha
        else:
            basal_area_per_ha = None
            
        # Volume par hectare
        volume_per_ha = None
        species_volume_per_ha = {}
        
        for species, analysis in species_analysis.items():
            if 'volume' in analysis:
                species_vol = analysis['volume']['total']
                species_volume_per_ha[species] = species_vol / area_ha
                
        if species_volume_per_ha:
            volume_per_ha = sum(species_volume_per_ha.values())
            
        result = {
            "density": density,
            "basal_area": basal_area_per_ha,
            "volume": volume_per_ha,
            "species_volume": species_volume_per_ha
        }
        
        return result
    
    def _determine_forest_type(self, df: pd.DataFrame) -> ForestType:
        """Détermine le type forestier en fonction des caractéristiques du peuplement."""
        if 'diameter' not in df.columns:
            return ForestType.UNKNOWN
            
        # Nombre d'espèces
        n_species = df['species'].nunique()
        
        # Répartition des espèces (proportion de l'espèce dominante)
        dominant_species_prop = df['species'].value_counts(normalize=True).max()
        
        # Coefficient de variation des diamètres
        cv_diameter = (df['diameter'].std() / df['diameter'].mean()) * 100 if df['diameter'].mean() > 0 else 0
        
        # Indicateurs de structure spatiale
        if cv_diameter < 30 and dominant_species_prop > 0.8:
            # Peuplement régulier et une espèce dominante -> plantation ou régénération naturelle
            if n_species < 3:
                return ForestType.PLANTATION
            else:
                return ForestType.NATURAL_REGENERATION
        elif n_species > 3 and dominant_species_prop < 0.6:
            # Plusieurs espèces, aucune fortement dominante -> peuplement mixte
            return ForestType.MIXED
        elif cv_diameter > 50:
            # Grande hétérogénéité de diamètres -> peuplement irrégulier
            return ForestType.IRREGULAR
        elif cv_diameter < 30:
            # Faible variation de diamètres -> peuplement régulier équienne
            return ForestType.EVEN_AGED
        else:
            # Variation moyenne de diamètres -> peuplement irrégulier inéquienne
            return ForestType.UNEVEN_AGED
    
    def _generate_visualizations(self, df: pd.DataFrame) -> Dict[str, str]:
        """Génère des visualisations des données d'inventaire."""
        visualizations = {}
        
        # Distribution des diamètres
        if 'diameter' in df.columns:
            plt.figure(figsize=(10, 6))
            plt.hist(df['diameter'], bins=20, color='skyblue', edgecolor='black')
            plt.title('Distribution des diamètres')
            plt.xlabel('Diamètre (cm)')
            plt.ylabel('Nombre d\'arbres')
            plt.grid(True, alpha=0.3)
            
            # Convertir en base64 pour inclusion dans le JSON
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            visualizations['diameter_distribution'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
        
        # Distribution des espèces
        if 'species' in df.columns:
            species_counts = df['species'].value_counts()
            
            plt.figure(figsize=(10, 6))
            species_counts.plot(kind='bar', color='lightgreen')
            plt.title('Distribution des espèces')
            plt.xlabel('Espèce')
            plt.ylabel('Nombre d\'arbres')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            visualizations['species_distribution'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
        return visualizations