from __future__ import annotations

from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware

from app.api import applications, auth, bounties, webhooks

app = FastAPI(title="Headhunt Bounty API", version="0.1.0")

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
