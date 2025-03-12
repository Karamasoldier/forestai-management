# forestai/core/domain/services/terrain_services/hydrology_service.py

import os
import time
import geopandas as gpd
from typing import Dict, Any, Optional, List
import pyproj
from shapely.ops import transform
from pathlib import Path

from forestai.core.domain.models.parcel import Parcel
from forestai.core.domain.services.terrain_services.base_terrain_service import BaseTerrainService
from forestai.core.utils.logging_config import log_function

class HydrologyService(BaseTerrainService):
    """
    Service spécialisé pour l'analyse hydrologique des parcelles.
    Analyse la proximité et l'interaction avec les points d'eau.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialise le service d'analyse hydrologique.
        
        Args:
            data_dir: Répertoire contenant les données géographiques
        """
        super().__init__(data_dir, "HydrologyService")
        
        # Trouver le fichier d'hydrographie
        self.hydro_path = self._find_hydro_file()
    
    def _find_hydro_file(self) -> Optional[Path]:
        """Trouve le fichier d'hydrographie dans le répertoire des données."""
        potential_paths = list(self.data_dir.glob("**/*hydro*.shp")) + \
                          list(self.data_dir.glob("**/*water*.shp")) + \
                          list(self.data_dir.glob("**/bdtopo*hydro*.shp"))
        
        if not potential_paths:
            self.logger.warning(f"Aucun fichier d'hydrographie trouvé dans {self.data_dir}")
            return None
        
        self.logger.info(f"Fichier d'hydrographie trouvé: {potential_paths[0]}")
        return potential_paths[0]
    
    @log_function(level="DEBUG")
    def analyze_hydrology(self, parcel: Parcel) -> Dict[str, Any]:
        """
        Analyse la proximité et l'interaction avec les points d'eau.
        
        Args:
            parcel: Objet Parcel à analyser
            
        Returns:
            Informations sur l'hydrologie de la parcelle
        """
        # Standardiser la parcelle (conversion Lambert 93)
        parcel = self.get_standardized_parcel(parcel)
        
        # Vérifier si le fichier d'hydrographie est disponible
        if not self.hydro_path or not self.hydro_path.exists():
            self.logger.warning("Données d'hydrographie non disponibles")
            return {
                "water_present": False,
                "distance_to_water": None,
                "water_features": []
            }
        
        try:
            # Lire les données hydrographiques
            hydro_data = gpd.read_file(self.hydro_path)
            
            # Vérifier si le système de coordonnées est le même
            if hydro_data.crs != parcel.crs:
                # Reprojeter la parcelle ou les données hydro si nécessaire
                parcel_geometry = parcel.geometry
                if not parcel.crs:
                    # Si la parcelle n'a pas de CRS défini, on la reprojette vers celui des données hydro
                    project = pyproj.Transformer.from_crs(
                        "EPSG:4326",  # WGS84 par défaut
                        hydro_data.crs,
                        always_xy=True
                    ).transform
                    parcel_geometry = transform(project, parcel_geometry)
                else:
                    # Sinon, on reprojette les données hydro vers le CRS de la parcelle
                    hydro_data = hydro_data.to_crs(parcel.crs)
            
            # Tampon autour de la parcelle pour trouver les points d'eau proches
            buffer_distance = 500  # mètres
            buffered_parcel = parcel.geometry.buffer(buffer_distance)
            
            # Filtrer les entités d'eau proches ou intersectant la parcelle
            nearby_water = hydro_data[hydro_data.intersects(buffered_parcel)]
            intersecting_water = hydro_data[hydro_data.intersects(parcel.geometry)]
            
            water_present = not intersecting_water.empty
            
            # Liste des entités d'eau
            water_features = []
            
            if not nearby_water.empty:
                for idx, water in nearby_water.iterrows():
                    water_type = water.get('type', water.get('nature', 'inconnu'))
                    water_name = water.get('nom', water.get('name', 'sans nom'))
                    
                    # Calculer la distance à la parcelle
                    if water.geometry.intersects(parcel.geometry):
                        distance = 0
                        relation = "traverse"
                    else:
                        distance = water.geometry.distance(parcel.geometry)
                        if distance <= buffer_distance / 5:  # Très proche
                            relation = "adjacent"
                        else:
                            relation = "proche"
                    
                    water_features.append({
                        "type": water_type,
                        "name": water_name,
                        "distance": float(distance),
                        "relation": relation
                    })
                
                # Trier par distance
                water_features.sort(key=lambda x: x["distance"])
                
                # Distance au point d'eau le plus proche
                min_distance = water_features[0]["distance"] if water_features else None
            else:
                min_distance = None
        
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'analyse hydrologique pour la parcelle {parcel.id}: {str(e)}")
            return {
                "water_present": False,
                "distance_to_water": None,
                "water_features": [],
                "error": str(e)
            }
        
        return {
            "water_present": water_present,
            "distance_to_water": min_distance,
            "water_features": water_features
        }
    
    @log_function(level="INFO")
    def get_hydrology_constraints(self, hydro_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifie les contraintes liées à l'hydrologie.
        
        Args:
            hydro_data: Résultats d'analyse hydrologique
            
        Returns:
            Liste des contraintes liées à l'hydrologie
        """
        constraints = []
        
        if not hydro_data:
            return []
        
        water_present = hydro_data.get("water_present", False)
        water_features = hydro_data.get("water_features", [])
        
        if water_present:
            constraints.append({
                "type": "eau_presente",
                "severity": "modérée",
                "description": "Présence d'eau sur la parcelle",
                "impact": "Zones humides nécessitant des essences adaptées, restrictions réglementaires possibles"
            })
        
        # Zones ripariennes (proche des cours d'eau)
        for feature in water_features:
            if feature.get('distance', float('inf')) < 10 and feature.get('type') in ['rivière', 'ruisseau', 'cours_eau']:
                constraints.append({
                    "type": "zone_riparienne",
                    "severity": "importante",
                    "description": f"Zone riparienne le long de {feature.get('name', 'cours d\'eau')}",
                    "impact": "Nécessité de maintenir une zone tampon non exploitée, réglementation spécifique"
                })
            
            # Zones humides
            if feature.get('type') in ['marais', 'étang', 'zone_humide'] and feature.get('distance', float('inf')) < 50:
                constraints.append({
                    "type": "zone_humide",
                    "severity": "importante",
                    "description": f"Proximité de zone humide ({feature.get('name', 'zone humide')})",
                    "impact": "Protection réglementaire, restrictions sur le drainage et l'exploitation"
                })
        
        return constraints
    
    @log_function(level="INFO")
    def get_hydrology_recommendations(self, hydro_data: Dict[str, Any]) -> List[str]:
        """
        Génère des recommandations basées sur l'hydrologie.
        
        Args:
            hydro_data: Résultats d'analyse hydrologique
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        if not hydro_data:
            return ["Données hydrologiques non disponibles. Vérifier la présence d'eau sur le terrain."]
        
        water_present = hydro_data.get("water_present", False)
        min_distance = hydro_data.get("distance_to_water")
        water_features = hydro_data.get("water_features", [])
        
        # Présence d'eau sur la parcelle
        if water_present:
            recommendations.append(
                "Présence d'eau sur la parcelle. Identifier précisément les zones humides et adapter "
                "la gestion forestière (essences adaptées aux milieux humides, protection des berges)."
            )
            
            # Vérifier le type d'eau présent
            water_types = [feature.get("type") for feature in water_features if feature.get("relation") == "traverse"]
            
            if any(t in ['rivière', 'cours_eau', 'ruisseau'] for t in water_types):
                recommendations.append(
                    "Cours d'eau traversant la parcelle: respecter une zone tampon non exploitée d'au moins 5m "
                    "de part et d'autre (ripisylve). Consulter la réglementation locale."
                )
            
            if any(t in ['marais', 'étang', 'zone_humide'] for t in water_types):
                recommendations.append(
                    "Zone humide détectée: zone à haute valeur écologique et réglementée. "
                    "Vérifier le statut exact et les contraintes associées avant tout projet."
                )
        
        # Proximité d'eau
        elif min_distance is not None and min_distance < 100:
            recommendations.append(
                f"Point d'eau à proximité ({min_distance:.0f}m). Prendre en compte les contraintes réglementaires "
                "et adapter les pratiques sylvicoles pour minimiser les impacts sur la qualité de l'eau."
            )
        
        # Recommandations spécifiques selon le type d'eau
        for feature in water_features:
            if feature.get('type') in ['source', 'captage'] and feature.get('distance', float('inf')) < 100:
                recommendations.append(
                    f"Proximité d'une source/captage ({feature.get('distance', '?')}m): restrictions probables "
                    "sur l'utilisation de produits phytosanitaires et la gestion forestière."
                )
        
        # Si aucune eau détectée
        if not water_present and (min_distance is None or min_distance > 500):
            recommendations.append(
                "Aucun point d'eau détecté à proximité immédiate. Évaluer les besoins en eau pour "
                "l'implantation forestière, notamment en période de sécheresse."
            )
        
        return recommendations
    
    @log_function(level="INFO") 
    def has_water_protection_status(self, hydro_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Évalue si la parcelle a un statut de protection lié à l'eau.
        
        Args:
            hydro_data: Résultats d'analyse hydrologique
            
        Returns:
            Informations sur les protections liées à l'eau
        """
        if not hydro_data:
            return {
                "has_protection": None,
                "protection_type": None,
                "details": "Données insuffisantes"
            }
        
        water_features = hydro_data.get("water_features", [])
        protections = []
        
        # Vérifier les facteurs de protection
        for feature in water_features:
            distance = feature.get('distance', float('inf'))
            water_type = feature.get('type', '')
            
            # Cours d'eau traversant la parcelle
            if feature.get('relation') == "traverse" and water_type in ['rivière', 'cours_eau', 'ruisseau']:
                protections.append({
                    "type": "ripisylve",
                    "description": f"Protection des berges du cours d'eau {feature.get('name', '')}",
                    "regulatory": True
                })
            
            # Captage d'eau potable
            if water_type in ['captage', 'eau_potable'] and distance < 200:
                protections.append({
                    "type": "périmètre_captage",
                    "description": f"Périmètre de protection de captage d'eau potable",
                    "regulatory": True
                })
            
            # Zone humide
            if water_type in ['marais', 'étang', 'zone_humide'] and distance < 50:
                protections.append({
                    "type": "zone_humide",
                    "description": f"Protection de zone humide",
                    "regulatory": True
                })
        
        return {
            "has_protection": len(protections) > 0,
            "protection_types": [p["type"] for p in protections],
            "details": protections
        }
