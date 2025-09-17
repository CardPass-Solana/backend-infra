from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings


@dataclass
class EscrowRecord:
    bounty_id: uuid.UUID
    escrow_account: str
    signature: str


@dataclass
class DepositRecord:
    application_id: uuid.UUID
    recruiter_wallet: str
    signature: str
    amount: float


@dataclass
class PayoutRecord:
    application_id: uuid.UUID
    signature: str
    recruit_amount: float
    referrer_amount: Optional[float]
    platform_amount: Optional[float]


class SolanaProgramClient:
    """Stub for Solana program interactions."""

    def __init__(self) -> None:
        settings = get_settings()
        self._rpc_url = settings.SOLANA_RPC_URL or "https://api.devnet.solana.com"

    def init_bounty_escrow(self, bounty_id: uuid.UUID, recruiter_wallet: str, amount: float) -> EscrowRecord:
        escrow_key = f"escrow-{bounty_id}"
        signature = f"tx-init-{bounty_id}"
        return EscrowRecord(
            bounty_id=bounty_id,
            escrow_account=escrow_key,
            signature=signature,
        )

    def record_deposit(self, application_id: uuid.UUID, recruiter_wallet: str, amount: float) -> DepositRecord:
        signature = f"tx-deposit-{application_id}"
        return DepositRecord(
            application_id=application_id,
            recruiter_wallet=recruiter_wallet,
            amount=amount,
            signature=signature,
        )

    def confirm_hire(
        self,
        application_id: uuid.UUID,
        recruit_amount: float,
        referrer_amount: Optional[float],
        platform_amount: Optional[float],
    ) -> PayoutRecord:
        signature = f"tx-payout-{application_id}"
        return PayoutRecord(
            application_id=application_id,
            signature=signature,
            recruit_amount=recruit_amount,
            referrer_amount=referrer_amount,
            platform_amount=platform_amount,
        )


_solana_client: Optional[SolanaProgramClient] = None


def get_solana_client() -> SolanaProgramClient:
    global _solana_client
    if _solana_client is None:
        _solana_client = SolanaProgramClient()
    return _solana_client
