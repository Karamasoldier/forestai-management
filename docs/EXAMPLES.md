# Exemples d'utilisation de ForestAI

Ce document fournit des exemples pratiques d'utilisation du système ForestAI pour différents cas d'usage en gestion forestière.

## Exemples par agent

### GeoAgent (Agent de géotraitement)

#### Recherche de parcelles dans une commune

Pour rechercher des parcelles cadastrales dans une commune spécifique :

```bash
python run.py --agent geoagent --action search_parcels --params '{
  "commune": "Saint-Martin-de-Crau", 
  "section": "B"
}'
```

Résultat :
```json
{
  "parcels": [
    {
      "id": "13097000B0012",
      "area_ha": 12.45,
      "commune": "Saint-Martin-de-Crau",
      "section": "B",
      "numero": "0012"
    },
    {
      "id": "13097000B0013",
      "area_ha": 8.72,
      "commune": "Saint-Martin-de-Crau",
      "section": "B",
      "numero": "0013"
    },
    // ...autres parcelles
  ],
  "count": 27,
  "commune_code": "13097"
}
```

#### Analyse du potentiel forestier d'une parcelle

Pour analyser le potentiel forestier d'une parcelle cadastrale :

```bash
python run.py --agent geoagent --action analyze_potential --params '{
  "parcel_id": "13097000B0012"
}'
```

Ou en utilisant une géométrie personnalisée (format GeoJSON) :

```bash
python run.py --agent geoagent --action analyze_potential --params '{
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[4.7842, 43.6721], [4.7893, 43.6721], [4.7893, 43.6772], [4.7842, 43.6772], [4.7842, 43.6721]]]
  }
}'
```

#### Génération de carte thématique

Pour générer une carte thématique d'une zone forestière :

```bash
python run.py --agent geoagent --action generate_map --params '{
  "parcel_id": "13097000B0012",
  "map_type": "vegetation",
  "output_format": "png",
  "include_basemap": true
}'
```

### ReglementationAgent (Agent de réglementation)

#### Vérification de conformité réglementaire

Pour vérifier la conformité réglementaire d'un projet forestier sur une parcelle :

```bash
python run.py --agent reglementation --action check_compliance --params '{
  "parcels": ["13097000B0012"],
  "project_type": "boisement",
  "species": ["pinus_halepensis", "quercus_ilex"],
  "area_ha": 10.5
}'
```

#### Recherche de textes réglementaires

Pour rechercher des textes réglementaires par mots-clés :

```bash
python run.py --agent reglementation --action search_texts --params '{
  "keywords": ["défrichement", "autorisation"],
  "limit": 5
}'
```

#### Vérification de zone protégée

Pour vérifier si une parcelle est située dans une zone protégée :

```bash
python run.py --agent reglementation --action check_protected_area --params '{
  "parcel_id": "13097000B0012",
  "check_types": ["natura2000", "znieff", "zone_humide"]
}'
```

### SubsidyAgent (Agent de subventions)

#### Recherche de subventions disponibles

Pour rechercher des subventions adaptées à un type de projet forestier :

```bash
python run.py --agent subsidy --action search_subsidies --params '{
  "project_type": "reboisement",
  "region": "Occitanie",
  "owner_type": "private"
}'
```

#### Analyse d'éligibilité à une subvention

Pour analyser l'éligibilité d'un projet à une subvention spécifique :

```bash
python run.py --agent subsidy --action analyze_eligibility --params '{
  "project": {
    "type": "reboisement",
    "area_ha": 5.2,
    "species": ["pinus_pinea", "quercus_suber"],
    "location": "13097000B0012"
  },
  "subsidy_id": "FR-2023-12"
}'
```

#### Génération d'un dossier de demande de subvention

Pour générer automatiquement un dossier de demande de subvention :

```bash
python run.py --agent subsidy --action generate_application --params '{
  "project": {
    "type": "reboisement",
    "area_ha": 5.2,
    "species": ["pinus_pinea", "quercus_suber"],
    "location": "13097000B0012"
  },
  "subsidy_id": "FR-2023-12",
  "applicant": {
    "name": "Domaine Forestier du Sud",
    "address": "Route des Pins 13200 Arles",
    "contact": "contact@domaineforestier.fr",
    "siret": "12345678900012"
  },
  "output_formats": ["pdf", "html"]
}'
```

## Exemples d'intégration entre agents

### Analyse complète pour un nouveau projet forestier

Cet exemple montre comment combiner les différents agents pour une analyse complète d'un projet forestier :

