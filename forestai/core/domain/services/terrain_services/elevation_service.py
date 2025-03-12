# forestai/core/domain/services/terrain_services/elevation_service.py

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

class ElevationService(BaseTerrainService):
    """
    Service spécialisé pour l'analyse d'élévation de terrain.
    Utilise des données MNT (Modèle Numérique de Terrain) pour calculer
    les statistiques d'altitude d'une parcelle.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialise le service d'analyse d'élévation.
        
        Args:
            data_dir: Répertoire contenant les données géographiques
        """
        super().__init__(data_dir, "ElevationService")
        
        # Trouver le fichier MNT
        self.mnt_path = self._find_mnt_file()
        
        # Cache pour les données MNT par région
        self._mnt_cache = {}
    
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
    def analyze_elevation(self, parcel: Parcel) -> Dict[str, Any]:
        """
        Analyse l'élévation (altitude) d'une parcelle à partir du MNT.
        
        Args:
            parcel: Objet Parcel à analyser
            
        Returns:
            Dictionnaire contenant les statistiques d'élévation
        """
        # Standardiser la parcelle (conversion Lambert 93)
        parcel = self.get_standardized_parcel(parcel)
        
        # Vérifier si les données MNT sont disponibles
        if not self.mnt_path or not self.mnt_path.exists():
            self.logger.warning("Données MNT non disponibles, estimation d'élévation par défaut")
            return {
                "mean": None,
                "min": None,
                "max": None,
                "std": None,
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
                
                # Calculer les statistiques
                if not elevation_data.mask.all():  # S'assurer qu'il y a des données valides
                    mean_elevation = float(elevation_data.mean())
                    min_elevation = float(elevation_data.min())
                    max_elevation = float(elevation_data.max())
                    std_elevation = float(elevation_data.std())
                    
                    # Discrétiser les élévations pour histogramme
                    bins = np.linspace(min_elevation, max_elevation, 10)
                    hist, bin_edges = np.histogram(elevation_data.compressed(), bins=bins)
                    
                    histogram = [{
                        "min": float(bin_edges[i]),
                        "max": float(bin_edges[i+1]),
                        "count": int(hist[i])
                    } for i in range(len(hist))]
                else:
                    # Pas de données valides dans la région d'intérêt
                    self.logger.warning(f"Pas de données d'élévation valides pour la parcelle {parcel.id}")
                    return {
                        "mean": None,
                        "min": None,
                        "max": None,
                        "std": None,
                        "source": "mnt_nodata"
                    }
        
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'analyse d'élévation pour la parcelle {parcel.id}: {str(e)}")
            return {
                "mean": None,
                "min": None,
                "max": None,
                "std": None,
                "error": str(e),
                "source": "error"
            }
        
        return {
            "mean": mean_elevation,
            "min": min_elevation,
            "max": max_elevation,
            "std": std_elevation,
            "histogram": histogram,
            "source": "mnt"
        }
    
    @log_function(level="INFO")
    def get_elevation_zone(self, mean_elevation: float) -> str:
        """
        Classifie l'élévation selon les zones d'altitude forestières.
        
        Args:
            mean_elevation: Altitude moyenne en mètres
            
        Returns:
            Classification de la zone d'altitude
        """
        if mean_elevation is None:
            return "inconnue"
        
        if mean_elevation < 400:
            return "plaine"
        elif mean_elevation < 800:
            return "collinéenne"
        elif mean_elevation < 1500:
            return "montagnarde"
        elif mean_elevation < 1900:
            return "subalpine"
        else:
            return "alpine"
    
    @log_function(level="INFO")
    def get_elevation_recommendations(self, elevation_data: Dict[str, Any]) -> List[str]:
        """
        Génère des recommandations basées sur l'élévation du terrain.
        
        Args:
            elevation_data: Résultats d'analyse d'élévation
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        if elevation_data["mean"] is None:
            return ["Données d'élévation non disponibles. Visite terrain recommandée."]
        
        mean_elevation = elevation_data["mean"]
        zone = self.get_elevation_zone(mean_elevation)
        
        # Recommandations basées sur la zone d'altitude
        if zone == "plaine":
            recommendations.append(
                f"Zone de plaine ({mean_elevation:.0f}m): convient à la majorité des essences forestières commerciales. "
                "Privilégier chênes, frênes, pins maritimes si le sol le permet."
            )
        elif zone == "collinéenne":
            recommendations.append(
                f"Zone collinéenne ({mean_elevation:.0f}m): bien adaptée pour la sylviculture productive. "
                "Chênes, hêtres, douglas, sapins sont recommandés."
            )
        elif zone == "montagnarde":
            recommendations.append(
                f"Zone montagnarde ({mean_elevation:.0f}m): conditions plus rudes, choisir des essences adaptées. "
                "Épicéas, sapins, mélèzes seront plus performants à cette altitude."
            )
        elif zone == "subalpine":
            recommendations.append(
                f"Zone subalpine ({mean_elevation:.0f}m): altitude élevée, saison de végétation courte. "
                "Les pins cembro, pins à crochets et mélèzes sont naturellement adaptés."
            )
        elif zone == "alpine":
            recommendations.append(
                f"Zone alpine ({mean_elevation:.0f}m): très haute altitude peu propice à la sylviculture commerciale. "
                "Rôle de protection et environnemental à privilégier."
            )
        
        # Variabilité du terrain
        if elevation_data["std"] is not None and elevation_data["std"] > 20:
            recommendations.append(
                f"Forte variabilité d'altitude (écart-type: {elevation_data['std']:.0f}m). "
                "Envisager une gestion par îlots homogènes adaptés aux différentes conditions."
            )
        
        # Amplitude max-min
        if elevation_data["min"] is not None and elevation_data["max"] is not None:
            amplitude = elevation_data["max"] - elevation_data["min"]
            if amplitude > 50:
                recommendations.append(
                    f"Grande amplitude altitudinale ({amplitude:.0f}m). "
                    "Vérifier l'accessibilité des zones les plus hautes et les plus basses."
                )
        
        return recommendations
