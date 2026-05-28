from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.anomalies import router as anomalies_router
from api.routes.auth import router as auth_router
from api.routes.claims import router as claims_router
from api.routes.connection import router as connection_router
from api.routes.dashboard import router as dashboard_router
from api.routes.dataset import router as dataset_router
from api.routes.departments import router as departments_router
from api.routes.exports import router as exports_router
from api.routes.health import router as health_router
from api.routes.insights import router as insights_router
from api.routes.project import router as project_router
from api.routes.refresh import router as refresh_router
from api.routes.run import router as run_router
from api.routes.source_type import router as source_type_router
from cache.cache_store import CacheStore
from cache.config_cache import ConfigCache
from cache.hooks import (
    register_listener,
)
from cache.invalidation import CacheInvalidator
from cache.routing_cache import RoutingCache
from common.database import init_db, session_factory
from common.errors import AppError, IngestionTransformNotAllowedError
from control_plane.admin_router import router as admin_router

_cache_listeners_registered = False


def create_app() -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _cache_listeners_registered
        init_db()
        if not _cache_listeners_registered:
            cache_store = CacheStore()
            routing_cache = RoutingCache(cache_store, session_factory)
            config_cache = ConfigCache(cache_store)
            invalidator = CacheInvalidator(routing_cache, config_cache)

            def handle_cache_event(event_type: str, tenant_id: str, **kwargs):
                handlers = {
                    "provisioned": lambda: invalidator.on_tenant_provisioned(tenant_id),
                    "suspended": lambda: invalidator.on_tenant_suspended(tenant_id),
                    "restored": lambda: invalidator.on_tenant_restored(tenant_id),
                    "config_changed": lambda: invalidator.on_tenant_config_changed(tenant_id, kwargs.get("key")),
                    "database_rotation": lambda: invalidator.on_database_rotation(
                        tenant_id, kwargs.get("old_ref", ""), kwargs.get("new_ref", "")
                    ),
                    "schema_rollout": invalidator.on_schema_rollout,
                }
                handler = handlers.get(event_type)
                if handler is not None:
                    handler()

            register_listener(handle_cache_event)
            _cache_listeners_registered = True
        yield

    app = FastAPI(title="Canopy Intelligence API", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(IngestionTransformNotAllowedError)
    async def ingestion_transform_not_allowed_handler(
        request: Request, exc: IngestionTransformNotAllowedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "blocked_keys": exc.blocked_keys,
            },
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3005"],
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
    app.include_router(admin_router)
    app.include_router(project_router, prefix="/api")
    app.include_router(source_type_router, prefix="/api")
    app.include_router(connection_router, prefix="/api")
    app.include_router(dataset_router, prefix="/api")
    app.include_router(run_router, prefix="/api")

    return app


app = create_app()
