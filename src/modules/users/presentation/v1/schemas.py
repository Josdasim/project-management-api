from pydantic import BaseModel


class ProfileResponse(BaseModel):
    username: str
    first_name: str
    last_name: str | None
