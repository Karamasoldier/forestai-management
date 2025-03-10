# forestai/agents/geo_agent/geo_agent.py

import os
import logging
from typing import List, Dict, Any, Tuple
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import requests
from anthropic import Anthropic

from ...core.utils.geo_utils import reproject_geometry
from ..base_agent import BaseAgent
from .cadastre import get_cadastre_data
from .parcel_analyzer import analyze_parcel_potential

class GeoAgent(BaseAgent):
    """
    Agent chargé des analyses géospatiales des parcelles forestières.
    
    Fonctionnalités:
    - Identification des parcelles à potentiel forestier
    - Analyse de regroupement de petites parcelles
    - Extraction de contacts des propriétaires via les mairies
    - Génération de cartes et rapports
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="GeoAgent", config=config)
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.logger = logging.getLogger(__name__)
        
        # Initialiser les connexions aux API géospatiales
        self.cadastre_api_key = os.environ.get("CADASTRE_API_KEY")
        self.ign_api_key = os.environ.get("IGN_API_KEY")
        
        # Charger les couches de référence
        self.load_reference_layers()
        
    def load_reference_layers(self):
        """Charge les couches de référence nécessaires aux analyses."""
        try:
            # Couche des limites administratives
            admin_boundaries_path = os.path.join(self.config["data_path"], "raw", "admin_boundaries.gpkg")
            if os.path.exists(admin_boundaries_path):
                self.admin_boundaries = gpd.read_file(admin_boundaries_path)
            else:
                self.admin_boundaries = gpd.GeoDataFrame()
                self.logger.warning("Fichier des limites administratives non trouvé")
            
            # Couche des zones forestières existantes
            forest_areas_path = os.path.join(self.config["data_path"], "raw", "forest_areas.gpkg")
            if os.path.exists(forest_areas_path):
                self.forest_areas = gpd.read_file(forest_areas_path)
            else:
                self.forest_areas = gpd.GeoDataFrame()
                self.logger.warning("Fichier des zones forestières non trouvé")
            
            # Couche des types de sols
            soil_types_path = os.path.join(self.config["data_path"], "raw", "soil_types.gpkg")
            if os.path.exists(soil_types_path):
                self.soil_types = gpd.read_file(soil_types_path)
            else:
                self.soil_types = gpd.GeoDataFrame()
                self.logger.warning("Fichier des types de sols non trouvé")
            
            self.logger.info("Chargement des couches de référence terminé")
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des couches de référence: {e}")
            # Créer des GeoDataFrames vides en cas d'échec
            self.admin_boundaries = gpd.GeoDataFrame()
            self.forest_areas = gpd.GeoDataFrame()
            self.soil_types = gpd.GeoDataFrame()
    
    def _execute(self):
        """Implémentation de la méthode d'exécution de l'agent."""
        self.logger.info("Exécution de l'agent GeoAgent")
        
        # Traiter les tâches en attente
        while self.is_running and self.tasks_queue:
            task = self.tasks_queue.pop(0)
            
            try:
                task_type = task.get("type")
                
                if task_type == "find_parcels":
                    department = task.get("department")
                    min_area = task.get("min_area", 1.0)
                    max_slope = task.get("max_slope", 30.0)
                    
                    self.logger.info(f"Recherche de parcelles dans le département {department}")
                    parcels = self.find_profitable_parcels(department, min_area, max_slope)
                    
                    # Enregistrer les résultats
                    output_path = os.path.join(
                        self.config["output_path"], 
                        f"parcels_{department}.geojson"
                    )
                    if not parcels.empty:
                        parcels.to_file(output_path, driver="GeoJSON")
                        self.logger.info(f"Résultats enregistrés dans {output_path}")
                
                elif task_type == "analyze_clustering":
                    geojson_path = task.get("geojson_path")
                    max_distance = task.get("max_distance", 100.0)
                    
                    if geojson_path and os.path.exists(geojson_path):
                        parcels = gpd.read_file(geojson_path)
                        clusters = self.analyze_small_parcels_clustering(
                            parcels, max_distance
                        )
                        
                        # Enregistrer les résultats
                        output_path = os.path.join(
                            self.config["output_path"], 
                            f"clusters_{os.path.basename(geojson_path)}"
                        )
                        if clusters.get("clusters"):
                            gpd.GeoDataFrame(clusters["clusters"]).to_file(
                                output_path, driver="GeoJSON"
                            )
                            self.logger.info(f"Clusters enregistrés dans {output_path}")
                
                elif task_type == "get_contacts":
                    department = task.get("department")
                    parcel_ids = task.get("parcel_ids")
                    
                    contacts = self.get_municipality_contacts(department, parcel_ids)
                    
                    # Enregistrer les résultats
                    output_path = os.path.join(
                        self.config["output_path"], 
                        f"contacts_{department}.csv"
                    )
                    
                    if contacts:
                        pd.DataFrame.from_dict(contacts, orient="index").to_csv(output_path)
                        self.logger.info(f"Contacts enregistrés dans {output_path}")
                
                else:
                    self.logger.warning(f"Type de tâche inconnu: {task_type}")
            
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de la tâche: {e}", exc_info=True)
    
    def find_profitable_parcels(self, 
                               department_code: str, 
                               min_area: float = 1.0,
                               max_slope: float = 30.0) -> gpd.GeoDataFrame:
        """
        Identifie les parcelles à potentiel forestier dans un département.
        
        Args:
            department_code: Code du département (ex: "01", "2A")
            min_area: Surface minimale en hectares
            max_slope: Pente maximale en degrés
            
        Returns:
            GeoDataFrame avec les parcelles identifiées et leurs attributs
        """
        self.logger.info(f"Recherche de parcelles dans le département {department_code}")
        
        try:
            # Simulation: dans une implémentation réelle, cette fonction appellerait 
            # l'API cadastrale et effectuerait des analyses spatiales complexes
            self.logger.info("Simulation: Appel à l'API cadastrale")
            
            # Exemple de données retournées
            # En production, ceci appelerait get_cadastre_data() pour obtenir les vraies données
            example_data = {
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": f"{department_code}0001",
                            "nature": "AB",  # Non forestier
                            "area_ha": 2.5,
                            "owner_id": "OWNER1",
                            "commune_code": f"{department_code}001"
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                        }
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "id": f"{department_code}0002",
                            "nature": "AB",  # Non forestier
                            "area_ha": 3.8,
                            "owner_id": "OWNER2",
                            "commune_code": f"{department_code}001"
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[1, 0], [1, 1], [2, 1], [2, 0], [1, 0]]]
                        }
                    }
                ]
            }
            
            # Créer un GeoDataFrame à partir des données d'exemple
            gdf = gpd.GeoDataFrame.from_features(example_data["features"])
            gdf["forestry_potential"] = [0.75, 0.82]  # Simulation de l'analyse
            gdf["department"] = department_code
            
            return gdf
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de parcelles: {e}")
            return gpd.GeoDataFrame()
    
    def analyze_small_parcels_clustering(self, 
                                        parcels_gdf: gpd.GeoDataFrame,
                                        max_distance: float = 100.0,
                                        min_cluster_size: int = 3) -> Dict[str, Any]:
        """
        Analyse les possibilités de regroupement de petites parcelles.
        
        Args:
            parcels_gdf: GeoDataFrame des parcelles à analyser
            max_distance: Distance maximale entre parcelles pour regroupement (m)
            min_cluster_size: Nombre minimum de parcelles pour former un groupe
            
        Returns:
            Dictionnaire avec clusters identifiés et métriques
        """
        self.logger.info("Analyse de regroupement de parcelles")
        
        # Simulation: en production, cette fonction effectuerait une analyse spatiale réelle
        
        # Exemple de résultat
        clusters = [
            {
                "id": 1,
                "parcels": [0, 1],
                "area_ha": 6.3,
                "owner_count": 2,
                "geometry": parcels_gdf.unary_union,
                "analysis": "Ce groupe de parcelles présente un bon potentiel de regroupement forestier."
            }
        ]
        
        return {
            "clusters": clusters,
            "metrics": {
                "cluster_count": len(clusters),
                "total_parcels": 2,
                "total_area_ha": 6.3
            }
        }
        
    def get_municipality_contacts(self, 
                                 department_code: str,
                                 parcel_ids: List[str] = None) -> Dict[str, Dict]:
        """
        Récupère les contacts des mairies pour les parcelles spécifiées.
        
        Args:
            department_code: Code du département
            parcel_ids: Liste d'identifiants de parcelles (optionnel)
            
        Returns:
            Dictionnaire des contacts par commune
        """
        self.logger.info(f"Récupération des contacts mairies pour département {department_code}")
        
        # Simulation: en production, cette fonction appellerait une API réelle
        
        # Exemple de résultat
        return {
            f"{department_code}001": {
                "nom": "Commune Test",
                "adresse": "1 Place de la Mairie, 01000 Commune Test",
                "telephone": "04 00 00 00 00",
                "email": "mairie@commune-test.fr",
                "site_web": "http://www.commune-test.fr",
                "horaires": "Lundi-Vendredi: 9h-12h, 14h-17h"
            }
        }
    
    def generate_report(self, 
                       parcels_gdf: gpd.GeoDataFrame,
                       clusters_data: Dict[str, Any] = None,
                       municipality_contacts: Dict[str, Dict] = None) -> Dict[str, Any]:
        """
        Génère un rapport complet d'analyse des parcelles.
        
        Args:
            parcels_gdf: GeoDataFrame des parcelles analysées
            clusters_data: Données de clustering (optionnel)
            municipality_contacts: Contacts des mairies (optionnel)
            
        Returns:
            Dictionnaire contenant les données du rapport et chemins des fichiers générés
        """
        self.logger.info("Génération du rapport d'analyse")
        
        # Préparer le contexte pour le rapport
        context = {
            "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "parcels_count": len(parcels_gdf),
            "total_area": parcels_gdf["area_ha"].sum() if "area_ha" in parcels_gdf.columns else 0,
            "department": parcels_gdf["department"].iloc[0] if "department" in parcels_gdf.columns else "N/A",
            "profitable_parcels": parcels_gdf,
            "clusters_data": clusters_data,
            "municipality_contacts": municipality_contacts,
        }
        
        # Simulation: en production, cette fonction générerait une carte et une analyse complète
        
        # Exemple de résultat
        context["map_path"] = None
        context["geojson_path"] = None
        context["analysis"] = """
        Analyse des parcelles à potentiel forestier dans le département XX. 
        Ce rapport identifie plusieurs opportunités d'investissement forestier...
        """
        
        return context
