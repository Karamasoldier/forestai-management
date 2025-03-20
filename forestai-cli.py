#!/usr/bin/env python
"""
Point d'entrée principal pour ForestAI.

Ce script est le point d'entrée unifié pour toutes les fonctionnalités
de l'application ForestAI. Il remplace les multiples scripts de démarrage
précédents.

Exemples d'utilisation:
    # Démarrer le système complet (API + interface web)
    python forestai-cli.py run
    
    # Démarrer uniquement l'API
    python forestai-cli.py api
    
    # Démarrer uniquement l'interface web
    python forestai-cli.py web --web-only
    
    # Exécuter un agent spécifique
    python forestai-cli.py agent geoagent --action search_parcels --params '{"commune": "Saint-Martin-de-Crau"}'
    
    # Exécuter des diagnostics
    python forestai-cli.py diagnostics --check-dependencies
"""

import sys
import os

# S'assurer que le répertoire du projet est dans le chemin d'importation
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Appliquer les correctifs au démarrage
try:
    from forestai.core.patches import apply_all_patches
    apply_all_patches()
except ImportError:
    print("Module de correctifs non trouvé. Continuez sans correctifs.")

# Importer et exécuter le point d'entrée CLI
try:
    from forestai.cli.main import main
    sys.exit(main())
except ImportError as e:
    print(f"Erreur lors de l'importation du module CLI: {e}")
    print("Vérifiez que ForestAI est correctement installé.")
    sys.exit(1)
