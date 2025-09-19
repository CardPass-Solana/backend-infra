from __future__ import annotations

import logging

from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware

from app.api import applications, auth, bounties, webhooks
from app.db import get_session
from app.services.bootstrap import seed_poc_data

app = FastAPI(title="Headhunt Bounty API", version="0.1.0")

logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    # frontend addr. here
    "https://cardpass.lidarbtc.workers.dev",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoint
@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "ok"}


# Register routers
app.include_router(auth.router)
app.include_router(bounties.router)
app.include_router(applications.router)
app.include_router(webhooks.router)


@app.on_event("startup")
async def _bootstrap_seed_data() -> None:
    try:
        async with get_session() as session:
            await seed_poc_data(session)
    except Exception as exc:  # noqa: BLE001 - best effort seed for POC
        logger.warning("Skipping seed bootstrap due to error: %s", exc)
