#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter les tests de régression de ForestAI.

Ce script exécute tous les tests de régression et génère un rapport
indiquant si des régressions ont été détectées.

Usage:
    python run_regression_tests.py
"""

import os
import sys
import unittest
import datetime
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("regression_tests")

def main():
    """
    Fonction principale qui exécute tous les tests de régression.
    """
    logger.info("Démarrage des tests de régression ForestAI")
    
    # Chemin vers le dossier des tests de régression
    test_dir = Path(__file__).parent
    
    # Chemin vers le dossier de sortie des rapports
    reports_dir = test_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Timestamp pour le rapport
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"regression_report_{timestamp}.txt"
    
    # Découverte et exécution des tests
    logger.info(f"Recherche des tests dans {test_dir}")
    
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern="test_*.py")
    
    # Exécution des tests avec un rapport de sortie texte
    with open(report_file, 'w') as f:
        f.write(f"Rapport de Tests de Régression ForestAI - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Exécuter les tests avec un rapport texte
        runner = unittest.TextTestRunner(verbosity=2, stream=f)
        result = runner.run(suite)
        
        # Résumé des résultats
        f.write("\n" + "="*80 + "\n")
        f.write("RÉSUMÉ DES TESTS\n")
        f.write("-"*80 + "\n")
        f.write(f"Tests exécutés: {result.testsRun}\n")
        f.write(f"Réussites: {result.testsRun - len(result.failures) - len(result.errors)}\n")
        f.write(f"Échecs: {len(result.failures)}\n")
        f.write(f"Erreurs: {len(result.errors)}\n")
        
        if result.failures:
            f.write("\nÉCHECS DÉTECTÉS:\n")
            for test, traceback in result.failures:
                f.write(f"- {test}\n")
        
        if result.errors:
            f.write("\nERREURS DÉTECTÉES:\n")
            for test, traceback in result.errors:
                f.write(f"- {test}\n")
    
    # Afficher le résumé dans le terminal
    logger.info(f"Tests exécutés: {result.testsRun}")
    logger.info(f"Réussites: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Échecs: {len(result.failures)}")
    logger.info(f"Erreurs: {len(result.errors)}")
    
    if result.wasSuccessful():
        logger.info("SUCCÈS: Tous les tests de régression ont réussi!")
        logger.info(f"Rapport détaillé sauvegardé dans: {report_file}")
        return 0
    else:
        logger.error("ÉCHEC: Des problèmes ont été détectés dans les tests de régression!")
        logger.error(f"Rapport détaillé sauvegardé dans: {report_file}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
