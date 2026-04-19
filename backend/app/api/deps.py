from typing import Any
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_client import supabase_client
from app.core.exceptions import AuthError

logger = logging.getLogger(__name__)
auth_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> dict[str, Any]:
    """
    Validate Bearer token via Supabase and return normalized user payload.
    """
    token: str = credentials.credentials
    try:
        user_response: Any = await supabase_client.get_user(token)

        # Normalize response shape (handles both supabase-py SDK objects and raw dicts)
        if hasattr(user_response, "user"):
            user = user_response.user
        else:
            user = user_response

        if not user:
            logger.warning("Auth failed: user not found for token")
            raise AuthError("User not found")

        if "id" not in user:
            logger.error("Auth failed: malformed user payload: %s", user)
            raise AuthError("Malformed user payload")

        return user

    except AuthError as e:
        logger.info("AuthError: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.exception("Unexpected auth failure: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
