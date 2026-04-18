from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def search(q: str) -> list:
    raise NotImplementedError
