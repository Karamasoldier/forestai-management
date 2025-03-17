#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module de gestion des données satellite pour la télédétection.

Ce module fournit les fonctionnalités pour récupérer, traiter et analyser
les images satellite pour la gestion forestière.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import json
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping, shape
import geopandas as gpd
import pandas as pd

from forestai.core.utils.logging_utils import get_logger
from forestai.core.infrastructure.cache.base import CacheType, CachePolicy
from forestai.core.infrastructure.cache.cache_utils import cached

from forestai.domain.services.remote_sensing.models import (
    RemoteSensingSource, 
    SatelliteImageMetadata,
    RemoteSensingData,
    VegetationIndex
)
from forestai.domain.services.remote_sensing.remote_data_connector import RemoteDataConnector
from forestai.domain.services.remote_sensing.processors.satellite_processor import SatelliteProcessor
from forestai.domain.services.remote_sensing.processors.index_calculator import IndexCalculator

logger = get_logger(__name__)


class SatelliteDataProvider:
    """
    Fournisseur de données satellite pour ForestAI.
    
    Cette classe gère l'acquisition, le stockage et le prétraitement 
    des images satellite pour l'analyse forestière.
    """
    
    def __init__(self, data_dir: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le fournisseur de données satellite.
        
        Args:
            data_dir: Répertoire pour stocker les données téléchargées (par défaut: ./data/satellite)
            config: Configuration supplémentaire
        """
        self.data_dir = data_dir or Path("./data/satellite")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or {}
        self.connector = RemoteDataConnector()
        self.connector.initialize(self.config.get("api_config"))
        
        # Initialiser les processeurs
        self.satellite_processor = SatelliteProcessor()
        self.index_calculator = IndexCalculator()
        
        logger.info(f"SatelliteDataProvider initialisé avec répertoire de données: {self.data_dir}")
    
    @cached(data_type=CacheType.GEODATA, policy=CachePolicy.WEEKLY)
    def search_available_images(self, 
                              geometry: Union[Dict[str, Any], gpd.GeoDataFrame],
                              start_date: datetime, 
                              end_date: datetime,
                              sources: List[RemoteSensingSource] = None,
                              max_cloud_cover: float = 20.0,
                              limit: int = 10,
                              **kwargs) -> List[Dict[str, Any]]:
        """
        Recherche les images satellite disponibles pour une zone géographique.
        
        Args:
            geometry: Géométrie de la zone d'intérêt (GeoJSON ou GeoDataFrame)
            start_date: Date de début de la période de recherche
            end_date: Date de fin de la période de recherche
            sources: Liste des sources à interroger (par défaut: Sentinel-2, Landsat)
            max_cloud_cover: Couverture nuageuse maximale autorisée (%)
            limit: Nombre maximal de résultats à retourner
            **kwargs: Arguments supplémentaires pour la recherche
            
        Returns:
            Liste des métadonnées d'images disponibles
        """
        if sources is None:
            # Par défaut, utiliser Sentinel-2 et Landsat 8/9
            sources = [RemoteSensingSource.SENTINEL_2, RemoteSensingSource.LANDSAT_8, RemoteSensingSource.LANDSAT_9]
        
        # Convertir la géométrie en bbox
        if isinstance(geometry, gpd.GeoDataFrame):
            # Utiliser les limites de la GeoDataFrame
            bounds = geometry.total_bounds  # [minx, miny, maxx, maxy]
            bbox = (bounds[0], bounds[1], bounds[2], bounds[3])
        else:
            # Convertir le GeoJSON en objet shapely puis obtenir les limites
            geom_shape = shape(geometry)
            bbox = geom_shape.bounds  # (minx, miny, maxx, maxy)
        
        all_results = []
        
        # Interroger chaque source configurée
        for source in sources:
            try:
                logger.info(f"Recherche d'images {source.name} du {start_date} au {end_date}")
                
                # Paramètres spécifiques selon la source
                search_params = kwargs.copy()
                
                if source == RemoteSensingSource.SENTINEL_2:
                    search_params.update({
                        "platform": "Sentinel-2",
                        "product_type": "S2MSI2A",  # Niveau 2A (réflectance BOA)
                        "cloud_cover_max": max_cloud_cover
                    })
                elif source in (RemoteSensingSource.LANDSAT_8, RemoteSensingSource.LANDSAT_9):
                    search_params.update({
                        "platform": f"Landsat-{8 if source == RemoteSensingSource.LANDSAT_8 else 9}",
                        "tier": "T1",  # Tier 1 (meilleure qualité)
                        "cloud_cover_max": max_cloud_cover
                    })
                
                # Effectuer la recherche
                results = self.connector.search_data(
                    source=source,
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    **search_params
                )
                
                # Ajouter la source aux résultats pour garder la trace
                for result in results:
                    result["source"] = source.name
                
                all_results.extend(results)
                logger.info(f"Trouvé {len(results)} images {source.name}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la recherche d'images {source.name}: {str(e)}")
        
        # Trier par date d'acquisition (plus récentes en premier) et limiter le nombre
        all_results.sort(key=lambda x: x.get("date", ""), reverse=True)
        return all_results[:limit]
    
    def download_image(self, 
                     product_id: str, 
                     source: RemoteSensingSource,
                     output_dir: Optional[Path] = None,
                     **kwargs) -> Optional[Path]:
        """
        Télécharge une image satellite spécifique.
        
        Args:
            product_id: Identifiant du produit à télécharger
            source: Source des données
            output_dir: Répertoire de sortie (si None, utilise le répertoire par défaut)
            **kwargs: Arguments supplémentaires pour le téléchargement
            
        Returns:
            Chemin vers l'image téléchargée ou None si échec
        """
        output_path = output_dir or self.data_dir / source.name.lower()
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Téléchargement de l'image {product_id} depuis {source.name}")
        
        try:
            # Télécharger via le connecteur
            downloaded_path = self.connector.download_data(
                source=source,
                product_id=product_id,
                output_dir=output_path,
                **kwargs
            )
            
            if downloaded_path and downloaded_path.exists():
                logger.info(f"Image téléchargée avec succès: {downloaded_path}")
                return downloaded_path
            else:
                logger.error(f"Échec du téléchargement de l'image {product_id}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de {product_id}: {str(e)}")
            return None
    
    def process_image(self, 
                    image_path: Path,
                    source: RemoteSensingSource,
                    parcel_geometry: Union[Dict[str, Any], gpd.GeoDataFrame],
                    metadata: Optional[SatelliteImageMetadata] = None,
                    **kwargs) -> Optional[RemoteSensingData]:
        """
        Traite une image satellite pour l'analyse forestière.
        
        Args:
            image_path: Chemin vers l'image à traiter
            source: Source des données
            parcel_geometry: Géométrie de la parcelle à extraire (GeoJSON ou GeoDataFrame)
            metadata: Métadonnées de l'image satellite (optionnel)
            **kwargs: Arguments supplémentaires pour le traitement
            
        Returns:
            Données de télédétection traitées ou None en cas d'échec
        """
        logger.info(f"Traitement de l'image {image_path.name}")
        
        try:
            # Vérifier que le fichier existe
            if not image_path.exists():
                logger.error(f"Fichier introuvable: {image_path}")
                return None
            
            # Préparer les métadonnées si elles ne sont pas fournies
            if metadata is None:
                logger.warning(f"Aucune métadonnée fournie pour {image_path.name}, utilisation de valeurs par défaut")
                # Extraire le nom du produit à partir du nom de fichier
                product_id = image_path.stem
                
                # Créer des métadonnées par défaut
                metadata = SatelliteImageMetadata(
                    source=source,
                    acquisition_date=datetime.now(),  # Date par défaut
                    cloud_cover_percentage=0.0,
                    spatial_resolution=10.0,  # Valeur par défaut pour Sentinel-2
                    bands=[],
                    utm_zone="",
                    epsg_code=4326  # WGS84 par défaut
                )
            
            # Créer l'objet de données
            data = RemoteSensingData(
                parcel_id=f"parcel_{image_path.stem}",
                source=source,
                acquisition_date=metadata.acquisition_date,
                raster_path=image_path,
                satellite_metadata=metadata
            )
            
            # Traiter l'image avec le processeur satellite
            processed_data = self.satellite_processor.process(
                data,
                geometry=parcel_geometry,
                **kwargs
            )
            
            # Calculer les indices de végétation si demandé
            if kwargs.get('calculate_indices', True):
                processed_data = self.index_calculator.calculate_indices(
                    processed_data,
                    indices=kwargs.get('indices', [
                        VegetationIndex.NDVI,
                        VegetationIndex.EVI,
                        VegetationIndex.NDMI
                    ])
                )
            
            logger.info(f"Traitement de {image_path.name} terminé avec succès")
            return processed_data
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de {image_path.name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def analyze_time_series(self,
                           images: List[RemoteSensingData],
                           metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyse une série temporelle d'images satellite.
        
        Args:
            images: Liste d'images satellite traitées (triées chronologiquement)
            metrics: Liste des métriques à analyser (par défaut, tous les indices disponibles)
            
        Returns:
            Résultats de l'analyse (tendances, changements, statistiques)
        """
        if not images:
            logger.error("Aucune image fournie pour l'analyse de série temporelle")
            return {}
        
        if len(images) < 2:
            logger.warning("Au moins 2 images sont nécessaires pour l'analyse de série temporelle")
            return {"warning": "Données insuffisantes pour l'analyse temporelle"}
        
        logger.info(f"Analyse de série temporelle sur {len(images)} images")
        
        # Trier les images par date si nécessaire
        sorted_images = sorted(images, key=lambda x: x.acquisition_date)
        
        # Structure pour stocker les résultats
        results = {
            "time_range": {
                "start": sorted_images[0].acquisition_date,
                "end": sorted_images[-1].acquisition_date,
                "duration_days": (sorted_images[-1].acquisition_date - sorted_images[0].acquisition_date).days
            },
            "metrics": {},
            "changes": {},
            "trends": {}
        }
        
        try:
            # Extraire les métriques disponibles dans toutes les images
            available_metrics = set()
            for img in sorted_images:
                if img.raster_data and isinstance(img.raster_data, dict):
                    for key in img.raster_data.keys():
                        if key != 'original':
                            available_metrics.add(key)
            
            # Filtrer les métriques si demandé
            if metrics:
                target_metrics = [m for m in metrics if m in available_metrics]
            else:
                target_metrics = list(available_metrics)
            
            if not target_metrics:
                logger.warning("Aucune métrique commune trouvée dans les images")
                return {"warning": "Aucune métrique commune disponible"}
            
            # Analyser chaque métrique
            for metric in target_metrics:
                # Collecter les valeurs et dates pour cette métrique
                dates = []
                values = []
                
                for img in sorted_images:
                    if img.raster_data and metric in img.raster_data:
                        # Calculer la moyenne pour l'image entière (pourrait être amélioré pour cibler la région d'intérêt)
                        metric_data = img.raster_data[metric]
                        if metric_data is not None:
                            mean_value = np.nanmean(metric_data)
                            dates.append(img.acquisition_date)
                            values.append(mean_value)
                
                if len(dates) >= 2:
                    # Calculer les changements
                    absolute_change = values[-1] - values[0]
                    percent_change = (absolute_change / values[0]) * 100 if values[0] != 0 else 0
                    
                    # Calculer les tendances (régression linéaire)
                    try:
                        import pandas as pd
                        from scipy import stats
                        
                        # Convertir les dates en nombres (jours depuis la première date)
                        days = [(d - dates[0]).days for d in dates]
                        
                        # Effectuer la régression
                        slope, intercept, r_value, p_value, std_err = stats.linregress(days, values)
                        
                        # Stocker les résultats
                        results["metrics"][metric] = {
                            "values": values,
                            "dates": dates
                        }
                        
                        results["changes"][metric] = {
                            "absolute": absolute_change,
                            "percent": percent_change
                        }
                        
                        results["trends"][metric] = {
                            "slope": slope,  # Changement par jour
                            "annual_rate": slope * 365,  # Changement par an
                            "r_squared": r_value ** 2,
                            "p_value": p_value,
                            "standard_error": std_err
                        }
                    except Exception as e:
                        logger.error(f"Erreur lors du calcul des tendances pour {metric}: {str(e)}")
                        results["trends"][metric] = {"error": str(e)}
            
            logger.info(f"Analyse de série temporelle terminée avec succès pour {len(target_metrics)} métriques")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de série temporelle: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def generate_satellite_report(self,
                               data: RemoteSensingData,
                               time_series_results: Optional[Dict[str, Any]] = None,
                               output_format: str = "markdown") -> Union[str, Dict[str, Any]]:
        """
        Génère un rapport d'analyse à partir des données satellite.
        
        Args:
            data: Données satellite traitées
            time_series_results: Résultats d'analyse de série temporelle (optionnel)
            output_format: Format de sortie (markdown, html, json)
            
        Returns:
            Rapport formaté (str) ou données du rapport (dict)
        """
        if not data:
            logger.error("Aucune donnée fournie pour la génération du rapport")
            return "Erreur: Aucune donnée disponible"
        
        # Structure du rapport
        report = {
            "title": f"Rapport d'analyse satellite - {data.parcel_id}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "metadata": {
                "source": data.source.name if data.source else "Inconnue",
                "acquisition_date": data.acquisition_date.strftime("%Y-%m-%d") if data.acquisition_date else "Inconnue",
                "parcel_id": data.parcel_id,
                "satellite": data.satellite_metadata.source.name if data.satellite_metadata else "Inconnu",
                "resolution": f"{data.satellite_metadata.spatial_resolution}m" if data.satellite_metadata else "Inconnue"
            },
            "metrics": {},
            "time_series": time_series_results
        }
        
        # Extraire les métriques disponibles
        if data.raster_data and isinstance(data.raster_data, dict):
            for key, raster in data.raster_data.items():
                if key != 'original' and raster is not None:
                    report["metrics"][key] = {
                        "mean": float(np.nanmean(raster)),
                        "min": float(np.nanmin(raster)),
                        "max": float(np.nanmax(raster)),
                        "std": float(np.nanstd(raster))
                    }
        
        # Générer le rapport dans le format demandé
        if output_format.lower() == "json":
            return report
        
        elif output_format.lower() == "html":
            # Template HTML simpliste pour l'exemple
            html = f"""
            <html>
            <head>
                <title>{report['title']}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #3498db; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>{report['title']}</h1>
                <p>Date du rapport: {report['date']}</p>
                
                <h2>Métadonnées</h2>
                <table>
                    <tr><th>Source</th><td>{report['metadata']['source']}</td></tr>
                    <tr><th>Date d'acquisition</th><td>{report['metadata']['acquisition_date']}</td></tr>
                    <tr><th>Identifiant de parcelle</th><td>{report['metadata']['parcel_id']}</td></tr>
                    <tr><th>Satellite</th><td>{report['metadata']['satellite']}</td></tr>
                    <tr><th>Résolution</th><td>{report['metadata']['resolution']}</td></tr>
                </table>
                
                <h2>Métriques</h2>
                <table>
                    <tr>
                        <th>Métrique</th>
                        <th>Moyenne</th>
                        <th>Min</th>
                        <th>Max</th>
                        <th>Écart-type</th>
                    </tr>
            """
            
            for metric, values in report["metrics"].items():
                html += f"""
                    <tr>
                        <td>{metric}</td>
                        <td>{values['mean']:.4f}</td>
                        <td>{values['min']:.4f}</td>
                        <td>{values['max']:.4f}</td>
                        <td>{values['std']:.4f}</td>
                    </tr>
                """
            
            html += """
                </table>
            """
            
            # Ajouter les résultats de série temporelle si disponibles
            if time_series_results:
                html += """
                <h2>Analyse temporelle</h2>
                """
                
                if "time_range" in time_series_results:
                    tr = time_series_results["time_range"]
                    html += f"""
                    <p>Période: {tr.get('start').strftime('%Y-%m-%d') if 'start' in tr else ''} à {tr.get('end').strftime('%Y-%m-%d') if 'end' in tr else ''} ({tr.get('duration_days')} jours)</p>
                    """
                
                if "trends" in time_series_results:
                    html += """
                    <h3>Tendances</h3>
                    <table>
                        <tr>
                            <th>Métrique</th>
                            <th>Taux annuel</th>
                            <th>R²</th>
                            <th>Valeur p</th>
                        </tr>
                    """
                    
                    for metric, trend in time_series_results["trends"].items():
                        if isinstance(trend, dict) and "error" not in trend:
                            html += f"""
                            <tr>
                                <td>{metric}</td>
                                <td>{trend.get('annual_rate', 0):.6f}</td>
                                <td>{trend.get('r_squared', 0):.4f}</td>
                                <td>{trend.get('p_value', 1):.4f}</td>
                            </tr>
                            """
                    
                    html += """
                    </table>
                    """
            
            html += """
            </body>
            </html>
            """
            
            return html
        
        else:  # Markdown par défaut
            markdown = f"# {report['title']}\n\nDate du rapport: {report['date']}\n\n"
            
            markdown += "## Métadonnées\n\n"
            markdown += f"- **Source**: {report['metadata']['source']}\n"
            markdown += f"- **Date d'acquisition**: {report['metadata']['acquisition_date']}\n"
            markdown += f"- **Identifiant de parcelle**: {report['metadata']['parcel_id']}\n"
            markdown += f"- **Satellite**: {report['metadata']['satellite']}\n"
            markdown += f"- **Résolution**: {report['metadata']['resolution']}\n\n"
            
            markdown += "## Métriques\n\n"
            markdown += "| Métrique | Moyenne | Min | Max | Écart-type |\n"
            markdown += "|---------|---------|-----|-----|------------|\n"
            
            for metric, values in report["metrics"].items():
                markdown += f"| {metric} | {values['mean']:.4f} | {values['min']:.4f} | {values['max']:.4f} | {values['std']:.4f} |\n"
            
            markdown += "\n"
            
            # Ajouter les résultats de série temporelle si disponibles
            if time_series_results:
                markdown += "## Analyse temporelle\n\n"
                
                if "time_range" in time_series_results:
                    tr = time_series_results["time_range"]
                    markdown += f"Période: {tr.get('start').strftime('%Y-%m-%d') if 'start' in tr else ''} à {tr.get('end').strftime('%Y-%m-%d') if 'end' in tr else ''} ({tr.get('duration_days')} jours)\n\n"
                
                if "trends" in time_series_results:
                    markdown += "### Tendances\n\n"
                    markdown += "| Métrique | Taux annuel | R² | Valeur p |\n"
                    markdown += "|---------|------------|----|---------|\n"
                    
                    for metric, trend in time_series_results["trends"].items():
                        if isinstance(trend, dict) and "error" not in trend:
                            markdown += f"| {metric} | {trend.get('annual_rate', 0):.6f} | {trend.get('r_squared', 0):.4f} | {trend.get('p_value', 1):.4f} |\n"
                    
                    markdown += "\n"
                
                if "changes" in time_series_results:
                    markdown += "### Changements\n\n"
                    markdown += "| Métrique | Absolu | Pourcentage |\n"
                    markdown += "|---------|--------|------------|\n"
                    
                    for metric, change in time_series_results["changes"].items():
                        if isinstance(change, dict):
                            markdown += f"| {metric} | {change.get('absolute', 0):.4f} | {change.get('percent', 0):.2f}% |\n"
            
            return markdown
