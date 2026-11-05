from fastapi import APIRouter

from src.modules.auth.presentation.v1.router import router as auth_router

api_router = APIRouter(prefix = "/api/v1")
api_router.include_router(auth_router)