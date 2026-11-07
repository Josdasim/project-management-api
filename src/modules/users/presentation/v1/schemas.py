from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

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

    @model_validator(mode = "after")
    def first_name_cannot_be_null(self) -> Self:
        if "fist_name" in self.model_fields_set and self.first_name is None:
            raise ValueError("El nombre no puede ser nulo")

        return self
