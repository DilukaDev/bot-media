from typing import Annotated
from asyncpg import Record
from fastapi import Header, HTTPException, status
from config import settings
from database import get_pool


async def require_agent(
    x_api_key: Annotated[str, Header(alias="X-API-KEY", description="Bot's unique API key.")],
) -> Record:
    """FastAPI dependency to inject bot authentication.
    
    Looks up X-API-KEY in the agents table and returns the full asyncpg
    Record for the matching agent.
    
    Args:
        x_api_key: The X-API-KEY header value.
    
    Returns:
        The asyncpg Record for the authenticated agent.
    
    Raises:
        HTTPException: 401 Unauthorized if the key is invalid or missing.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        agent = await conn.fetchrow(
            "SELECT * FROM agents WHERE api_key = $1",
            x_api_key,
        )
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
    return agent


async def require_admin(
    x_api_key: Annotated[str, Header(alias="X-API-KEY", description="Master admin API key.")],
) -> None:
    """FastAPI dependency to inject admin authentication.
    
    Args:
        x_api_key: The X-API-KEY header value.
    
    Raises:
        HTTPException: 401 Unauthorized if the key does not match ADMIN_API_KEY.
    """
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin access required.",
        )
