from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.interfaces import AuthProvider
from src.core.config import get_settings
from src.core import security
from src.models.all_models import User

settings = get_settings()

class BasicAuthProvider(AuthProvider):
    """
    Standard username/password authentication using OAuth2 Password Bearer flow.
    Uses bcrypt for hashing and JWT for tokens.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        # Context moved to src.core.security
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Checks if the password matches the hash."""
        return security.verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hashes a password using bcrypt."""
        return security.pwd_context.hash(password)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Retrieves user by username (or email) and verifies password.
        """
        stmt = select(User).where(User.email == username) # Start with email
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            # Fallback to username
            stmt = select(User).where(User.username == username)
            result = await self.db.execute(stmt)
            user = result.scalars().first()

        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
            
        return user

    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Generates a JWT token signed with the application secret key.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: str) -> User:
        """
        Decodes JWT token and retrieves user from DB.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
            
        # For simplicity, we query by ID or email. 
        # Ideally the token 'sub' should be the user ID (UUID).
        # But if we stored email/username in sub, we query that.
        # Let's assume 'sub' is user ID for robustness, or handle email.
        
        # Validating if it's a UUID or email
        # For this implementation, let's assume we store user_id as 'sub' in token creation
        
        stmt = select(User).where(str(User.id) == username) # Casting might be tricky in SQL, better to just try fetching
        # If 'sub' is not UUID formatted string, this might fail if we cast to UUID
        # So commonly we store user_id (str) in token.
        
        # Let's fix this logic: we will store user_id as string in 'sub'
        try:
            import uuid
            user_uuid = uuid.UUID(username)
            stmt = select(User).where(User.id == user_uuid)
            result = await self.db.execute(stmt)
            user = result.scalars().first()
        except ValueError:
            user = None
            
        if user is None:
            raise credentials_exception
            
        return user
