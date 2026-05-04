from fastapi import APIRouter, Depends

from app.api.deps import current_user
from app.services.connections import connections_service


router = APIRouter()


@router.get("/")
async def get_graph(
    threshold: float = 0.15,
    user_id: str = Depends(current_user),
) -> dict:
    return await connections_service.build_graph(user_id, threshold=threshold)
