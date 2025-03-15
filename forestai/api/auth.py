"""
Module d'authentification pour l'API REST ForestAI.

Ce module gère l'authentification et l'autorisation des requêtes
API en utilisant des jetons JWT et des niveaux d'accès définis.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from forestai.core.utils.config import Config

# Configuration du logger
logger = logging.getLogger("forestai.api.auth")

# Configuration du système d'authentification
JWT_SECRET = os.getenv("JWT_SECRET", "forestai-dev-secret-key")  # À changer en production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 heures par défaut

# Définir le système de sécurité
security = HTTPBearer()

# Modèles de données pour l'authentification
class TokenData(BaseModel):
    """Données contenues dans un jeton d'authentification."""
    sub: str
    exp: int
    iat: int
    scope: List[str]
    name: Optional[str] = None
    admin: bool = False

class User(BaseModel):
    """Modèle représentant un utilisateur du système."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: List[str] = []
    admin: bool = False

class TokenResponse(BaseModel):
    """Réponse contenant un jeton d'accès."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]

# Niveaux d'accès définis dans le système
SCOPES = {
    "geo:read": "Accès en lecture aux données géographiques",
    "geo:write": "Accès en écriture aux données géographiques",
    "subsidy:read": "Accès en lecture aux données de subventions",
    "subsidy:write": "Accès en écriture aux données de subventions",
    "diagnostic:read": "Accès en lecture aux diagnostics",
    "diagnostic:write": "Accès en écriture aux diagnostics",
    "regulation:read": "Accès en lecture aux données réglementaires",
    "admin": "Accès administrateur complet",
}

# Stockage simple des utilisateurs (à remplacer par une base de données en production)
USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@forestai.fr",
        "full_name": "Administrateur ForestAI",
        "hashed_password": "$2b$12$H8oGFkZZ2J9b6vULjj0WEuiGcJ9a4eMqZ8I0YKjwRBfGJk.smj6/6",  # "adminpassword"
        "disabled": False,
        "scopes": ["geo:read", "geo:write", "subsidy:read", "subsidy:write", 
                  "diagnostic:read", "diagnostic:write", "regulation:read", "admin"],
        "admin": True
    },
    "user": {
        "username": "user",
        "email": "user@forestai.fr",
        "full_name": "Utilisateur Standard",
        "hashed_password": "$2b$12$Hr/RQMTrgIaXbW8CKhz7YeJFe3hT6WIl26Ym28xMkw0l5OxxYjYVq",  # "userpassword"
        "disabled": False,
        "scopes": ["geo:read", "subsidy:read", "diagnostic:read", "regulation:read"],
        "admin": False
    },
    "diagnostic": {
        "username": "diagnostic",
        "email": "diagnostic@forestai.fr",
        "full_name": "Agent Diagnostic",
        "hashed_password": "$2b$12$NyUmK4WxGS4kgkK1B87xN.ZmxOAyQjyJbUXSW2ZpT4IPCDJOqGJMa",  # "diagnosticpassword"
        "disabled": False,
        "scopes": ["diagnostic:read", "diagnostic:write"],
        "admin": False
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si le mot de passe fourni correspond au mot de passe haché.
    
    En production, utiliser une fonction comme bcrypt.checkpw().
    
    Args:
        plain_password: Mot de passe en clair
        hashed_password: Mot de passe haché
        
    Returns:
        True si le mot de passe est valide, False sinon
    """
    # Simulation pour le développement
    # À remplacer par une vérification réelle en production
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[User]:
    """
    Récupère un utilisateur depuis la base de données.
    
    Args:
        username: Nom d'utilisateur
        
    Returns:
        User si trouvé, None sinon
    """
    if username in USERS_DB:
        user_data = USERS_DB[username]
        return User(
            username=user_data["username"],
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            disabled=user_data.get("disabled", False),
            scopes=user_data.get("scopes", []),
            admin=user_data.get("admin", False)
        )
    return None

def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authentifie un utilisateur avec son nom d'utilisateur et son mot de passe.
    
    Args:
        username: Nom d'utilisateur
        password: Mot de passe en clair
        
    Returns:
        User si authentifié, None sinon
    """
    user = get_user(username)
    if not user:
        return None
    user_data = USERS_DB.get(username)
    if not user_data:
        return None
    
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un jeton d'accès JWT.
    
    Args:
        data: Données à inclure dans le jeton
        expires_delta: Délai d'expiration optionnel
        
    Returns:
        Jeton JWT encodé
    """
    to_encode = data.copy()
    
    # Définir le délai d'expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    # Ajouter les claims standards
    to_encode.update({
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp()
    })
    
    # Encoder le jeton
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """
    Récupère l'utilisateur courant à partir du jeton JWT.
    
    Args:
        credentials: Informations d'authentification
        
    Returns:
        User correspondant au jeton
        
    Raises:
        HTTPException: Si le jeton est invalide ou l'utilisateur n'existe pas
    """
    # Initialiser les exceptions
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Informations d'identification invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Décoder le jeton
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Extraire les données du jeton
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Vérifier si le jeton a expiré
        exp = payload.get("exp")
        if exp is None or int(time.time()) > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Jeton expiré",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Créer l'objet TokenData
        token_data = TokenData(
            sub=username,
            exp=exp,
            iat=payload.get("iat", int(time.time())),
            scope=payload.get("scope", []),
            name=payload.get("name"),
            admin=payload.get("admin", False)
        )
    except jwt.PyJWTError:
        logger.warning("Erreur de décodage du jeton JWT", exc_info=True)
        raise credentials_exception
    
    # Récupérer l'utilisateur
    user = get_user(token_data.sub)
    if user is None:
        logger.warning(f"Utilisateur {token_data.sub} non trouvé")
        raise credentials_exception
    
    # Vérifier si l'utilisateur est désactivé
    if user.disabled:
        logger.warning(f"Tentative d'accès par l'utilisateur désactivé {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur désactivé",
        )
    
    return user

def check_scope(required_scopes: List[str]):
    """
    Crée un dépendant qui vérifie si l'utilisateur a les autorisations requises.
    
    Args:
        required_scopes: Liste des autorisations requises
        
    Returns:
        Fonction de dépendance
    """
    async def scope_checker(user: User = Depends(get_current_user)) -> User:
        # Les administrateurs ont accès à tout
        if user.admin:
            return user
        
        # Vérifier que l'utilisateur a au moins une des autorisations requises
        for scope in required_scopes:
            if scope in user.scopes:
                return user
        
        # Si aucune autorisation n'est trouvée, lever une exception
        logger.warning(f"Accès refusé pour {user.username}: manque les scopes {required_scopes}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Autorisations insuffisantes. Requises: {', '.join(required_scopes)}",
        )
    
    return scope_checker

# Accès pratiques pour les niveaux d'autorisation courants
geo_read = check_scope(["geo:read"])
geo_write = check_scope(["geo:write"])
subsidy_read = check_scope(["subsidy:read"])
subsidy_write = check_scope(["subsidy:write"])
diagnostic_read = check_scope(["diagnostic:read"])
diagnostic_write = check_scope(["diagnostic:write"])
regulation_read = check_scope(["regulation:read"])
admin_only = check_scope(["admin"])
