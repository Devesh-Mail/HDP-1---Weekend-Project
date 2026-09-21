# Business Rules — HR Employee Chatbot

## Overview

The HR chatbot enforces strict role-based access control (RBAC) across three employee levels. These rules govern what each level can **read**, **modify**, and **create** through the chatbot interface. Rules are enforced in the backend agent tools and must never be overridden by the LLM.

---

## Employee Levels

| Level | Role | Status Value |
|---|---|---|
| Level 1 | Staff | `level1` |
| Level 2 | Manager | `level2` |
| Level 3 | Boss | `level3` |

---

## Rule 1 — Self-Access (All Levels)

> **All employees at every level can view their own details and update their own details.**

- A Level 1 staff member can see their own `name`, `contact_number`, and `current_address`.
- A Level 2 manager can see their own `name`, `contact_number`, `office_number`, and `current_address`.
- A Level 3 boss can see their own `name` and `current_address`.
- Any employee can request updates to **their own fields only**.
- An update to one's own details is always permitted, regardless of level.

---

## Rule 2 — Adding New Employees

> **Level 2 Managers can add new Level 1 Staff. Level 3 Bosses can add new Level 1 Staff and new Level 2 Managers. No employee can add a new employee of the same or higher level.**

### Level 2 Manager Permissions:
- ✅ Can add a new Level 1 Staff record.
- ❌ Cannot add a new Level 2 Manager.
- ❌ Cannot add a new Level 3 Boss.
- ❌ Level 1 Staff cannot add any new employees.

### Level 3 Boss Permissions:
- ✅ Can add a new Level 1 Staff record.
- ✅ Can add a new Level 2 Manager record.
- ❌ Cannot add a new Level 3 Boss (no one can create a boss-level account).

---

## Rule 3 — No Cross-Employee Modification

> **No employee can modify another employee's details, regardless of level.**

- A Level 2 Manager who can view Level 1 Staff records **cannot edit** any of those fields.
- A Level 3 Boss who can view Level 1 and Level 2 records **cannot edit** any of those fields.
- The only record any employee can write to is their **own** record.
- Any tool call that attempts to update another employee's record must return an error.

---

## Rule 4 — Cross-Level Read Access

> **Higher-level employees can view (read-only) records of all employees below their level, but cannot modify them.**

### Level 1 Staff:
- ✅ Can read: own details only.
- ❌ Cannot read: any other employee's details.

### Level 2 Manager:
- ✅ Can read: own details.
- ✅ Can read: all Level 1 Staff details (read-only).
- ❌ Cannot read: other Level 2 Managers' details.
- ❌ Cannot read: Level 3 Boss details.

### Level 3 Boss:
- ✅ Can read: own details.
- ✅ Can read: all Level 1 Staff details (read-only).
- ✅ Can read: all Level 2 Manager details (read-only).
- ❌ Cannot read: other Level 3 Boss details.

---

## Rule Enforcement

These rules are enforced at **three layers**:
1. **Agent system prompt** — The supervisor and specialist agents are instructed never to violate these rules.
2. **Tool-level enforcement** — Each tool function checks the caller's `employee_id` and `level` before executing. If a rule would be violated, the tool returns `{"error": "not_permitted", "reason": "..."}`.
3. **JWT middleware** — The FastAPI backend validates the JWT on every request and attaches the employee's level. The agent context is always scoped to the authenticated user.

---

## Summary Table

| Action | Level 1 | Level 2 | Level 3 |
|---|:---:|:---:|:---:|
| View own details | ✅ | ✅ | ✅ |
| Update own details | ✅ | ✅ | ✅ |
| View Level 1 details | ❌ | ✅ (read) | ✅ (read) |
| View Level 2 details | ❌ | ❌ | ✅ (read) |
| View Level 3 details | ❌ | ❌ | ❌ |
| Edit Level 1 details | ❌ | ❌ | ❌ |
| Edit Level 2 details | ❌ | ❌ | ❌ |
| Add Level 1 Staff | ❌ | ✅ | ✅ |
| Add Level 2 Manager | ❌ | ❌ | ✅ |
| Add Level 3 Boss | ❌ | ❌ | ❌ |
