"""Write tools for the Details Agent (self-update) and Service Agent (add employees).

Rules enforced here (write tier):
- update_my_details: only the caller's own record; field whitelist enforced.
- add_level1_staff: Level 2 and Level 3 only.
- add_level2_manager: Level 3 only.
- add_level3_boss: NOBODY — always returns not_permitted.
"""
import uuid
from typing import Optional
from backend.supabase_client import get_supabase
from backend.auth import hash_password

# Fields each level is allowed to update in their own record
UPDATABLE_FIELDS = {
    "level1": {"name", "contact_number", "current_address"},
    "level2": {"name", "contact_number", "office_number", "current_address"},
    "level3": {"name", "current_address"},
}

TABLE_BY_LEVEL = {
    "level1": "level1_staff",
    "level2": "level2_manager",
    "level3": "level3_boss",
}


def update_my_details(
    caller_id: str,
    caller_level: str,
    field: str,
    value: str,
) -> dict:
    """Update a single field in the calling employee's own profile. CHANGES DATA.

    Use when the user says 'update my address', 'change my contact number', etc.
    Only allowed on the caller's own record. Cannot modify another employee.

    Args:
        field: The field name to update (e.g., 'name', 'contact_number', 'current_address').
        value: The new value as a string (numbers will be cast automatically).

    Returns:
        {"status": "updated", "field": ..., "new_value": ...} or an error dict.
    """
    allowed_fields = UPDATABLE_FIELDS.get(caller_level, set())
    if field not in allowed_fields:
        return {
            "error": "invalid_field",
            "reason": (
                f"'{field}' is not a modifiable field for {caller_level}. "
                f"Allowed fields: {', '.join(sorted(allowed_fields))}."
            ),
        }

    # Cast numeric fields
    cast_value: str | int = value
    if field in ("contact_number", "office_number"):
        try:
            cast_value = int(value)
        except ValueError:
            return {"error": "invalid_value", "reason": f"'{field}' must be a number."}

    sb = get_supabase()
    table = TABLE_BY_LEVEL[caller_level]
    result = (
        sb.table(table)
        .update({field: cast_value})
        .eq("employee_id", caller_id)
        .execute()
    )

    if not result.data:
        return {"error": "update_failed", "hint": "Record not found or no change made."}

    return {"status": "updated", "field": field, "new_value": cast_value}


def add_level1_staff(
    caller_id: str,
    caller_level: str,
    name: str,
    contact_number: int,
    current_address: str,
    temp_password: Optional[str] = "Welcome@123",
) -> dict:
    """Add a new Level 1 Staff employee. CHANGES DATA — creates login + staff record.

    Only available to Level 2 Managers and Level 3 Bosses.
    A new employee_id and staff_id are generated automatically.
    The new employee gets a temporary password they must change on first login.

    Args:
        name: Full name of the new staff member.
        contact_number: Phone number (must be unique).
        current_address: Home address.
        temp_password: Temporary password (default: Welcome@123).

    Returns:
        {"status": "created", "employee_id": ..., "staff_id": ...} or error.
    """
    if caller_level not in ("level2", "level3"):
        return {
            "error": "not_permitted",
            "reason": "Only Level 2 Managers and Level 3 Bosses can add new Level 1 Staff.",
        }

    sb = get_supabase()
    employee_id = f"EMP{uuid.uuid4().hex[:6].upper()}"
    staff_id = f"STF{uuid.uuid4().hex[:6].upper()}"
    hashed = hash_password(temp_password or "Welcome@123")

    # Create login record
    login_res = sb.table("login").insert({
        "employee_id": employee_id,
        "password": hashed,
        "status": "level1",
    }).execute()

    if not login_res.data:
        return {"error": "creation_failed", "hint": "Could not create login record."}

    # Create staff detail record
    staff_res = sb.table("level1_staff").insert({
        "staff_id": staff_id,
        "employee_id": employee_id,
        "name": name,
        "contact_number": contact_number,
        "current_address": current_address,
    }).execute()

    if not staff_res.data:
        # Roll back login if staff insert fails
        sb.table("login").delete().eq("employee_id", employee_id).execute()
        return {"error": "creation_failed", "hint": "Could not create staff record."}

    return {
        "status": "created",
        "employee_id": employee_id,
        "staff_id": staff_id,
        "name": name,
        "temp_password": temp_password or "Welcome@123",
        "message": f"New Level 1 Staff '{name}' created successfully. Share their credentials.",
    }


def add_level2_manager(
    caller_id: str,
    caller_level: str,
    name: str,
    contact_number: int,
    office_number: int,
    current_address: str,
    temp_password: Optional[str] = "Welcome@123",
) -> dict:
    """Add a new Level 2 Manager. CHANGES DATA — creates login + manager record.

    Only available to Level 3 Bosses. Level 2 managers cannot create other managers.

    Args:
        name: Full name of the new manager.
        contact_number: Phone number (must be unique).
        office_number: Office extension number (must be unique).
        current_address: Home address.
        temp_password: Temporary password (default: Welcome@123).

    Returns:
        {"status": "created", "employee_id": ..., "manager_id": ...} or error.
    """
    if caller_level != "level3":
        return {
            "error": "not_permitted",
            "reason": "Only Level 3 Bosses can add new Level 2 Managers.",
        }

    sb = get_supabase()
    employee_id = f"EMP{uuid.uuid4().hex[:6].upper()}"
    manager_id = f"MGR{uuid.uuid4().hex[:6].upper()}"
    hashed = hash_password(temp_password or "Welcome@123")

    login_res = sb.table("login").insert({
        "employee_id": employee_id,
        "password": hashed,
        "status": "level2",
    }).execute()

    if not login_res.data:
        return {"error": "creation_failed", "hint": "Could not create login record."}

    mgr_res = sb.table("level2_manager").insert({
        "manager_id": manager_id,
        "employee_id": employee_id,
        "name": name,
        "contact_number": contact_number,
        "office_number": office_number,
        "current_address": current_address,
    }).execute()

    if not mgr_res.data:
        sb.table("login").delete().eq("employee_id", employee_id).execute()
        return {"error": "creation_failed", "hint": "Could not create manager record."}

    return {
        "status": "created",
        "employee_id": employee_id,
        "manager_id": manager_id,
        "name": name,
        "temp_password": temp_password or "Welcome@123",
        "message": f"New Level 2 Manager '{name}' created successfully.",
    }


def add_level3_boss(caller_id: str, caller_level: str, **kwargs) -> dict:
    """Attempt to add a Level 3 Boss. Always denied — no one can create a boss-level account.

    Returns:
        {"error": "not_permitted", ...} always.
    """
    return {
        "error": "not_permitted",
        "reason": "Creating a Level 3 Boss account is not allowed through this system.",
    }
