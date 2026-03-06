from datetime import datetime, timezone
from fastapi import APIRouter
from database import get_pool
from services.connection_manager import ConnectionManager


def get_health_router(manager: ConnectionManager) -> APIRouter:
    """Create and configure the health check router.
    
    Args:
        manager: The WebSocket connection manager.
    
    Returns:
        The configured router.
    """
    router = APIRouter(tags=["System"])

    @router.get("/health")
    async def health():
        """Health check and connection status.
        
        Returns:
            A dict with status, WebSocket connection count, and timestamp.
        """
        pool = await get_pool()
        # Quick DB ping
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {
            "status": "ok",
            "websocket_connections": manager.connection_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return router
