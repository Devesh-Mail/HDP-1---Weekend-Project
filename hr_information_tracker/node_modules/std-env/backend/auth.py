"""JWT authentication and current-user dependency."""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from backend.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from backend.supabase_client import get_supabase

bearer_scheme = HTTPBearer()


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt (direct, no passlib wrapper)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(employee_id: str, status: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": employee_id, "status": status, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )


def authenticate_user(employee_id: str, password: str) -> dict | None:
    """Validate credentials against Supabase login table. Returns user row or None."""
    sb = get_supabase()
    result = sb.table("login").select("*").eq("employee_id", employee_id).single().execute()
    if not result.data:
        return None
    user = result.data
    if not verify_password(password, user["password"]):
        return None
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    """FastAPI dependency — validates JWT and returns {employee_id, status}."""
    payload = decode_token(credentials.credentials)
    employee_id: str = payload.get("sub", "")
    emp_status: str = payload.get("status", "")
    if not employee_id or not emp_status:
        raise HTTPException(status_code=401, detail="Invalid token payload.")
    return {"employee_id": employee_id, "status": emp_status}