```python
# Exemple de script Python combinant les agents
from forestai.agents.geo_agent import GeoAgent
from forestai.agents.reglementation_agent import ReglementationAgent
from forestai.agents.subsidy_agent import SubsidyAgent
from forestai.core.utils.config import Config

# Chargement de la configuration
config = Config().load_config(".env")

# Initialisation des agents
geo_agent = GeoAgent(config)
reglementation_agent = ReglementationAgent(config)
subsidy_agent = SubsidyAgent(config)

# 1. Recherche de la parcelle
parcels = geo_agent.search_parcels(commune="Saint-Martin-de-Crau", section="B")
target_parcel = parcels["parcels"][0]["id"]

# 2. Analyse du potentiel forestier
potential = geo_agent.analyze_potential(parcel_id=target_parcel)

# 3. Vérification de la réglementation applicable
compliance = reglementation_agent.check_compliance(
    parcels=[target_parcel],
    project_type="reboisement",
    species=["pinus_halepensis", "quercus_ilex"],
    area_ha=potential["area_ha"]
)

# 4. Recherche de subventions adaptées
subsidies = subsidy_agent.search_subsidies(
    project_type="reboisement",
    region="Provence-Alpes-Côte d'Azur",
    owner_type="private"
)

# 5. Analyse d'éligibilité aux subventions
eligible_subsidies = []
for subsidy in subsidies:
    eligibility = subsidy_agent.analyze_eligibility(
        project={
            "type": "reboisement",
            "area_ha": potential["area_ha"],
            "species": ["pinus_halepensis", "quercus_ilex"],
            "location": target_parcel
        },
        subsidy_id=subsidy["id"]
    )
    if eligibility["eligible"]:
        eligible_subsidies.append(subsidy)

# 6. Génération d'un rapport complet
report = {
    "parcel": target_parcel,
    "forestry_potential": potential,
    "regulatory_compliance": compliance,
    "eligible_subsidies": eligible_subsidies
}

print(f"Rapport complet pour la parcelle {target_parcel}:")
print(f"Potentiel forestier: {potential['potential_score']} ({potential['potential_class']})")
print(f"Conformité réglementaire: {'Conforme' if compliance['compliant'] else 'Non conforme'}")
print(f"Nombre de subventions éligibles: {len(eligible_subsidies)}")
```

### Intégration GeoAgent et ClimateAnalyzer

Cet exemple montre comment combiner l'agent de géotraitement avec l'analyseur climatique :

```python
from forestai.agents.geo_agent import GeoAgent
from forestai.core.domain.services import ClimateAnalyzer
from forestai.core.utils.config import Config
import geopandas as gpd
from shapely.geometry import shape
import json

# Chargement de la configuration
config = Config().load_config(".env")

# Initialisation des agents
geo_agent = GeoAgent(config)
climate_analyzer = ClimateAnalyzer()

# 1. Obtenir la géométrie d'une parcelle
parcel_data = geo_agent.get_parcel_geometry(parcel_id="13097000B0012")
geometry = shape(json.loads(parcel_data["geometry"]))

# 2. Analyser le potentiel forestier
forestry_potential = geo_agent.analyze_potential(geometry=geometry.wkt)

# 3. Obtenir la zone climatique
climate_zone = climate_analyzer.get_climate_zone(geometry)

# 4. Obtenir les recommandations d'espèces pour le climat actuel
current_recommendations = climate_analyzer.recommend_species(
    geometry=geometry, 
    scenario="current"
)

# 5. Obtenir les recommandations d'espèces pour le climat futur
future_recommendations = climate_analyzer.recommend_species(
    geometry=geometry, 
    scenario="2050_rcp45"
)

# 6. Filtrer les recommandations selon les contraintes du terrain
terrain_constraints = forestry_potential.get("constraints", [])
filtered_recommendations = []

for species in current_recommendations:
    compatible = True
    
    # Vérifier la compatibilité avec les contraintes de terrain
    if "sol_sec" in terrain_constraints and species["drought_tolerance"] < 3:
        compatible = False
    if "pente_forte" in terrain_constraints and species["erosion_control"] < 3:
        compatible = False
    if "gel_frequent" in terrain_constraints and species["frost_resistance"] < 3:
        compatible = False
        
    if compatible:
        filtered_recommendations.append(species)

print(f"Zone climatique actuelle: {climate_zone['name']}")
print(f"Nombre d'espèces recommandées (climat actuel): {len(current_recommendations)}")
print(f"Nombre d'espèces recommandées (climat 2050): {len(future_recommendations)}")
print(f"Nombre d'espèces compatibles avec le terrain: {len(filtered_recommendations)}")
```

## Exemples spécifiques par cas d'usage

### 1. Diagnostic forestier pour une nouvelle acquisition

