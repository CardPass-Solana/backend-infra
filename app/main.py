from __future__ import annotations

from fastapi import FastAPI

from app.api import applications, auth, bounties, webhooks

app = FastAPI(title="Headhunt Bounty API", version="0.1.0")

# Health endpoint


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "ok"}


# Register routers
app.include_router(auth.router)
app.include_router(bounties.router)
app.include_router(applications.router)
app.include_router(webhooks.router)
