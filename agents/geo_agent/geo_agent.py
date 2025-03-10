#!/usr/bin/env python3
"""
Agent de géotraitement (GeoAgent) pour l'identification et l'analyse
de parcelles forestières potentielles.
"""

import os
import logging
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, box
import matplotlib.pyplot as plt
import contextily as ctx

from forestai.agents.base_agent import BaseAgent
from forestai.utils.geo_utils.local_data import LocalDataManager

logger = logging.getLogger(__name__)

class GeoAgent(BaseAgent):
    """
    Agent responsable de l'analyse géospatiale des parcelles et propriétés forestières.
    Utilise des données téléchargées localement au lieu des API Géoservices suite à
    l'arrêt de la génération de clés en 2024.
    """
    
    def __init__(self, config):
        """
        Initialise l'agent de géotraitement.
        
        Args:
            config (dict): Configuration de l'agent
        """
        super().__init__(config)
        
        # Initialiser le gestionnaire de données locales
        self.data_manager = LocalDataManager(
            data_path=os.path.join(config.get("data_path", "./data")),
            cache_path=os.path.join(config.get("data_path", "./data"), "cache")
        )
        
        # Initialiser l'état interne
        self.current_commune = None
        self.current_section = None
        self.current_parcels = None
        self.current_analysis = None
        
        logger.info("GeoAgent initialisé")
    
    def run(self):
        """Exécute l'agent de géotraitement avec les paramètres par défaut"""
        logger.info("Démarrage de l'agent de géotraitement")
        # Dans une implémentation complète, cette méthode pourrait lancer 
        # un processus de découverte automatique des parcelles à potentiel forestier
        return {"status": "success", "message": "Agent de géotraitement démarré"}
    
    def search_parcels(self, commune, section=None, criteria=None):
        """
        Recherche des parcelles selon les critères spécifiés.
        
        Args:
            commune (str): Code INSEE de la commune
            section (str, optional): Section cadastrale
            criteria (dict, optional): Critères de filtrage des parcelles
            
        Returns:
            dict: Résultat de la recherche contenant les parcelles trouvées
        """
        logger.info(f"Recherche de parcelles dans la commune {commune}, section {section}")
        
        # Charger les données cadastrales
        parcels = self.data_manager.load_cadastre(commune_code=commune, section=section)
        
        if parcels is None:
            return {"status": "error", "message": f"Aucune donnée cadastrale trouvée pour {commune}"}
        
        # Appliquer les critères de filtrage si spécifiés
        if criteria:
            if "min_area" in criteria:
                parcels = parcels[parcels.geometry.area >= criteria["min_area"]]
            
            if "max_area" in criteria:
                parcels = parcels[parcels.geometry.area <= criteria["max_area"]]
            
            # Autres critères possibles: type de propriété, proximité d'une route, etc.
        
        # Mise à jour de l'état interne
        self.current_commune = commune
        self.current_section = section
        self.current_parcels = parcels
        
        # Retourner le résultat
        result = {
            "status": "success",
            "count": len(parcels),
            "parcels": parcels.to_dict("records") if len(parcels) < 100 else f"{len(parcels)} parcelles trouvées"
        }
        
        logger.info(f"Recherche terminée: {len(parcels)} parcelles trouvées")
        return result
    
    def analyze_forest_potential(self, parcels=None, criteria=None):
        """
        Analyse le potentiel forestier des parcelles spécifiées.
        
        Args:
            parcels (list, optional): Liste d'identifiants de parcelles à analyser
            criteria (dict, optional): Critères d'analyse
            
        Returns:
            dict: Résultat de l'analyse
        """
        # Si aucune parcelle n'est spécifiée, utiliser les parcelles actuelles
        if parcels is None:
            if self.current_parcels is None:
                return {"status": "error", "message": "Aucune parcelle sélectionnée"}
            parcels_to_analyze = self.current_parcels
        else:
            # Filtrer les parcelles actuelles par identifiant
            if self.current_parcels is None:
                return {"status": "error", "message": "Aucune parcelle chargée, utilisez search_parcels d'abord"}
            
            parcels_to_analyze = self.current_parcels[self.current_parcels["id"].isin(parcels)]
            
            if len(parcels_to_analyze) == 0:
                return {"status": "error", "message": "Aucune parcelle trouvée avec les identifiants fournis"}
        
        logger.info(f"Analyse du potentiel forestier pour {len(parcels_to_analyze)} parcelles")
        
        # Initialiser les résultats d'analyse
        analysis_results = []
        
        # Pour chaque parcelle, effectuer l'analyse
        for _, parcel in parcels_to_analyze.iterrows():
            # Obtenir la géométrie et la bbox de la parcelle
            geom = parcel.geometry
            bbox = geom.bounds  # (minx, miny, maxx, maxy)
            
            # Charger les données d'élévation pour la parcelle
            elevation_data = self.data_manager.load_elevation(bbox)
            
            # Charger les données d'occupation du sol
            landcover_data = self.data_manager.load_landcover(bbox)
            
            # Analyser la pente (à partir des données d'élévation)
            slope = self._calculate_slope(elevation_data, geom) if elevation_data else None
            
            # Analyser l'exposition (à partir des données d'élévation)
            aspect = self._calculate_aspect(elevation_data, geom) if elevation_data else None
            
            # Déterminer l'occupation du sol actuelle
            current_landcover = self._determine_landcover(landcover_data, geom) if landcover_data else None
            
            # Calculer le score de potentiel forestier
            forest_potential_score = self._calculate_forest_potential(
                slope=slope,
                aspect=aspect,
                landcover=current_landcover,
                parcel_area=geom.area,
                criteria=criteria
            )
            
            # Ajouter les résultats à la liste
            analysis_results.append({
                "parcel_id": parcel.get("id", ""),
                "area_ha": geom.area / 10000,  # Conversion en hectares
                "slope_avg": None if slope is None else slope.get("average"),
                "slope_max": None if slope is None else slope.get("max"),
                "aspect": None if aspect is None else aspect.get("dominant"),
                "current_landcover": current_landcover,
                "forest_potential_score": forest_potential_score,
                "recommendation": self._get_recommendation(forest_potential_score)
            })
        
        # Mettre à jour l'état interne
        self.current_analysis = analysis_results
        
        # Retourner les résultats
        return {
            "status": "success",
            "count": len(analysis_results),
            "results": analysis_results
        }
    
    def generate_map(self, output_file=None, show_analysis=True):
        """
        Génère une carte des parcelles analysées.
        
        Args:
            output_file (str, optional): Chemin du fichier de sortie
            show_analysis (bool): Afficher les résultats d'analyse sur la carte
            
        Returns:
            dict: Informations sur la carte générée
        """
        if self.current_parcels is None:
            return {"status": "error", "message": "Aucune parcelle à afficher"}
        
        # Créer une copie du GeoDataFrame pour la visualisation
        gdf_viz = self.current_parcels.copy()
        
        # Si l'analyse est disponible et show_analysis est True, ajouter les résultats à la visualisation
        if show_analysis and self.current_analysis:
            # Créer un DataFrame à partir des résultats d'analyse
            analysis_df = pd.DataFrame(self.current_analysis)
            
            # Joindre les résultats d'analyse au GeoDataFrame
            # (en supposant que l'identifiant de parcelle est dans la colonne 'id')
            gdf_viz = gdf_viz.merge(analysis_df, left_on="id", right_on="parcel_id", how="left")
            
            # Utiliser le score de potentiel forestier comme couleur
            cmap = plt.cm.RdYlGn  # Rouge (faible) à Vert (élevé)
            gdf_viz["color"] = gdf_viz["forest_potential_score"].apply(
                lambda x: cmap(x/100) if x is not None else (0.7, 0.7, 0.7, 1.0)
            )
        else:
            # Couleur uniforme si pas d'analyse
            gdf_viz["color"] = (0.5, 0.5, 0.8, 0.7)  # Bleu semi-transparent
        
        # Créer la figure et l'axe
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Tracer les parcelles
        gdf_viz.plot(ax=ax, color=gdf_viz["color"], edgecolor="black", linewidth=0.5)
        
        # Ajouter un fond de carte (OpenStreetMap par défaut)
        try:
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        except Exception as e:
            logger.warning(f"Impossible d'ajouter le fond de carte: {e}")
        
        # Ajouter un titre et une légende
        commune_name = self.current_commune or "Commune inconnue"
        section_text = f" - Section {self.current_section}" if self.current_section else ""
        ax.set_title(f"Parcelles - {commune_name}{section_text}")
        
        # Ajouter une légende si l'analyse est affichée
        if show_analysis and self.current_analysis:
            # Créer une légende pour le potentiel forestier
            import matplotlib.patches as mpatches
            legend_items = [
                mpatches.Patch(color=cmap(0.2), label="Faible potentiel"),
                mpatches.Patch(color=cmap(0.5), label="Potentiel moyen"),
                mpatches.Patch(color=cmap(0.8), label="Fort potentiel")
            ]
            ax.legend(handles=legend_items, loc="lower right")
        
        # Enregistrer la carte si un fichier de sortie est spécifié
        output_path = None
        if output_file:
            output_path = os.path.join(self.config.get("output_path", "./data/outputs"), output_file)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            logger.info(f"Carte enregistrée: {output_path}")
        else:
            plt.close(fig)
        
        return {
            "status": "success",
            "file_path": output_path,
            "parcels_count": len(gdf_viz)
        }
    
    def export_results(self, output_format="geojson", output_file=None):
        """
        Exporte les résultats d'analyse dans différents formats.
        
        Args:
            output_format (str): Format d'export (geojson, shp, csv)
            output_file (str, optional): Nom du fichier de sortie
            
        Returns:
            dict: Informations sur le fichier exporté
        """
        if self.current_parcels is None:
            return {"status": "error", "message": "Aucune parcelle à exporter"}
        
        # Créer un GeoDataFrame combiné avec les résultats d'analyse
        gdf_export = self.current_parcels.copy()
        
        # Si l'analyse est disponible, joindre les résultats
        if self.current_analysis:
            analysis_df = pd.DataFrame(self.current_analysis)
            gdf_export = gdf_export.merge(analysis_df, left_on="id", right_on="parcel_id", how="left")
        
        # Déterminer le nom du fichier
        if output_file is None:
            commune = self.current_commune or "commune"
            section = self.current_section or "section"
            output_file = f"parcelles_{commune}_{section}.{output_format}"
        
        # Chemin complet du fichier
        output_path = os.path.join(self.config.get("output_path", "./data/outputs"), output_file)
        
        # Exporter selon le format demandé
        try:
            if output_format == "geojson":
                gdf_export.to_file(output_path, driver="GeoJSON")
            elif output_format == "shp":
                gdf_export.to_file(output_path)
            elif output_format == "csv":
                # Pour CSV, on doit convertir la géométrie en texte WKT
                gdf_export["geometry_wkt"] = gdf_export.geometry.apply(lambda g: g.wkt)
                gdf_export_csv = pd.DataFrame(gdf_export.drop(columns=["geometry"]))
                gdf_export_csv.to_csv(output_path, index=False)
            else:
                return {"status": "error", "message": f"Format non supporté: {output_format}"}
            
            logger.info(f"Résultats exportés: {output_path}")
            return {
                "status": "success",
                "file_path": output_path,
                "format": output_format,
                "records_count": len(gdf_export)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            return {"status": "error", "message": str(e)}
    
    # Méthodes privées pour les calculs
    
    def _calculate_slope(self, elevation_data, geometry):
        """Calcule la pente à partir des données d'élévation pour une géométrie"""
        # Exemple simplifié - à remplacer par un calcul réel de pente
        if elevation_data is None:
            return None
        
        # Simuler un calcul de pente
        return {
            "average": 5.0,  # Pente moyenne en degrés
            "max": 12.0,     # Pente maximale en degrés
            "min": 1.0,      # Pente minimale en degrés
            "std": 2.5       # Écart-type des pentes
        }
    
    def _calculate_aspect(self, elevation_data, geometry):
        """Calcule l'exposition (aspect) à partir des données d'élévation pour une géométrie"""
        # Exemple simplifié - à remplacer par un calcul réel d'exposition
        if elevation_data is None:
            return None
        
        # Simuler des calculs d'exposition
        # 0/360° = Nord, 90° = Est, 180° = Sud, 270° = Ouest
        aspects = {
            "N": 0.15,   # Proportion orientée Nord
            "NE": 0.10,  # Proportion orientée Nord-Est
            "E": 0.20,   # Proportion orientée Est
            "SE": 0.25,  # Proportion orientée Sud-Est
            "S": 0.15,   # Proportion orientée Sud
            "SW": 0.05,  # Proportion orientée Sud-Ouest
            "W": 0.05,   # Proportion orientée Ouest
            "NW": 0.05   # Proportion orientée Nord-Ouest
        }
        
        # Déterminer l'orientation dominante
        dominant = max(aspects.items(), key=lambda x: x[1])[0]
        
        return {
            "aspects": aspects,
            "dominant": dominant,
            "average_degrees": 135.0  # Moyenne en degrés (exemple: 135° = Sud-Est)
        }
    
    def _determine_landcover(self, landcover_data, geometry):
        """Détermine l'occupation du sol actuelle pour une géométrie"""
        # Exemple simplifié - à remplacer par une analyse réelle
        if landcover_data is None:
            return "unknown"
        
        # Simuler une détermination d'occupation du sol
        # Par exemple, en choisissant aléatoirement parmi des types courants
        landcover_types = [
            "agricultural",
            "grassland",
            "shrubland",
            "mixed_forest",
            "deciduous_forest",
            "coniferous_forest",
            "urban",
            "water"
        ]
        
        # En pratique, on déterminerait le type réel en croisant la géométrie avec les données d'occupation du sol
        # Pour cet exemple, on renvoie une valeur fixe
        return "grassland"
    
    def _calculate_forest_potential(self, slope=None, aspect=None, landcover=None, parcel_area=None, criteria=None):
        """
        Calcule un score de potentiel forestier basé sur différents facteurs.
        
        Le score est compris entre 0 (très faible potentiel) et 100 (excellent potentiel).
        """
        # Score de base
        base_score = 50
        
        # Ajustements en fonction de la pente
        if slope:
            avg_slope = slope.get("average", 0)
            # Pénaliser les pentes trop fortes (>20°) ou trop faibles (<2°)
            if avg_slope > 20:
                base_score -= min(40, (avg_slope - 20) * 2)  # -2 points par degré au-dessus de 20°
            elif avg_slope < 2:
                base_score -= min(10, (2 - avg_slope) * 5)   # -5 points par degré en dessous de 2°
            else:
                # Bonus pour les pentes idéales (entre 5° et 15°)
                if 5 <= avg_slope <= 15:
                    base_score += 10
        
        # Ajustements en fonction de l'exposition
        if aspect:
            dominant = aspect.get("dominant", "")
            # Bonus pour exposition sud, sud-est (meilleure croissance)
            if dominant in ["S", "SE"]:
                base_score += 15
            elif dominant in ["SW", "E"]:
                base_score += 10
            elif dominant in ["NE", "W"]:
                base_score += 5
            # Pas de bonus pour exposition nord et nord-ouest
        
        # Ajustements en fonction de l'occupation du sol
        if landcover:
            # Bonus pour les terrains faciles à convertir en forêt
            if landcover in ["grassland", "shrubland", "agricultural"]:
                base_score += 15
            # Bonus pour les terrains déjà forestiers
            elif "forest" in landcover:
                base_score += 20
            # Pénalité pour les terrains difficiles à convertir
            elif landcover in ["urban", "water"]:
                base_score -= 30
        
        # Ajustements en fonction de la surface
        if parcel_area:
            # Conversion en hectares
            area_ha = parcel_area / 10000
            
            # Bonus pour les grandes parcelles (économies d'échelle)
            if area_ha >= 10:
                base_score += 10
            elif area_ha >= 5:
                base_score += 5
            elif area_ha >= 2:
                base_score += 2
            # Pénalité pour les très petites parcelles
            elif area_ha < 0.5:
                base_score -= 10
        
        # Appliquer des critères spécifiques si fournis
        if criteria:
            # Exemples de critères personnalisés
            if "preferred_landcover" in criteria and landcover == criteria["preferred_landcover"]:
                base_score += 10
            
            if "preferred_aspect" in criteria and aspect and criteria["preferred_aspect"] == aspect.get("dominant"):
                base_score += 10
            
            if "min_area_ha" in criteria and parcel_area:
                area_ha = parcel_area / 10000
                if area_ha < criteria["min_area_ha"]:
                    base_score -= 20
        
        # Limiter le score entre 0 et 100
        final_score = max(0, min(100, base_score))
        
        return final_score
    
    def _get_recommendation(self, forest_potential_score):
        """Génère une recommandation basée sur le score de potentiel forestier"""
        if forest_potential_score >= 80:
            return "Excellent potentiel forestier. Parcelle prioritaire pour reboisement."
        elif forest_potential_score >= 60:
            return "Bon potentiel forestier. Parcelle à considérer pour reboisement."
        elif forest_potential_score >= 40:
            return "Potentiel forestier moyen. Nécessite étude de terrain approfondie."
        elif forest_potential_score >= 20:
            return "Potentiel forestier faible. Considérer d'autres usages."
        else:
            return "Potentiel forestier très faible. Non recommandé pour reboisement."