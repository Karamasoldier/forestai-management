"""
Commande pour démarrer l'interface web ForestAI.

Ce module contient le code pour démarrer l'interface web.
"""

import os
import sys
import logging
import argparse
import subprocess
from typing import Optional, List, Dict, Any, Union
import threading
import time

# Configuration du logger
logger = logging.getLogger("forestai.cli.web")

def run_api_process(host: str, port: int, wait_ready: bool = True) -> subprocess.Popen:
    """
    Démarre un processus séparé pour l'API.
    
    Args:
        host (str): L'hôte sur lequel l'API sera disponible.
        port (int): Le port sur lequel l'API écoutera.
        wait_ready (bool): Si True, attend que l'API soit prête.
    
    Returns:
        subprocess.Popen: Processus de l'API.
    """
    from forestai.cli.commands.api_command import run_api
    
    # Démarrer l'API dans un processus séparé
    logger.info(f"Démarrage de l'API sur {host}:{port}...")
    
    # Préparer les arguments pour le script Python
    api_cmd = [
        sys.executable,
        "-c",
        f"from forestai.cli.commands.api_command import run_api; run_api(['--host', '{host}', '--port', '{port}'])"
    ]
    
    # Démarrer le processus
    api_process = subprocess.Popen(
        api_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Attendre que l'API soit prête si demandé
    if wait_ready:
        logger.info("Attente du démarrage de l'API...")
        time.sleep(2)  # Attente pour permettre à l'API de démarrer
        
        # TODO: Implémenter une vérification plus robuste de l'état de l'API
    
    return api_process

def run_web_interface(web_dir: str, port: int, dev_mode: bool = False) -> subprocess.Popen:
    """
    Démarre l'interface web.
    
    Args:
        web_dir (str): Chemin vers le répertoire de l'interface web.
        port (int): Port sur lequel l'interface web écoutera.
        dev_mode (bool): Si True, démarre en mode développement.
    
    Returns:
        subprocess.Popen: Processus de l'interface web.
    """
    # Vérifier que le répertoire existe
    if not os.path.exists(web_dir):
        raise FileNotFoundError(f"Répertoire de l'interface web non trouvé: {web_dir}")
    
    logger.info(f"Démarrage de l'interface web depuis {web_dir} sur le port {port}...")
    
    # Changer de répertoire pour le démarrage
    cwd = os.getcwd()
    os.chdir(web_dir)
    
    try:
        # Déterminer la commande selon le mode
        if dev_mode:
            web_cmd = ["npm", "run", "dev", "--", "--port", str(port)]
        else:
            web_cmd = ["npm", "run", "serve", "--", "--port", str(port)]
        
        # Démarrer le processus
        web_process = subprocess.Popen(
            web_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        return web_process
    
    finally:
        # Revenir au répertoire d'origine
        os.chdir(cwd)

def monitor_process_output(process: subprocess.Popen, name: str):
    """
    Surveille la sortie d'un processus et la journalise.
    
    Args:
        process (subprocess.Popen): Processus à surveiller.
        name (str): Nom du processus (pour la journalisation).
    """
    while True:
        # Lire stdout
        stdout_line = process.stdout.readline()
        if stdout_line:
            logger.info(f"[{name}] {stdout_line.strip()}")
        
        # Lire stderr
        stderr_line = process.stderr.readline()
        if stderr_line:
            logger.warning(f"[{name}] {stderr_line.strip()}")
        
        # Vérifier si le processus est toujours en cours
        if process.poll() is not None:
            remaining_stdout, remaining_stderr = process.communicate()
            
            if remaining_stdout:
                logger.info(f"[{name}] {remaining_stdout.strip()}")
            
            if remaining_stderr:
                logger.warning(f"[{name}] {remaining_stderr.strip()}")
            
            break

def run_web(args: Optional[List[str]] = None) -> int:
    """
    Démarre l'interface web ForestAI.
    
    Args:
        args (Optional[List[str]]): Arguments de ligne de commande.
            Si None, utilise sys.argv[1:].
    
    Returns:
        int: Code de sortie (0 pour succès, non-zéro pour erreur)
    """
    # Créer le parseur d'arguments
    parser = argparse.ArgumentParser(description="Démarrer l'interface web ForestAI")
    
    # Options de configuration
    parser.add_argument("--port", type=int, default=3000, help="Port de l'interface web (défaut: 3000)")
    parser.add_argument("--api-host", default="127.0.0.1", help="Hôte de l'API (défaut: 127.0.0.1)")
    parser.add_argument("--api-port", type=int, default=8000, help="Port de l'API (défaut: 8000)")
    parser.add_argument("--web-dir", help="Répertoire de l'interface web (défaut: détection automatique)")
    parser.add_argument("--dev", action="store_true", help="Démarrer en mode développement")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default="INFO", help="Niveau de journalisation (défaut: INFO)")
    parser.add_argument("--api-only", action="store_true", help="Démarrer uniquement l'API")
    parser.add_argument("--web-only", action="store_true", help="Démarrer uniquement l'interface web")
    parser.add_argument("--interface", choices=["vite", "vue"], default="vite",
                       help="Interface à utiliser (vite ou vue) (défaut: vite)")
    
    # Analyser les arguments
    if args is None:
        args = sys.argv[1:]
    parsed_args = parser.parse_args(args)
    
    # Configurer la journalisation
    logging.basicConfig(
        level=getattr(logging, parsed_args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        # Déterminer le répertoire de l'interface web si non spécifié
        if parsed_args.web_dir is None:
            # Détecter le répertoire du projet
            project_root = os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../../../"
            ))
            
            # Définir le répertoire selon l'interface choisie
            if parsed_args.interface == "vite":
                web_dir = os.path.join(project_root, "web")
            else:  # vue
                web_dir = os.path.join(project_root, "webui")
        else:
            web_dir = parsed_args.web_dir
        
        # Valider le répertoire de l'interface web
        if not os.path.exists(web_dir) and not parsed_args.api_only:
            logger.error(f"Répertoire de l'interface web non trouvé: {web_dir}")
            logger.info(f"Essayez de spécifier le répertoire avec --web-dir ou utilisez --api-only")
            return 1
        
        # Liste des processus à surveiller
        processes = []
        
        # Démarrer l'API si nécessaire
        api_process = None
        if not parsed_args.web_only:
            try:
                api_process = run_api_process(
                    host=parsed_args.api_host,
                    port=parsed_args.api_port,
                    wait_ready=True
                )
                processes.append((api_process, "API"))
            except Exception as e:
                logger.error(f"Erreur lors du démarrage de l'API: {e}")
                if parsed_args.api_only:
                    return 1
                logger.warning("Continuez sans API...")
        
        # Démarrer l'interface web si nécessaire
        web_process = None
        if not parsed_args.api_only:
            try:
                web_process = run_web_interface(
                    web_dir=web_dir,
                    port=parsed_args.port,
                    dev_mode=parsed_args.dev
                )
                processes.append((web_process, "Web"))
            except Exception as e:
                logger.error(f"Erreur lors du démarrage de l'interface web: {e}")
                
                # Si l'API est également démarrée, essayer de la fermer proprement
                if api_process is not None and not parsed_args.api_only:
                    api_process.terminate()
                
                return 1
        
        # Créer des threads pour surveiller les sorties des processus
        threads = []
        for process, name in processes:
            thread = threading.Thread(
                target=monitor_process_output,
                args=(process, name),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Afficher les informations sur les services démarrés
        if api_process is not None:
            logger.info(f"API démarrée sur http://{parsed_args.api_host}:{parsed_args.api_port}")
        
        if web_process is not None:
            logger.info(f"Interface web démarrée sur http://localhost:{parsed_args.port}")
        
        # Attendre l'interruption de l'utilisateur
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            logger.info("Arrêt des services par l'utilisateur...")
            
            # Fermer proprement les processus
            for process, name in processes:
                logger.info(f"Arrêt de {name}...")
                process.terminate()
                process.wait(timeout=5)
            
            return 0
        
        return 0
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'interface web: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_web())
