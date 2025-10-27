from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocket as StarletteWebSocket

from core.connection_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connection message
        await websocket.send_json({"type": "connected", "data": "WebSocket connected successfully"})
        
        while True:   
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "data": "Echo: " + data})
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass
    finally:
        manager.disconnect(websocket)