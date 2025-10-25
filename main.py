from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
import uvicorn
from core.settings import settings

app = FastAPI(title="Votez API", version="1.0.0")

add_pagination(app)


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=32400,
        expose_headers=["Content-Disposition"],
    )
@app.get("/")
async def root():
    return {"message": "Votez API", "version": "1.0.0"}


if __name__ == "__main__":
    run_args = {
        "app": "main:app",
        "host": settings.SERVER_ADDRESS,
        "port": settings.SERVER_PORT,
        "log_level": settings.LOG_LEVEL,
        "reload": settings.WATCH_FILES,
    }

    uvicorn.run(**run_args)
