# DocumentAgent - Générateur de documents administratifs forestiers

Le DocumentAgent est un agent spécialisé dans la génération automatisée de documents administratifs liés à la gestion forestière. Il permet de créer des contrats, cahiers des charges, plans de gestion et autres documents administratifs avec un minimum d'effort, en s'appuyant sur des modèles prédéfinis et personnalisables.

## Fonctionnalités principales

- **Génération multi-format** : PDF, DOCX, HTML et TXT
- **Système de templates** : Templates personnalisables avec Jinja2
- **Enrichissement automatique des données** : Complétion intelligente des données manquantes
- **Validation des documents** : Vérification de conformité réglementaire
- **Stockage et gestion** : Organisation des documents par type, date et projet

## Types de documents supportés

### Contrats forestiers
- Contrats de vente de bois
- Contrats de travaux forestiers
- Baux forestiers
- Contrats de gestion déléguée

### Cahiers des charges
- Cahiers des charges pour travaux forestiers
- Cahiers des charges pour coupe de bois
- Cahiers des charges pour plantation

### Plans de gestion
- Plans simples de gestion (PSG)
- Documents d'aménagement
- Plans de gestion durable

### Documents administratifs
- Autorisations de coupe
- Déclarations fiscales forestières
- Demandes d'aide
- Notices d'impact environnemental
- Documents de certification forestière

## Architecture

Le DocumentAgent est organisé en plusieurs composants modulaires :

1. **Générateurs de documents spécifiques** :
   - `ContractGenerator` : Générateur de contrats
   - `SpecificationGenerator` : Générateur de cahiers des charges
   - `ManagementPlanGenerator` : Générateur de plans de gestion
   - `AdministrativeDocumentGenerator` : Générateur de documents administratifs

2. **Système de templates** :
   - `TemplateManager` : Gestion des templates Jinja2
   - Templates HTML personnalisables par type de document

3. **Validation et vérification** :
   - `DocumentValidator` : Validation des documents selon différents critères

4. **Stockage et organisation** :
   - `DocumentStorage` : Gestion du stockage des documents générés

## Utilisation

### Génération d'un contrat

```python
from forestai.agents.document_agent import DocumentAgent

agent = DocumentAgent()

# Données du contrat
contract_data = {
    "contract_type": "vente de bois",
    "title": "Contrat de Vente de Bois",
    "parties": [
        {
            "name": "Commune de Saint-Martin-de-Crau",
            "type": "vendor"
        },
        {
            "name": "Scierie Provençale SARL",
            "type": "buyer"
        }
    ],
    "parcels": [
        {
            "id": "13097000B0012",
            "area_ha": 15.5,
            "volume_estimated_m3": 450
        }
    ],
    "amount": "22 500 €",
    "special_conditions": "L'exploitation devra être réalisée en période sèche."
}

# Générer le contrat
result = agent.execute_action(
    "generate_contract",
    {
        "contract_data": contract_data,
        "formats": ["pdf", "docx"]
    }
)

# Récupérer les chemins des fichiers générés
if result["status"] == "success":
    files = result["result"]["files"]
    pdf_path = files["pdf"]
    docx_path = files["docx"]
```

### Génération d'un cahier des charges

```python
# Données du cahier des charges
spec_data = {
    "spec_type": "plantation forestière",
    "title": "Cahier des Charges - Travaux de Plantation",
    "client": {
        "name": "ONF - Direction Territoriale Méditerranée"
    },
    "parcels": [
        {
            "id": "13097000B0012",
            "area_ha": 8.3,
            "description": "Parcelle à reboiser suite à un incendie"
        }
    ],
    "species": [
        {
            "name": "Pinus halepensis",
            "french_name": "Pin d'Alep",
            "density": 1100,
            "percentage": 60
        }
    ]
}

# Générer le cahier des charges
result = agent.execute_action(
    "generate_specifications",
    {
        "spec_data": spec_data,
        "formats": ["pdf"]
    }
)
```

### Validation d'un document existant

```python
# Valider un document existant
result = agent.execute_action(
    "validate_document",
    {
        "document_path": "/path/to/document.pdf",
        "document_type": "contract",
        "strict_mode": True
    }
)

# Vérifier les résultats de validation
if result["status"] == "success":
    validation = result["result"]
    is_valid = validation["is_valid"]
    issues = validation["issues"]
    warnings = validation["warnings"]
```

## Personnalisation des templates

Les templates sont stockés dans le répertoire `forestai/agents/document_agent/templates/template_files/` et sont organisés par type de document :

- `contracts/` : Templates de contrats
- `specifications/` : Templates de cahiers des charges
- `management_plans/` : Templates de plans de gestion
- `administrative/` : Templates de documents administratifs

Chaque template est composé de deux fichiers :
1. Un fichier de définition (YAML/JSON) décrivant les variables et métadonnées
2. Un fichier HTML contenant le template Jinja2

Pour créer un nouveau template :

```python
from forestai.agents.document_agent.templates import TemplateManager
from forestai.agents.document_agent.models.document_models import DocumentType

# Initialiser le gestionnaire de templates
template_manager = TemplateManager()

# Créer un nouveau template
template_manager.create_template_skeleton(
    template_id="contract_custom",
    document_type=DocumentType.CONTRACT,
    name="Contrat Personnalisé",
    description="Template personnalisé pour des contrats spécifiques"
)
```

## Enrichissement des données

Le DocumentAgent enrichit automatiquement les données fournies pour compléter les informations manquantes :

- Génération de références et numéros de document
- Ajout de la date actuelle si non fournie
- Création de structures par défaut (clauses, sections, etc.)
- Enrichissement des données entre parties liées

## Intégration avec les autres agents

Le DocumentAgent s'intègre avec les autres agents du système ForestAI :

- **GeoAgent** : Récupération des données de parcelles pour les documents
- **ReglementationAgent** : Validation de la conformité réglementaire des documents
- **SubsidyAgent** : Génération de documents de demande d'aide

## Exemples d'utilisation

Un exemple complet d'utilisation est disponible dans le script `examples/document_agent_example.py`. Ce script montre comment :

1. Générer différents types de documents
2. Utiliser des formats multiples (PDF, DOCX, HTML)
3. Personnaliser les données et options de génération

Pour l'exécuter :

```bash
python examples/document_agent_example.py
```

## Limitations actuelles

- Support limité pour les éléments complexes (tableaux imbriqués, graphiques)
- Les templates sont principalement en français
- Les documents générés peuvent nécessiter des ajustements manuels pour certains cas spécifiques

## Développements futurs

- Support multilingue des templates
- Intégration de signatures électroniques
- Interface utilisateur pour la création et l'édition de templates
- Reconnaissance de documents existants pour extraction de données
