from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/helius", status_code=status.HTTP_202_ACCEPTED)
async def helius_webhook(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    # TODO: validate and update application cnft_mint once Solana integration is ready.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Helius webhook handling not yet implemented; stub endpoint.",
    )
