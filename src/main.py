from fastapi import FastAPI
from src.api.router import api_router
import src.core.models_registry

app = FastAPI(
    title="Project Management API",
    description="API REST para la gestion de proyectos, equipos y tareas.",
    version="0.1.0"
)

app.include_router(api_router)