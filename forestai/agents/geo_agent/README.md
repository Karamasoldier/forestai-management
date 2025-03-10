# Agent de Géotraitement

Cet agent est responsable de l'analyse géospatiale des parcelles forestières potentielles.

## Fonctionnalités

- Identification des parcelles à potentiel forestier à partir de données cadastrales
- Analyse des sols, pentes et proximités avec des forêts existantes
- Regroupement de petites parcelles adjacentes pour optimisation forestière
- Génération de rapports cartographiques et analytiques
- Extraction des contacts de propriétaires via les mairies

## Utilisation

```python
from forestai.agents.geo_agent import GeoAgent

# Initialiser l'agent avec la configuration
agent = GeoAgent(config)

# Rechercher des parcelles dans un département
parcels = agent.find_profitable_parcels("01", min_area=1.5)

# Analyser les possibilités de regroupement
clusters = agent.analyze_small_parcels_clustering(parcels)

# Obtenir les contacts des mairies
contacts = agent.get_municipality_contacts("01")

# Générer un rapport complet
report = agent.generate_report(parcels, clusters, contacts)
```

## API Utilisées

- API cadastrale (cadastre.gouv.fr)
- API Géoportail de l'IGN 
- API gouvernementale (etablissements-publics.api.gouv.fr)

## Modèles de Données

### Parcelles

Attributs principaux des parcelles analysées:

- `id`: Identifiant unique de la parcelle
- `geometry`: Géométrie (Polygon)
- `area_ha`: Surface en hectares
- `nature`: Code nature cadastral
- `commune_code`: Code INSEE de la commune
- `owner_id`: Identifiant du propriétaire
- `forestry_potential`: Score de potentiel forestier (0-1)
- `soil_suitability`: Score de compatibilité du sol (0-1)
- `forest_proximity`: Score de proximité avec des forêts existantes (0-1)
- `recommended_species`: Liste d'essences recommandées

## Extensions Futures

- Intégration d'images satellite (Sentinel-2) pour analyse automatique
- Prédiction de croissance forestière par apprentissage automatique
- Interface cartographique interactive
- Extraction automatique des données LiDAR pour analyse topographique détaillée
