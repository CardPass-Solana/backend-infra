from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, AccountRole


async def get_or_create_account(
    session: AsyncSession,
    wallet: str,
    role: AccountRole,
    display_name: Optional[str] = None,
) -> Account:
    """Fetch an account by wallet or create it with the provided role."""
    normalized_wallet = wallet.strip()
    if not normalized_wallet:
        raise ValueError("wallet must be provided")

    result = await session.execute(
        select(Account).where(Account.wallet == normalized_wallet)
    )
    account = result.scalar_one_or_none()
    if account:
        return account

    account = Account(
        wallet=normalized_wallet,
        role=role,
        display_name=display_name,
    )
    session.add(account)
    await session.flush()
    return account


async def get_account_by_wallet(
    session: AsyncSession, wallet: str
) -> Optional[Account]:
    result = await session.execute(select(Account).where(Account.wallet == wallet))
    return result.scalar_one_or_none()

