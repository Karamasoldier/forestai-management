#!/usr/bin/env python
"""
Script pour exécuter les tests unitaires du projet ForestAI.

Usage:
    python run_tests.py [options]

Options:
    --api     Exécuter uniquement les tests de l'API REST
    --agents  Exécuter uniquement les tests des agents
    --all     Exécuter tous les tests (par défaut)
    -v        Mode verbeux
    -q        Mode silencieux
"""

import os
import sys
import pytest
import argparse

def parse_arguments():
    """
    Parse les arguments de ligne de commande.
    
    Returns:
        Arguments parsés.
    """
    parser = argparse.ArgumentParser(description='Exécuter les tests du projet ForestAI')
    parser.add_argument('--api', action='store_true', help='Exécuter uniquement les tests de l\'API REST')
    parser.add_argument('--agents', action='store_true', help='Exécuter uniquement les tests des agents')
    parser.add_argument('--all', action='store_true', help='Exécuter tous les tests (par défaut)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mode verbeux')
    parser.add_argument('-q', '--quiet', action='store_true', help='Mode silencieux')
    
    return parser.parse_args()

def main():
    """
    Fonction principale.
    """
    args = parse_arguments()
    
    # Déterminer le mode de verbosité
    if args.verbose:
        verbosity = '-v'
    elif args.quiet:
        verbosity = '-q'
    else:
        verbosity = ''
    
    # Déterminer les tests à exécuter
    if args.api:
        test_path = 'tests/api'
    elif args.agents:
        test_path = 'tests/agents'
    else:  # Par défaut ou --all
        test_path = 'tests'
    
    # Construire la commande pytest
    pytest_args = [test_path]
    if verbosity:
        pytest_args.append(verbosity)
    
    # Exécuter les tests
    print(f"Exécution des tests dans {test_path}...")
    result = pytest.main(pytest_args)
    
    # Retourner le résultat
    sys.exit(result)

if __name__ == '__main__':
    main()
