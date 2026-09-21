"""Pydantic models for request/response validation."""
from pydantic import BaseModel
from typing import Optional


# ── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    employee_id: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee_id: str
    status: str  # level1 / level2 / level3


class ConfigureKeyRequest(BaseModel):
    groq_api_key: str


class UserInfo(BaseModel):
    employee_id: str
    status: str
    name: str
    details: dict


# ── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    steps: list[dict] = []  # agent tool call trace for debugging


# ── Employee detail models ───────────────────────────────────────────────────

class Level1Staff(BaseModel):
    staff_id: str
    employee_id: str
    name: str
    contact_number: int
    current_address: str


class Level2Manager(BaseModel):
    manager_id: str
    employee_id: str
    name: str
    contact_number: int
    office_number: int
    current_address: str


class Level3Boss(BaseModel):
    boss_id: str
    employee_id: str
    name: str
    current_address: str
