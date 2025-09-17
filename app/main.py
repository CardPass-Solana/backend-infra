from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import applications, auth, bounties, webhooks
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Headhunt Bounty API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mihari.yeongmin.net",
        "http://mihari.yeongmin.net",
    ],
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
