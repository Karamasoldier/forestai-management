# Guide d'utilisation de l'interface desktop (PyQt6)

Ce document décrit l'interface graphique desktop (GUI) basée sur PyQt6 pour tester et interagir avec les agents ForestAI.

## Table des matières

1. [Installation](#installation)
2. [Démarrage](#démarrage)
3. [Fonctionnalités](#fonctionnalités)
4. [Modes de fonctionnement](#modes-de-fonctionnement)
5. [Fenêtre principale](#fenêtre-principale)
6. [Panneau de contrôle](#panneau-de-contrôle)
7. [Panneau de surveillance](#panneau-de-surveillance)
8. [Configuration](#configuration)
9. [Dépannage](#dépannage)
10. [Développement](#développement)

## Installation

Pour utiliser l'interface desktop, vous devez d'abord installer les dépendances PyQt6 :

```bash
# Installation des dépendances de l'interface desktop
pip install -r requirements-gui.txt
```

## Démarrage

L'interface desktop peut être démarrée de plusieurs façons :

### Scripts de démarrage

**Windows**:
```bash
run_gui.bat
```

**Linux/macOS**:
```bash
chmod +x run_gui.sh
./run_gui.sh
```

### Démarrage manuel

```bash
# Mode API REST (par défaut)
python run_gui.py

# Mode direct (sans API REST)
python run_gui.py --direct

# Spécifier une URL d'API personnalisée
python run_gui.py --api-url http://localhost:8080
```

## Fonctionnalités

L'interface desktop offre les fonctionnalités suivantes :

- Visualisation en temps réel de l'état des agents
- Exécution d'actions sur les agents
- Surveillance des tâches en cours
- Configuration des paramètres de connexion
- Export des résultats au format JSON

## Modes de fonctionnement

L'interface desktop peut fonctionner dans deux modes différents :

### Mode API REST

Dans ce mode, l'interface communique avec les agents via l'API REST du système. Ce mode nécessite que l'API soit démarrée (via `run_api_with_fix.py` par exemple).

Avantages :
- Séparation des composants (client/serveur)
- Possibilité de se connecter à une API distante
- N'affecte pas les performances du système

Inconvénients :
- Nécessite que l'API soit démarrée séparément
- Latence potentielle des communications réseau

### Mode Direct

Dans ce mode, l'interface interagit directement avec les agents en local, sans passer par l'API.

Avantages :
- Ne nécessite pas d'API séparée
- Démarrage plus rapide
- Latence réduite

Inconvénients :
- Exécution dans le même processus que l'interface
- Impact potentiel sur les performances

## Fenêtre principale

La fenêtre principale de l'application est divisée en plusieurs zones :

- **Barre de menus** : Accès aux principales fonctionnalités
- **Barre d'outils** : Accès rapide aux actions courantes
- **Panneau de contrôle** : Contrôle des agents et exécution d'actions
- **Panneau de surveillance** : Affichage de l'état des agents et des tâches
- **Barre de statut** : Affichage des informations d'état

## Panneau de contrôle

Le panneau de contrôle permet d'interagir avec les agents :

### Sélection de l'agent

- Utilisez la liste déroulante pour sélectionner l'agent avec lequel vous souhaitez interagir
- Les boutons permettent de démarrer, arrêter ou rafraîchir l'agent sélectionné

### Exécution d'action

- Sélectionnez une action dans la liste déroulante
- Entrez les paramètres au format JSON
- Cliquez sur "Exécuter" pour lancer l'action

Exemple de paramètres JSON :
```json
{
  "commune": "Saint-Martin-de-Crau",
  "section": "B"
}
```

## Panneau de surveillance

Le panneau de surveillance affiche l'état actuel du système :

### Agents actifs

Cette section affiche un tableau des agents disponibles avec leur statut :
- **Nom** : Nom de l'agent
- **Type** : Type d'agent
- **Statut** : État actuel (Actif/Inactif)
- **Tâches en attente** : Nombre de tâches en attente

### Tâches récentes

Cette section affiche un tableau des tâches récentes :
- **ID** : Identifiant de la tâche
- **Agent** : Nom de l'agent associé
- **Action** : Action exécutée
- **Statut** : État de la tâche (En cours/Terminée/Erreur)
- **Date de création** : Date et heure de création de la tâche

## Configuration

Les paramètres de l'application peuvent être configurés via la boîte de dialogue "Paramètres" accessible depuis le menu "Fichier" :

- **Mode de connexion** : API REST ou Mode direct
- **URL de l'API** : URL de connexion à l'API REST
- **Intervalle de rafraîchissement** : Fréquence de mise à jour des données (en secondes)
- **Mode verbeux** : Activation/désactivation des logs détaillés

## Dépannage

### Problèmes courants

1. **L'interface ne se connecte pas à l'API**
   - Vérifiez que l'API est bien démarrée (`python run_api_with_fix.py`)
   - Vérifiez l'URL de l'API dans les paramètres
   - Vérifiez qu'aucun pare-feu ne bloque les connexions

2. **Les actions sur les agents ne fonctionnent pas**
   - Vérifiez que les paramètres JSON sont valides
   - Consultez les logs pour plus de détails

3. **L'interface est lente ou ne répond pas**
   - Augmentez l'intervalle de rafraîchissement dans les paramètres
   - Passez en mode API si vous êtes en mode direct

### Logs

Les logs de l'application sont stockés dans le dossier `logs/` et peuvent être utiles pour diagnostiquer les problèmes.

## Développement

L'interface desktop est développée avec PyQt6 et suit une architecture MVC (Modèle-Vue-Contrôleur) :

- **Modèles** (`gui/models.py`) : Gestion des données
- **Vues** (`gui/components.py`) : Composants d'interface utilisateur
- **Contrôleurs** (`gui/main_window.py` et `gui/agent_api.py`) : Logique de contrôle

Pour étendre l'interface :

1. Ajoutez de nouveaux composants dans `gui/components.py`
2. Modifiez les modèles de données dans `gui/models.py` si nécessaire
3. Intégrez vos composants dans la fenêtre principale (`gui/main_window.py`)
