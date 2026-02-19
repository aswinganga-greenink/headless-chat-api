from typing import Protocol, Optional
from src.models.all_models import User

class AuthProvider(Protocol):
    """
    Interface for authentication providers.
    Allows swapping between Basic (Username/Password), OAuth2, LDAP, etc.
    """

    async def authenticate_user(self, **kwargs) -> Optional[User]:
        """
        Validates credentials and returns the user if successful.
        """
        ...

    async def create_access_token(self, data: dict) -> str:
        """
        Creates a JWT or equivalent access token.
        """
        ...

    async def get_current_user(self, token: str) -> User:
        """
        Validates a token and retrieves the associated user.
        Raises HTTPException if invalid.
        """
        ...
