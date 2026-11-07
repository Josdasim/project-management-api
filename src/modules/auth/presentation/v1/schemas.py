from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel, ConfigDict, EmailStr,
    Field, StringConstraints, field_validator
)

from src.modules.auth.domain.enums import AccountStatus

USERNAME_MIN, USERNAME_MAX = 3, 30
EMAIL_MAX = 255
PASSWORD_MIN, PASSWORD_MAX = 12, 128
NAME_MAX = 100

NameStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX)
    ]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra = "forbid")

    username: str = Field(
        min_length = USERNAME_MIN,
        max_length = USERNAME_MAX,
        pattern = r"^[A-Za-z0-9_.-]+$"
    )
    email: EmailStr
    password: str = Field(
        min_length = PASSWORD_MIN,
        max_length = PASSWORD_MAX,
        repr = False
    )
    first_name: NameStr
    last_name: NameStr | None = None

    @field_validator("email")
    @classmethod
    def email_not_too_long(cls, value: str) -> str:
        if len(value) > EMAIL_MAX:
            raise ValueError(f"El correo no puede superar {EMAIL_MAX} caracteres")
        return value


class RegisterResponse(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str | None
    status: AccountStatus
    created_at: datetime

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra = "forbid")

    identifier: str = Field(min_length = 1, max_length = EMAIL_MAX)
    password: str = Field(min_length = 1, max_length = PASSWORD_MAX, repr = False)

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AccountResponse(BaseModel):
    username: str
    email: str
    status: AccountStatus
    created_at: datetime