"""
Router de Autenticação.
POST /api/auth/login → retorna JWT.
"""

from fastapi import APIRouter, HTTPException, status

from backend.core.auth import authenticate_user, create_access_token
from backend.models.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Autentica o usuário e retorna um token JWT.
    Mesmas credenciais provisórias do Streamlit (CREDENCIAIS + SENHA_PADRAO).
    """
    user = authenticate_user(request.username, request.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return TokenResponse(
        access_token=token,
        user_role=user["role"],
    )
