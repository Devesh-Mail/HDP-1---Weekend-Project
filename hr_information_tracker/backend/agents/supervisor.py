"""Supervisor Agent — orchestrates Details and Service specialists.

Flow:
  user message
      │
  supervisor ──→ ask_details ──→ Details Agent (read/update own; read subordinates)
                └─ ask_service ──→ Service Agent (add new employees)

The supervisor decides which specialist to delegate to based on the intent.
It never calls Supabase directly — all data operations go through the specialists.
"""
import json
from groq import Groq

from backend.agents.details_agent import run_details_agent
from backend.agents.service_agent import run_service_agent
from backend.logger import log

SUPERVISOR_SYSTEM = """\
You are the HR Assistant Chatbot supervisor for employee {employee_id} (level: {level}).

Your job is to understand what the employee wants and delegate to the correct specialist:
- ask_details: For anything about viewing or updating employee details (own or subordinates').
- ask_service: For adding new employees to the system.

Delegation rules:
- Level 1 staff: Can only use ask_details (for their own profile).
- Level 2 managers: Can use ask_details (own + Level 1 staff) and ask_service (add Level 1 only).
- Level 3 bosses: Can use ask_details (own + Level 1 + Level 2) and ask_service (add Level 1 + Level 2).

You must NEVER:
- Make up data or policies.
- Allow actions that exceed the employee's level permissions.
- Use a specialist for the wrong purpose.

Greet warmly, be professional, and summarise the specialist's reply clearly for the user.
Level display: level1 = Staff, level2 = Manager, level3 = Boss.
"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "ask_details",
            "description": "Delegate to the Details specialist to view or update employee details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "A complete, specific instruction for the Details specialist.",
                    }
                },
                "required": ["request"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_service",
            "description": "Delegate to the Service specialist to add a new employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "A complete, specific instruction for the Service specialist.",
                    }
                },
                "required": ["request"],
            },
        },
    },
]

MAX_STEPS = 6


def run_supervisor(
    groq_client: Groq,
    employee_id: str,
    level: str,
    user_message: str,
    history: list[dict],
) -> dict:
    """Run the Supervisor agent, delegating to Details or Service specialists as needed.

    Args:
        groq_client: Authenticated Groq client.
        employee_id: The authenticated employee's ID.
        level: 'level1', 'level2', or 'level3'.
        user_message: The raw user message.
        history: Full conversation history [{role, content}].

    Returns:
        {"reply": str, "steps": [...]}.
    """
    system = SUPERVISOR_SYSTEM.format(employee_id=employee_id, level=level)

    messages = []
    for h in history[-8:]:  # last 4 exchanges
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    all_steps = []

    def delegate(name: str, args: dict) -> dict:
        request = args.get("request", user_message)
        log.agent("supervisor", f"delegating to '{name}'", employee_id=employee_id, level=level, request_preview=request[:80])
        if name == "ask_details":
            return run_details_agent(
                groq_client, employee_id, level, request, history, on_step=lambda s: all_steps.append(s)
            )
        elif name == "ask_service":
            return run_service_agent(
                groq_client, employee_id, level, request, history, on_step=lambda s: all_steps.append(s)
            )
        log.warn(f"supervisor: unknown specialist '{name}'")
        return {"error": "unknown_specialist", "hint": f"No specialist named {name}."}

    for step_num in range(MAX_STEPS):
        log.agent("supervisor", f"LLM call #{step_num + 1}", employee_id=employee_id, level=level)
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}] + messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            log.agent("supervisor", "final reply ready", employee_id=employee_id, reply_preview=(msg.content or "")[:80])
            return {"reply": msg.content or "I'm sorry, I couldn't process your request.", "steps": all_steps}

        tool_results_content = []
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            specialist_result = delegate(name, args)
            all_steps.append({
                "agent": "supervisor",
                "tool": name,
                "args": args,
                "result": specialist_result,
            })

            # Feed the specialist's answer back to the supervisor
            answer_text = specialist_result.get("answer", json.dumps(specialist_result))
            tool_results_content.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": answer_text,
            })

        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})
        messages.extend(tool_results_content)

    return {
        "reply": "I wasn't able to complete your request. Please try rephrasing.",
        "steps": all_steps,
    }
