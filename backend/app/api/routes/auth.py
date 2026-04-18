from fastapi import APIRouter

router = APIRouter()


@router.post("/signup")
async def signup() -> dict:
    raise NotImplementedError


@router.post("/login")
async def login() -> dict:
    raise NotImplementedError


@router.post("/logout")
async def logout() -> dict:
    raise NotImplementedError
