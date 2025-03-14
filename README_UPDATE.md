# Mise à jour du README principal

Cette mise à jour vise à intégrer les nouvelles fonctionnalités du SubsidyAgent dans le README principal du projet. Ces modifications devraient être fusionnées avec le README.md existant.

## Nouveaux modules et fonctionnalités

### Agent de Subventions (SubsidyAgent)

L'agent de subventions (SubsidyAgent) est désormais pleinement implémenté et intégré au projet ForestAI. Cet agent permet :

- **Veille sur les aides disponibles** via différents scrapers spécialisés
- **Analyse d'éligibilité** des projets aux différentes subventions
- **Génération automatique de dossiers de demande** aux formats PDF, DOCX et HTML
- **Stockage et mise à jour** des informations sur les subventions
- **Recommandation de subventions** adaptées aux parcelles et projets spécifiques

#### Architecture de l'agent de subventions

```
forestai/agents/subsidy_agent/
├── __init__.py                    # Point d'entrée du package
├── subsidy_agent.py               # Implémentation principale de l'agent
├── eligibility.py                 # Système d'analyse d'éligibilité
├── scrapers/                      # Scrapers de subventions
│   ├── __init__.py
│   ├── base_scraper.py            # Classe de base pour tous les scrapers
│   ├── france_relance_scraper.py  # Scraper pour les aides France Relance
│   ├── europe_invest_scraper.py   # Scraper pour les aides européennes
│   └── regional_scraper.py        # Scraper pour les aides régionales
└── document_generation/           # Génération de documents
    ├── __init__.py
    ├── document_generator.py      # Coordinateur des générateurs
    ├── pdf_generator.py           # Génération de PDF
    ├── html_generator.py          # Génération de HTML
    └── docx_generator.py          # Génération de DOCX
```

#### Intégration avec les autres agents

L'agent de subventions peut être utilisé conjointement avec le GeoAgent et le ReglementationAgent pour fournir une analyse complète des parcelles forestières :

1. Le **GeoAgent** fournit les caractéristiques géographiques de la parcelle
2. Le **ReglementationAgent** vérifie les contraintes légales et réglementaires
3. Le **SubsidyAgent** identifie les subventions disponibles et évalue l'éligibilité

Un exemple d'intégration est disponible dans `examples/subsidy_geo_integration_example.py`.

## Nouveaux exemples

De nouveaux exemples ont été ajoutés pour démontrer l'utilisation de l'agent de subventions :

- `examples/subsidy_agent_example.py` : Utilisation basique de l'agent de subventions
- `examples/subsidy_eligibility_example.py` : Analyse d'éligibilité pour différents types de projets
- `examples/document_generation_example.py` : Génération de dossiers de demande
- `examples/subsidy_geo_integration_example.py` : Intégration avec le GeoAgent

## Nouvelle documentation

Une nouvelle documentation a été ajoutée pour détailler l'agent de subventions et son utilisation :

- `docs/SubsidyAgent.md` : Documentation complète de l'agent de subventions
- `docs/SubsidyDocGeneration.md` : Guide d'utilisation du système de génération de documents

## État d'avancement du projet

La phase 3 a progressé avec l'implémentation complète de l'agent de subventions :

- [x] Implémentation du crawler de subventions
- [x] Implémentation du système d'analyse d'éligibilité
- [x] Implémentation du générateur de dossiers
- [x] Intégration avec le GeoAgent

## Prochaines étapes

Les prochaines étapes prioritaires sont :

1. **Amélioration de l'agent de subventions**
   - [ ] Ajout de sources de subventions supplémentaires
   - [ ] Amélioration de la précision de l'analyse d'éligibilité
   - [ ] Intégration de données sur les aides dynamiques (API)

2. **Développement du DiagnosticAgent**
   - [ ] Système d'analyse forestière
   - [ ] Intégration avec les données géospatiales et climatiques
   - [ ] Génération de rapports de diagnostic

3. **Interface utilisateur**
   - [ ] Conception des wireframes
   - [ ] Implémentation du frontend FastAPI
   - [ ] Tests d'acceptation utilisateur
