# Agent de Réglementation Forestière

## Vue d'ensemble
L'agent de réglementation forestière est un expert du Code Forestier et des autres réglementations applicables à la gestion et l'exploitation des forêts. Il fournit des analyses et recommandations juridiques pour assurer la conformité des projets forestiers avec le cadre légal français et européen.

## Domaines d'expertise

### Code Forestier
- Interprétation et application des articles du Code Forestier
- Règles de défrichement et autorisations nécessaires
- Obligations de reboisement et compensations
- Documents de gestion durable (PSG, CBPS, RTG)
- Statuts de protection des forêts (forêts de protection, espaces boisés classés)

### Autres réglementations
- Réglementation environnementale (étude d'impact, zones humides, espèces protégées)
- Natura 2000 et autres zonages environnementaux
- Plan Local d'Urbanisme (PLU) et règles d'urbanisme applicables aux espaces forestiers
- Fiscalité forestière (DEFI Forêt, IFI, exonérations)
- Dispositifs d'aides à l'investissement forestier

## Fonctionnalités principales

### Analyse réglementaire
- Évaluation de la conformité réglementaire d'un projet forestier
- Identification des contraintes légales sur une parcelle
- Détermination des autorisations et démarches administratives requises

### Accompagnement juridique
- Génération de fiches synthétiques sur les obligations réglementaires
- Assistance à la préparation des dossiers administratifs
- Veille juridique sur les évolutions législatives

### Optimisation juridique
- Recommandations pour maximiser les avantages fiscaux
- Stratégies de conformité avec impact minimal sur le projet
- Identification des opportunités d'aides et subventions

## Intégration avec les autres agents

- Avec **GeoAgent**: Croisement des données cadastrales avec les zonages réglementaires
- Avec **DiagnosticAgent**: Vérification de la conformité des préconisations sylvicoles
- Avec **DocumentAgent**: Intégration des clauses légales dans les contrats et cahiers des charges
- Avec **SubventionAgent**: Validation de l'éligibilité juridique aux dispositifs d'aide

## Utilisation

```bash
# Vérifier la conformité réglementaire d'une parcelle
python run.py --agent reglementation --action check_compliance --params '{"parcels": ["123456789"], "project_type": "boisement"}'

# Générer une fiche réglementaire pour un projet forestier
python run.py --agent reglementation --action generate_legal_brief --params '{"project_type": "coupe", "location": "Aquitaine", "area_ha": 12.5}'

# Obtenir les règles spécifiques à une région
python run.py --agent reglementation --action get_regional_rules --params '{"region": "Nouvelle-Aquitaine"}'
```

## Base de connaissances
L'agent s'appuie sur une base de connaissances constamment mise à jour qui comprend:

- Le Code Forestier consolidé (version actuelle)
- Les arrêtés préfectoraux par région et département
- Les circulaires et instructions techniques de l'ONF et du Ministère
- La jurisprudence pertinente en matière forestière
- Les guides pratiques et doctrine administrative

## Développement futur
- Intégration d'un système expert basé sur des règles pour l'analyse automatique des cas complexes
- Mise en place d'un système d'alerte sur les changements réglementaires impactant les projets en cours
- Développement d'une interface de dialogue en langage naturel pour les questions juridiques