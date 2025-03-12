## Intégration des données Climessences

### Contexte
[Climessences](https://climessences.fr/) est un outil développé par le CNPF et l'ONF pour aider au choix des essences forestières en contexte de changement climatique.

### Recommandations d'intégration
1. **Contact direct** : Contacter le CNPF ou l'ONF pour obtenir un accès aux données.
2. **Fiches espèces** : Intégrer manuellement les informations des fiches espèces dans le `DiagnosticAgent`.
3. **Critères d'évaluation** : Utiliser le modèle IKS (Indice de Compatibilité Stationnel) comme référence pour l'évaluation des parcelles.

### Axes d'amélioration
- Développer un parseur pour extraire automatiquement les données du site
- Créer un service dédié à l'analyse des recommandations Climessences
- Implémenter une logique de scoring basée sur les 37 critères des fiches espèces

### Méthode proposée
```python
class ClimessencesService:
    def __init__(self, diagnostic_agent):
        self.diagnostic_agent = diagnostic_agent
    
    def analyze_parcel_compatibility(self, parcel_data):
        # Logique d'analyse basée sur Climessences
        pass
    
    def get_recommended_species(self, parcel_data):
        # Recommander des essences adaptées
        pass
```

### Sources complémentaires
- [Site officiel Climessences](https://climessences.fr/)
- [Réseau AFORCE](https://www.reseau-aforce.fr/)
