# API REST ForestAI

Cette documentation détaille l'API REST de ForestAI qui permet d'accéder aux fonctionnalités des agents forestiers via des requêtes HTTP.

## Informations générales

- **URL de base** : `http://localhost:8000` (par défaut)
- **Format des réponses** : JSON
- **Format des erreurs** : 
  ```json
  {
    "status": "error",
    "error_message": "Description détaillée de l'erreur"
  }
  ```
- **Format des succès** : 
  ```json
  {
    "status": "success",
    "result": { ... } // Les données spécifiques à chaque endpoint
  }
  ```

## Démarrage du serveur

Pour démarrer le serveur d'API, exécutez :

```bash
python api_server.py [--host HOST] [--port PORT] [--reload]
```

Options :
- `--host` : Hôte d'écoute (défaut: 0.0.0.0)
- `--port` : Port d'écoute (défaut: 8000)
- `--reload` : Active le rechargement automatique (utile en développement)

## Documentation OpenAPI

Une fois le serveur démarré, la documentation interactive OpenAPI est disponible à l'adresse :

```
http://localhost:8000/docs
```

## Endpoints disponibles

### Informations générales

#### Statut de l'API

```
GET /status
```

Retourne l'état opérationnel de l'API et la disponibilité des agents.

**Exemple de réponse :**

```json
{
  "status": "operational",
  "agents": {
    "geo_agent": "available",
    "subsidy_agent": "available",
    "reglementation_agent": "planned"
  },
  "api_version": "0.1.0"
}
```

### Endpoints GeoAgent

#### Recherche de parcelles

```
POST /geo/search
```

Recherche des parcelles cadastrales en fonction de critères spécifiés.

**Corps de la requête :**

```json
{
  "commune": "Saint-Martin-de-Crau",  // Requis: nom ou code INSEE de la commune
  "section": "B",                     // Optionnel: section cadastrale
  "numero": "0012"                    // Optionnel: numéro de parcelle
}
```

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": {
    "parcels": [
      {
        "id": "13097000B0012",
        "commune": "Saint-Martin-de-Crau",
        "section": "B",
        "numero": "0012",
        "area_m2": 152340,
        "address": "Route des Marais"
      },
      // ... autres parcelles
    ]
  }
}
```

#### Analyse de parcelle

```
POST /geo/analyze
```

Analyse une parcelle pour évaluer son potentiel forestier et autres caractéristiques.

**Corps de la requête :**

```json
{
  "parcel_id": "13097000B0012",  // Requis: identifiant de la parcelle
  "analyses": [                   // Optionnel: types d'analyses à effectuer
    "terrain", 
    "forest_potential",
    "risks"
  ]
}
```

Types d'analyses disponibles :
- `basic` : Informations de base (surface, géométrie)
- `terrain` : Analyse du terrain (pente, élévation)
- `forest_potential` : Analyse du potentiel forestier
- `climate` : Analyse climatique
- `risks` : Analyse des risques naturels
- `complete` : Toutes les analyses ci-dessus

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": {
    "parcel_id": "13097000B0012",
    "area_ha": 15.234,
    "average_elevation": 42.5,
    "average_slope": 8.3,
    "soil_type": "argileux",
    "forest_potential": {
      "score": 78,
      "recommended_species": ["pinus_pinea", "quercus_ilex", "cedrus_atlantica"]
    },
    "risks": [
      {
        "type": "fire",
        "level": "medium",
        "details": "Zone à risque incendie modéré"
      },
      {
        "type": "drought",
        "level": "high",
        "details": "Zone sensible à la sécheresse"
      }
    ]
  }
}
```

### Endpoints SubsidyAgent

#### Recherche de subventions

```
POST /subsidies/search
```

Recherche des subventions disponibles pour un projet forestier.

**Corps de la requête :**

