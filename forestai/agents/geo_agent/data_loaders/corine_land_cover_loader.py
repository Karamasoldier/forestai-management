# forestai/agents/geo_agent/data_loaders/corine_land_cover_loader.py

import os
import json
from typing import Dict, List, Any, Union, Optional
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, box, Polygon
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from forestai.core.utils.logging import get_logger

class CorineLandCoverLoader:
    """
    Chargeur de données Corine Land Cover à partir d'une base de données PostgreSQL/PostGIS.
    
    Ce loader permet d'extraire les données d'occupation des sols pour une géométrie donnée
    en effectuant des requêtes spatiales sur une base de données contenant le Corine Land Cover.
    """
    
    # Mapping des codes CLC vers des catégories générales
    CLC_CATEGORIES = {
        # Territoires artificialisés (classe 1xx)
        "urban": [111, 112, 121, 122, 123, 124, 131, 132, 133, 141, 142],
        
        # Territoires agricoles (classe 2xx)
        "agriculture": [211, 212, 213, 221, 222, 223, 231, 241, 242, 243, 244],
        
        # Forêts et milieux semi-naturels (classe 3xx)
        "forest": [311, 312, 313],  # Forêts de feuillus, conifères et mixtes
        "shrub": [321, 322, 323, 324],  # Pelouses, landes, végétation sclérophylle, etc.
        "open_space": [331, 332, 333, 334, 335],  # Plages, roches, végétation clairsemée, etc.
        
        # Zones humides (classe 4xx)
        "wetland": [411, 412, 421, 422, 423],
        
        # Surfaces en eau (classe 5xx)
        "water": [511, 512, 521, 522, 523]
    }
    
    # Description détaillée des codes CLC
    CLC_DESCRIPTIONS = {
        111: "Tissu urbain continu",
        112: "Tissu urbain discontinu",
        121: "Zones industrielles ou commerciales",
        122: "Réseaux routiers et ferroviaires et espaces associés",
        123: "Zones portuaires",
        124: "Aéroports",
        131: "Extraction de matériaux",
        132: "Décharges",
        133: "Chantiers",
        141: "Espaces verts urbains",
        142: "Équipements sportifs et de loisirs",
        211: "Terres arables hors périmètres d'irrigation",
        212: "Périmètres irrigués en permanence",
        213: "Rizières",
        221: "Vignobles",
        222: "Vergers et petits fruits",
        223: "Oliveraies",
        231: "Prairies",
        241: "Cultures annuelles associées aux cultures permanentes",
        242: "Systèmes culturaux et parcellaires complexes",
        243: "Surfaces essentiellement agricoles, interrompues par des espaces naturels importants",
        244: "Territoires agroforestiers",
        311: "Forêts de feuillus",
        312: "Forêts de conifères",
        313: "Forêts mélangées",
        321: "Pelouses et pâturages naturels",
        322: "Landes et broussailles",
        323: "Végétation sclérophylle",
        324: "Forêt et végétation arbustive en mutation",
        331: "Plages, dunes et sable",
        332: "Roches nues",
        333: "Végétation clairsemée",
        334: "Zones incendiées",
        335: "Glaciers et neiges éternelles",
        411: "Marais intérieurs",
        412: "Tourbières",
        421: "Marais maritimes",
        422: "Marais salants",
        423: "Zones intertidales",
        511: "Cours et voies d'eau",
        512: "Plans d'eau",
        521: "Lagunes littorales",
        522: "Estuaires",
        523: "Mers et océans"
    }
    
    def __init__(self, db_params: Dict[str, str] = None):
        """
        Initialise le chargeur de données Corine Land Cover.
        
        Args:
            db_params: Paramètres de connexion à la base de données (si None, utilise les variables d'env)
        """
        # Charger les variables d'environnement si pas encore fait
        load_dotenv()
        
        # Initialiser le logger
        self.logger = get_logger(name="loader.corine", level="INFO")
        
        # Paramètres de connexion par défaut (depuis variables d'environnement)
        if db_params is None:
            db_params = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': os.environ.get('DB_PORT', '5432'),
                'database': os.environ.get('DB_NAME', 'forestai'),
                'user': os.environ.get('DB_USER', 'postgres'),
                'password': os.environ.get('DB_PASSWORD', '')
            }
        
        # Construire l'URI de connexion SQLAlchemy
        self.db_uri = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        
        # Créer l'engine SQLAlchemy
        try:
            self.engine = create_engine(self.db_uri)
            # Tester la connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info("Connexion à la base de données PostgreSQL réussie")
        except Exception as e:
            self.logger.error(f"Erreur de connexion à la base de données: {str(e)}")
            self.engine = None
    
    def get_table_name(self) -> str:
        """
        Détermine le nom de la table Corine Land Cover dans la base de données.
        
        Returns:
            Nom de la table trouvée, ou 'corine_land_cover' par défaut
        """
        # Noms possibles de tables pour Corine Land Cover
        potential_tables = [
            'corine_land_cover',
            'clc',
            'clc_france',
            'corine'
        ]
        
        if self.engine is None:
            self.logger.warning("Engine de base de données non initialisé")
            return potential_tables[0]
        
        try:
            # Requête pour lister les tables existantes
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                ))
                tables = [row[0] for row in result]
                
            # Chercher une correspondance
            for table in potential_tables:
                if table in tables:
                    self.logger.info(f"Table trouvée: {table}")
                    return table
                    
            # Recherche moins stricte (si aucune correspondance exacte)
            for table in tables:
                if 'corine' in table.lower() or 'clc' in table.lower():
                    self.logger.info(f"Table trouvée: {table}")
                    return table
            
            # Aucune table trouvée
            self.logger.warning("Aucune table Corine Land Cover trouvée dans la base de données")
            return potential_tables[0]
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de tables: {str(e)}")
            return potential_tables[0]
    
    def get_column_names(self, table_name: str) -> Dict[str, str]:
        """
        Détermine les noms de colonnes dans la table Corine Land Cover.
        
        Args:
            table_name: Nom de la table à examiner
            
        Returns:
            Dictionnaire mappant les colonnes requises vers leur nom réel dans la table
        """
        # Mappings par défaut (selon conventions)
        column_mappings = {
            'code': 'code',
            'label': 'label',
            'geometry': 'geom'
        }
        
        if self.engine is None:
            self.logger.warning("Engine de base de données non initialisé")
            return column_mappings
        
        try:
            # Requête pour lister les colonnes de la table
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_schema = 'public' AND table_name = '{table_name}'"
                ))
                columns = [row[0] for row in result]
            
            # Rechercher la colonne du code CLC
            code_columns = ['code', 'clc_code', 'code_clc', 'id_clc', 'code_2018', 'code_2012']
            for col in code_columns:
                if col in columns:
                    column_mappings['code'] = col
                    break
            
            # Rechercher la colonne de libellé
            label_columns = ['label', 'nom', 'libelle', 'clc_label', 'description']
            for col in label_columns:
                if col in columns:
                    column_mappings['label'] = col
                    break
            
            # Rechercher la colonne de géométrie
            geom_columns = ['geom', 'geometry', 'the_geom', 'shape', 'wkb_geometry']
            for col in geom_columns:
                if col in columns:
                    column_mappings['geometry'] = col
                    break
            
            self.logger.info(f"Colonnes identifiées: {column_mappings}")
            return column_mappings
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de colonnes: {str(e)}")
            return column_mappings
    
    def load_landcover_for_geometry(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon], 
                                   buffer_distance: float = 0) -> Optional[gpd.GeoDataFrame]:
        """
        Charge les données Corine Land Cover pour une géométrie donnée.
        
        Args:
            geometry: Géométrie pour laquelle charger les données (GeoJSON, GeoDataFrame ou Polygon)
            buffer_distance: Distance de buffer en mètres à appliquer à la géométrie
            
        Returns:
            GeoDataFrame contenant les données d'occupation des sols, ou None en cas d'erreur
        """
        if self.engine is None:
            self.logger.error("Engine de base de données non initialisé")
            return None
        
        try:
            # Conversion de la géométrie en wkt
            if isinstance(geometry, dict):  # GeoJSON
                geom = shape(geometry)
            elif isinstance(geometry, gpd.GeoDataFrame):
                geom = geometry.geometry.iloc[0]
            else:
                geom = geometry
            
            wkt = geom.wkt
            
            # Déterminer le nom de la table et les colonnes
            table_name = self.get_table_name()
            columns = self.get_column_names(table_name)
            
            # Construire la requête SQL avec intersection spatiale
            query = f"""
            SELECT 
                {columns['code']} as code, 
                {columns['label']} as label,
                ST_AsGeoJSON(ST_Transform({columns['geometry']}, 2154)) as geometry,
                ST_Area(ST_Intersection(
                    ST_Transform({columns['geometry']}, 2154),
                    ST_Buffer(ST_GeomFromText('{wkt}', 2154), {buffer_distance})
                )) as overlap_area
            FROM {table_name}
            WHERE ST_Intersects(
                ST_Transform({columns['geometry']}, 2154),
                ST_Buffer(ST_GeomFromText('{wkt}', 2154), {buffer_distance})
            )
            """
            
            self.logger.debug(f"Exécution de la requête SQL: {query}")
            
            # Exécuter la requête
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
            
            # Si aucun résultat
            if not rows:
                self.logger.warning(f"Aucune donnée Corine Land Cover trouvée pour la géométrie")
                return None
            
            # Convertir les résultats en GeoDataFrame
            features = []
            for row in rows:
                # Conversion du code en entier si possible
                try:
                    clc_code = int(row.code)
                except (ValueError, TypeError):
                    clc_code = row.code
                
                # Créer la feature
                features.append({
                    "type": "Feature",
                    "properties": {
                        "code": clc_code,
                        "label": row.label,
                        "overlap_area": row.overlap_area,
                        "description": self.CLC_DESCRIPTIONS.get(clc_code, "")
                    },
                    "geometry": json.loads(row.geometry)
                })
            
            gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:2154")
            
            # Ajouter la catégorie générale
            gdf['category'] = gdf['code'].apply(self._get_category)
            
            self.logger.info(f"Données Corine Land Cover chargées: {len(gdf)} polygones")
            return gdf
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données: {str(e)}")
            return None
    
    def _get_category(self, code: Union[int, str]) -> str:
        """
        Détermine la catégorie générale d'un code CLC.
        
        Args:
            code: Code Corine Land Cover
            
        Returns:
            Catégorie générale (urban, agriculture, forest, etc.)
        """
        # Conversion en entier si nécessaire
        try:
            code_int = int(code)
        except (ValueError, TypeError):
            return "unknown"
        
        # Recherche dans les catégories
        for category, codes in self.CLC_CATEGORIES.items():
            if code_int in codes:
                return category
        
        # Par défaut, catégorisation basée sur le premier chiffre
        if 100 <= code_int < 200:
            return "urban"
        elif 200 <= code_int < 300:
            return "agriculture"
        elif 300 <= code_int < 400:
            return "natural"
        elif 400 <= code_int < 500:
            return "wetland"
        elif 500 <= code_int < 600:
            return "water"
        
        return "unknown"
    
    def get_dominant_landcover(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon]) -> Dict[str, Any]:
        """
        Détermine l'occupation des sols dominante pour une géométrie donnée.
        
        Args:
            geometry: Géométrie à analyser
            
        Returns:
            Dictionnaire contenant les informations sur l'occupation des sols dominante
        """
        # Charger les données
        landcover_data = self.load_landcover_for_geometry(geometry)
        
        if landcover_data is None or len(landcover_data) == 0:
            self.logger.warning("Pas de données d'occupation des sols disponibles")
            return {
                "dominant_code": None,
                "dominant_label": "Inconnu",
                "dominant_category": "unknown",
                "coverage_percentage": 0,
                "coverage_details": {}
            }
        
        # Calculer la surface totale des intersections
        total_area = landcover_data['overlap_area'].sum()
        
        # Agréger par code CLC
        coverage = landcover_data.groupby(['code', 'label', 'category']).agg({
            'overlap_area': 'sum'
        }).reset_index()
        
        # Calculer les pourcentages
        coverage['percentage'] = (coverage['overlap_area'] / total_area) * 100
        
        # Trouver le code dominant
        dominant = coverage.loc[coverage['overlap_area'].idxmax()]
        
        # Créer le dictionnaire des couvertures détaillées
        coverage_details = {}
        for _, row in coverage.iterrows():
            coverage_details[int(row['code']) if isinstance(row['code'], (int, float)) else row['code']] = {
                'label': row['label'],
                'category': row['category'],
                'area': float(row['overlap_area']),
                'percentage': float(row['percentage'])
            }
        
        # Agréger par catégorie générale
        category_coverage = landcover_data.groupby('category').agg({
            'overlap_area': 'sum'
        }).reset_index()
        category_coverage['percentage'] = (category_coverage['overlap_area'] / total_area) * 100
        
        category_details = {}
        for _, row in category_coverage.iterrows():
            category_details[row['category']] = {
                'area': float(row['overlap_area']),
                'percentage': float(row['percentage'])
            }
        
        # Construire le résultat
        result = {
            "dominant_code": int(dominant['code']) if isinstance(dominant['code'], (int, float)) else dominant['code'],
            "dominant_label": dominant['label'],
            "dominant_category": dominant['category'],
            "coverage_percentage": float(dominant['percentage']),
            "coverage_details": coverage_details,
            "category_details": category_details
        }
        
        self.logger.info(f"Occupation des sols dominante: {result['dominant_label']} "
                        f"({result['dominant_category']}, {result['coverage_percentage']:.1f}%)")
        
        return result
    
    def calculate_forestry_potential(self, geometry: Union[dict, gpd.GeoDataFrame, Polygon]) -> Dict[str, Any]:
        """
        Calcule le potentiel forestier basé sur l'occupation des sols.
        
        Args:
            geometry: Géométrie à analyser
            
        Returns:
            Dictionnaire contenant le score de potentiel et les justifications
        """
        # Obtenir les détails d'occupation des sols
        landcover = self.get_dominant_landcover(geometry)
        
        # Initialiser les résultats
        result = {
            "potential_score": 0.5,  # Score par défaut (neutre)
            "constraints": [],
            "opportunities": [],
            "context": landcover
        }
        
        # Si pas de données disponibles
        if landcover["dominant_code"] is None:
            result["potential_score"] = 0.5
            result["constraints"].append("Données d'occupation des sols non disponibles")
            return result
        
        # Scores de base par catégorie
        category_scores = {
            "forest": 0.9,        # Déjà forestier = très bon potentiel
            "shrub": 0.8,         # Broussailles = bon potentiel
            "agriculture": 0.6,   # Agricole = potentiel moyen à bon
            "open_space": 0.7,    # Espaces ouverts = potentiel assez bon
            "wetland": 0.4,       # Zones humides = potentiel limité
            "water": 0.1,         # Eau = potentiel très limité
            "urban": 0.2          # Zones urbaines = potentiel faible
        }
        
        # Récupérer le score de base pour la catégorie dominante
        dominant_category = landcover["dominant_category"]
        base_score = category_scores.get(dominant_category, 0.5)
        
        # Ajuster selon le pourcentage de couverture
        coverage_multiplier = min(1.0, landcover["coverage_percentage"] / 70.0)
        adjusted_score = base_score * coverage_multiplier
        
        # Analyse des contraintes et opportunités
        if dominant_category == "forest":
            result["opportunities"].append("Terrain déjà forestier, adapté à la sylviculture")
            if landcover["coverage_percentage"] > 80:
                result["constraints"].append("Forte couverture forestière existante, possibilités de nouvelles plantations limitées")
        
        elif dominant_category == "agriculture":
            result["opportunities"].append("Terrain agricole potentiellement convertible en forêt")
            if landcover["coverage_percentage"] > 70:
                result["constraints"].append("Conversion agricole nécessaire, procédures administratives à prévoir")
        
        elif dominant_category == "urban":
            result["constraints"].append("Zone urbanisée, potentiel forestier très limité")
            if landcover["coverage_percentage"] > 50:
                adjusted_score *= 0.5  # Pénalité supplémentaire
        
        elif dominant_category == "wetland":
            result["constraints"].append("Zone humide, nécessite des espèces adaptées")
            result["opportunities"].append("Potentiel pour forêt humide spécialisée (aulnes, saules)")
        
        # Analyse des catégories mixtes
        category_details = landcover.get("category_details", {})
        
        # Vérifier s'il y a une proportion significative de forêt
        forest_percentage = category_details.get("forest", {}).get("percentage", 0)
        if 20 < forest_percentage < 60:
            result["opportunities"].append(f"Présence partielle de forêt ({forest_percentage:.1f}%), extension possible")
            adjusted_score = max(adjusted_score, 0.7)  # Améliorer le score
        
        # Vérifier s'il y a une proportion significative d'agriculture
        agriculture_percentage = category_details.get("agriculture", {}).get("percentage", 0)
        if agriculture_percentage > 40:
            result["opportunities"].append(f"Potentiel agroforestier ({agriculture_percentage:.1f}% de terres agricoles)")
        
        # Vérifier les contraintes urbaines
        urban_percentage = category_details.get("urban", {}).get("percentage", 0)
        if urban_percentage > 30:
            result["constraints"].append(f"Présence significative de zones urbanisées ({urban_percentage:.1f}%)")
            adjusted_score *= 0.8  # Pénalité
        
        # Normaliser le score final entre 0 et 1
        result["potential_score"] = round(min(max(adjusted_score, 0), 1), 2)
        
        # Déterminer des espèces recommandées basées sur le type d'occupation des sols
        result["recommended_species"] = self._recommend_species(landcover)
        
        return result
    
    def _recommend_species(self, landcover: Dict[str, Any]) -> List[str]:
        """
        Recommande des espèces forestières adaptées au type d'occupation des sols.
        
        Args:
            landcover: Informations d'occupation des sols
            
        Returns:
            Liste d'espèces recommandées
        """
        recommended = []
        dominant_category = landcover["dominant_category"]
        
        # Recommendations basées sur la catégorie dominante
        if dominant_category == "forest":
            # Regarder le code précis pour déterminer le type de forêt
            if landcover["dominant_code"] == 311:  # Forêt de feuillus
                recommended.extend(["chêne sessile", "chêne pédonculé", "hêtre", "érable"])
            elif landcover["dominant_code"] == 312:  # Forêt de conifères
                recommended.extend(["pin sylvestre", "épicéa", "douglas", "mélèze"])
            elif landcover["dominant_code"] == 313:  # Forêt mixte
                recommended.extend(["chêne", "pin maritime", "châtaignier"])
            else:
                recommended.extend(["chêne", "pin", "douglas"])
        
        elif dominant_category == "agriculture":
            recommended.extend(["chêne", "érable champêtre", "noyer", "merisier", "cormier"])
        
        elif dominant_category == "shrub":
            recommended.extend(["pin maritime", "chêne vert", "châtaignier"])
        
        elif dominant_category == "wetland":
            recommended.extend(["aulne glutineux", "frêne commun", "saule blanc", "peuplier"])
        
        elif dominant_category == "open_space":
            recommended.extend(["pin sylvestre", "bouleau", "chêne pubescent"])
        
        # Si peu de recommendations, ajouter des espèces polyvalentes
        if len(recommended) < 3:
            recommended.extend(["chêne sessile", "pin sylvestre", "érable champêtre"])
        
        # Dédupliquer
        return list(set(recommended))

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une géométrie de test (un rectangle)
    minx, miny, maxx, maxy = 843000, 6278000, 844000, 6279000  # Coordonnées Lambert 93
    test_geometry = box(minx, miny, maxx, maxy)
    
    # Initialiser le loader
    loader = CorineLandCoverLoader()
    
    # Charger les données pour la géométrie
    clc_data = loader.load_landcover_for_geometry(test_geometry)
    
    if clc_data is not None:
        print(f"Données chargées: {len(clc_data)} polygones")
        print(clc_data[['code', 'label', 'category']].head())
    
    # Obtenir l'occupation des sols dominante
    dominant = loader.get_dominant_landcover(test_geometry)
    print(f"\nOccupation dominante: {dominant['dominant_label']} ({dominant['coverage_percentage']:.1f}%)")
    
    # Calculer le potentiel forestier
    potential = loader.calculate_forestry_potential(test_geometry)
    print(f"\nPotentiel forestier: {potential['potential_score']}")
    print("Opportunités:", potential['opportunities'])
    print("Contraintes:", potential['constraints'])
    print("Espèces recommandées:", potential['recommended_species'])
