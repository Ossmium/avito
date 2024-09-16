import uuid
import datetime
from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    username: str
    first_name: str
    last_name: str


class UserSchema(BaseModel):
    id: uuid.UUID
    username: str
    first_name: str
    last_name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
