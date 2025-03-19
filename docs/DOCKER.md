# Déploiement avec Docker

Ce document explique comment déployer ForestAI en utilisant Docker, ce qui permet d'éviter les problèmes de dépendances et de configuration.

## Prérequis

- [Docker](https://www.docker.com/products/docker-desktop) installé et fonctionnel
- [Docker Compose](https://docs.docker.com/compose/install/) (inclus dans Docker Desktop)

## Démarrage rapide

### Windows

Exécutez simplement le script `run_docker.bat` à la racine du projet. Ce script va:
1. Vérifier que Docker est installé et en cours d'exécution
2. Construire et démarrer les conteneurs
3. Ouvrir l'interface de documentation API dans votre navigateur

### Linux/macOS

```bash
# Construire et démarrer les conteneurs
docker-compose up -d

# Vérifier que le conteneur est en cours d'exécution
docker-compose ps

# Voir les logs (Ctrl+C pour quitter)
docker-compose logs -f
```

## Accès à l'application

Une fois les conteneurs démarrés:

- **API Documentation**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

## Gestion des données

Les données sont persistantes grâce aux volumes Docker configurés dans `docker-compose.yml`:

- `./data:/app/data` - Stocke les données persistantes
- `./logs:/app/logs` - Stocke les logs de l'application

## Commandes utiles

```bash
# Arrêter les conteneurs
docker-compose down

# Reconstruire et redémarrer (en cas de modifications du code)
docker-compose up -d --build

# Voir les logs
docker-compose logs -f

# Exécuter une commande dans le conteneur
docker-compose exec api python -c "import sys; print(sys.version)"
```

## Dépannage

### Problème: Les conteneurs ne démarrent pas

Vérifiez les logs pour identifier le problème:
```bash
docker-compose logs
```

### Problème: Conflits de port

Si le port 8000 est déjà utilisé, modifiez le fichier `docker-compose.yml` pour utiliser un port différent:
```yaml
ports:
  - "8001:8000"  # Utilise le port 8001 au lieu de 8000
```

### Problème: Permissions sur les volumes

Si vous rencontrez des problèmes de permissions:

**Linux/macOS**:
```bash
sudo chown -R $(id -u):$(id -g) ./data ./logs
```

**Windows**:
Assurez-vous que les dossiers `data` et `logs` sont accessibles en écriture.

## Personnalisation

### Variables d'environnement

Vous pouvez définir des variables d'environnement dans le fichier `docker-compose.yml`:

```yaml
environment:
  - DEBUG=True
  - LOG_LEVEL=INFO
  # Autres variables...
```

### Ports

Pour changer les ports exposés, modifiez la section `ports` dans `docker-compose.yml`.
