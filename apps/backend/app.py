from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.anomalies import router as anomalies_router
from api.routes.auth import router as auth_router
from api.routes.claims import router as claims_router
from api.routes.dashboard import router as dashboard_router
from api.routes.departments import router as departments_router
from api.routes.exports import router as exports_router
from api.routes.health import router as health_router
from api.routes.insights import router as insights_router
from api.routes.project import router as project_router
from api.routes.source_type import router as source_type_router
from api.routes.connection import router as connection_router
from api.routes.dataset import router as dataset_router
from api.routes.run import router as run_router
from api.routes.refresh import router as refresh_router
from common.database import init_db
from common.errors import AppError


def create_app() -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db()
        yield

    app = FastAPI(title="HERD Aggregator API", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(departments_router)
    app.include_router(claims_router)
    app.include_router(anomalies_router)
    app.include_router(refresh_router)
    app.include_router(exports_router)
    app.include_router(insights_router)
    app.include_router(project_router, prefix="/api")
    app.include_router(source_type_router, prefix="/api")
    app.include_router(connection_router, prefix="/api")
    app.include_router(dataset_router, prefix="/api")
    app.include_router(run_router, prefix="/api")

    app.include_router(project_router, prefix="/api/v4")
    app.include_router(source_type_router, prefix="/api/v4")
    app.include_router(connection_router, prefix="/api/v4")
    app.include_router(dataset_router, prefix="/api/v4")
    app.include_router(run_router, prefix="/api/v4")

    return app


app = create_app()
