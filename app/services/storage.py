from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

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
        self._bucket_ensured = False
        self._region = settings.AWS_REGION

    def _ensure_bucket(self) -> None:
        if self._bucket_ensured:
            return
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:  # pragma: no cover - AWS client error codes vary
            error_code = exc.response.get("Error", {}).get("Code", "") if exc.response else ""
            if error_code in {"404", "NoSuchBucket", "NotFound"}:
                params = {"Bucket": self._bucket}
                if self._region and self._region != "us-east-1":
                    params["CreateBucketConfiguration"] = {
                        "LocationConstraint": self._region
                    }
                self._client.create_bucket(**params)
            else:
                raise
        self._bucket_ensured = True

    @staticmethod
    def build_private_key(application_id: uuid.UUID, version_id: uuid.UUID, filename: str = "profile.json") -> str:
        return f"applications/{application_id}/private/{version_id}/{filename}"

    @staticmethod
    def build_attachment_key(
        application_id: uuid.UUID, version_id: uuid.UUID, filename: str
    ) -> str:
        return f"applications/{application_id}/attachments/{version_id}/{filename}"

    def generate_put_url(self, key: str, content_type: str = "application/json") -> PresignedUrl:
        self._ensure_bucket()
        url = self._client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=self._expires,
        )
        return PresignedUrl(url=url, expires_in=self._expires)

    def generate_get_url(self, key: str) -> PresignedUrl:
        self._ensure_bucket()
        url = self._client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=self._expires,
        )
        return PresignedUrl(url=url, expires_in=self._expires)

    def put_object(self, key: str, content: bytes, content_type: str = "application/json") -> None:
        self._ensure_bucket()
        self._client.put_object(
            Bucket=self._bucket, Key=key, Body=content, ContentType=content_type
        )

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

_storage_service: Optional[PrivateStorageService] = None


def get_private_storage_service() -> PrivateStorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = PrivateStorageService()
    return _storage_service
