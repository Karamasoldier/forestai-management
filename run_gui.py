#!/usr/bin/env python
"""
Script d'exécution de l'interface graphique pour tester les agents ForestAI.

Usage:
    python run_gui.py [--api-url URL] [--direct]

Options:
    --api-url URL  URL de l'API REST (par défaut: http://localhost:8000)
    --direct       Utiliser le mode direct au lieu de l'API REST

Exemples:
    # Utiliser l'API REST par défaut
    python run_gui.py

    # Spécifier une URL d'API personnalisée
    python run_gui.py --api-url http://localhost:8080

    # Utiliser le mode direct (sans API REST)
    python run_gui.py --direct
"""

import os
import sys
import argparse
import logging
from PyQt6.QtWidgets import QApplication

from forestai.core.utils.config import Config
from forestai.core.utils.logging_config import LoggingConfig
from gui.main_window import MainWindow

# Configuration du logging
LoggingConfig.get_instance().init({
    "level": "INFO",
    "log_dir": "logs",
    "format_string": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
})

logger = logging.getLogger("forestai.gui")


def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Les arguments parsés
    """
    parser = argparse.ArgumentParser(description='ForestAI - Interface de test des agents')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000', 
                        help='URL de l\'API REST (par défaut: http://localhost:8000)')
    parser.add_argument('--direct', action='store_true', 
                        help='Utiliser le mode direct au lieu de l\'API REST')
    
    return parser.parse_args()


def setup():
    """
    Effectue les opérations de configuration initiales.
    """
    # Chargement de la configuration
    config = Config.get_instance()
    config.load_config(".env")
    
    # Vérification des dépendances
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        logger.info(f"Version de Qt: {QT_VERSION_STR}")
    except ImportError as e:
        logger.error(f"Erreur de dépendance PyQt6: {str(e)}")
        print("Erreur: PyQt6 n'est pas installé. Installez-le avec la commande suivante:")
        print("pip install -r requirements-gui.txt")
        sys.exit(1)


def main():
    """
    Fonction principale.
    """
    # Parse les arguments
    args = parse_arguments()
    
    # Configuration initiale
    setup()
    
    # Création de l'application Qt
    app = QApplication(sys.argv)
    app.setApplicationName("ForestAI - Agent GUI")
    app.setOrganizationName("ForestAI")
    
    # Création et affichage de la fenêtre principale
    window = MainWindow()
    
    # Configuration des paramètres selon les arguments
    if hasattr(window, 'settings'):
        window.settings.setValue("api_mode", "direct" if args.direct else "api")
        window.settings.setValue("api_url", args.api_url)
    
    # Affichage de la fenêtre
    window.show()
    
    # Exécution de l'application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
