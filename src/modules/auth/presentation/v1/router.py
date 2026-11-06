from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.application.services.register_account import RegisterAccountService
from src.modules.auth.domain.exceptions import (
    EmailAlreadyExistsError, UsernameAlreadyExistsError
)
from src.modules.auth.presentation.dependencies import get_register_service
from src.modules.auth.presentation.v1.schemas import RegisterRequest, RegisterResponse


router = APIRouter(prefix = "/auth", tags = ["auth"])

@router.post(
    "/register", response_model = RegisterResponse,
    status_code = status.HTTP_201_CREATED
)
def register(
    payload: RegisterRequest,
    service: Annotated[RegisterAccountService, Depends(get_register_service)]
) -> RegisterResponse:
    try:
        result = service.register(
            username = payload.username,
            email = payload.email,
            password = payload.password,
            first_name = payload.first_name,
            last_name = payload.last_name
        )
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El nombre de usuario ya esta registrado"
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El correo electronico ya esta registrado"
        )

    return RegisterResponse(
        username = result.account.username,
        email = result.account.email,
        first_name = result.user.first_name,
        last_name = result.user.last_name,
        status = result.account.status,
        created_at = result.account.created_at
    )