from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.config import get_settings


@dataclass
class MintRequest:
    application_id: uuid.UUID
    applicant_wallet: str
    public_profile: Dict[str, Any]


@dataclass
class MintResponse:
    request_id: str
    simulated: bool
    message: str


class HeliusClient:
    """Helius mint/indexing stub for the POC."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.HELIUS_API_KEY

    def mint_cnft(self, payload: MintRequest) -> MintResponse:
        # POC stub returns deterministic identifier. Real implementation would call Helius API.
        request_id = f"mint-{payload.application_id}"
        return MintResponse(
            request_id=request_id,
            simulated=True,
            message="Mint request simulated; waiting for webhook confirmation.",
        )


_helius_client: Optional[HeliusClient] = None


def get_helius_client() -> HeliusClient:
    global _helius_client
    if _helius_client is None:
        _helius_client = HeliusClient()
    return _helius_client
