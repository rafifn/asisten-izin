from fastapi import FastAPI

from app.errors import install_error_handlers
from app.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Asisten Izin Kuliner")
    install_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
