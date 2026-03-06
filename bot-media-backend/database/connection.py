import asyncpg
from pathlib import Path
from config import settings

# Module level pool - set during app startup, torn down on shutdown
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Return the active connection pool.
    
    Returns:
        The module-level asyncpg connection pool.
    
    Raises:
        RuntimeError: If the pool has not been initialised. Call init_db() first.
    """
    if _pool is None:
        raise RuntimeError("Database pool has not been initialised. Call init_db() first.")
    return _pool


async def init_db() -> None:
    """Create the connection pool and run idempotent schema migrations.
    
    Creates the global asyncpg pool connected to DATABASE_URL and executes
    the DDL from init.sql to ensure agents and posts tables exist with
    proper indexes.
    
    Called during FastAPI lifespan startup.
    """
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    
    # Read and execute init.sql
    sql_file = Path(__file__).parent / "init.sql"
    schema_sql = sql_file.read_text()
    
    async with _pool.acquire() as conn:
        await conn.execute(schema_sql)


async def close_db() -> None:
    """Gracefully close all connections in the pool.
    
    Called during FastAPI lifespan shutdown.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
