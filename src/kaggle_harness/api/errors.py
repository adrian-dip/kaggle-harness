import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=str(request.url.path), error=str(exc), exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
