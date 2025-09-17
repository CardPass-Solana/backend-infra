from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from app.config import get_settings


@dataclass
class PresignedUrl:
    url: str
    expires_in: int
    fields: Optional[dict] = None


class PrivateStorageService:
    """Wrapper around S3 (or compatible) for applicant private data."""

    def __init__(self) -> None:
        settings = get_settings()
        session = boto3.session.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self._client: BaseClient = session.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            config=Config(signature_version="s3v4"),
        )
        self._bucket = settings.S3_PRIVATE_BUCKET
        self._expires = settings.S3_PRESIGN_EXPIRES_SECONDS

    @staticmethod
    def build_private_key(application_id: uuid.UUID, version_id: uuid.UUID, filename: str = "profile.json") -> str:
        return f"applications/{application_id}/private/{version_id}/{filename}"

    @staticmethod
    def build_attachment_key(
        application_id: uuid.UUID, version_id: uuid.UUID, filename: str
    ) -> str:
        return f"applications/{application_id}/attachments/{version_id}/{filename}"

    def generate_put_url(self, key: str, content_type: str = "application/json") -> PresignedUrl:
        url = self._client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=self._expires,
        )
        return PresignedUrl(url=url, expires_in=self._expires)

    def generate_get_url(self, key: str) -> PresignedUrl:
        url = self._client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=self._expires,
        )
        return PresignedUrl(url=url, expires_in=self._expires)

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

_storage_service: Optional[PrivateStorageService] = None


def get_private_storage_service() -> PrivateStorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = PrivateStorageService()
    return _storage_service
