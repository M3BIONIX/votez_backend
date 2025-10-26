from fastapi import APIRouter
from api.poll_api import router as poll_router
from api.websocket_api import router as websocket_router


api_router = APIRouter()
api_router.include_router(poll_router, tags=["poll"])
api_router.include_router(websocket_router, tags=["websocket"])