# Agent de Réglementation Forestière (ReglementationAgent)

L'agent de réglementation forestière est responsable de l'analyse de conformité réglementaire des projets forestiers selon le Code Forestier français et d'autres réglementations environnementales applicables.

## Fonctionnalités

- Vérification de la conformité réglementaire des projets forestiers
- Identification des autorisations nécessaires pour différents types de projets
- Génération de rapports de conformité détaillés (JSON, TXT, HTML)
- Proposition de recommandations pour la mise en conformité
- Vérification des protections spécifiques (zones humides, Natura 2000, etc.)
- Recherche de réglementations par mots-clés

## Architecture

Le `ReglementationAgent` s'appuie sur deux services de domaine principaux :

1. **RegulatoryFrameworkService** : Gère le chargement, la recherche et le filtrage des réglementations forestières.
2. **ComplianceCheckerService** : Vérifie la conformité des projets et génère des recommandations.

Cette architecture modulaire facilite la maintenance et l'extension des fonctionnalités.

```
┌─────────────────────────┐
│  ReglementationAgent    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ComplianceCheckerService │◄────┐
└───────────┬─────────────┘     │
            │                   │
            ▼                   │
┌─────────────────────────┐     │
│RegulatoryFrameworkService├────┘
└─────────────────────────┘
```

## Installation et Configuration

### Prérequis

- Python 3.8 ou supérieur
- Modules requis: voir `requirements.txt`
- Dossier de données avec les réglementations (créé automatiquement si absent)

### Configuration

Les réglementations sont stockées dans le dossier `data/reglementation` au format JSON. Un ensemble de réglementations d'exemple est automatiquement créé si ce fichier n'existe pas.

## Utilisation

### Initialisation de l'agent

```python
from forestai.agents.reglementation_agent import ReglementationAgent

# Configuration minimale
config = {
    "data_path": "./data",
    "output_path": "./data/outputs"
}

# Créer l'agent
agent = ReglementationAgent(config)
```

### Vérification de conformité d'un projet

```python
# Vérifier la conformité d'un projet de défrichement
result = agent.check_compliance(
    parcels=["123456789", "987654321"],  # Identifiants de parcelles
    project_type="defrichement",         # Type de projet
    params={                             # Paramètres additionnels
        "zone_humide": True,
        "natura_2000": False
    }
)

# Accéder aux résultats
print(f"Conforme: {result['overall_compliant']}")
print(f"Réglementations non conformes: {result['compliance_summary']['non_compliant']}")

# Obtenir des recommandations
for rec in result['recommendations']:
    print(f"- {rec['issue']}: {rec['action']}")
```

### Obtenir les autorisations nécessaires

```python
# Identifier les autorisations nécessaires pour un projet
authorizations = agent.get_required_authorizations(
    project_type="boisement",
    area=30.0,                # Surface en hectares
    region="Aquitaine"        # Région administrative (optionnel)
)

# Afficher les autorisations
for auth in authorizations:
    print(f"- {auth['description']}")
    print(f"  Référence: {auth['reference']}")
    print(f"  Autorité: {auth['authority']}")
```

### Génération de rapports formatés

```python
# Générer un rapport au format HTML
html_report = agent.generate_compliance_report(result, "html")

# Sauvegarder le rapport
with open("rapport_conformite.html", "w", encoding="utf-8") as f:
    f.write(html_report)

# Formats disponibles: "json", "txt", "html"
```

### Vérification des protections des eaux

```python
# Vérifier si des parcelles sont en zone de protection des eaux
water_protection = agent.check_parcels_water_protection(
    parcel_ids=["123456789", "987654321"]
)

# Nombre de parcelles protégées
print(f"Parcelles protégées: {water_protection['protected_parcels']}")

# Détails pour chaque parcelle
for result in water_protection['parcel_results']:
    print(f"Parcelle {result['parcel_id']}: {'Protégée' if result['is_water_protected'] else 'Non protégée'}")
    
    # Afficher les détails de protection si présents
    for protection in result['protection_details']:
        print(f"- {protection['name']}: {protection['description']}")
```

### Recherche de réglementations

```python
# Rechercher des réglementations par mot-clé
regulations = agent.search_regulation("zone humide")

# Afficher les résultats
for reg in regulations:
    print(f"- {reg['id']}: {reg['name']}")
    print(f"  {reg['description']}")
    print(f"  Référence: {reg['reference_text']}")
```

