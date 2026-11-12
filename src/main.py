from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.core.models_registry
from src.api.v1.router import api_router
from src.core.config import settings
from src.core.exceptions import register_exception_handlers

app = FastAPI(
    title="Project Management API",
    description="API REST para la gestion de proyectos, equipos y tareas.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"]
)
register_exception_handlers(app)

app.include_router(api_router)
