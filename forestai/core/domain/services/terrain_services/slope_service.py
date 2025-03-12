# forestai/core/domain/services/terrain_services/slope_service.py

import os
import time
import numpy as np
import rasterio
from typing import Dict, Any, Optional, List
import pyproj
from shapely.ops import transform
from pathlib import Path

from forestai.core.domain.models.parcel import Parcel
from forestai.core.domain.services.terrain_services.base_terrain_service import BaseTerrainService
from forestai.core.utils.logging_config import log_function

class SlopeService(BaseTerrainService):
    """
    Service spécialisé pour l'analyse de pente et d'exposition du terrain.
    Utilise des données MNT pour calculer les pentes et orientations du terrain.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialise le service d'analyse de pente.
        
        Args:
            data_dir: Répertoire contenant les données géographiques
        """
        super().__init__(data_dir, "SlopeService")
        
        # Trouver le fichier MNT
        self.mnt_path = self._find_mnt_file()
    
    def _find_mnt_file(self) -> Optional[Path]:
        """Trouve le fichier MNT (Modèle Numérique de Terrain) dans le répertoire des données."""
        # Chercher selon différentes extensions possibles: .tif, .asc, etc.
        potential_paths = list(self.data_dir.glob("**/*mnt*.tif")) + \
                          list(self.data_dir.glob("**/*mnt*.asc")) + \
                          list(self.data_dir.glob("**/rgealti*.tif"))
        
        if not potential_paths:
            self.logger.warning(f"Aucun fichier MNT trouvé dans {self.data_dir}")
            return None
        
        self.logger.info(f"Fichier MNT trouvé: {potential_paths[0]}")
        return potential_paths[0]
    
    @log_function(level="DEBUG")
    def calculate_slope(self, parcel: Parcel) -> Dict[str, Any]:
        """
        Calcule la pente et l'exposition du terrain d'une parcelle.
        
        Args:
            parcel: Objet Parcel à analyser
            
        Returns:
            Dictionnaire contenant les informations de pente et d'exposition
        """
        # Standardiser la parcelle (conversion Lambert 93)
        parcel = self.get_standardized_parcel(parcel)
        
        # Vérifier si les données MNT sont disponibles
        if not self.mnt_path or not self.mnt_path.exists():
            self.logger.warning("Données MNT non disponibles, estimation de pente par défaut")
            return {
                "mean_slope": None,
                "max_slope": None,
                "min_slope": None,
                "slope_classification": None,
                "aspect_cardinal": None,
                "source": "default"
            }
        
        try:
            # Convertir la géométrie de la parcelle en système de coordonnées du MNT si nécessaire
            parcel_geometry = parcel.geometry
            
            # Ouvrir le fichier MNT
            with rasterio.open(self.mnt_path) as src:
                # Obtenir l'emprise de la parcelle
                bounds = parcel_geometry.bounds
                
                # Transformer les coordonnées de la parcelle vers le système du MNT si nécessaire
                if src.crs != parcel.crs:
                    project = pyproj.Transformer.from_crs(
                        parcel.crs if parcel.crs else "EPSG:4326",  # WGS84 par défaut
                        src.crs.to_string(),
                        always_xy=True
                    ).transform
                    parcel_geometry = transform(project, parcel_geometry)
                    bounds = parcel_geometry.bounds
                
                # Extraire la région d'intérêt
                window = src.window(*bounds)
                
                # Lire les données d'élévation
                elevation_data = src.read(1, window=window)
                
                # Masquer les valeurs NoData
                elevation_data = np.ma.masked_equal(elevation_data, src.nodata)
                
                # Calculer la pente
                pixel_size_x = src.transform[0]
                pixel_size_y = src.transform[4]
                
                if elevation_data.shape[0] < 3 or elevation_data.shape[1] < 3:
                    # Trop peu de pixels pour calculer la pente
                    self.logger.warning(f"Trop peu de pixels pour calculer la pente pour la parcelle {parcel.id}")
                    return {
                        "mean_slope": None,
                        "max_slope": None,
                        "min_slope": None,
                        "slope_classification": None,
                        "aspect_cardinal": None,
                        "source": "insufficient_data"
                    }
                
                # Calculer la pente en degrés
                dy, dx = np.gradient(elevation_data, pixel_size_y, pixel_size_x)
                slope = np.degrees(np.arctan(np.sqrt(dx*dx + dy*dy)))
                
                # Calculer l'orientation (aspect) en degrés (0=Nord, 90=Est, 180=Sud, 270=Ouest)
                aspect = np.degrees(np.arctan2(-dx, dy))
                aspect = np.where(aspect < 0, aspect + 360, aspect)
                
                # Calculer les statistiques de pente
                mean_slope = float(np.ma.mean(slope))
                min_slope = float(np.ma.min(slope))
                max_slope = float(np.ma.max(slope))
                
                # Classification de la pente pour la foresterie
                if mean_slope < 5:
                    slope_class = "plat"
                elif mean_slope < 15:
                    slope_class = "doux"
                elif mean_slope < 30:
                    slope_class = "modéré"
                else:
                    slope_class = "abrupt"
                
                # Orientation cardinale dominante
                aspect_mean = float(np.ma.mean(aspect))
                if aspect_mean < 22.5 or aspect_mean >= 337.5:
                    cardinal = "Nord"
                elif aspect_mean < 67.5:
                    cardinal = "Nord-Est"
                elif aspect_mean < 112.5:
                    cardinal = "Est"
                elif aspect_mean < 157.5:
                    cardinal = "Sud-Est"
                elif aspect_mean < 202.5:
                    cardinal = "Sud"
                elif aspect_mean < 247.5:
                    cardinal = "Sud-Ouest"
                elif aspect_mean < 292.5:
                    cardinal = "Ouest"
                else:
                    cardinal = "Nord-Ouest"
        
        except Exception as e:
            self.logger.exception(f"Erreur lors du calcul de pente pour la parcelle {parcel.id}: {str(e)}")
            return {
                "mean_slope": None,
                "max_slope": None,
                "min_slope": None,
                "slope_classification": None,
                "aspect_cardinal": None,
                "error": str(e),
                "source": "error"
            }
        
        return {
            "mean_slope": mean_slope,
            "max_slope": max_slope,
            "min_slope": min_slope,
            "slope_classification": slope_class,
            "aspect_mean": aspect_mean,
            "aspect_cardinal": cardinal,
            "source": "calculated"
        }
    
    @log_function(level="INFO")
    def get_slope_constraints(self, slope_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifie les contraintes basées sur les données de pente.
        
        Args:
            slope_data: Résultats d'analyse de pente
            
        Returns:
            Liste des contraintes liées à la pente
        """
        constraints = []
        
        if not slope_data or slope_data.get("mean_slope") is None:
            return []
        
        mean_slope = slope_data.get("mean_slope")
        max_slope = slope_data.get("max_slope")
        slope_class = slope_data.get("slope_classification")
        
        if mean_slope > 15:
            severity = "modérée" if mean_slope < 30 else "importante"
            constraints.append({
                "type": "pente",
                "severity": severity,
                "description": f"Pente moyenne de {mean_slope:.1f}° ({slope_class})",
                "impact": "Limite l'accès aux machines, augmente coûts d'exploitation et risques d'érosion"
            })
        
        if max_slope is not None and max_slope > 35:
            constraints.append({
                "type": "forte_pente",
                "severity": "importante",
                "description": f"Zones à forte pente (maximum {max_slope:.1f}°)",
                "impact": "Zones inexploitables par machines, fort risque d'érosion"
            })
        
        return constraints
    
    @log_function(level="INFO")
    def get_slope_recommendations(self, slope_data: Dict[str, Any]) -> List[str]:
        """
        Génère des recommandations basées sur la pente et l'exposition du terrain.
        
        Args:
            slope_data: Résultats d'analyse de pente
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        if not slope_data or slope_data.get("mean_slope") is None:
            return ["Données de pente non disponibles. Visite terrain recommandée."]
        
        slope_class = slope_data.get("slope_classification")
        aspect = slope_data.get("aspect_cardinal")
        mean_slope = slope_data.get("mean_slope")
        
        # Recommandations basées sur la pente
        if slope_class == "abrupt":
            recommendations.append(
                f"Terrain à forte pente (moyenne: {mean_slope:.1f}°): privilégier des techniques d'exploitation à faible impact "
                "(câble, débardage animal). Plantation en terrasses ou gradins recommandée."
            )
        elif slope_class == "modéré":
            recommendations.append(
                f"Terrain en pente modérée (moyenne: {mean_slope:.1f}°): adapter les méthodes de plantation et d'exploitation. "
                "Prévoir des mesures anti-érosion sur les zones les plus pentues."
            )
        elif slope_class == "doux":
            recommendations.append(
                f"Terrain en pente douce (moyenne: {mean_slope:.1f}°): bonne accessibilité pour la mécanisation. "
                "Surveiller toutefois le ruissellement sur les longues pentes."
            )
        elif slope_class == "plat":
            recommendations.append(
                f"Terrain plat (moyenne: {mean_slope:.1f}°): excellent pour l'exploitation mécanisée. "
                "Vérifier néanmoins le drainage du sol qui peut être limité."
            )
        
        # Recommandations basées sur l'exposition
        if aspect:
            if aspect in ["Sud", "Sud-Est", "Sud-Ouest"]:
                recommendations.append(
                    f"Exposition {aspect}: parcelle ensoleillée, plus chaude et sèche. "
                    "Privilégier des essences tolérantes à la chaleur et à la sécheresse."
                )
            elif aspect in ["Nord", "Nord-Est", "Nord-Ouest"]:
                recommendations.append(
                    f"Exposition {aspect}: parcelle ombragée, plus froide et humide. "
                    "Les essences sensibles à la sécheresse y seront favorisées."
                )
        
        return recommendations
    
    @log_function(level="INFO")
    def is_mechanizable(self, slope_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détermine si le terrain est mécanisable pour l'exploitation forestière.
        
        Args:
            slope_data: Résultats d'analyse de pente
            
        Returns:
            Informations sur la mécanisabilité du terrain
        """
        if not slope_data or slope_data.get("mean_slope") is None:
            return {
                "mechanizable": None,
                "percentage": None,
                "comment": "Données insuffisantes pour évaluer la mécanisabilité"
            }
        
        mean_slope = slope_data.get("mean_slope")
        max_slope = slope_data.get("max_slope")
        
        # Seuils de mécanisabilité
        if mean_slope <= 10:
            mechanizable = True
            percentage = 100
            comment = "Terrain entièrement mécanisable"
        elif mean_slope <= 20:
            mechanizable = True
            percentage = 100 - (mean_slope - 10) * 5  # 100% à 10°, 50% à 20°
            comment = "Terrain partiellement mécanisable, contraintes sur certaines zones"
        elif mean_slope <= 30:
            mechanizable = False
            percentage = 50 - (mean_slope - 20) * 5  # 50% à 20°, 0% à 30°
            comment = "Mécanisation difficile et limitée, techniques alternatives recommandées"
        else:
            mechanizable = False
            percentage = 0
            comment = "Mécanisation conventionnelle impossible, recourir au débardage par câble ou animal"
        
        return {
            "mechanizable": mechanizable,
            "percentage": percentage,
            "comment": comment
        }
