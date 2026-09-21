"""Centralized structured logger for the HR Employee Chatbot backend.

Emits colourised, timestamped records to stdout AND writes to a rotating
log file (logs/backend.log, max 5 MB × 3 backups).

Usage
-----
    from backend.logger import log

    log.api("POST /auth/login", employee_id="EMP001", status=200)
    log.tool("get_my_details", caller="EMP001", level="level1", result_summary={"status":"ok"})
    log.agent("details", "Fetching own profile", employee_id="EMP001")
    log.auth("login_attempt", employee_id="EMP001", success=True)
    log.warn("Something unexpected happened")
    log.error("Unhandled exception")
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Colours (ANSI) ────────────────────────────────────────────────────────────

_NO_COLOUR = not sys.stdout.isatty() or bool(os.environ.get("NO_COLOR"))

_C = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "cyan":    "\033[96m",
    "magenta": "\033[95m",
    "red":     "\033[91m",
    "blue":    "\033[94m",
    "white":   "\033[97m",
}


def _c(colour: str, text: str) -> str:
    if _NO_COLOUR:
        return text
    return f"{_C.get(colour, '')}{text}{_C['reset']}"


# ── Label colours per category ────────────────────────────────────────────────

_CATEGORY_STYLE: dict[str, tuple[str, str]] = {
    "API":    ("green",   "NET "),
    "TOOL":   ("cyan",    "TOOL"),
    "AGENT":  ("magenta", "AGNT"),
    "AUTH":   ("yellow",  "AUTH"),
    "DB":     ("blue",    " DB "),
    "WARN":   ("yellow",  "WARN"),
    "ERROR":  ("red",     " ERR"),
    "INFO":   ("white",   "INFO"),
}


# ── File handler (rotating JSON lines) ───────────────────────────────────────

_LOG_DIR = Path(__file__).parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "backend.log"

_file_handler = logging.handlers.RotatingFileHandler(
    _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter("%(message)s"))

_logger_root = logging.getLogger("hr_chatbot")
_logger_root.setLevel(logging.DEBUG)
# Avoid duplicate handlers if module is reloaded
if not _logger_root.handlers:
    _logger_root.addHandler(_file_handler)
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setFormatter(logging.Formatter("%(message)s"))
    _logger_root.addHandler(_console_handler)
else:
    _console_handler = next(
        (h for h in _logger_root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)),
        logging.StreamHandler(sys.stdout),
    )


# ── Core emit ────────────────────────────────────────────────────────────────

def _emit(category: str, message: str, **fields: Any) -> None:
    """Format and emit one log line to both console (coloured) and file (JSON)."""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    colour, icon = _CATEGORY_STYLE.get(category, ("white", "    "))
    label_text = f"[{icon}]"
    label = _c(colour, label_text)
    timestamp = _c("dim", f"[{ts}]")

    # Build extras string for console
    extras_parts = []
    for k, v in fields.items():
        key_str = _c("dim", f"{k}=")
        val_str = _c("white", repr(v))
        extras_parts.append(key_str + val_str)
    extras_str = ("  " + "  ".join(extras_parts)) if extras_parts else ""

    console_line = f"{timestamp} {label} {_c('bold', message)}{extras_str}"

    # JSON line for the log file
    log_record = {
        "ts": now.timestamp(),
        "time": ts,
        "category": category,
        "message": message,
        **fields,
    }
    file_line = json.dumps(log_record, default=str)

    _logger_root.info(console_line)  # goes to both handlers via logger
    # Also write raw JSON to file handler directly
    _file_handler.stream.write(file_line + "\n")
    _file_handler.stream.flush()


# ── Public Logger API ─────────────────────────────────────────────────────────

class _Logger:
    """Typed log helpers for each layer of the backend."""

    def api(self, method_path: str, *, employee_id: str = "-", status: int | str = "-", **kw: Any) -> None:
        """Log an incoming API request."""
        _emit("API", method_path, employee_id=employee_id, http_status=status, **kw)

    def tool(
        self,
        tool_name: str,
        *,
        caller: str = "-",
        level: str = "-",
        args: dict | None = None,
        result_summary: str | dict | None = None,
        elapsed_ms: float | None = None,
        **kw: Any,
    ) -> None:
        """Log a tool invocation (read or write)."""
        extra: dict[str, Any] = {"caller": caller, "level": level}
        if args:
            safe_args = {k: ("***" if k in ("password", "temp_password") else v) for k, v in args.items()}
            extra["args"] = safe_args
        if result_summary is not None:
            extra["result"] = result_summary
        if elapsed_ms is not None:
            extra["elapsed_ms"] = round(elapsed_ms, 2)
        _emit("TOOL", tool_name, **extra, **kw)

    def agent(self, agent_name: str, event: str, *, employee_id: str = "-", **kw: Any) -> None:
        """Log an agent reasoning / delegation event."""
        _emit("AGENT", f"[{agent_name.upper()}] {event}", employee_id=employee_id, **kw)

    def auth(self, event: str, *, employee_id: str = "-", success: bool | None = None, **kw: Any) -> None:
        """Log an authentication event."""
        _emit("AUTH", event, employee_id=employee_id, success=success, **kw)

    def db(self, operation: str, *, table: str = "-", **kw: Any) -> None:
        """Log a direct Supabase / DB operation."""
        _emit("DB", operation, table=table, **kw)

    def info(self, message: str, **kw: Any) -> None:
        _emit("INFO", message, **kw)

    def warn(self, message: str, **kw: Any) -> None:
        _emit("WARN", message, **kw)

    def error(self, message: str, **kw: Any) -> None:
        _emit("ERROR", message, **kw)


# Singleton — import this everywhere
log = _Logger()
