from pydantic import BaseModel


class CurrentUser(BaseModel):
    sub: str
    username: str | None = None
    client_id: str | None = None
    token_use: str | None = None
    scope: str | None = None
    iss: str | None = None