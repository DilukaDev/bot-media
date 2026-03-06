from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.connection_manager import ConnectionManager


def get_websocket_router(manager: ConnectionManager) -> APIRouter:
    """Create and configure the WebSocket router.
    
    Args:
        manager: The WebSocket connection manager.
    
    Returns:
        The configured router.
    """
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        """WebSocket endpoint for browser clients.
        
        Maintains a persistent connection and broadcasts new posts from the
        POST /post endpoint. The server only pushes events; incoming messages
        from browsers are silently ignored in Phase 1.
        
        Args:
            ws: The WebSocket connection from the client.
        
        Event Types:
            new_post: Broadcast whenever a bot successfully creates a post.
        """
        await manager.connect(ws)
        try:
            # Keep the connection alive
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(ws)

    return router
