"""Read-only Supabase tools for the Details Agent.

Rules enforced here (read tier):
- get_my_details: always scoped to the caller's employee_id.
- list_subordinates: Level 2 → Level 1 only; Level 3 → Level 1 & Level 2.
- get_subordinate_detail: same level restrictions; NO write access.
"""
from typing import Optional
from backend.supabase_client import get_supabase


# ── Table router ─────────────────────────────────────────────────────────────

TABLE_BY_LEVEL = {
    "level1": "level1_staff",
    "level2": "level2_manager",
    "level3": "level3_boss",
}

ID_FIELD_BY_LEVEL = {
    "level1": "staff_id",
    "level2": "manager_id",
    "level3": "boss_id",
}

# Levels that each level can READ (subordinate read access)
READABLE_LEVELS = {
    "level1": [],            # Can only read own
    "level2": ["level1"],   # Can read level1
    "level3": ["level1", "level2"],  # Can read level1 and level2
}


def _get_employee_row(employee_id: str, level: str) -> dict | None:
    sb = get_supabase()
    table = TABLE_BY_LEVEL.get(level)
    if not table:
        return None
    result = sb.table(table).select("*").eq("employee_id", employee_id).maybe_single().execute()
    return result.data


# ── Tool functions ────────────────────────────────────────────────────────────

def get_my_details(caller_id: str, caller_level: str) -> dict:
    """Retrieve the calling employee's own profile details.

    Use when the user asks 'show me my details', 'what is my address',
    'what is my contact number', etc. Read-only: changes nothing.

    Returns the employee's full profile from the appropriate table.
    """
    row = _get_employee_row(caller_id, caller_level)
    if row is None:
        return {"error": "not_found", "hint": "Your employee record could not be found."}
    return {"status": "ok", "data": row, "level": caller_level}


def list_subordinates(caller_id: str, caller_level: str, target_level: Optional[str] = None) -> dict:
    """List all employees at a level below the caller. Read-only.

    Use when a Level 2 Manager or Level 3 Boss asks to see staff/manager details.
    Level 2 can only list Level 1. Level 3 can list Level 1 or Level 2.
    Level 1 employees cannot use this tool.

    Args:
        target_level: 'level1' or 'level2'. If omitted, returns all accessible levels.

    Returns:
        {"status": "ok", "employees": [...]} or {"error": "not_permitted", ...}
    """
    allowed = READABLE_LEVELS.get(caller_level, [])
    if not allowed:
        return {
            "error": "not_permitted",
            "reason": "Level 1 staff can only view their own details.",
        }

    if target_level and target_level not in allowed:
        return {
            "error": "not_permitted",
            "reason": f"You ({caller_level}) are not allowed to view {target_level} records.",
        }

    levels_to_fetch = [target_level] if target_level else allowed
    sb = get_supabase()
    result_list = []

    for lvl in levels_to_fetch:
        table = TABLE_BY_LEVEL[lvl]
        rows = sb.table(table).select("*").execute()
        for r in (rows.data or []):
            result_list.append({**r, "_level": lvl})

    return {"status": "ok", "employees": result_list, "count": len(result_list)}


def get_subordinate_detail(
    caller_id: str, caller_level: str, target_employee_id: str
) -> dict:
    """Get one specific subordinate employee's full profile. Read-only.

    Use when a Manager/Boss asks about a specific staff member by ID or name.
    Caller cannot use this to view peers or superiors — only subordinates.

    Args:
        target_employee_id: The employee_id of the person to look up.

    Returns:
        The employee's profile, or an error if access is denied.
    """
    if target_employee_id == caller_id:
        return get_my_details(caller_id, caller_level)

    allowed = READABLE_LEVELS.get(caller_level, [])
    sb = get_supabase()

    for lvl in allowed:
        table = TABLE_BY_LEVEL[lvl]
        result = sb.table(table).select("*").eq("employee_id", target_employee_id).maybe_single().execute()
        if result.data:
            return {"status": "ok", "data": result.data, "level": lvl}

    return {
        "error": "not_permitted",
        "reason": (
            f"Employee {target_employee_id} is either not found, not below your level, "
            "or you do not have permission to view their details."
        ),
    }
