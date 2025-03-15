# API Diagnostic et Analyse Sanitaire Forestière

Cette documentation détaille les endpoints de l'API REST ForestAI liés au diagnostic forestier et à l'analyse sanitaire. Ces fonctionnalités sont fournies par le DiagnosticAgent et le module HealthAnalyzer.

## Informations générales

- **Base URL** : `http://localhost:8000` (par défaut)
- **Format des réponses** : JSON (sauf pour les rapports qui peuvent être au format PDF, HTML ou TXT)
- **Endpoints accessibles** : `/diagnostic/*`

## Endpoints disponibles

### Générer un diagnostic forestier

```
POST /diagnostic/generate
```

Génère un diagnostic forestier complet pour une parcelle donnée, incluant optionnellement une analyse sanitaire.

**Corps de la requête :**

```json
{
  "parcel_id": "13097000B0012",
  "inventory_data": {
    "items": [
      {
        "species": "quercus_ilex",
        "diameter": 25.5,
        "height": 12.0,
        "health_status": "bon"
      }
    ],
    "area": 1.5,
    "date": "2025-03-01",
    "method": "placettes"
  },
  "include_health_analysis": true
}
```

**Paramètres :**
- `parcel_id` (requis) : Identifiant de la parcelle à analyser
- `inventory_data` (optionnel) : Données d'inventaire forestier
- `include_health_analysis` (optionnel, défaut=true) : Inclure l'analyse sanitaire dans le diagnostic

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": {
    "parcel_id": "13097000B0012",
    "parcel_data": {
      "area_ha": 15.234,
      "commune": "Saint-Martin-de-Crau",
      "section": "B",
      "numero": "0012",
      "geometry": { /* ... */ }
    },
    "potential": {
      "score": 78,
      "recommended_species": ["pinus_pinea", "quercus_ilex", "cedrus_atlantica"]
    },
    "climate": {
      "zone": "Méditerranéen",
      "annual_temp": 14.2,
      "annual_precip": 650
    },
    "species_recommendations": {
      "recommended_species": [
        {
          "species_name": "Quercus ilex",
          "common_name": "Chêne vert",
          "compatibility_score": 0.92,
          "climate_resilience": "high"
        }
      ]
    },
    "inventory": {
      "species_distribution": { "quercus_ilex": 1 },
      "density": 67,
      "volume": { "total": 2.45 }
    },
    "health": {
      "summary": "État sanitaire satisfaisant avec vigilance recommandée.",
      "overall_health_score": 7.5,
      "health_status": "Bon",
      "detected_issues": [
        {
          "id": "leaf_discoloration",
          "name": "Décoloration foliaire",
          "severity": 0.2
        }
      ],
      "recommendations": {
        "summary": "Surveillance sanitaire annuelle recommandée.",
        "priority_actions": [
          {
            "action": "Mise en place d'un système de surveillance sanitaire",
            "deadline": "Dans les 60 jours"
          }
        ]
      }
    },
    "timestamp": "2025-03-15T16:30:45.123Z"
  }
}
```

### Générer un plan de gestion forestière

```
POST /diagnostic/management-plan
```

Génère un plan de gestion forestière pour une parcelle, basé sur des objectifs spécifiques.

**Corps de la requête :**

```json
{
  "parcel_id": "13097000B0012",
  "goals": ["production", "resilience"],
  "horizon_years": 15,
  "use_existing_diagnostic": true
}
```

**Paramètres :**
- `parcel_id` (requis) : Identifiant de la parcelle
- `goals` (requis) : Liste des objectifs de gestion
- `horizon_years` (optionnel, défaut=10) : Horizon temporel du plan en années
- `use_existing_diagnostic` (optionnel, défaut=false) : Utiliser un diagnostic existant

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": {
    "parcel_id": "13097000B0012",
    "created_at": "2025-03-15T16:35:12.654Z",
    "horizon": {
      "start_year": 2025,
      "end_year": 2040,
      "duration_years": 15
    },
    "goals": ["production", "resilience"],
    "summary": "Plan de gestion forestière sur 15 ans avec focus sur production, resilience",
    "phases": [
      {
        "name": "Diagnostic et préparation",
        "year": 2025,
        "actions": [
          "Analyse complète du terrain",
          "Définition des zones d'intervention",
          "Planification des accès"
        ],
        "expected_outcomes": "Plan détaillé d'intervention"
      },
      {
        "name": "Plantation productive",
        "year": 2026,
        "actions": [
          "Plantation de Pinus pinea",
          "Mise en place de protections",
          "Planification des éclaircies"
        ],
        "expected_outcomes": "Établissement d'un peuplement productif"
      }
    ],
    "recommended_species": [
      {
        "species_name": "Pinus pinea",
        "common_name": "Pin parasol",
        "compatibility_score": 0.85
      }
    ],
    "estimated_costs": {
      "total": 75800,
      "per_hectare": 4975,
      "phase_breakdown": [
        {
          "phase": "Diagnostic initial",
          "cost": 3047,
          "details": "Diagnostic complet à 200€/ha sur 15.234 ha"
        }
      ]
    }
  }
}
```

### Effectuer une analyse sanitaire forestière

```
POST /diagnostic/health-analysis
```

Analyse l'état sanitaire d'un peuplement forestier à partir de données d'inventaire.

**Corps de la requête :**

