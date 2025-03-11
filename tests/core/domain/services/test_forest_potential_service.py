"""
Tests unitaires pour le service d'analyse du potentiel forestier.
"""

import unittest
from unittest import mock
import datetime
from typing import Dict, Any

from forestai.core.domain.models.parcel import (
    Parcel, 
    ParcelIdentifier, 
    ParcelGeometry, 
    TerrainCharacteristics
)
from forestai.core.domain.services.forest_potential_service import ForestPotentialService


class MockClimateRepository:
    """Mock pour le repository de climat."""
    
    def get_climate_data(self, x: float, y: float) -> Dict[str, Any]:
        """Retourne des données climatiques simulées."""
        return {
            "annual_precipitation": 850,
            "avg_temperature": 12.5,
            "min_temperature": 3.0,
            "max_temperature": 26.0
        }


class MockSpeciesRepository:
    """Mock pour le repository d'espèces."""
    
    def find_suitable_species(self, characteristics: Dict[str, Any]) -> list:
        """Retourne des espèces recommandées simulées."""
        if characteristics.get("soil_type") == "limon":
            return ["chêne sessile", "hêtre", "douglas"]
        elif characteristics.get("soil_type") == "sable":
            return ["pin maritime", "pin sylvestre"]
        else:
            return ["bouleau", "aulne"]


class TestForestPotentialService(unittest.TestCase):
    """Tests pour le service ForestPotentialService."""
    
    def setUp(self):
        """Initialise l'environnement de test."""
        self.climate_repository = MockClimateRepository()
        self.species_repository = MockSpeciesRepository()
        
        self.service = ForestPotentialService(
            climate_repository=self.climate_repository,
            species_repository=self.species_repository
        )
        
        # Créer une parcelle test
        self.parcel = Parcel(
            identifier=ParcelIdentifier(
                department_code="13",
                commune_code="056",
                section="A",
                number="123"
            ),
            geometry=ParcelGeometry(
                wkt="POLYGON((0 0, 0 100, 100 100, 100 0, 0 0))",
                area_ha=2.5,
                perimeter_m=400,
                centroid_x=50,
                centroid_y=50,
                bbox=[0, 0, 100, 100]
            ),
            terrain=TerrainCharacteristics(
                avg_slope=10.0,
                max_slope=15.0,
                min_elevation=100.0,
                max_elevation=150.0,
                avg_elevation=125.0,
                aspect="S",
                soil_type="limon",
                water_presence=True,
                wetland_area_pct=10.0
            ),
            current_land_use="friche"
        )
    
    def test_analyze_parcel_potential(self):
        """Teste l'analyse du potentiel forestier d'une parcelle."""
        # Analyser la parcelle
        potential = self.service.analyze_parcel_potential(self.parcel)
        
        # Vérifier le résultat
        self.assertIsNotNone(potential)
        self.assertGreaterEqual(potential.score, 0.0)
        self.assertLessEqual(potential.score, 1.0)
        
        # Vérifier que les espèces recommandées correspondent à celles du mock
        self.assertEqual(potential.suitable_species, ["chêne sessile", "hêtre", "douglas"])
        
        # Vérifier la présence des autres attributs
        self.assertIsNotNone(potential.carbon_potential)
        self.assertIsNotNone(potential.timber_potential)
        self.assertIsNotNone(potential.biodiversity_score)
        self.assertIsInstance(potential.limitations, list)
        self.assertIsInstance(potential.opportunities, list)
    
    def test_analyze_parcel_potential_with_poor_conditions(self):
        """Teste l'analyse d'une parcelle avec des conditions défavorables."""
        # Modifier la parcelle pour avoir des conditions défavorables
        poor_parcel = Parcel(
            identifier=self.parcel.identifier,
            geometry=self.parcel.geometry,
            terrain=TerrainCharacteristics(
                avg_slope=35.0,  # Pente très forte
                max_slope=40.0,
                min_elevation=100.0,
                max_elevation=150.0,
                avg_elevation=125.0,
                aspect="N",  # Exposition nord (moins favorable)
                soil_type="rocheux",  # Sol rocheux
                water_presence=False,
                wetland_area_pct=0.0
            ),
            current_land_use="friche"
        )
        
        # Analyser la parcelle
        potential = self.service.analyze_parcel_potential(poor_parcel)
        
        # Vérifier le résultat
        self.assertIsNotNone(potential)
        
        # Le score devrait être faible
        self.assertLess(potential.score, 0.5)
        
        # Vérifier la présence de limitations
        self.assertGreater(len(potential.limitations), 0)
    
    def test_analyze_parcel_potential_with_partial_terrain(self):
        """Teste l'analyse d'une parcelle avec des données terrain partielles."""
        # Créer une parcelle avec des informations terrain minimales
        minimal_parcel = Parcel(
            identifier=self.parcel.identifier,
            geometry=self.parcel.geometry,
            terrain=TerrainCharacteristics(
                avg_slope=5.0,
                soil_type="sable"
            ),
            current_land_use="friche"
        )
        
        # Analyser la parcelle
        potential = self.service.analyze_parcel_potential(minimal_parcel)
        
        # Vérifier le résultat
        self.assertIsNotNone(potential)
        
        # Vérifier que les espèces correspondent au type de sol
        self.assertEqual(potential.suitable_species, ["pin maritime", "pin sylvestre"])
    
    def test_analyze_parcel_potential_with_no_terrain(self):
        """Teste l'analyse d'une parcelle sans informations terrain."""
        # Créer une parcelle sans terrain
        no_terrain_parcel = Parcel(
            identifier=self.parcel.identifier,
            geometry=self.parcel.geometry,
            terrain=None,
            current_land_use="friche"
        )
        
        # Analyser la parcelle
        potential = self.service.analyze_parcel_potential(no_terrain_parcel)
        
        # Vérifier le résultat
        self.assertIsNotNone(potential)
    
    def test_slope_analysis(self):
        """Teste l'analyse de la pente."""
        # Pente favorable
        terrain_good = TerrainCharacteristics(avg_slope=5.0)
        slope_score_good = self.service._analyze_slope(terrain_good)
        
        # Pente défavorable
        terrain_bad = TerrainCharacteristics(avg_slope=35.0)
        slope_score_bad = self.service._analyze_slope(terrain_bad)
        
        # Vérifier les résultats
        self.assertGreater(slope_score_good, 0.8)
        self.assertEqual(slope_score_bad, 0.0)
    
    def test_soil_analysis(self):
        """Teste l'analyse du sol."""
        # Sol favorable
        terrain_good = TerrainCharacteristics(soil_type="limon", wetland_area_pct=0.0)
        soil_score_good = self.service._analyze_soil(terrain_good)
        
        # Sol défavorable
        terrain_bad = TerrainCharacteristics(soil_type="rocheux", wetland_area_pct=50.0)
        soil_score_bad = self.service._analyze_soil(terrain_bad)
        
        # Vérifier les résultats
        self.assertGreater(soil_score_good, 0.8)
        self.assertLess(soil_score_bad, 0.3)
    
    def test_climate_analysis(self):
        """Teste l'analyse du climat."""
        # Exposition favorable
        parcel_good = self.parcel
        parcel_good.terrain.aspect = "S"
        climate_score_good = self.service._analyze_climate(parcel_good)
        
        # Exposition défavorable
        parcel_bad = self.parcel
        parcel_bad.terrain.aspect = "N"
        climate_score_bad = self.service._analyze_climate(parcel_bad)
        
        # Vérifier les résultats
        self.assertGreater(climate_score_good, climate_score_bad)


if __name__ == "__main__":
    unittest.main()
