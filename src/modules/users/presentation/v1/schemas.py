from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

NAME_MAX = 100
NameStr = Annotated[
    str, StringConstraints(strip_whitespace = True, min_length = 1, max_length = NAME_MAX)
]


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
