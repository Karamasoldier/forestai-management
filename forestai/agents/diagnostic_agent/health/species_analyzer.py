# -*- coding: utf-8 -*-
"""
Module d'analyse sanitaire par espèce forestière.
"""

import logging
import numpy as np
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SpeciesHealthAnalyzer:
    """Analyseur de santé par espèce forestière."""
    
    def analyze_species_health(self, trees: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Analyse l'état sanitaire par espèce.
        
        Args:
            trees: Liste des arbres de l'inventaire
            
        Returns:
            Dictionnaire avec l'état sanitaire par espèce
        """
        species_data = {}
        
        # Regrouper les arbres par espèce
        for tree in trees:
            species = tree.get("species", "Unknown")
            if species not in species_data:
                species_data[species] = {
                    "count": 0,
                    "health_scores": [],
                    "symptoms_count": {},
                    "vigor_index": []
                }
            
            species_data[species]["count"] += 1
            
            # Traiter le score de santé s'il existe
            if "health_score" in tree:
                species_data[species]["health_scores"].append(tree["health_score"])
            
            # Traiter l'indice de vigueur s'il existe
            if "vigor_index" in tree:
                species_data[species]["vigor_index"].append(tree["vigor_index"])
            
            # Comptabiliser les symptômes
            if "symptoms" in tree and isinstance(tree["symptoms"], list):
                for symptom in tree["symptoms"]:
                    sympt_name = symptom if isinstance(symptom, str) else symptom.get("name", "unknown")
                    if sympt_name not in species_data[species]["symptoms_count"]:
                        species_data[species]["symptoms_count"][sympt_name] = 0
                    species_data[species]["symptoms_count"][sympt_name] += 1
        
        # Calculer les statistiques par espèce
        species_health = {}
        for species, data in species_data.items():
            # Score de santé moyen (sur 10)
            health_score = 10.0  # Par défaut
            if data["health_scores"]:
                # Si les scores sont entre 0-1, les convertir en échelle 0-10
                sample_score = data["health_scores"][0]
                if isinstance(sample_score, (int, float)) and 0 <= sample_score <= 1:
                    health_score = np.mean(data["health_scores"]) * 10
                else:
                    health_score = np.mean(data["health_scores"])
            
            # Indice de vigueur moyen
            vigor_index = None
            if data["vigor_index"]:
                vigor_index = np.mean(data["vigor_index"])
            
            # Symptômes principaux
            main_symptoms = []
            for symptom, count in sorted(data["symptoms_count"].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / data["count"]) * 100
                if percentage > 5:  # Ne conserver que les symptômes affectant plus de 5% des arbres
                    main_symptoms.append({
                        "name": symptom,
                        "count": count,
                        "percentage": round(percentage, 1)
                    })
            
            # Statut sanitaire
            health_status = "Bon"
            if health_score < 4:
                health_status = "Critique"
            elif health_score < 6:
                health_status = "Mauvais"
            elif health_score < 7.5:
                health_status = "Moyen"
            
            species_health[species] = {
                "count": data["count"],
                "health_score": round(health_score, 1),
                "health_status": health_status,
                "main_symptoms": main_symptoms[:5],  # Limiter aux 5 principaux symptômes
                "vigor_index": round(vigor_index, 2) if vigor_index is not None else None
            }
        
        return species_health
