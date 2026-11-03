from __future__ import annotations

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    nome: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    email: str


class User(BaseModel):
    id: str
    email: str


class MetaOAuthURL(BaseModel):
    url: str


class MetaCallbackResponse(BaseModel):
    success: bool
    accounts_found: int
    accounts: list[dict]