```json
{
  "inventory_data": {
    "items": [
      {
        "species": "quercus_ilex",
        "diameter": 25.5,
        "height": 12.0,
        "health_status": "moyen",
        "notes": "Présence de taches foliaires"
      }
    ],
    "area": 1.5,
    "date": "2025-03-01",
    "method": "placettes"
  },
  "additional_symptoms": {
    "leaf_discoloration": 0.35,
    "observed_pests": ["bark_beetle"],
    "crown_thinning": 0.25
  },
  "parcel_id": "13097000B0012"
}
```

**Paramètres :**
- `inventory_data` (requis) : Données d'inventaire forestier
- `additional_symptoms` (optionnel) : Observations supplémentaires de symptômes
- `climate_data` (optionnel) : Données climatiques pour l'analyse de risques
- `parcel_id` (optionnel) : Identifiant de parcelle pour enrichissement des données

**Exemple de réponse :**

```json
{
  "status": "success",
  "result": {
    "summary": "État sanitaire moyen nécessitant une vigilance particulière.",
    "overall_health_score": 5.8,
    "health_status": "Moyen",
    "detected_issues": [
      {
        "id": "leaf_discoloration",
        "name": "Décoloration foliaire",
        "type": "physiological",
        "severity": 0.35,
        "confidence": 0.9,
        "affected_species": ["quercus_ilex"],
        "symptoms": ["discoloration", "wilting"],
        "description": "Décoloration anormale du feuillage, souvent liée au stress hydrique",
        "treatment_options": [
          {
            "name": "Suivi hydrique",
            "description": "Surveillance de l'humidité du sol et arrosage en période critique",
            "efficacy": 0.7
          }
        ]
      },
      {
        "id": "bark_beetle",
        "name": "Scolyte",
        "type": "pest",
        "severity": 0.6,
        "confidence": 0.85
      }
    ],
    "species_health": {
      "quercus_ilex": {
        "health_score": 5.8,
        "main_issues": ["leaf_discoloration", "bark_beetle"]
      }
    },
    "health_indicators": {
      "leaf_loss": 0.2,
      "crown_transparency": 0.25,
      "bark_damage": 0.0
    },
    "recommendations": {
      "summary": "Surveillance sanitaire semestrielle et traitement contre les scolytes recommandés.",
      "specific_recommendations": [
        {
          "issue_id": "bark_beetle",
          "issue_name": "Scolyte",
          "urgency": "Élevée",
          "treatments": [
            {
              "name": "Pièges à phéromones",
              "description": "Installation de pièges à phéromones pour capturer les scolytes adultes",
              "efficacy": 0.75
            }
          ]
        }
      ],
      "priority_actions": [
        {
          "action": "Installation de pièges à phéromones pour scolytes",
          "deadline": "Dans les 30 jours",
          "description": "Installation de pièges à phéromones pour capturer les scolytes adultes"
        }
      ]
    },
    "metadata": {
      "analysis_date": "2025-03-15T16:40:23.456Z",
      "analyzer_version": "1.0.0"
    }
  }
}
```

### Générer un rapport forestier

```
POST /diagnostic/report
```

Génère un rapport forestier au format demandé (PDF, HTML, TXT).

**Corps de la requête :**

```json
{
  "report_type": "diagnostic",
  "data_id": "13097000B0012",
  "format": "pdf",
  "health_detail_level": "standard"
}
```

**Paramètres :**
- `report_type` (requis) : Type de rapport (`diagnostic`, `management_plan`, `health`)
- `data_id` (requis) : Identifiant des données (parcelle, diagnostic, etc.)
- `format` (optionnel, défaut="pdf") : Format du rapport (`pdf`, `html`, `txt`)
- `health_detail_level` (optionnel, défaut="standard") : Niveau de détail sanitaire (`minimal`, `standard`, `complete`)

**Réponse :**

La réponse contient directement le fichier du rapport dans le format demandé.

## Niveaux de détail des rapports sanitaires

Le système supporte trois niveaux de détail pour les rapports sanitaires :

1. **minimal** : Uniquement les informations essentielles (score global, statut sanitaire, problèmes critiques)
2. **standard** : Niveau intermédiaire avec tous les problèmes détectés et recommandations principales
3. **complete** : Rapport détaillé avec toutes les données d'analyse, recommandations complètes et indicateurs

## Formats de rapport disponibles

- **PDF** : Format optimisé pour l'impression et le partage
- **HTML** : Format interactif pour consultation en ligne
- **TXT** : Format texte brut pour l'intégration avec d'autres systèmes

## Exemples d'utilisation

Un exemple complet d'utilisation de l'API est disponible dans le script `examples/api_health_analysis_example.py`. Ce script montre comment :

1. Vérifier le statut de l'API
2. Effectuer une analyse sanitaire
3. Générer un rapport sanitaire
4. Intégrer l'analyse sanitaire dans un diagnostic complet

Pour l'exécuter :

```bash
python examples/api_health_analysis_example.py
```

## Codes d'erreur

En cas d'erreur, l'API retourne un code HTTP approprié et un message détaillé :

- `400 Bad Request` : Paramètres manquants ou invalides
- `404 Not Found` : Ressource non trouvée (parcelle inexistante, etc.)
- `500 Internal Server Error` : Erreur interne du serveur

Exemple de réponse d'erreur :

```json
{
  "status": "error",
  "error_message": "Impossible de trouver la parcelle avec l'identifiant 13097000B9999"
}
```
