from __future__ import annotations

from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware

from app.api import applications, auth, bounties, webhooks

app = FastAPI(title="Headhunt Bounty API", version="0.1.0")

ALLOWED_ORIGINS = [
    # frontend addr. here
    "https://cardpass.lidarbtc.workers.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{path:path}", include_in_schema=False)
async def handle_options(path: str) -> Response:
    return Response(status_code=200)


@app.middleware("http")
async def ensure_cors_headers(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    allow_origin = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    if "access-control-allow-origin" not in response.headers:
        response.headers["Access-Control-Allow-Origin"] = allow_origin
    if "access-control-allow-credentials" not in response.headers:
        response.headers["Access-Control-Allow-Credentials"] = "true"
    if "access-control-allow-methods" not in response.headers:
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    if "access-control-allow-headers" not in response.headers:
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Health endpoint


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "ok"}


# Register routers
app.include_router(auth.router)
app.include_router(bounties.router)
app.include_router(applications.router)
app.include_router(webhooks.router)
