import uuid
from app.core.exceptions import TagNotFoundError, DuplicateTagError
from app.models.note import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.note import TagCreate, TagUpdate


class TagService:

    def __init__(self, tag_repo: TagRepository):
        self.tag_repo = tag_repo

    async def create_tag(self, data: TagCreate) -> Tag:
        existing = await self.tag_repo.get_by_name(data.name)
        if existing:
            raise DuplicateTagError(data.name)
        tag = Tag(name=data.name, color=data.color)
        return await self.tag_repo.create(tag)

    async def get_tag(self, tag_id: uuid.UUID) -> Tag:
        tag = await self.tag_repo.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(str(tag_id))
        return tag

    async def list_tags(self) -> list[Tag]:
        return await self.tag_repo.list_all()

    async def update_tag(self, tag_id: uuid.UUID, data: TagUpdate) -> Tag:
        tag = await self.get_tag(tag_id)
        if data.name is not None:
            conflict = await self.tag_repo.get_by_name(data.name)
            if conflict and conflict.id != tag.id:
                raise DuplicateTagError(data.name)
            tag.name = data.name
        if data.color is not None:
            tag.color = data.color
        return await self.tag_repo.update(tag)

    async def delete_tag(self, tag_id: uuid.UUID) -> None:
        tag = await self.get_tag(tag_id)
        await self.tag_repo.delete(tag)