```python
# Ce script génère un diagnostic forestier complet pour une nouvelle acquisition
from forestai.agents.geo_agent import GeoAgent
from forestai.core.domain.services import ClimateAnalyzer, ForestDiagnosticService
from forestai.core.utils.config import Config

# Initialisation
config = Config().load_config(".env")
geo_agent = GeoAgent(config)
climate_analyzer = ClimateAnalyzer()
diagnostic_service = ForestDiagnosticService()

# Identifier la parcelle
parcel_id = "13097000B0012"  # Exemple de code parcellaire

# Générer le diagnostic complet
diagnostic = diagnostic_service.generate_complete_diagnostic(
    parcel_id=parcel_id,
    include_climate_analysis=True,
    include_economic_analysis=True
)

# Sauvegarder le diagnostic au format PDF
diagnostic_service.export_diagnostic(
    diagnostic=diagnostic,
    output_format="pdf",
    output_path="outputs/diagnostics/diagnostic_parcelle_13097000B0012.pdf"
)
```

### 2. Recherche des meilleures parcelles à acquérir dans une région

```python
# Ce script identifie les meilleures parcelles forestières à acquérir dans une région
from forestai.agents.geo_agent import GeoAgent
from forestai.core.domain.services import ParcelRankingService
from forestai.core.utils.config import Config

# Initialisation
config = Config().load_config(".env")
geo_agent = GeoAgent(config)
ranking_service = ParcelRankingService()

# Définir les critères de recherche
search_criteria = {
    "region": "Provence-Alpes-Côte d'Azur",
    "min_area_ha": 5,
    "max_area_ha": 50,
    "max_slope": 15,  # pente maximale en degrés
    "min_forest_potential": 0.7,  # potentiel forestier minimum (0-1)
    "price_data_available": True  # uniquement les parcelles avec données de prix
}

# Rechercher et classer les parcelles
ranked_parcels = ranking_service.rank_parcels_for_acquisition(
    criteria=search_criteria,
    limit=20,
    order_by="roi"  # Classement par retour sur investissement
)

# Exporter les résultats
import pandas as pd
df = pd.DataFrame(ranked_parcels)
df.to_excel("outputs/acquisitions/meilleures_parcelles_PACA.xlsx", index=False)
```

### 3. Plan de reboisement post-incendie

```python
# Ce script crée un plan de reboisement après un incendie
from forestai.agents.geo_agent import GeoAgent
from forestai.core.domain.services import ClimateAnalyzer, ReforestationPlanService
from forestai.core.utils.config import Config

# Initialisation
config = Config().load_config(".env")
geo_agent = GeoAgent(config)
climate_analyzer = ClimateAnalyzer()
reforestation_service = ReforestationPlanService()

# Définir la zone incendiée (plusieurs parcelles)
fire_area_parcels = ["13097000B0012", "13097000B0013", "13097000B0014"]

# Générer un plan de reboisement
reforestation_plan = reforestation_service.generate_plan(
    parcels=fire_area_parcels,
    fire_intensity_data="data/fire_intensity_map.tif",  # Carte d'intensité de l'incendie
    prioritize_fire_resistant_species=True,
    climate_scenario="2050_rcp45"  # Prendre en compte le changement climatique
)

# Exporter le plan
reforestation_service.export_plan(
    plan=reforestation_plan,
    output_formats=["pdf", "html", "shp"],
    output_dir="outputs/reforestation_plans/incendie_2023"
)
```

## Exemples d'utilisation de l'API

Si vous avez activé l'API REST de ForestAI, vous pouvez l'utiliser comme suit :

### Analyse du potentiel forestier via l'API REST

```python
import requests
import json

# Configuration
api_url = "http://localhost:8000"

# Analyser le potentiel forestier d'une parcelle
response = requests.post(
    f"{api_url}/geo/analyze_potential",
    json={"parcel_id": "13097000B0012"}
)

# Vérifier la réponse
if response.status_code == 200:
    potential = response.json()
    print(f"Potentiel forestier: {potential['potential_score']} ({potential['potential_class']})")
    print(f"Contraintes: {potential['constraints']}")
    print(f"Opportunités: {potential['opportunities']}")
else:
    print(f"Erreur: {response.status_code}")
    print(response.text)
```

### Recherche de subventions via l'API REST

```python
import requests

# Configuration
api_url = "http://localhost:8000"

# Rechercher des subventions
response = requests.post(
    f"{api_url}/subsidies/search",
    json={
        "project_type": "reboisement",
        "region": "Occitanie",
        "owner_type": "private"
    }
)

# Afficher les subventions trouvées
if response.status_code == 200:
    subsidies = response.json()
    print(f"Nombre de subventions trouvées: {len(subsidies)}")
    for subsidy in subsidies:
        print(f"- {subsidy['title']} ({subsidy['id']})")
        print(f"  Montant: {subsidy['amount']}")
        print(f"  Date limite: {subsidy['deadline']}")
        print()
else:
    print(f"Erreur: {response.status_code}")
    print(response.text)
```
