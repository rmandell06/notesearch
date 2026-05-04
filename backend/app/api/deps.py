from fastapi import Header, HTTPException

from app.services.supabase_client import SupabaseNotConfigured, supabase_client


async def current_user(authorization: str | None = Header(default=None)) -> str:
    """Validate the bearer token against Supabase and return the user id."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")

    try:
        client = await supabase_client.client()
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    user_resp = await client.auth.get_user(token)
    if not user_resp or not user_resp.user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_resp.user.id
