"""Turns a model's tool call into a Python call. Adapted from library-assistant sample."""
import inspect
import time
import typing

from backend.logger import log


def _coerce(value, annotation):
    args = typing.get_args(annotation)
    if args and type(None) in args:  # Optional[X]
        if value is None:
            return None
        annotation = next(a for a in args if a is not type(None))
    if annotation is int:
        if isinstance(value, bool):
            raise ValueError("expected an integer")
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
        if isinstance(value, int):
            return value
        raise ValueError(f"expected an integer, got {value!r}")
    if annotation is str:
        if not isinstance(value, str):
            raise ValueError(f"expected a string, got {value!r}")
        return value
    return value


def dispatch(functions: dict, name: str, args: dict) -> dict:
    fn = functions.get(name)
    if fn is None:
        err = {
            "error": "unknown_tool",
            "hint": f"Available tools: {', '.join(sorted(functions))}.",
        }
        log.error(f"dispatch: unknown tool '{name}'", available=sorted(functions))
        return err

    sig = inspect.signature(fn)
    hints = typing.get_type_hints(fn)
    try:
        bound = sig.bind(**(args or {}))
        kwargs = {k: _coerce(v, hints.get(k)) for k, v in bound.arguments.items()}
    except (TypeError, ValueError) as e:
        err = {
            "error": "invalid_arguments",
            "hint": f"{name}: {e}. Check the parameter descriptions.",
        }
        log.error(f"dispatch: invalid args for '{name}'", reason=str(e), args=args)
        return err

    # Extract caller context for richer logs (injected by agents)
    caller = kwargs.get("caller_id", "-")
    level = kwargs.get("caller_level", "-")

    # Strip context-only keys for a cleaner args log
    loggable_args = {k: v for k, v in kwargs.items() if k not in ("caller_id", "caller_level")}

    t0 = time.perf_counter()
    result = fn(**kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Summarise result: show status/error key + limited data preview
    result_summary = result.get("status") or result.get("error") or str(result)[:80]

    log.tool(
        name,
        caller=caller,
        level=level,
        args=loggable_args,
        result_summary=result_summary,
        elapsed_ms=elapsed_ms,
    )
    return result
