from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.connection_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:   
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "data": "Connected"})
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)