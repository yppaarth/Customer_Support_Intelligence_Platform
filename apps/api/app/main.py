from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import Base, engine
import app.models  # noqa: F401
from app.observability.logging import configure_logging, correlation_middleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(title="ResolveIQ API", version="0.1.0")
    app.middleware("http")(correlation_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.on_event("startup")
    def create_dev_schema() -> None:
        if settings.database_url.startswith("sqlite"):
            Base.metadata.create_all(bind=engine)

    return app


app = create_app()
