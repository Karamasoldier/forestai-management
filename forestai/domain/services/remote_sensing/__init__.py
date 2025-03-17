#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module d'intégration de télédétection pour ForestAI.

Ce module fournit des services permettant d'acquérir, traiter et analyser
des données de télédétection (satellites, LIDAR, drones) dans le cadre de la
gestion forestière.
"""

from forestai.domain.services.remote_sensing.remote_data_connector import RemoteDataConnector
from forestai.domain.services.remote_sensing.satellite_data_provider import SatelliteDataProvider
from forestai.domain.services.remote_sensing.lidar_data_provider import LidarDataProvider
from forestai.domain.services.remote_sensing.data_processor import RemoteSensingDataProcessor
from forestai.domain.services.remote_sensing.forest_metrics_calculator import ForestMetricsCalculator
from forestai.domain.services.remote_sensing.models import (
    RemoteSensingData,
    SatelliteImageMetadata,
    LidarPointCloudMetadata,
    ForestMetrics,
    VegetationIndex,
    RemoteSensingSource
)

__all__ = [
    'RemoteDataConnector',
    'SatelliteDataProvider',
    'LidarDataProvider',
    'RemoteSensingDataProcessor',
    'ForestMetricsCalculator',
    'RemoteSensingData',
    'SatelliteImageMetadata',
    'LidarPointCloudMetadata',
    'ForestMetrics',
    'VegetationIndex',
    'RemoteSensingSource'
]
