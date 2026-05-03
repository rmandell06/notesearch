from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCredentials
from app.services.supabase_client import supabase_client

router = APIRouter()


@router.post("/signup")
async def signup(creds: UserCredentials) -> dict:
    try:
        result = supabase_client.sign_up(str(creds.email), creds.password)
        return {
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": {"id": result["user_id"], "email": str(creds.email)},
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(creds: UserCredentials) -> dict:
    try:
        result = supabase_client.sign_in(str(creds.email), creds.password)
        return {
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": {"id": result["user_id"], "email": str(creds.email)},
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout")
async def logout() -> dict:
    return {"message": "logged out"}
