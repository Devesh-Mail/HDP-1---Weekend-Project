"""Service Agent — adds new employees, enforcing level-based creation rules.

This specialist can:
  - Add Level 1 Staff (Level 2 and Level 3 callers only)
  - Add Level 2 Manager (Level 3 callers only)
  - add_level3_boss always returns not_permitted

It has NO read tools and NO ability to modify existing records.
"""
import json
from groq import Groq

from backend.tools.write_tools import add_level1_staff, add_level2_manager, add_level3_boss
from backend.tools.dispatch import dispatch
from backend.logger import log

SERVICE_SYSTEM = """\
You are the Service Specialist for an HR employee chatbot.
You are acting for employee {employee_id} (level: {level}).

Your available tools:
- add_level1_staff: Add a new Level 1 Staff employee. (Level 2 & 3 only)
- add_level2_manager: Add a new Level 2 Manager. (Level 3 only)
- add_level3_boss: Always denied — returns an error. Never attempt this.

Rules you must NEVER break:
1. A Level 1 employee cannot add anyone. Refuse immediately.
2. A Level 2 Manager can only add Level 1 Staff.
3. A Level 3 Boss can add Level 1 Staff or Level 2 Manager. NOT Level 3.
4. Before adding anyone, confirm all required details with the user.
5. After adding, show the new employee_id and temporary password clearly.
6. Never invent or assume missing required fields — ask the user for them.
"""

TOOL_FUNCTIONS = {
    "add_level1_staff": add_level1_staff,
    "add_level2_manager": add_level2_manager,
    "add_level3_boss": add_level3_boss,
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "add_level1_staff",
            "description": "Add a new Level 1 Staff employee. CHANGES DATA. Only Level 2 & 3 may call this. Requires name, contact number, and address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the new staff member."},
                    "contact_number": {"type": "integer", "description": "Phone number (must be unique)."},
                    "current_address": {"type": "string", "description": "Home address."},
                    "temp_password": {"type": "string", "description": "Temporary password. Defaults to Welcome@123 if not provided."},
                },
                "required": ["name", "contact_number", "current_address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_level2_manager",
            "description": "Add a new Level 2 Manager. CHANGES DATA. Only Level 3 Boss may call this. Requires name, contact, office number, and address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the new manager."},
                    "contact_number": {"type": "integer", "description": "Phone number (must be unique)."},
                    "office_number": {"type": "integer", "description": "Office extension number (must be unique)."},
                    "current_address": {"type": "string", "description": "Home address."},
                    "temp_password": {"type": "string", "description": "Temporary password. Defaults to Welcome@123 if not provided."},
                },
                "required": ["name", "contact_number", "office_number", "current_address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_level3_boss",
            "description": "Attempt to add a Level 3 Boss. Always denied.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

MAX_STEPS = 6


def run_service_agent(
    groq_client: Groq,
    employee_id: str,
    level: str,
    task: str,
    history: list[dict],
    on_step=None,
) -> dict:
    """Run the Service specialist agent loop.

    Args:
        groq_client: Authenticated Groq client.
        employee_id: The authenticated user's employee ID.
        level: 'level1', 'level2', or 'level3'.
        task: Delegated task from the supervisor.
        history: Recent conversation history.
        on_step: Optional trace callback.

    Returns:
        {"agent": "service", "answer": str, "steps": [...]}.
    """
    system = SERVICE_SYSTEM.format(employee_id=employee_id, level=level)

    def call_tool(name: str, args: dict) -> dict:
        args_with_ctx = {"caller_id": employee_id, "caller_level": level, **args}
        return dispatch(TOOL_FUNCTIONS, name, args_with_ctx)

    messages = []
    for h in history[-4:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": task})

    steps = []
    for step_num in range(MAX_STEPS):
        log.agent("service", f"LLM call #{step_num + 1}", employee_id=employee_id, level=level)
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
            log.agent("service", "final answer ready", employee_id=employee_id, answer_preview=answer[:80])
            return {"agent": "service", "answer": answer, "steps": steps}

        tool_results_content = []
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = call_tool(name, args)
            step = {"agent": "service", "tool": name, "args": args, "result": result}
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
        "agent": "service",
        "answer": "I could not complete the request. Please try again.",
        "steps": steps,
    }
