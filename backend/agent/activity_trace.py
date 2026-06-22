from typing import Any, Dict, List


def format_tool_name(name: str) -> str:
    return str(name or "").replace("_", " ")


def build_activity_steps(
    user_message: str,
    tools_called: List[Dict[str, Any]] | None,
) -> List[Dict[str, str]]:
    tools_called = tools_called or []

    steps: List[Dict[str, str]] = [
        {
            "label": "Received request",
            "status": "done",
            "detail": "The backend received the user message.",
        },
        {
            "label": "Analyzed request",
            "status": "done",
            "detail": _infer_request_type(user_message, tools_called),
        },
    ]

    if tools_called:
        steps.append(
            {
                "label": "Selected tool workflow",
                "status": "done",
                "detail": f"The Agent selected {len(tools_called)} tool call"
                f"{'' if len(tools_called) == 1 else 's'} for this request.",
            }
        )

        for tool in tools_called:
            steps.append(_build_tool_step(tool))
    else:
        steps.append(
            {
                "label": "Direct response path",
                "status": "done",
                "detail": "The Agent answered without calling database tools.",
            }
        )

    steps.append(
        {
            "label": "Generated final response",
            "status": "done",
            "detail": "The backend returned the final answer to the chat UI.",
        }
    )

    return steps


def _infer_request_type(
    user_message: str,
    tools_called: List[Dict[str, Any]],
) -> str:
    message = str(user_message or "").lower()
    tool_names = {str(tool.get("name", "")) for tool in tools_called}

    if "book_appointment" in tool_names:
        return "Detected an appointment booking workflow."

    if "available_slots" in tool_names:
        return "Detected an appointment availability workflow."

    if "busiest_doctor" in tool_names:
        return "Detected a clinic analytics workflow."

    if "department_load" in tool_names:
        return "Detected a department workload analytics workflow."

    if "patient_history" in tool_names:
        return "Detected a patient history workflow."

    if "search_patient" in tool_names:
        return "Detected a patient search workflow."

    if "help" in message or "what can you" in message:
        return "Detected a general help/capabilities question."

    return "Detected the request type and selected the response path."


def _build_tool_step(tool: Dict[str, Any]) -> Dict[str, str]:
    tool_name = str(tool.get("name", "unknown_tool"))
    readable_name = format_tool_name(tool_name)

    detail = "Tool executed successfully."

    if isinstance(tool.get("result_count"), int):
        count = tool["result_count"]
        detail = f"Returned {count} result{'' if count == 1 else 's'}."

    result = tool.get("result")

    if isinstance(result, dict):
        status = result.get("status")
        record_id = result.get("id")

        if status and record_id:
            detail = (
                f"Tool executed successfully. Record ID {record_id} "
                f"has status {status}."
            )
        elif status:
            detail = f"Tool executed successfully with status {status}."

    return {
        "label": f"Called {readable_name}",
        "status": "done",
        "detail": detail,
    }