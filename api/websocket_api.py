import json
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
            await websocket.send_text(json.dumps({"type": "pong", "data": "Connected"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)