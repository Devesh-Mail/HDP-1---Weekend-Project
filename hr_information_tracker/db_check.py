"""
db_check.py — Diagnostic script to verify every backend tool can reach
               Supabase and returns the expected data shape.

Run from the project root:
    python db_check.py

Tests covered
─────────────
READ TOOLS
  [1] get_my_details  — level1 (EMP001)
  [2] get_my_details  — level2 (EMP002)
  [3] get_my_details  — level3 (EMP003)
  [4] list_subordinates — level2 (all)
  [5] list_subordinates — level3 (level1 only)
  [6] list_subordinates — level3 (level2 only)
  [7] list_subordinates — level1 (should be denied)
  [8] get_subordinate_detail — level2 reads a level1 employee
  [9] get_subordinate_detail — level1 tries to read a level2 (should be denied)

WRITE TOOLS  (non-destructive: rollback any creates)
  [10] update_my_details — level1 updates contact_number (valid)
  [11] update_my_details — level1 tries to update office_number (should be denied)
  [12] add_level1_staff  — level2 creates, then deletes the new record
  [13] add_level2_manager — level3 creates, then deletes the new record
  [14] add_level3_boss   — always denied
  [15] add_level1_staff  — level1 tries (should be denied)
"""
from __future__ import annotations

import sys
import os

# ── Allow running from project root ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from backend.tools.read_tools import get_my_details, list_subordinates, get_subordinate_detail
from backend.tools.write_tools import update_my_details, add_level1_staff, add_level2_manager, add_level3_boss
from backend.supabase_client import get_supabase

# ── Known test identities (from README) ──────────────────────────────────────
L1_ID = "EMP001"   # Level 1 Staff
L2_ID = "EMP002"   # Level 2 Manager
L3_ID = "EMP003"   # Level 3 Boss

# ── Helpers ───────────────────────────────────────────────────────────────────

_PASS  = "\033[92m  PASS\033[0m"
_FAIL  = "\033[91m  FAIL\033[0m"
_SKIP  = "\033[93m  SKIP\033[0m"
_WARN  = "\033[93m  WARN\033[0m"

_results: list[tuple[str, bool, str]] = []


def check(test_id: str, description: str, result: dict, *, expect_ok: bool = True, expect_key: str | None = None):
    """Evaluate a tool result and record pass/fail."""
    has_error = "error" in result
    has_status = result.get("status") in ("ok", "updated", "created")

    if expect_ok:
        passed = not has_error and has_status
        if expect_key:
            passed = passed and expect_key in result
    else:
        # Expect a denied / error response
        passed = has_error

    icon = _PASS if passed else _FAIL
    print(f"\n{'─'*60}")
    print(f"[{test_id:>2}] {description}")
    print(f"      Result  : {result}")
    print(f"      Verdict : {icon}")
    _results.append((test_id, passed, description))
    return result


def cleanup_employee(employee_id: str, level_table: str):
    """Remove a test-created employee from login + detail table."""
    sb = get_supabase()
    sb.table(level_table).delete().eq("employee_id", employee_id).execute()
    sb.table("login").delete().eq("employee_id", employee_id).execute()
    print(f"      Cleanup : deleted {employee_id} from {level_table} + login")


# ══════════════════════════════════════════════════════════════════════════════
#  READ TOOL CHECKS
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "═"*60)
print("  BACKEND DATABASE DIAGNOSTIC — READ TOOLS")
print("═"*60)

# [1] get_my_details — level1
r = get_my_details(L1_ID, "level1")
check("1", f"get_my_details({L1_ID}, level1)", r, expect_ok=True, expect_key="data")

# [2] get_my_details — level2
r = get_my_details(L2_ID, "level2")
check("2", f"get_my_details({L2_ID}, level2)", r, expect_ok=True, expect_key="data")

# [3] get_my_details — level3
r = get_my_details(L3_ID, "level3")
check("3", f"get_my_details({L3_ID}, level3)", r, expect_ok=True, expect_key="data")

# [4] list_subordinates — level2, all levels
r = list_subordinates(L2_ID, "level2")
check("4", f"list_subordinates({L2_ID}, level2, all)", r, expect_ok=True, expect_key="employees")

# [5] list_subordinates — level3, level1 only
r = list_subordinates(L3_ID, "level3", target_level="level1")
check("5", f"list_subordinates({L3_ID}, level3, target=level1)", r, expect_ok=True, expect_key="employees")

# [6] list_subordinates — level3, level2 only
r = list_subordinates(L3_ID, "level3", target_level="level2")
check("6", f"list_subordinates({L3_ID}, level3, target=level2)", r, expect_ok=True, expect_key="employees")

