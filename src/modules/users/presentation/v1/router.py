from typing import Annotated

from fastapi import APIRouter, Depends

from src.modules.auth.public import Account, get_current_account
from src.modules.users.application.services.get_profile import GetProfileService
from src.modules.users.application.services.update_profile import UpdateProfileService
from src.modules.users.presentation.dependencies import (
    get_profile_service, get_update_profile_service
)
from src.modules.users.presentation.v1.schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix = "/users", tags = ["users"])


@router.get("/me", response_model = ProfileResponse)
def read_profile(
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[GetProfileService, Depends(get_profile_service)]
) -> ProfileResponse:
    user = service.get(account.user_id)

    return ProfileResponse(
        username = account.username,
        first_name = user.first_name,
        last_name = user.last_name
    )

@router.patch("/me", response_model = ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[UpdateProfileService, Depends(get_update_profile_service)]
) -> ProfileResponse:
    user = service.update(account.user_id, payload.model_dump(exclude_unset = True))
    return ProfileResponse(
        username = account.username,
        first_name = user.first_name,
        last_name = user.last_name
    )
