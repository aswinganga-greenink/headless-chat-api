from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status, Query, WebSocketException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.core.config import get_settings
from src.core.interfaces import AuthProvider
from src.core.storage_interfaces import StorageProvider
from src.models.all_models import User
from src.modules.auth.basic_provider import BasicAuthProvider
from src.modules.media.local_storage import LocalFileStorage

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_auth_provider(
    db: AsyncSession = Depends(get_db)
) -> AuthProvider:
    """
    Dependency to get the authentication provider.
    Currently hardcoded to BasicAuthProvider, but can be switched based on config.
    """
    return BasicAuthProvider(db_session=db)

async def get_storage_provider() -> StorageProvider:
    """
    Dependency to get the storage provider.
    Currently hardcoded to LocalFileStorage.
    """
    # Create media directory in project root
    return LocalFileStorage(base_path="media_uploads")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_provider: AuthProvider = Depends(get_auth_provider)
) -> User:
    """
    Dependency to get the current authenticated user.
    validates the token using the active auth provider.
    """
    user = await auth_provider.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_user_ws(
    token: str = Query(...),
    auth_provider: AuthProvider = Depends(get_auth_provider)
) -> User:
    """
    Dependency for WebSocket authentication via query parameter.
    """
    try:
        user = await auth_provider.get_current_user(token)
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        
    if not user or not user.is_active:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
DB = Annotated[AsyncSession, Depends(get_db)]

