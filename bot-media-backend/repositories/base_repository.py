import asyncpg
from database import get_pool


class BaseRepository:

    async def get_pool(self) -> asyncpg.Pool:
        """Get the active database connection pool.
        
        Returns:
            The asyncpg connection pool.
        """
        return await get_pool()
