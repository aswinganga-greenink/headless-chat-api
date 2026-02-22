import uuid
from typing import Dict, List, Any
from fastapi import WebSocket

class ConnectionManager:
    """
    Manages active WebSocket connections to the API.
    A single user might have multiple active connections (e.g., mobile and desktop).
    """
    def __init__(self):
        # Maps user ID (as string) to a list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: Any, user_id: str):
        """
        Send a JSON message to all active connections of a specific user.
        """
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be dead
                    pass

# Global instance for the server
manager = ConnectionManager()
