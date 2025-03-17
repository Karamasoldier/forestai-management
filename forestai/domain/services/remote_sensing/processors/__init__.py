"""
Package de processeurs de données de télédétection pour ForestAI.

Ce package contient les différentes implémentations de processeurs pour traiter
les données de télédétection issues de différentes sources.
"""

from forestai.domain.services.remote_sensing.processors.base_processor import BaseDataProcessor
from forestai.domain.services.remote_sensing.processors.satellite_processor import SatelliteDataProcessor
from forestai.domain.services.remote_sensing.processors.lidar_processor import LidarDataProcessor
from forestai.domain.services.remote_sensing.processors.index_calculator import VegetationIndexCalculator

__all__ = [
    'BaseDataProcessor',
    'SatelliteDataProcessor',
    'LidarDataProcessor',
    'VegetationIndexCalculator'
]
