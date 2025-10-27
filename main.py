from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
import uvicorn
from core.settings import settings
from api.api import api_router

app = FastAPI(title="Votez API", version="1.0.0")

# Debug: Log CORS configuration
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"BACKEND_CORS_ORIGINS value: {settings.BACKEND_CORS_ORIGINS}")
logger.info(f"BACKEND_CORS_ORIGINS type: {type(settings.BACKEND_CORS_ORIGINS)}")
logger.info(f"BACKEND_CORS_ORIGINS length: {len(settings.BACKEND_CORS_ORIGINS) if settings.BACKEND_CORS_ORIGINS else 0}")

# Add CORS middleware BEFORE including routes (important for WebSocket)
# Always add CORS middleware to ensure WebSocket connections work
if settings.BACKEND_CORS_ORIGINS:
    logger.info(f"Adding CORS middleware with origins: {settings.BACKEND_CORS_ORIGINS}")
    cors_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
else:
    # Default to wildcard for development/production flexibility
    logger.info("No CORS origins configured, using wildcard")
    cors_origins = ["*"]

# Always add CORS middleware to ensure WebSocket connections work
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],  # Don't use credentials with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=32400,
    expose_headers=["Content-Disposition"],
)

add_pagination(app)

app.include_router(api_router)

logger.info("FastAPI app initialized with CORS middleware")

@app.get("/")
async def root():
    return {"message": "Votez API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "frontend_url": settings.FRONTEND_URL
    }


if __name__ == "__main__":
    run_args = {
        "app": "main:app",
        "host": settings.SERVER_ADDRESS,
        "port": settings.SERVER_PORT,
        "log_level": settings.LOG_LEVEL,
        "reload": settings.WATCH_FILES,
    }

    uvicorn.run(**run_args)
