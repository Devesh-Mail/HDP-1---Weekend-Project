"""Application configuration — reads from .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in backend directory first, then cwd/parents
_backend_env = Path(__file__).resolve().parent / ".env"
if _backend_env.exists():
    load_dotenv(dotenv_path=_backend_env)
else:
    load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
JWT_SECRET: str = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

# GROQ API key — set at runtime via /auth/configure-key endpoint
# Never persisted to disk; resets on server restart.
_groq_api_key: str = ""


def get_groq_key() -> str:
    return _groq_api_key


def set_groq_key(key: str) -> None:
    global _groq_api_key
    _groq_api_key = key.strip()
