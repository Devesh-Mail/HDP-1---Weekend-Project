"""FastAPI main application — HR Employee Chatbot backend."""
import uuid
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq

import backend.config as cfg
from backend.auth import authenticate_user, create_access_token, get_current_user
from backend.logger import log
from backend.models import (
    LoginRequest,
    LoginResponse,
    ConfigureKeyRequest,
    ChatRequest,
    ChatResponse,
    UserInfo,
)
from backend.agents.supervisor import run_supervisor
from backend.tools.read_tools import get_my_details

app = FastAPI(
    title="HR Employee Chatbot API",
    description="Multi-agent HR chatbot backed by Supabase and GROQ.",
    version="1.0.0",
)


@app.on_event("startup")
async def _on_startup() -> None:
    log.info("HR Employee Chatbot backend starting up", version="1.0.0")

# ── CORS — allow the React dev server ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store: session_id → [{"role", "content"}] ──────────────
_sessions: dict[str, list[dict]] = {}


def _get_or_create_session(session_id: str | None) -> tuple[str, list[dict]]:
    sid = session_id or str(uuid.uuid4())
    if sid not in _sessions:
        _sessions[sid] = []
    return sid, _sessions[sid]


def _require_groq() -> Groq:
    key = cfg.get_groq_key()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GROQ API key not configured. Please set it via POST /auth/configure-key.",
        )
    return Groq(api_key=key)


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/auth/login", response_model=LoginResponse, tags=["Auth"])
async def login(body: LoginRequest):
    """Authenticate with employee_id + password. Returns a JWT."""
    log.api("POST /auth/login", employee_id=body.employee_id)
    user = authenticate_user(body.employee_id, body.password)
    if not user:
        log.auth("login_failed", employee_id=body.employee_id, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid employee ID or password.",
        )
    token = create_access_token(user["employee_id"], user["status"])
    log.auth("login_success", employee_id=user["employee_id"], level=user["status"], success=True)
    return LoginResponse(
        access_token=token,
        employee_id=user["employee_id"],
        status=user["status"],
    )


@app.post("/auth/configure-key", tags=["Auth"])
async def configure_groq_key(body: ConfigureKeyRequest):
    """Set the GROQ API key at runtime. Key is kept in memory only."""
    log.api("POST /auth/configure-key")
    if not body.groq_api_key.startswith("gsk_"):
        log.warn("configure-key rejected: bad format")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GROQ API key format. It should start with 'gsk_'.",
        )
    cfg.set_groq_key(body.groq_api_key)
    log.auth("groq_key_configured", success=True)
    return {"status": "ok", "message": "GROQ API key configured successfully."}


@app.get("/auth/key-status", tags=["Auth"])
async def key_status():
    """Check whether the GROQ API key has been configured."""
    log.api("GET /auth/key-status")
    return {"configured": bool(cfg.get_groq_key())}


@app.get("/auth/me", response_model=UserInfo, tags=["Auth"])
async def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    """Get the authenticated employee's profile info."""
    employee_id = current_user["employee_id"]
    level = current_user["status"]
    log.api("GET /auth/me", employee_id=employee_id, level=level)
    details = get_my_details(employee_id, level)
    name = ""
    if details.get("status") == "ok" and details.get("data"):
        name = details["data"].get("name", "")
    return UserInfo(
        employee_id=employee_id,
        status=level,
        name=name,
        details=details.get("data", {}),
    )


# ── Chat routes ───────────────────────────────────────────────────────────────

@app.post("/chat/message", response_model=ChatResponse, tags=["Chat"])
async def chat_message(
    body: ChatRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Send a message to the HR chatbot. Returns the AI's reply."""
    groq = _require_groq()
    employee_id = current_user["employee_id"]
    level = current_user["status"]

    session_id, history = _get_or_create_session(body.session_id)
    log.api(
        "POST /chat/message",
        employee_id=employee_id,
        level=level,
        session_id=session_id,
        message_preview=body.message[:80],
    )

    result = run_supervisor(
        groq_client=groq,
        employee_id=employee_id,
        level=level,
        user_message=body.message,
        history=history,
    )

    steps_count = len(result.get("steps", []))
    log.agent("supervisor", "turn complete", employee_id=employee_id, steps=steps_count)

    # Update session history
    history.append({"role": "user", "content": body.message})
    history.append({"role": "assistant", "content": result["reply"]})
    # Keep last 20 messages to avoid unbounded growth
    _sessions[session_id] = history[-20:]

    return ChatResponse(
        reply=result["reply"],
        session_id=session_id,
        steps=result.get("steps", []),
    )


@app.get("/chat/history", tags=["Chat"])
async def chat_history(
    session_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Retrieve conversation history for a given session."""
    employee_id = current_user["employee_id"]
    log.api("GET /chat/history", employee_id=employee_id, session_id=session_id)
    history = _sessions.get(session_id, [])
    return {"session_id": session_id, "messages": history}


@app.delete("/chat/history", tags=["Chat"])
async def clear_history(
    session_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Clear the conversation history for a session."""
    employee_id = current_user["employee_id"]
    log.api("DELETE /chat/history", employee_id=employee_id, session_id=session_id)
    _sessions.pop(session_id, None)
    return {"status": "cleared"}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    log.api("GET /health")
    return {"status": "ok", "groq_key_set": bool(cfg.get_groq_key())}
