from fastapi import APIRouter, HTTPException
from supabase_auth.errors import AuthApiError

from app.schemas.user import UserCredentials
from app.services.supabase_client import SupabaseNotConfigured, supabase_client


router = APIRouter()


def _config_error(exc: SupabaseNotConfigured) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


@router.post("/signup")
async def signup(creds: UserCredentials) -> dict:
    try:
        client = await supabase_client.client()
    except SupabaseNotConfigured as exc:
        raise _config_error(exc) from exc

    try:
        resp = await client.auth.sign_up(
            {"email": creds.email, "password": creds.password}
        )
    except AuthApiError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    if not resp.user:
        raise HTTPException(status_code=400, detail="Signup failed")
    return {
        "user_id": resp.user.id,
        "email": resp.user.email,
        "access_token": resp.session.access_token if resp.session else None,
    }


@router.post("/login")
async def login(creds: UserCredentials) -> dict:
    try:
        client = await supabase_client.client()
    except SupabaseNotConfigured as exc:
        raise _config_error(exc) from exc

    try:
        resp = await client.auth.sign_in_with_password(
            {"email": creds.email, "password": creds.password}
        )
    except AuthApiError as exc:
        # Wrong password / unverified email / unknown user all surface here.
        raise HTTPException(status_code=401, detail=exc.message) from exc

    if not resp.session:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "user_id": resp.user.id,
        "access_token": resp.session.access_token,
        "refresh_token": resp.session.refresh_token,
    }


@router.post("/logout")
async def logout() -> dict:
    try:
        client = await supabase_client.client()
    except SupabaseNotConfigured as exc:
        raise _config_error(exc) from exc

    await client.auth.sign_out()
    return {"status": "ok"}
