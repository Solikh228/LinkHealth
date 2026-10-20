from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    id: str
    email: str
    createdAt: str

    model_config = ConfigDict(from_attributes=True)


class Workspace(BaseModel):
    id: str
    name: str
    ownerUserId: str
    baseCurrency: str = "USD"
    createdAt: str

    model_config = ConfigDict(from_attributes=True)


class SessionRequest(BaseModel):
    email: str
    password: str


class SessionResponse(BaseModel):
    token: str
    user: User
