# -*- coding: utf-8 -*-
"""
Module d'analyse d'inventaire forestier pour le DiagnosticAgent.

Ce module fournit des fonctionnalités avancées pour analyser les données d'inventaire
forestier, calculer les volumes, densités, et statistiques de peuplement.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from scipy import stats

logger = logging.getLogger(__name__)

class InventoryAnalyzer:
    """Analyseur spécialisé pour les données d'inventaire forestier."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialise l'analyseur d'inventaire.
        
        Args:
            config: Configuration optionnelle
        """
        self.config = config or {}
        logger.debug("InventoryAnalyzer initialisé")
    
    def analyze(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse complète des données d'inventaire forestier.
        
        Args:
            inventory_data: Données d'inventaire forestier
            
        Returns:
            Résultats de l'analyse
        """
        try:
            # Conversion en DataFrame
            if isinstance(inventory_data, Dict) and "items" in inventory_data:
                df = pd.DataFrame(inventory_data["items"])
            elif isinstance(inventory_data, List):
                df = pd.DataFrame(inventory_data)
            else:
                raise ValueError("Format d'inventaire non reconnu")
            
            # Vérification des colonnes requises
            required_columns = ["species"]
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Colonne '{col}' manquante dans les données d'inventaire")
            
            # Calcul des métriques de base
            basic_metrics = self._calculate_basic_metrics(df, inventory_data)
            
            # Calcul des volumes si les données le permettent
            volume_metrics = {}
            if "diameter" in df.columns and "height" in df.columns:
                volume_metrics = self._calculate_volumes(df)
            
            # Analyse de la structure du peuplement
            structure_analysis = self._analyze_stand_structure(df)
            
            # Analyse de diversité
            diversity_analysis = self._analyze_diversity(df)
            
            # Santé du peuplement
            health_analysis = {}
            if "health_status" in df.columns:
                health_analysis = self._analyze_health(df)
            
            # Combinaison des résultats
            result = {
                "basic_metrics": basic_metrics,
                "volumes": volume_metrics,
                "stand_structure": structure_analysis,
                "diversity": diversity_analysis
            }
            
            if health_analysis:
                result["health"] = health_analysis
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'inventaire: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_basic_metrics(self, df: pd.DataFrame, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule les métriques de base de l'inventaire.
        
        Args:
            df: DataFrame des arbres individuels
            inventory_data: Données d'inventaire complètes
            
        Returns:
            Métriques de base
        """
        # Nombre d'arbres par espèce
        species_count = df["species"].value_counts()
        species_percent = species_count / len(df) * 100
        species_distribution = {species: {
            "count": int(count),
            "percent": float(species_percent[species])
        } for species, count in species_count.items()}
        
        # Statistiques par espèce pour le diamètre et la hauteur
        species_stats = {}
        if "diameter" in df.columns:
            for species in df["species"].unique():
                species_df = df[df["species"] == species]
                species_stats[species] = {
                    "diameter": {
                        "mean": float(species_df["diameter"].mean()),
                        "median": float(species_df["diameter"].median()),
                        "std": float(species_df["diameter"].std()),
                        "min": float(species_df["diameter"].min()),
                        "max": float(species_df["diameter"].max()),
                        "q25": float(species_df["diameter"].quantile(0.25)),
                        "q75": float(species_df["diameter"].quantile(0.75))
                    }
                }
                if "height" in df.columns:
                    species_stats[species]["height"] = {
                        "mean": float(species_df["height"].mean()),
                        "median": float(species_df["height"].median()),
                        "std": float(species_df["height"].std()),
                        "min": float(species_df["height"].min()),
                        "max": float(species_df["height"].max()),
                        "q25": float(species_df["height"].quantile(0.25)),
                        "q75": float(species_df["height"].quantile(0.75))
                    }
        
        # Calcul de densité
        density = None
        if "area" in inventory_data and isinstance(inventory_data["area"], (int, float)) and inventory_data["area"] > 0:
            area_ha = inventory_data["area"] if inventory_data.get("area_unit") == "ha" else inventory_data["area"] / 10000
            density = len(df) / area_ha
        
        result = {
            "total_trees": len(df),
            "species_count": len(species_count),
            "species_distribution": species_distribution
        }
        
        if species_stats:
            result["species_stats"] = species_stats
            
        if density is not None:
            result["density"] = {
                "trees_per_ha": float(density),
                "area_ha": float(area_ha)
            }
            
        return result
    
    def _calculate_volumes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcule les volumes de bois.
        
        Args:
            df: DataFrame avec diamètres et hauteurs
            
        Returns:
            Métriques de volume
        """
        # S'assurer que les colonnes nécessaires existent
        if "diameter" not in df.columns or "height" not in df.columns:
            return {}
        
        # Cloner pour éviter de modifier l'original
        df_vol = df.copy()
        
        # Conversion du diamètre en cm à m si nécessaire
        if df_vol["diameter"].mean() > 10:  # probablement en cm
            df_vol["diameter_m"] = df_vol["diameter"] / 100
        else:  # déjà en mètres
            df_vol["diameter_m"] = df_vol["diameter"]
        
        # Calcul du volume individuel de chaque arbre (formule de Huber simplifiée)
        # V = pi * (d/2)² * h * f, où f est le facteur de forme (par défaut 0.5)
        df_vol["volume"] = np.pi * (df_vol["diameter_m"] / 2) ** 2 * df_vol["height"] * 0.5
        
        # Facteurs de forme spécifiques par espèce si disponibles
        form_factors = {
            "Pinus sylvestris": 0.48,  # Pin sylvestre
            "Quercus robur": 0.55,    # Chêne pédonculé
            "Quercus petraea": 0.55,  # Chêne sessile
            "Fagus sylvatica": 0.53,  # Hêtre
            "Picea abies": 0.47,      # Épicéa commun
            "Pseudotsuga menziesii": 0.49,  # Douglas
            "Abies alba": 0.50        # Sapin pectiné
        }
        
        # Appliquer les facteurs de forme spécifiques
        for species, factor in form_factors.items():
            mask = df_vol["species"] == species
            if mask.any():
                df_vol.loc[mask, "volume"] = np.pi * (df_vol.loc[mask, "diameter_m"] / 2) ** 2 * df_vol.loc[mask, "height"] * factor
        
        # Volume total
        total_volume = df_vol["volume"].sum()
        
        # Volume par espèce
        volume_by_species = df_vol.groupby("species")["volume"].agg(["sum", "mean"]).reset_index()
        volume_by_species = {
            row["species"]: {
                "total_m3": float(row["sum"]),
                "average_m3_per_tree": float(row["mean"]),
                "percent_of_total": float(row["sum"] / total_volume * 100)
            } for _, row in volume_by_species.iterrows()
        }
        
        # Classes de diamètre et volume par classe
        if len(df_vol) > 1:  # Assez d'arbres pour faire des classes
            # Définition des classes de diamètre (en cm pour faciliter la compréhension)
            diameter_cm = df_vol["diameter_m"] * 100
            
            # Déterminer les bornes des classes (adaptatives)
            min_diam = diameter_cm.min()
            max_diam = diameter_cm.max()
            range_diam = max_diam - min_diam
            
            if range_diam > 50:  # Large gamme de diamètres
                # Classes de 10 cm
                bin_width = 10
            elif range_diam > 25:  # Gamme moyenne
                # Classes de 5 cm
                bin_width = 5
            else:  # Petite gamme
                # Classes de 2.5 cm
                bin_width = 2.5
                
            # Arrondir les bornes pour des classes propres
            lower_bound = np.floor(min_diam / bin_width) * bin_width
            upper_bound = np.ceil(max_diam / bin_width) * bin_width
            
            # Créer les bins
            bins = np.arange(lower_bound, upper_bound + bin_width, bin_width)
            labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
            
            # Créer les catégories
            df_vol["diameter_class"] = pd.cut(diameter_cm, bins=bins, labels=labels, include_lowest=True)
            
            # Volume par classe de diamètre
            volume_by_class = df_vol.groupby("diameter_class")["volume"].sum().reset_index()
            volume_by_diameter_class = {
                str(row["diameter_class"]): float(row["volume"]) for _, row in volume_by_class.iterrows()
            }
        else:
            volume_by_diameter_class = {}
        
        return {
            "total_volume_m3": float(total_volume),
            "by_species": volume_by_species,
            "by_diameter_class": volume_by_diameter_class
        }
    
    def _analyze_stand_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyse la structure du peuplement.
        
        Args:
            df: DataFrame des arbres individuels
            
        Returns:
            Analyse de structure
        """
        result = {}
        
        # Analyse des diamètres si disponible
        if "diameter" in df.columns and len(df) >= 10:
            # Déterminer le type de distribution (normale, bimodale, etc.)
            diameters = df["diameter"]
            
            # Test de normalité
            _, normality_p_value = stats.shapiro(diameters) if len(diameters) < 5000 else (0, 0)
            is_normal = normality_p_value > 0.05
            
            # Asymétrie et aplatissement
            skewness = float(stats.skew(diameters))
            kurtosis = float(stats.kurtosis(diameters))
            
            # Détection de distribution bimodale avec KMeans
            is_bimodal = False
            if len(diameters) >= 20:  # Assez de données pour détecter une bimodalité
                X = diameters.values.reshape(-1, 1)
                kmeans = KMeans(n_clusters=2, random_state=42).fit(X)
                centers = sorted(kmeans.cluster_centers_.flatten())
                # Si centres suffisamment éloignés, potentiellement bimodal
                if len(centers) == 2 and (centers[1] - centers[0]) > (diameters.std()):
                    is_bimodal = True
            
            # Interprétation de la structure
            structure_type = "irrégulière"
            if is_normal:
                structure_type = "régulière équienne"
            elif is_bimodal:
                structure_type = "bimodale (potentiellement deux âges distincts)"
            elif skewness > 1.0:
                structure_type = "irrégulière à dominance de petits diamètres"
            elif skewness < -1.0:
                structure_type = "irrégulière à dominance de gros diamètres"
            
            # Interprétation sylvicole basée sur la distribution
            if is_normal:
                sylvicultural_interpretation = "Peuplement équienne, probablement issu d'une plantation ou régénération homogène"
            elif is_bimodal:
                sylvicultural_interpretation = "Peuplement à deux strates distinctes, possible mélange générationnel ou intervention sylvicole passée"
            elif skewness > 1.0:
                sylvicultural_interpretation = "Dominance de jeunes arbres, indiquant un renouvellement récent ou une dynamique de recrutement active"
            elif skewness < -1.0:
                sylvicultural_interpretation = "Dominance de vieux arbres, pouvant indiquer un problème de régénération ou un peuplement mature"
            else:
                sylvicultural_interpretation = "Structure irrégulière équilibrée, typique d'une forêt gérée en futaie irrégulière ou naturelle ancienne"
            
            result["diameter_distribution"] = {
                "normality_test": {
                    "is_normal": bool(is_normal),
                    "p_value": float(normality_p_value)
                },
                "skewness": skewness,
                "kurtosis": kurtosis,
                "is_bimodal": bool(is_bimodal),
                "structure_type": structure_type,
                "sylvicultural_interpretation": sylvicultural_interpretation
            }
        
        # Analyse verticale (strates) si hauteur disponible
        if "height" in df.columns and len(df) >= 5:
            heights = df["height"]
            
            # Définition des strates (en mètres)
            strata_def = {
                "regeneration": (0, 1.5),
                "sous-etage": (1.5, 8),
                "etage-intermediaire": (8, 20),
                "etage-dominant": (20, float('inf'))
            }
            
            # Comptage par strate
            strata_counts = {}
            for stratum, (min_h, max_h) in strata_def.items():
                count = ((heights >= min_h) & (heights < max_h)).sum()
                strata_counts[stratum] = int(count)
            
            # Présence/absence de strates
            strata_presence = {stratum: (count > 0) for stratum, count in strata_counts.items()}
            
            # Nombre de strates présentes
            num_strata = sum(strata_presence.values())
            
            # Caractérisation globale
            if num_strata == 1:
                vertical_structure = "monostrate"
            elif num_strata == 2:
                vertical_structure = "bistrate"
            elif num_strata >= 3:
                vertical_structure = "multistrate"
            else:
                vertical_structure = "indéterminé"
            
            result["vertical_structure"] = {
                "strata_counts": strata_counts,
                "strata_presence": strata_presence,
                "number_of_strata": num_strata,
                "classification": vertical_structure
            }
        
        return result
    
    def _analyze_diversity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyse la diversité des espèces.
        
        Args:
            df: DataFrame des arbres individuels
            
        Returns:
            Indices de diversité
        """
        if "species" not in df.columns or len(df) == 0:
            return {}
            
        # Comptage par espèce
        species_counts = df["species"].value_counts()
        total_trees = len(df)
        
        # Indice de Shannon
        proportions = species_counts / total_trees
        shannon_index = -sum(p * np.log(p) for p in proportions)
        
        # Indice de Simpson
        simpson_index = 1 - sum((n / total_trees) ** 2 for n in species_counts)
        
        # Indice d'équitabilité de Pielou (normalise Shannon entre 0 et 1)
        species_richness = len(species_counts)
        max_shannon = np.log(species_richness) if species_richness > 1 else 0
        pielou_evenness = shannon_index / max_shannon if max_shannon > 0 else 0
        
        # Espèce dominante
        dominant_species = species_counts.idxmax() if not species_counts.empty else None
        dominant_percentage = (species_counts.max() / total_trees * 100) if not species_counts.empty else 0
        
        # Type de mélange
        if species_richness == 1:
            mixture_type = "peuplement pur"
        elif species_richness == 2:
            mixture_type = "mélange binaire"
        elif species_richness <= 4:
            mixture_type = "mélange limité"
        else:
            mixture_type = "mélange diversifié"
        
        # Recommandation écologique
        if pielou_evenness > 0.7 and species_richness > 3:
            ecological_value = "élevée - mélange équilibré et diversifié favorable à la biodiversité"
        elif species_richness > 2:
            ecological_value = "moyenne - présence de mélange mais déséquilibre dans les proportions"
        else:
            ecological_value = "faible - peu d'espèces présentes, vulnérabilité aux perturbations"
        
        return {
            "species_richness": int(species_richness),
            "shannon_index": float(shannon_index),
            "simpson_index": float(simpson_index),
            "pielou_evenness": float(pielou_evenness),
            "dominant_species": dominant_species,
            "dominant_percentage": float(dominant_percentage),
            "mixture_type": mixture_type,
            "ecological_value": ecological_value
        }
    
    def _analyze_health(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyse l'état sanitaire du peuplement.
        
        Args:
            df: DataFrame avec statut sanitaire
            
        Returns:
            Analyse sanitaire
        """
        if "health_status" not in df.columns:
            return {}
        
        # Vérifier que la colonne existe et n'est pas vide
        if df["health_status"].isnull().all():
            return {}
        
        # Comptage par statut sanitaire
        health_counts = df["health_status"].value_counts()
        health_percent = health_counts / len(df) * 100
        
        # Conversion en dictionnaire
        health_distribution = {
            status: {
                "count": int(count),
                "percent": float(health_percent[status])
            } for status, count in health_counts.items()
        }
        
        # Score de santé global (0-100%)
        # Exemple: healthy=100%, stressed=50%, damaged=25%, dying=10%, dead=0%
        health_scores = {
            "healthy": 1.0,
            "stressed": 0.5,
            "damaged": 0.25,
            "dying": 0.1,
            "dead": 0.0
        }
        
        # Statuts standard à assigner si autres termes utilisés
        status_mapping = {
            # Français
            "sain": "healthy",
            "stressé": "stressed",
            "endommagé": "damaged",
            "mourant": "dying",
            "mort": "dead",
            # Anglais autres termes
            "good": "healthy",
            "fair": "stressed",
            "poor": "damaged",
            "critical": "dying",
            # Numérique
            "1": "healthy",
            "2": "stressed",
            "3": "damaged",
            "4": "dying",
            "5": "dead"
        }
        
        # Calcul du score sanitaire global
        total_score = 0
        scored_trees = 0
        
        for status, stats in health_distribution.items():
            # Déterminer le score pour ce statut
            status_key = status.lower() if isinstance(status, str) else str(status)
            
            # Utiliser le statut mappé si disponible
            mapped_status = status_mapping.get(status_key, status_key)
            score = health_scores.get(mapped_status)
            
            if score is not None:
                total_score += score * stats["count"]
                scored_trees += stats["count"]
        
        # Calculer le score global en pourcentage
        health_score = (total_score / scored_trees * 100) if scored_trees > 0 else None
        
        # Déterminer les problèmes majeurs si disponibles
        major_issues = None
        if "health_issue" in df.columns and not df["health_issue"].isnull().all():
            issue_counts = df["health_issue"].value_counts()
            major_issues = {
                issue: {
                    "count": int(count),
                    "percent": float(count / len(df) * 100)
                } for issue, count in issue_counts.items() if not pd.isna(issue)
            }
        
        result = {
            "health_distribution": health_distribution
        }
        
        if health_score is not None:
            result["health_score"] = float(health_score)
            
            # Interprétation du score
            if health_score >= 90:
                result["health_interpretation"] = "excellent - peuplement très sain"
            elif health_score >= 75:
                result["health_interpretation"] = "bon - peuplement majoritairement sain"
            elif health_score >= 50:
                result["health_interpretation"] = "moyen - signes de stress significatifs"
            elif health_score >= 25:
                result["health_interpretation"] = "préoccupant - problèmes sanitaires importants"
            else:
                result["health_interpretation"] = "critique - peuplement fortement compromis"
        
        if major_issues:
            result["major_issues"] = major_issues
            
        return result