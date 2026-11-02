from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.exceptions import AppError
from app.schemas.generation import CardResponse, GenerateRequest
from app.services.generation_service import generate_card


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        f"{'.'.join(str(part) for part in error['loc'][1:])}: {error['msg']}"
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": {
                "code": "validation_error",
                "message": "Некорректные входные данные",
                "details": details,
            },
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": {
                "code": "internal_error",
                "message": "Внутренняя ошибка приложения",
            },
        },
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
        ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "up"}

    @app.post("/api/v1/generate", response_model=CardResponse)
    async def generate(payload: GenerateRequest) -> CardResponse:
        card = await generate_card(payload)
        return CardResponse(data=card)

    @app.get("/api/v1/models")
    async def list_models() -> dict:
        tiers = settings.model_tiers
        return {
            "models": {
                provider: {tier: settings.model_for(provider, tier) for tier in tiers}
                for provider in ("openai", "gemini", "routerai")
            }
        }

    return app


app = create_app()