```json
{
  "project_type": "reboisement",                  // Requis: type de projet
  "region": "Provence-Alpes-Côte d'Azur",         // Optionnel: région concernée
  "owner_type": "private",                        // Optionnel: type de propriétaire
  "parcel_id": "13097000B0012"                    // Optionnel: ID de parcelle pour enrichissement
}
```

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": [
    {
      "id": "fr_reforest_2025",
      "title": "Aide au reboisement France Relance 2025",
      "organization": "Ministère de l'Agriculture",
      "deadline": "2025-12-31",
      "funding_rate": 60,
      "amount_per_ha": 3500,
      "max_funding": 200000,
      "url": "https://www.francerelance.gouv.fr/aides-forestieres",
      "eligibility_summary": "Reboisement de parcelles dégradées ou peu productives"
    },
    // ... autres subventions
  ]
}
```

#### Analyse d'éligibilité

```
POST /subsidies/eligibility
```

Analyse l'éligibilité d'un projet à une subvention spécifique.

**Corps de la requête :**

```json
{
  "project": {
    "type": "reboisement",
    "area_ha": 5.2,
    "species": ["pinus_pinea", "quercus_suber"],
    "region": "Provence-Alpes-Côte d'Azur",
    "location": "13097000B0012",
    "owner_type": "private",
    "planting_density": 1200,
    "has_management_document": true,
    "maintenance_commitment_years": 5,
    "certifications": ["PEFC"]
  },
  "subsidy_id": "fr_reforest_2025"
}
```

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": {
    "subsidy_id": "fr_reforest_2025",
    "subsidy_title": "Aide au reboisement France Relance 2025",
    "eligible": true,
    "conditions": [
      {
        "condition": "Surface minimale",
        "satisfied": true,
        "details": "Surface de 5.2 ha > minimum de 1 ha"
      },
      {
        "condition": "Espèces éligibles",
        "satisfied": true,
        "details": "Toutes les espèces sont éligibles"
      },
      {
        "condition": "Document de gestion",
        "satisfied": true,
        "details": "Document de gestion forestière présent"
      }
    ],
    "funding_details": {
      "base_amount": 18200,
      "bonus_amount": 2600,
      "total_amount": 20800,
      "details": {
        "base_calculation": "5.2 ha × 3500 €/ha",
        "bonus_details": [
          {
            "type": "certification",
            "rate": 10,
            "amount": 1820
          },
          {
            "type": "diversity",
            "rate": 5,
            "amount": 780
          }
        ]
      }
    }
  }
}
```

#### Génération de documents de demande

```
POST /subsidies/application
```

Génère des documents de demande de subvention dans les formats spécifiés.

**Corps de la requête :**

```json
{
  "project": {
    "type": "reboisement",
    "area_ha": 5.2,
    "species": ["pinus_pinea", "quercus_suber"],
    "region": "Provence-Alpes-Côte d'Azur",
    "location": "13097000B0012",
    "owner_type": "private",
    "planting_density": 1200
  },
  "subsidy_id": "fr_reforest_2025",
  "applicant": {
    "name": "Domaine Forestier du Sud",
    "address": "Route des Pins 13200 Arles",
    "contact": "contact@domaineforestier.fr",
    "siret": "12345678900012",
    "contact_name": "Jean Dupont",
    "contact_phone": "0612345678"
  },
  "output_formats": ["pdf", "html"]
}
```

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": {
    "pdf": "/outputs/applications/fr_reforest_2025_20250315_123456.pdf",
    "html": "/outputs/applications/fr_reforest_2025_20250315_123456.html"
  }
}
```

## Exemples d'utilisation

Un exemple complet d'utilisation de l'API est disponible dans le script `examples/api_usage_example.py`. Ce script montre comment :

1. Vérifier le statut de l'API
2. Rechercher des parcelles
3. Analyser une parcelle
4. Rechercher des subventions adaptées
5. Analyser l'éligibilité d'un projet
6. Générer des documents de demande

Pour l'exécuter :

```bash
python examples/api_usage_example.py
```

## Gestion des erreurs

L'API retourne des codes HTTP standards :

- `200 OK` : Requête traitée avec succès
- `400 Bad Request` : Paramètres manquants ou invalides
- `404 Not Found` : Ressource non trouvée
- `500 Internal Server Error` : Erreur côté serveur

En cas d'erreur, le corps de la réponse contiendra :

```json
{
  "status": "error",
  "error_message": "Description détaillée de l'erreur"
}
```

## Notes de sécurité

Cette API est conçue pour un usage en environnement contrôlé et ne contient pas d'authentification ni d'autorisation par défaut. Pour une utilisation en production, il est recommandé d'ajouter :

- TLS (HTTPS)
- Authentification (JWT, OAuth2, etc.)
- Rate limiting
- Validation des entrées plus stricte
