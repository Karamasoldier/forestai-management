# -*- coding: utf-8 -*-
"""
Module de chargement de la base de données de problèmes sanitaires.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, List

from forestai.agents.diagnostic_agent.health.health_issue import HealthIssue

logger = logging.getLogger(__name__)

class HealthDatabaseLoader:
    """Chargeur de base de données de problèmes sanitaires."""
    
    def __init__(self, data_dir: Path, reference_db_path: Optional[str] = None):
        """
        Initialise le chargeur de base de données.
        
        Args:
            data_dir: Répertoire des données
            reference_db_path: Chemin vers une base de données de référence (optionnel)
        """
        self.data_dir = data_dir
        self.reference_db_path = reference_db_path
    
    def load_database(self) -> Dict[str, HealthIssue]:
        """
        Charge la base de données des problèmes sanitaires.
        
        Returns:
            Dictionnaire des problèmes sanitaires indexés par ID
        """
        # Utiliser la base fournie en priorité
        if self.reference_db_path and Path(self.reference_db_path).exists():
            try:
                with open(self.reference_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {item["id"]: HealthIssue.from_dict(item) for item in data}
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la base de données sanitaire: {str(e)}")
        
        # Chercher un fichier par défaut dans le répertoire des données
        default_db_path = self.data_dir / "health_issues_database.json"
        if default_db_path.exists():
            try:
                with open(default_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {item["id"]: HealthIssue.from_dict(item) for item in data}
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la base de données sanitaire par défaut: {str(e)}")
        
        # Si aucune base n'est disponible, créer une base minimale
        logger.warning("Aucune base de données sanitaire trouvée, création d'une base minimale")
        return self._create_default_database()
    
    def _create_default_database(self) -> Dict[str, HealthIssue]:
        """
        Crée une base de données par défaut avec les problèmes sanitaires courants.
        
        Returns:
            Dictionnaire des problèmes sanitaires indexés par ID
        """
        default_issues = [
            HealthIssue(
                id="HI001",
                name="Processionnaire du pin",
                type="pest",
                severity=0.7,
                confidence=0.9,
                affected_species=["Pinus halepensis", "Pinus pinaster", "Pinus sylvestris", "Pinus nigra", "Cedrus"],
                symptoms=["Nids soyeux dans les branches", "Défoliation", "Dessèchement des aiguilles", "Processions de chenilles"],
                description="Chenille qui se nourrit des aiguilles de diverses espèces de pins et cèdres, causant des défoliations importantes et pouvant affaiblir l'arbre.",
                treatment_options=[
                    {"name": "Échenillage", "description": "Élimination manuelle des nids en hiver", "efficacy": 0.6, "cost": "Medium"},
                    {"name": "Piégeage à phéromones", "description": "Installation de pièges à phéromones pour capturer les papillons mâles", "efficacy": 0.5, "cost": "Low"},
                    {"name": "Traitement biologique Btk", "description": "Pulvérisation de Bacillus thuringiensis var. kurstaki", "efficacy": 0.8, "cost": "High"}
                ],
                prevention_measures=["Favoriser la biodiversité et les prédateurs naturels", "Diversifier les essences forestières", "Planter des espèces moins sensibles"],
                spreading_risk=0.8,
                references=["Rapport ONF 2020 sur les processionnaires", "Guide de la santé des forêts - DSF"]
            ),
            HealthIssue(
                id="HI002",
                name="Fomes (Heterobasidion annosum)",
                type="disease",
                severity=0.8,
                confidence=0.9,
                affected_species=["Picea abies", "Pinus sylvestris", "Abies alba", "Pseudotsuga menziesii"],
                symptoms=["Pourriture du cœur", "Mycélium blanc entre écorce et bois", "Carpophores brun-rougeâtre", "Dépérissement du houppier"],
                description="Champignon lignivore qui attaque le système racinaire et la base du tronc, provoquant une pourriture du bois et affaiblissant l'arbre.",
                treatment_options=[
                    {"name": "Coupe sanitaire", "description": "Élimination des arbres infectés", "efficacy": 0.7, "cost": "Medium"},
                    {"name": "Traitement des souches", "description": "Application d'urée ou de Rotstop® sur les souches fraîches", "efficacy": 0.9, "cost": "Medium"}
                ],
                prevention_measures=["Traitement préventif des souches après coupe", "Éviter les blessures aux arbres", "Adapter les périodes d'exploitation"],
                spreading_risk=0.7,
                references=["Manuel de pathologie forestière", "Fiches techniques du Département Santé des Forêts"]
            ),
            HealthIssue(
                id="HI003",
                name="Sécheresse",
                type="abiotic",
                severity=0.9,
                confidence=1.0,
                affected_species=["Toutes espèces", "Particulièrement les résineux peu adaptés"],
                symptoms=["Jaunissement/rougissement des aiguilles/feuilles", "Descente de cime", "Mortalité des branches", "Écoulement de résine"],
                description="Stress hydrique prolongé affectant la vitalité des arbres, augmentant leur vulnérabilité aux bioagresseurs et pouvant causer la mort.",
                treatment_options=[
                    {"name": "Irrigation d'urgence", "description": "Pour peuplements à forte valeur", "efficacy": 0.6, "cost": "Very High"},
                    {"name": "Réduction de la densité", "description": "Éclaircies pour limiter la compétition pour l'eau", "efficacy": 0.7, "cost": "Medium"}
                ],
                prevention_measures=["Adapter les essences aux conditions stationnelles", "Maintenir une densité adéquate", "Diversifier les essences et les structures"],
                spreading_risk=0.4,  # Pas de propagation en tant que telle mais risque d'extension géographique
                references=["Guide de gestion forestière face au changement climatique", "Rapports sur l'impact des sécheresses - INRAE"]
            )
        ]
        
        # Enregistrer cette base par défaut
        default_db_path = self.data_dir / "health_issues_database.json"
        try:
            with open(default_db_path, 'w', encoding='utf-8') as f:
                json.dump([issue.to_dict() for issue in default_issues], f, ensure_ascii=False, indent=2)
            logger.info(f"Base de données sanitaire par défaut créée: {default_db_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la base de données sanitaire par défaut: {str(e)}")
        
        return {issue.id: issue for issue in default_issues}
