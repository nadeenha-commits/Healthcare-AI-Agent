from backend.agent.tools import (
    add_patient,
    add_treatment,
    available_slots,
    book_appointment,
    busiest_doctor,
    cancel_appointment,
    department_load_tool,
    doctor_schedule,
    get_patient_details,
    list_doctors,
    monthly_appointments,
    patient_history,
    search_patient,
)


TOOL_REGISTRY = {
    "search_patient": search_patient,
    "get_patient_details": get_patient_details,
    "add_patient": add_patient,
    "list_doctors": list_doctors,
    "doctor_schedule": doctor_schedule,
    "available_slots": available_slots,
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "patient_history": patient_history,
    "add_treatment": add_treatment,
    "busiest_doctor": busiest_doctor,
    "monthly_appointments": monthly_appointments,
    "department_load": department_load_tool,
}


def get_registered_tool(action_name):
    return TOOL_REGISTRY.get(action_name)


def list_registered_tools():
    return sorted(TOOL_REGISTRY.keys())


def run_registered_tool(action_name, args=None):
    args = args or {}

    tool = get_registered_tool(action_name)

    if tool is None:
        return {
            "error": "unknown_tool",
            "message": f'Tool "{action_name}" is not registered.',
        }

    try:
        if not isinstance(args, dict):
            return {
                "error": "invalid_args",
                "message": "Tool arguments must be a JSON object.",
            }

        return tool(**args)

    except TypeError as exc:
        return {
            "error": "invalid_tool_arguments",
            "message": str(exc),
        }

    except Exception as exc:
        return {
            "error": "tool_execution_failed",
            "message": str(exc),
        }