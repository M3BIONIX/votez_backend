from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocket as StarletteWebSocket

from core.connection_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    import logging
    logger = logging.getLogger(__name__)
    logger.info("WebSocket connection attempt received")
    
    await manager.connect(websocket)
    logger.info("WebSocket connected successfully")
    
    try:
        # Send initial connection message
        await websocket.send_json({"type": "connected", "data": "WebSocket connected successfully"})
        logger.info("Sent initial connection message")
        
        while True:   
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
            await websocket.send_json({"type": "pong", "data": "Echo: " + data})
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        logger.info("WebSocket connection closed")