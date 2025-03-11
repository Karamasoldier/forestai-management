# ForestAI - Gestion Forestière Intelligente

Système multi-agents pour l'automatisation et l'optimisation de la gestion forestière.

## Objectifs

- Identifier les parcelles à potentiel forestier via géotraitement
- Automatiser la prospection de subventions et compensations carbone
- Générer des diagnostics forestiers et plans de gestion
- Créer automatiquement des documents administratifs (cahiers des charges, contrats)
- Centraliser les données des exploitants forestiers
- Assurer la conformité réglementaire avec le Code Forestier

## Architecture des agents

- **GeoAgent** : Analyse géospatiale des parcelles et propriétés (utilise des données locales)
- **ReglementationAgent** : Expert du Code Forestier et des réglementations applicables
- **SubventionAgent** : Veille sur les aides disponibles
- **DiagnosticAgent** : Analyse des données terrain
- **DocumentAgent** : Génération de documents administratifs
- **ExploitantAgent** : Base de données des opérateurs forestiers

## Données géographiques

Suite à l'arrêt de la génération de clés API Geoservices par l'IGN début 2024, ForestAI fonctionne avec des données géographiques téléchargées localement dans le dossier `data/raw/`. Pour plus d'informations, consultez la [documentation du GeoAgent](docs/GeoAgent.md).

## Installation

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos clés API et chemins de données
```

## Téléchargement des données

Les données géographiques doivent être téléchargées manuellement depuis les sources suivantes:

- [Données cadastrales](https://cadastre.data.gouv.fr/datasets/cadastre-etalab)
- [BD TOPO IGN](https://geoservices.ign.fr/bdtopo)
- [Occupation des sols (Corine Land Cover)](https://www.data.gouv.fr/fr/datasets/corine-land-cover-occupation-des-sols-en-france/)
- [Modèle Numérique de Terrain (MNT)](https://geoservices.ign.fr/rgealti)

Placez les données téléchargées dans les dossiers appropriés définis dans le fichier `.env`.

## Agents et documentation

- [Agent de géotraitement (GeoAgent)](docs/GeoAgent.md)
- [Agent de réglementation forestière](docs/ReglementationAgent.md)

## Utilisation

```bash
# Lancer le système complet
python run.py

# Utiliser un agent spécifique
python run.py --agent geoagent

# Rechercher des parcelles dans une commune spécifique
python run.py --agent geoagent --action search_parcels --params '{"commune": "Saint-Martin-de-Crau", "section": "B"}'

# Vérifier la conformité réglementaire d'une parcelle
python run.py --agent reglementation --action check_compliance --params '{"parcels": ["123456789"], "project_type": "boisement"}'
```

## Roadmap

- [x] Architecture de base du système
- [x] Implémentation de l'agent de géotraitement avec données locales
- [ ] Implémentation de l'agent de réglementation forestière
- [ ] Implémentation de l'agent de subventions
- [ ] Implémentation de l'agent de diagnostic
- [ ] Interface utilisateur
- [ ] Déploiement cloud

## Licence

Ce projet est sous licence MIT.
