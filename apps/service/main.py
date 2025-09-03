from fastapi import FastAPI
from .routes import router

def create_app() -> FastAPI:
    app = FastAPI(title="APF Service", version="0.1.0")
    app.include_router(router)
    return app

app = create_app()