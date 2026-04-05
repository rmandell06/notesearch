import uuid
import hashlib
import aiofiles
import os
from pathlib import Path
from typing import BinaryIO, AsyncIterator

from app.core.config import settings
from app.core.exceptions import StorageError


class StorageService:
    """
    Abstracts file storage behind a common interface.
    Supports local filesystem today; swap to S3 by changing STORAGE_BACKEND.
    """

    async def save(self, file_data: bytes, filename: str, mime_type: str) -> tuple[str, str]:
        """
        Persist file bytes and return (storage_key, sha256_checksum).
        storage_key is an opaque identifier used to retrieve or delete the file.
        """
        checksum = hashlib.sha256(file_data).hexdigest()
        ext = Path(filename).suffix.lower()
        storage_key = f"{uuid.uuid4().hex}{ext}"

        if settings.STORAGE_BACKEND == "local":
            return await self._save_local(file_data, storage_key), checksum
        elif settings.STORAGE_BACKEND == "s3":
            return await self._save_s3(file_data, storage_key, mime_type), checksum
        else:
            raise StorageError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")

    async def read(self, storage_key: str) -> bytes:
        if settings.STORAGE_BACKEND == "local":
            return await self._read_local(storage_key)
        elif settings.STORAGE_BACKEND == "s3":
            return await self._read_s3(storage_key)
        raise StorageError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")

    async def delete(self, storage_key: str) -> None:
        if settings.STORAGE_BACKEND == "local":
            await self._delete_local(storage_key)
        elif settings.STORAGE_BACKEND == "s3":
            await self._delete_s3(storage_key)
        else:
            raise StorageError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")

    async def stream(self, storage_key: str, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        """Stream file in chunks to avoid loading large files into memory."""
        if settings.STORAGE_BACKEND == "local":
            path = self._local_path(storage_key)
            async with aiofiles.open(path, "rb") as f:
                while chunk := await f.read(chunk_size):
                    yield chunk
        else:
            # For S3 we'd use boto3 streaming body
            data = await self.read(storage_key)
            for i in range(0, len(data), chunk_size):
                yield data[i : i + chunk_size]

    # ── Local backend ─────────────────────────────────────────────────────────

    def _local_path(self, storage_key: str) -> Path:
        # Shard into subdirectories to avoid FS inode limits
        shard = storage_key[:2]
        path = Path(settings.LOCAL_STORAGE_PATH) / shard
        path.mkdir(parents=True, exist_ok=True)
        return path / storage_key

    async def _save_local(self, data: bytes, storage_key: str) -> str:
        path = self._local_path(storage_key)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return storage_key

    async def _read_local(self, storage_key: str) -> bytes:
        path = self._local_path(storage_key)
        if not path.exists():
            raise StorageError(f"File not found: {storage_key}")
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def _delete_local(self, storage_key: str) -> None:
        path = self._local_path(storage_key)
        if path.exists():
            os.remove(path)

    # ── S3 backend ────────────────────────────────────────────────────────────

    async def _save_s3(self, data: bytes, storage_key: str, mime_type: str) -> str:
        import boto3
        import asyncio
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=storage_key,
                Body=data,
                ContentType=mime_type,
            ),
        )
        return storage_key

    async def _read_s3(self, storage_key: str) -> bytes:
        import boto3
        import asyncio
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key),
        )
        return response["Body"].read()

    async def _delete_s3(self, storage_key: str) -> None:
        import boto3
        import asyncio
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key),
        )


storage_service = StorageService()
