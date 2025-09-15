import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _str_to_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv_if_available():
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    # Load root .env if present, then app/.env overriding
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(Path(__file__).resolve().parent / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    # Auth challenge
    AUTH_DOMAIN: str = "example.com"
    AUTH_CHALLENGE_TTL_SECONDS: int = 300

    # JWT
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALG: str = "HS256"
    JWT_TTL_SECONDS: int = 3600
    JWT_ISSUER: str = "example.com"
    JWT_AUDIENCE: Optional[str] = None

    # Cookie
    JWT_COOKIE_NAME: str = "auth_token"
    JWT_COOKIE_DOMAIN: Optional[str] = None
    JWT_COOKIE_SECURE: bool = True
    JWT_COOKIE_SAMESITE: str = "lax"  # lax | strict | none
    JWT_COOKIE_PATH: str = "/"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is not None:
        return _settings

    _load_dotenv_if_available()

    auth_domain = os.getenv("AUTH_DOMAIN", Settings.AUTH_DOMAIN)
    settings = Settings(
        AUTH_DOMAIN=auth_domain,
        AUTH_CHALLENGE_TTL_SECONDS=int(
            os.getenv("AUTH_CHALLENGE_TTL_SECONDS", Settings.AUTH_CHALLENGE_TTL_SECONDS)
        ),
        JWT_SECRET=os.getenv("JWT_SECRET", Settings.JWT_SECRET),
        JWT_ALG=os.getenv("JWT_ALG", Settings.JWT_ALG),
        JWT_TTL_SECONDS=int(os.getenv("JWT_TTL_SECONDS", Settings.JWT_TTL_SECONDS)),
        JWT_ISSUER=os.getenv("JWT_ISSUER", auth_domain),
        JWT_AUDIENCE=os.getenv("JWT_AUDIENCE", None) or None,
        JWT_COOKIE_NAME=os.getenv("JWT_COOKIE_NAME", Settings.JWT_COOKIE_NAME),
        JWT_COOKIE_DOMAIN=os.getenv("JWT_COOKIE_DOMAIN", None) or None,
        JWT_COOKIE_SECURE=_str_to_bool(os.getenv("JWT_COOKIE_SECURE"), True),
        JWT_COOKIE_SAMESITE=os.getenv("JWT_COOKIE_SAMESITE", Settings.JWT_COOKIE_SAMESITE).lower(),
        JWT_COOKIE_PATH=os.getenv("JWT_COOKIE_PATH", Settings.JWT_COOKIE_PATH),
    )

    _settings = settings
    return settings
