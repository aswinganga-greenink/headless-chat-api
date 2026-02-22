from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.core.connection_manager import manager
from src.models.all_models import User
from src.api.deps import get_current_user_ws

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for realtime communication.
    Clients connect here with their token as a query parameter.
    """
    user_id_str = str(current_user.id)
    await manager.connect(user_id_str, websocket)
    
    try:
        while True:
            # We just wait for incoming messages to keep the connection open
            # Future expansion: handle incoming 'typing' events, presence, etc.
            data = await websocket.receive_text()
            
            # For debugging/ping-pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(user_id_str, websocket)
