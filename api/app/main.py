from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.deps import build_embedder, build_llm, warn_on_embedder_mismatch
from app.errors import CatchAllMiddleware, install_error_handlers
from app.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    cors_cfg = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Built once at startup; tests bypass this by overriding the dependencies.
        cfg = settings or Settings.from_env()
        app.state.settings = cfg
        app.state.llm = build_llm(cfg)
        app.state.embedder = build_embedder(cfg)
        warn_on_embedder_mismatch(cfg)
        yield

    app = FastAPI(title="Asisten Izin Kuliner", lifespan=lifespan)
    # Order matters: the middleware added last is outermost. CORS must wrap the catch-all so
    # unhandled 500s carry CORS headers.
    app.add_middleware(CatchAllMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_cfg.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )
    install_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