# [7] list_subordinates — level1 (should be denied)
r = list_subordinates(L1_ID, "level1")
check("7", f"list_subordinates({L1_ID}, level1) [expect DENIED]", r, expect_ok=False)

# [8] get_subordinate_detail — level2 reads a level1
#   First find a real level1 employee from list
level1_list = list_subordinates(L2_ID, "level2", target_level="level1")
if level1_list.get("employees"):
    target_l1 = level1_list["employees"][0]["employee_id"]
    r = get_subordinate_detail(L2_ID, "level2", target_l1)
    check("8", f"get_subordinate_detail({L2_ID}, level2 → {target_l1})", r, expect_ok=True, expect_key="data")
else:
    print(f"\n[{'8':>2}] get_subordinate_detail — {_SKIP} (no level1 employees found)")
    _results.append(("8", None, "get_subordinate_detail (skipped — no level1 data)"))

# [9] get_subordinate_detail — level1 tries to read level2 (should be denied)
r = get_subordinate_detail(L1_ID, "level1", L2_ID)
check("9", f"get_subordinate_detail({L1_ID}, level1 → {L2_ID}) [expect DENIED]", r, expect_ok=False)


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE TOOL CHECKS
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "═"*60)
print("  BACKEND DATABASE DIAGNOSTIC — WRITE TOOLS")
print("═"*60)

# [10] update_my_details — level1 changes contact_number (valid field)
#   First read current value so we can restore it
current = get_my_details(L1_ID, "level1")
original_contact = None
if current.get("data"):
    original_contact = current["data"].get("contact_number")

r = update_my_details(L1_ID, "level1", "contact_number", "9999999999")
check("10", f"update_my_details({L1_ID}, level1, contact_number=9999999999)", r, expect_ok=True)

# Restore original value
if original_contact is not None:
    update_my_details(L1_ID, "level1", "contact_number", str(original_contact))
    print(f"      Restore : contact_number reset to {original_contact}")

# [11] update_my_details — level1 tries office_number (not in their allowed fields)
r = update_my_details(L1_ID, "level1", "office_number", "12345")
check("11", f"update_my_details({L1_ID}, level1, office_number=12345) [expect DENIED]", r, expect_ok=False)

# [12] add_level1_staff — level2 creates a test employee, then cleans up
r = add_level1_staff(
    caller_id=L2_ID,
    caller_level="level2",
    name="Test Staff Diagnostic",
    contact_number=8000000001,
    current_address="1 Diagnostic Lane, Testville",
    temp_password="Diag@Test1",
)
check("12", f"add_level1_staff({L2_ID}, level2)", r, expect_ok=True)
if r.get("status") == "created":
    cleanup_employee(r["employee_id"], "level1_staff")

# [13] add_level2_manager — level3 creates a test manager, then cleans up
r = add_level2_manager(
    caller_id=L3_ID,
    caller_level="level3",
    name="Test Manager Diagnostic",
    contact_number=8000000002,
    office_number=9000,
    current_address="2 Diagnostic Ave, Testville",
    temp_password="Diag@Test2",
)
check("13", f"add_level2_manager({L3_ID}, level3)", r, expect_ok=True)
if r.get("status") == "created":
    cleanup_employee(r["employee_id"], "level2_manager")

# [14] add_level3_boss — always denied
r = add_level3_boss(caller_id=L3_ID, caller_level="level3")
check("14", "add_level3_boss (always denied)", r, expect_ok=False)

# [15] add_level1_staff — level1 tries to add (should be denied)
r = add_level1_staff(
    caller_id=L1_ID,
    caller_level="level1",
    name="Should Not Exist",
    contact_number=8000000003,
    current_address="3 Denied Road",
)
check("15", f"add_level1_staff({L1_ID}, level1) [expect DENIED]", r, expect_ok=False)


# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "═"*60)
print("  SUMMARY")
print("═"*60)

passed   = [r for r in _results if r[1] is True]
failed   = [r for r in _results if r[1] is False]
skipped  = [r for r in _results if r[1] is None]

for tid, ok, desc in _results:
    if ok is None:
        icon = _SKIP
    elif ok:
        icon = _PASS
    else:
        icon = _FAIL
    print(f"  [{tid:>2}] {icon}  {desc}")

print(f"\n  Total : {len(_results)}   Passed : {len(passed)}   Failed : {len(failed)}   Skipped : {len(skipped)}")

if failed:
    print("\n\033[91m  One or more checks FAILED — see details above.\033[0m")
    sys.exit(1)
else:
    print("\n\033[92m  All checks passed!\033[0m")
