from typing import Any
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_client import supabase_client

logger = logging.getLogger(__name__)
auth_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> dict[str, Any]:
    """Validate Bearer token via Supabase and return {id: user_id}."""
    token: str = credentials.credentials
    user_id = supabase_client.get_user_id(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": user_id}
