# Authentification pour l'API ForestAI

Ce document explique comment mettre en œuvre l'authentification pour l'API REST ForestAI, qui utilise des jetons JWT (JSON Web Tokens) pour sécuriser les endpoints.

## Vue d'ensemble

L'API ForestAI implémente un système d'authentification basé sur les standards suivants:

- **OAuth 2.0 Password Flow** pour l'obtention des jetons
- **JWT (JSON Web Tokens)** pour la représentation des jetons d'accès
- **RBAC (Role-Based Access Control)** pour la gestion des permissions

## Obtention d'un jeton d'accès

### Endpoint d'authentification

```
POST /auth/token
```

### Format de la requête

La requête doit être au format `application/x-www-form-urlencoded` avec les paramètres suivants:

```
username: <nom d'utilisateur>
password: <mot de passe>
grant_type: password
```

### Exemple avec cURL

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=userpassword&grant_type=password"
```

### Exemple avec Python

```python
import requests

response = requests.post(
    "http://localhost:8000/auth/token",
    data={
        "username": "user",
        "password": "userpassword",
        "grant_type": "password"
    },
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

token_data = response.json()
access_token = token_data["access_token"]
```

### Réponse

En cas de succès, le serveur renvoie un jeton d'accès et des métadonnées:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_info": {
    "username": "user",
    "scopes": ["geo:read", "subsidy:read", "diagnostic:read", "regulation:read"],
    "full_name": "Utilisateur Standard",
    "is_admin": false
  }
}
```

## Utilisation du jeton d'accès

### En-tête d'autorisation

Pour les requêtes authentifiées, ajoutez l'en-tête `Authorization` avec le format suivant:

```
Authorization: Bearer <access_token>
```

### Exemple avec cURL

```bash
curl -X GET "http://localhost:8000/diagnostic/generate" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"parcel_id": "13097000B0012"}'
```

### Exemple avec Python

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/diagnostic/generate",
    json={"parcel_id": "13097000B0012"},
    headers=headers
)
```

## Gestion des niveaux d'accès

L'API ForestAI utilise un système d'autorisations basé sur des scopes (portées). Chaque utilisateur se voit attribuer un ensemble de scopes qui déterminent à quels endpoints il peut accéder.

### Niveaux d'accès disponibles

| Scope | Description |
|-------|-------------|
| `geo:read` | Accès en lecture aux données géographiques |
| `geo:write` | Accès en écriture aux données géographiques |
| `subsidy:read` | Accès en lecture aux données de subventions |
| `subsidy:write` | Accès en écriture aux données de subventions |
| `diagnostic:read` | Accès en lecture aux diagnostics |
| `diagnostic:write` | Accès en écriture aux diagnostics |
| `regulation:read` | Accès en lecture aux données réglementaires |
| `admin` | Accès administrateur complet |

### Endpoints et niveaux d'accès requis

| Endpoint | Méthode | Scope requis |
|----------|---------|--------------|
| `/geo/search` | POST | `geo:read` |
| `/geo/analyze` | POST | `geo:read` |
| `/subsidies/search` | POST | `subsidy:read` |
| `/subsidies/eligibility` | POST | `subsidy:read` |
| `/subsidies/application` | POST | `subsidy:write` |
| `/diagnostic/generate` | POST | `diagnostic:read` |
| `/diagnostic/management-plan` | POST | `diagnostic:write` |
| `/diagnostic/health-analysis` | POST | `diagnostic:read` |
| `/diagnostic/report` | POST | `diagnostic:read` |
| `/admin/stats` | GET | `admin` |

## Gestion des erreurs

### Codes d'erreur d'authentification

| Code | Description |
|------|-------------|
| 401 | Non authentifié (jeton manquant ou invalide) |
| 403 | Autorisations insuffisantes (jeton valide mais scopes insuffisants) |

### Exemple de réponse d'erreur

```json
{
  "detail": "Autorisations insuffisantes. Requises: diagnostic:write"
}
```

## Profils d'utilisateurs

Le système inclut plusieurs profils d'utilisateurs préconfigurés pour différents cas d'usage:

### Utilisateur standard

- **Username:** `user`
- **Password:** `userpassword`
- **Scopes:** `geo:read`, `subsidy:read`, `diagnostic:read`, `regulation:read`

Utilisateur avec des permissions de lecture uniquement. Idéal pour la consultation de données.

### Agent de diagnostic

- **Username:** `diagnostic`
- **Password:** `diagnosticpassword`
- **Scopes:** `diagnostic:read`, `diagnostic:write`

Spécialisé pour les opérations de diagnostic forestier. Ne peut pas accéder aux autres modules.

### Administrateur

- **Username:** `admin`
- **Password:** `adminpassword`
- **Scopes:** tous les scopes disponibles, y compris `admin`

Accès complet à toutes les fonctionnalités du système.

## Configuration du système d'authentification

En production, vous devrez configurer les paramètres suivants:

### Variables d'environnement

```
JWT_SECRET=<clé secrète pour la signature des jetons>
JWT_EXPIRATION_MINUTES=1440  # 24 heures par défaut
```

### Sécurité

La clé secrète JWT doit être:
- Générée aléatoirement
- D'au moins 32 caractères
- Stockée de manière sécurisée
- Différente entre les environnements (dev/prod)

### Production vs Développement

En production, assurez-vous de:
1. Utiliser HTTPS pour toutes les communications
2. Stocker les utilisateurs dans une base de données sécurisée
3. Implémenter le rate limiting pour prévenir les attaques par force brute
4. Définir un délai d'expiration approprié pour les jetons

## Exemple de code complet

Un exemple d'utilisation de l'API avec authentification est disponible dans:
```
examples/api_auth_example.py
```

Cet exemple démontre:
- L'obtention d'un jeton d'authentification
- L'utilisation du jeton pour accéder aux endpoints protégés
- La gestion des erreurs d'authentification
