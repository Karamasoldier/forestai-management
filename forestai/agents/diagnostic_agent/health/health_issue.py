# -*- coding: utf-8 -*-
"""
Module définissant le modèle de problème sanitaire forestier.
"""

from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class HealthIssue:
    """Représentation d'un problème sanitaire forestier."""
    
    id: str
    name: str
    type: str  # 'disease', 'pest', 'abiotic', 'physiological'
    severity: float  # De 0 (aucun impact) à 1 (impact maximal)
    confidence: float  # De 0 (hypothèse) à 1 (certitude)
    affected_species: List[str]
    symptoms: List[str]
    description: str
    treatment_options: List[Dict[str, Any]]
    prevention_measures: List[str]
    spreading_risk: float  # De 0 (aucun risque) à 1 (risque maximal)
    references: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "severity": self.severity,
            "confidence": self.confidence,
            "affected_species": self.affected_species,
            "symptoms": self.symptoms,
            "description": self.description,
            "treatment_options": self.treatment_options,
            "prevention_measures": self.prevention_measures,
            "spreading_risk": self.spreading_risk,
            "references": self.references or []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthIssue':
        """Crée une instance à partir d'un dictionnaire."""
        return cls(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            severity=data["severity"],
            confidence=data["confidence"],
            affected_species=data["affected_species"],
            symptoms=data["symptoms"],
            description=data["description"],
            treatment_options=data["treatment_options"],
            prevention_measures=data["prevention_measures"],
            spreading_risk=data["spreading_risk"],
            references=data.get("references", [])
        )
