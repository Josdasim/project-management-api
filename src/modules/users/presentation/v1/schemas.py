from typing import Annotated, Self

from pydantic import (
    BaseModel, ConfigDict, StringConstraints, field_validator, Field, model_validator
)

NAME_MAX = 100
NameStr = Annotated[
    str, StringConstraints(strip_whitespace = True, min_length = 1, max_length = NAME_MAX)
]
USERNAME_MAX = 30
EMAIL_MAX = 255


class ProfileResponse(BaseModel):
    username: str
    first_name: str
    last_name: str | None

class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra = "forbid")

    first_name: NameStr | None = None
    last_name: NameStr | None = None

    @field_validator("first_name")
    @classmethod
    def first_name_cannot_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("El nombre no puede ser nulo")

        return value

class UserSearchParams(BaseModel):
    model_config = ConfigDict(extra = "forbid")

    username: str | None = Field(default = None, min_length = 1, max_length = USERNAME_MAX)
    email: str | None = Field(default = None, min_length = 1, max_length = EMAIL_MAX)

    @model_validator(mode = "after")
    def exactly_one_criterion(self) -> Self:
        if (self.username is None) == (self.email is None):
            raise ValueError(
                "Debe proporcionar exactamente uno de los parametros username o email"
            )
        return self