## Communication Inter-agents

L'agent de réglementation peut communiquer avec d'autres agents, notamment le GeoAgent pour obtenir des informations sur les parcelles.

### Utilisation du Message Bus

```python
# Activer la communication inter-agents
agent = ReglementationAgent(config, use_messaging=True)

# Le message bus est automatiquement utilisé pour les opérations nécessitant
# des données de parcelles
result = agent.check_compliance(parcels=["123456789"], project_type="boisement")
```

### Écoute des événements

L'agent s'abonne automatiquement aux événements suivants :
- `PROJECT_CREATED` : Déclenche une vérification automatique de conformité
- `PARCEL_ANALYZED` : Met à jour les données de parcelle en cache
- `COMPLIANCE_CHECK_REQUESTED` : Répond aux demandes de vérification

## Structure des Données Réglementaires

Les réglementations sont structurées comme suit :

```json
{
  "id": "CF-ART-L341-1",
  "name": "Défrichement - Autorisation préalable",
  "description": "Nul ne peut défricher sans autorisation préalable.",
  "applicable_regions": ["*"],
  "project_types": ["defrichement"],
  "effective_date": "2001-07-11",
  "requirements": [
    {
      "id": "CF-ART-L341-1-R1",
      "description": "Tout défrichement nécessite une autorisation préalable",
      "condition": "project_type == 'defrichement'",
      "category": "autorisation",
      "reference": "Article L341-1 du Code Forestier",
      "severity": "high"
    }
  ],
  "reference_text": "Article L341-1 du Code Forestier",
  "authority": "DDT/DDTM"
}
```

### Catégories d'exigences

Les exigences réglementaires sont classées par catégories :
- `autorisation` : Nécessite une autorisation préalable
- `compensation` : Exige des mesures de compensation
- `document` : Requiert un document spécifique
- `notification` : Demande une notification préalable
- `evaluation` : Nécessite une évaluation d'impact

### Conditions d'exigence

Les conditions sont exprimées en Python et évaluées avec un contexte incluant :
- `project_type` : Type de projet (boisement, reboisement, defrichement, etc.)
- `area` : Surface totale des parcelles
- `parcel_count` : Nombre de parcelles
- `parameters` : Paramètres additionnels fournis

## Extension des Réglementations

Vous pouvez ajouter de nouvelles réglementations ou mettre à jour celles existantes programmatiquement :

```python
from forestai.core.domain.models.regulation import Regulation, RegulatoryRequirement
from forestai.core.domain.services.regulatory_framework_service import RegulatoryFrameworkService

# Initialiser le service
service = RegulatoryFrameworkService("./data/reglementation")

# Créer une nouvelle réglementation
new_regulation = Regulation(
    id="CF-NEW-REG",
    name="Nouvelle réglementation",
    description="Description de la nouvelle réglementation",
    applicable_regions=["*"],
    project_types=["boisement", "reboisement"],
    effective_date=datetime.datetime.now(),
    requirements=[
        RegulatoryRequirement(
            id="CF-NEW-REG-R1",
            description="Description de l'exigence",
            condition="area > 10",
            threshold=10,
            category="notification",
            reference="Référence légale",
            severity="medium"
        )
    ],
    reference_text="Référence légale complète",
    authority="Autorité compétente"
)

# Ajouter la réglementation
service.add_regulation(new_regulation)
```

## Exemple Complet

Un exemple complet d'utilisation de l'agent est disponible dans `examples/reglementation_agent_example.py`.

## Intégration avec ForestAI

L'agent de réglementation s'intègre parfaitement avec les autres composants de ForestAI :

1. Le **GeoAgent** fournit les données des parcelles
2. Le **SubventionAgent** peut utiliser les analyses de conformité pour identifier les subventions applicables
3. Le **DocumentAgent** peut utiliser les rapports pour générer des documents administratifs

## Limitations actuelles

- Les conditions sont évaluées via `eval()`, ce qui impose des restrictions de sécurité
- Les règles régionales spécifiques nécessitent une mise à jour manuelle du fichier de réglementations
- L'intégration avec d'autres bases de données réglementaires n'est pas encore implémentée

## Roadmap

- Intégration de la base de données Legifrance pour les mises à jour automatiques
- Support des réglementations locales (PLU, chartes forestières, etc.)
- Interface graphique pour la gestion des réglementations
- Moteur de règles plus sophistiqué avec expressions régulières et arbres de décision
