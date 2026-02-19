"""
Autenticação JWT provisória.
Simula o login atual do Streamlit, preparando terreno para o futuro SSO.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.core.config import get_settings

# Esquema OAuth2 — o frontend enviará o token via header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Credenciais provisórias (espelhando app_metricas.py)
CREDENCIAIS = {
    "fabricio": "admin",
    "fernando": "viewer",
    "gustavo": "viewer",
    "admin": "admin",
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Valida credenciais. Retorna dict com dados do usuário ou None.
    Mesma lógica do Streamlit: usuário no dicionário + senha padrão.
    """
    settings = get_settings()
    username_lower = username.lower().strip()

    if username_lower in CREDENCIAIS and password == settings.DEFAULT_PASSWORD:
        return {
            "username": username_lower,
            "role": CREDENCIAIS[username_lower],
        }
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um JWT com expiração configurável."""
    settings = get_settings()
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency do FastAPI: decodifica o JWT e retorna os dados do usuário.
    Aceita dois formatos de token:
      - Hub Taxbase: payload com 'email', 'permissao', 'funcao_id', 'sistemas'
      - Local (dev): payload com 'sub', 'role'
    Levanta 401 se o token for inválido ou expirado.
    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        # --- Detectar formato do token ---
        # Hub format: contém 'email' e 'permissao'
        # Local format: contém 'sub' e 'role'
        username: str = payload.get("email") or payload.get("sub")
        raw_role: str = payload.get("permissao") or payload.get("role")

        if username is None:
            raise credentials_exception

        # Normalizar permissão do Hub para role do Metricas
        # Hub: 'admin', 'admin_master', 'usuario'  →  Metricas: 'admin', 'viewer'
        if raw_role in ("admin", "admin_master"):
            role = "admin"
        elif raw_role in ("viewer",):
            role = "viewer"
        else:
            role = "viewer"  # 'usuario' do Hub → 'viewer'

        return {
            "username": username,
            "role": role,
            "nome": payload.get("nome", username),
            "hub_origin": "email" in payload,  # Flag para saber se veio do Hub
        }

    except JWTError:
        raise credentials_exception


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency que exige role 'admin'. Levanta 403 se não for admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user
