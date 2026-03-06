import json
from fastapi import WebSocket


class ConnectionManager:

    def __init__(self) -> None:
        self._active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        """Accept and register a new WebSocket connection.
        
        Args:
            ws: The WebSocket connection from a client.
        """
        await ws.accept()
        self._active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        """Remove a disconnected WebSocket from tracking.
        
        Args:
            ws: The WebSocket connection to remove.
        """
        self._active.remove(ws)

    async def broadcast(self, payload: dict) -> None:
        """Send JSON to all connected browser clients.
        
        Automatically removes dead sockets that fail during transmission.
        
        Args:
            payload: Dictionary to JSON-encode and push to clients.
        """
        message = json.dumps(payload, default=str)
        dead: list[WebSocket] = []
        for ws in self._active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._active.remove(ws)

    @property
    def connection_count(self) -> int:
        """Return the number of active WebSocket connections.
        
        Returns:
            Count of active connections.
        """
        return len(self._active)
