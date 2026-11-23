import logging
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(
        self, status: int, code: str, message: str, request_id: UUID | None = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        # Set when the failed request was logged to query_log (lets the eval find its cost).
        self.request_id = request_id


def _body(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _body(exc.status, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return _body(404, "not_found", "Tidak ditemukan.")
        if exc.status_code < 500:
            return _body(400, "invalid_input", "Permintaan tidak valid.")
        return _body(500, "internal", "Terjadi kesalahan pada server.")

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _body(400, "invalid_input", "Input tidak valid.")

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", exc_info=exc)
        return _body(500, "internal", "Terjadi kesalahan pada server.")


class CatchAllMiddleware:
    """Turns an unhandled exception into the 500 error envelope.

    Added *inside* CORSMiddleware, so the 500 still carries CORS headers and the browser can read
    it. (A handler for `Exception` alone runs in Starlette's outermost ServerErrorMiddleware,
    outside CORS, so its response has no `access-control-allow-origin`.)
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def _send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception:
            log.exception("unhandled error")
            if started:
                raise
            await _body(500, "internal", "Terjadi kesalahan pada server.")(scope, receive, send)
