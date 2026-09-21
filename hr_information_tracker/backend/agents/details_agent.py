"""Details Agent — reads and updates the authenticated employee's own record.

This specialist can:
  - Read the caller's own profile (get_my_details)
  - Update the caller's own profile fields (update_my_details)
  - List subordinate employees (list_subordinates) — Level 2 & 3 only
  - Fetch a specific subordinate's details (get_subordinate_detail) — Level 2 & 3 only

It CANNOT modify any other employee's record.
"""
import json
from groq import Groq

from backend.tools.read_tools import get_my_details, list_subordinates, get_subordinate_detail
from backend.tools.write_tools import update_my_details
from backend.tools.dispatch import dispatch
from backend.logger import log

DETAILS_SYSTEM = """\
You are the Details Specialist for an HR employee chatbot.
You are currently serving employee {employee_id} (level: {level}).

Your available tools:
- get_my_details: Fetch the employee's own HR profile.
- update_my_details: Update ONE field in the employee's own profile. Ask for confirmation before updating.
- list_subordinates: (Level 2/3 only) List staff/managers below the caller's level.
- get_subordinate_detail: (Level 2/3 only) Get a specific subordinate's profile by employee_id.

Rules you must NEVER break:
1. You can only update the CALLING employee's own record — never another person's.
2. If the user asks to change another person's details, politely refuse and explain the policy.
3. Only use tools you have; do not invent data.
4. Be concise, professional, and friendly.
5. When displaying addresses or contact numbers, show them clearly formatted.
"""

TOOL_FUNCTIONS = {
    "get_my_details": get_my_details,
    "update_my_details": update_my_details,
    "list_subordinates": list_subordinates,
    "get_subordinate_detail": get_subordinate_detail,
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_my_details",
            "description": "Fetch the calling employee's own HR profile. Use for 'show my details', 'what is my address', etc.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_my_details",
            "description": "Update a single field in the calling employee's own profile. Ask user to confirm before calling. CHANGES DATA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "Field name: 'name', 'contact_number', 'current_address', 'office_number'.",
                    },
                    "value": {
                        "type": "string",
                        "description": "New value for the field.",
                    },
                },
                "required": ["field", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_subordinates",
            "description": "List all employees at a level below the caller. Level 2 → Level 1 only. Level 3 → Level 1 or Level 2. Level 1 cannot use this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_level": {
                        "type": "string",
                        "enum": ["level1", "level2"],
                        "description": "Which level to list. Omit to get all accessible levels.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_subordinate_detail",
            "description": "Get one specific subordinate employee's profile by employee_id. Read-only. Cannot be used on peers or superiors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_employee_id": {
                        "type": "string",
                        "description": "The employee_id of the subordinate to look up.",
                    }
                },
                "required": ["target_employee_id"],
            },
        },
    },
]

MAX_STEPS = 8


def run_details_agent(
    groq_client: Groq,
    employee_id: str,
    level: str,
    task: str,
    history: list[dict],
    on_step=None,
) -> dict:
    """Run the Details specialist agent loop.

    Args:
        groq_client: Authenticated Groq client.
        employee_id: The authenticated user's employee ID.
        level: 'level1', 'level2', or 'level3'.
        task: The user's message / request delegated from the supervisor.
        history: Previous conversation turns for context.
        on_step: Optional callback for each tool call step (for tracing).

    Returns:
        {"agent": "details", "answer": str, "steps": [...]}.
    """
    system = DETAILS_SYSTEM.format(employee_id=employee_id, level=level)

    # Inject caller context into every tool call automatically
    def call_tool(name: str, args: dict) -> dict:
        args_with_ctx = {"caller_id": employee_id, "caller_level": level, **args}
        return dispatch(TOOL_FUNCTIONS, name, args_with_ctx)

    messages = []
    for h in history[-6:]:  # last 3 exchanges for context
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": task})

    steps = []
    for step_num in range(MAX_STEPS):
        log.agent("details", f"LLM call #{step_num + 1}", employee_id=employee_id, level=level)
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}] + messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.1,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            answer = msg.content or ""
            log.agent("details", "final answer ready", employee_id=employee_id, answer_preview=answer[:80])
            return {"agent": "details", "answer": answer, "steps": steps}

        # Process tool calls
        tool_results_content = []
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = call_tool(name, args)
            step = {"agent": "details", "tool": name, "args": args, "result": result}
            steps.append(step)
            if on_step:
                on_step(step)

            tool_results_content.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})
        messages.extend(tool_results_content)

    return {
        "agent": "details",
        "answer": "I ran into an issue completing your request. Please try again with a simpler question.",
        "steps": steps,
    }
