from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.services.connections import connections_service

router = APIRouter()


@router.get("/")
async def get_graph(
    threshold: float = 0.15,
    user: dict = Depends(get_current_user),
) -> dict:
    user_id: str = user["id"]
    return connections_service.build_graph(user_id, threshold=threshold)
