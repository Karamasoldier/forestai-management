# Agent de Géotraitement (GeoAgent)

## Vue d'ensemble
L'agent de géotraitement est responsable de l'analyse géospatiale des parcelles forestières. Cet agent effectue diverses opérations de géotraitement pour identifier les parcelles à potentiel forestier, analyser les caractéristiques du terrain, et évaluer leur compatibilité avec différents types de plantations forestières.

## Accès aux données géographiques
Suite à l'arrêt de la génération de nouvelles clés API par l'IGN début 2024 et à la bascule vers la Géoplateforme en 2025, l'agent de géotraitement fonctionne principalement avec des données téléchargées localement.

### Sources de données
- **Données cadastrales**: Téléchargées depuis le site des impôts (cadastre.gouv.fr) ou data.gouv.fr
- **Données topographiques**: BDTOPO, BDFORET de l'IGN téléchargées depuis geoservices.ign.fr
- **Données d'occupation des sols**: Corine Land Cover, disponible sur data.gouv.fr
- **Modèles numériques de terrain (MNT)**: RGE ALTI de l'IGN téléchargé localement
- **Images aériennes et satellites**: Téléchargées ou accessibles via les URLs publiques IGN pour les données libres

### Organisation des données locales
- `/data/raw`: Données brutes téléchargées
- `/data/processed`: Données transformées et optimisées
- `/data/cache`: Cache pour les résultats d'analyses et de traitements

## Fonctionnalités principales

### Identification de parcelles
- Recherche de parcelles cadastrales par commune, section, numéro
- Calcul de métriques (surface, périmètre, pente moyenne)
- Filtrage des parcelles selon critères d'éligibilité aux projets forestiers

### Analyse du potentiel forestier
- Évaluation des caractéristiques pédoclimatiques
- Calcul des pentes et de l'exposition des terrains
- Analyse des zones d'exclusion (zones humides, proximité cours d'eau, etc.)

### Visualisation et export
- Génération de cartes de potentiel forestier
- Export de données au format SHP, GeoJSON, CSV
- Production de rapports d'analyse par parcelle ou groupe de parcelles

## Utilisation

```bash
# Exécuter l'agent de géotraitement avec les paramètres par défaut
python run.py --agent geoagent

# Rechercher des parcelles dans une commune spécifique
python run.py --agent geoagent --action search_parcels --params '{"commune": "Saint-Martin-de-Crau", "section": "B"}'

# Analyser le potentiel forestier d'une liste de parcelles
python run.py --agent geoagent --action analyze_forest_potential --params '{"parcels": ["123456789", "987654321"]}'
```

## Configuration

Dans le fichier d'environnement `.env`, ajoutez les chemins des données géographiques locales:

```
# Chemins des données géographiques
CADASTRE_DATA_PATH=./data/raw/cadastre
BDTOPO_DATA_PATH=./data/raw/bdtopo
MNT_DATA_PATH=./data/raw/mnt
```

## Intégration des URLs publiques IGN

Pour les données libres, utilisez les URLs publiques fournies par l'IGN:

```python
# Exemple d'URL publique pour le fond cartographique PLANIGN
PLAN_IGN_URL = "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=PLAN.IGN&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}"

# URL pour les orthophotos
ORTHO_HR_URL = "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}"
```