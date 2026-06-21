import json
from typing import Callable, Optional

from backend.agent.response_formatters import (
    format_datetime,
    format_doctor_schedule,
    format_patient_history,
)
from backend.agent.tool_registry import (
    list_registered_tools,
    run_registered_tool,
)


def handle_registered_tool_action(
    payload: dict,
    session_id: Optional[str] = None,
    add_history: Optional[Callable] = None,
):
    tools_called = []

    def finish(reply: str):
        if add_history:
            add_history(session_id, "assistant", reply)

        return {
            "reply": reply,
            "tools_called": tools_called,
        }

    action = payload.get("action")
    args = payload.get("args") or {}

    if not action:
        return finish("I could not understand which tool should be used.")

    action = _normalize_action_name(action)
    args = _normalize_tool_args(action, args)

    result = run_registered_tool(action, args)

    tools_called.append({
        "name": action,
        "args": args,
        "result": result,
    })

    reply = _format_registered_tool_reply(action, result)
    return finish(reply)


def _normalize_action_name(action):
    action = str(action).strip()

    action_aliases = {
        "department_load_tool": "department_load",
    }

    return action_aliases.get(action, action)


def _normalize_tool_args(action, args):
    if not isinstance(args, dict):
        return {}

    normalized = dict(args)

    if action == "book_appointment" and "datetime" in normalized:
        normalized["dt_iso"] = normalized.pop("datetime")

    if action == "department_load":
        return {}

    return normalized


def _format_registered_tool_reply(action, result):
    if isinstance(result, dict) and "error" in result:
        message = result.get("message") or result.get("error")
        available_tools = ", ".join(list_registered_tools())

        return (
            f"Tool execution failed: {message}\n"
            f"Available tools: {available_tools}"
        )

    if action == "search_patient":
        return _format_search_patient_result(result)

    if action == "list_doctors":
        return _format_list_doctors_result(result)

    if action == "available_slots":
        return _format_available_slots_result(result)

    if action == "patient_history":
        patient_info = result.get("patient", {}) if isinstance(result, dict) else {}
        return format_patient_history(patient_info, result)

    if action == "doctor_schedule":
        return format_doctor_schedule(
            doctor_id="requested",
            schedule=result,
        )

    if action == "busiest_doctor":
        return _format_busiest_doctor_result(result)

    if action == "monthly_appointments":
        return _format_monthly_appointments_result(result)

    if action == "department_load":
        return _format_department_load_result(result)

    if action == "cancel_appointment":
        return _format_cancel_appointment_result(result)

    if action == "book_appointment":
        return _format_book_appointment_result(result)

    if action == "add_patient":
        return _format_add_patient_result(result)

    if action == "add_treatment":
        return _format_add_treatment_result(result)

    if action == "get_patient_details":
        return _safe_json(result)

    return _safe_json(result)


def _format_search_patient_result(result):
    if not result:
        return "No patients found."

    lines = ["Patients found:"]

    for patient in result:
        lines.append(
            f"• {patient.get('full_name')} | "
            f"Age: {patient.get('age')} | "
            f"Phone: {patient.get('phone')}"
        )

    return "\n".join(lines)


def _format_list_doctors_result(result):
    if not result:
        return "No doctors found."

    lines = ["Doctors found:"]

    for doctor in result:
        lines.append(
            f"• Dr. {doctor.get('full_name')} | "
            f"{doctor.get('specialty')} | "
            f"{doctor.get('department_name')}"
        )

    return "\n".join(lines)


def _format_available_slots_result(result):
    if not result:
        return "No available slots found."

    lines = ["Available slots:"]

    for doctor_option in result:
        doctor_name = doctor_option.get("doctor_name")
        specialty = doctor_option.get("specialty")
        slots = doctor_option.get("slots", [])

        lines.append(f"• Dr. {doctor_name} ({specialty})")

        for slot in slots:
            lines.append(f"  - {format_datetime(slot)}")

    return "\n".join(lines)


def _format_busiest_doctor_result(result):
    if not result or "error" in result:
        return "I could not calculate the busiest doctor."

    doctor_name = (
        result.get("doctor")
        or result.get("doctor_name")
        or result.get("full_name")
        or result.get("name")
        or "Unknown doctor"
    )

    count = (
        result.get("appointments")
        or result.get("appointment_count")
        or result.get("count")
        or 0
    )

    return f"The busiest doctor is Dr. {doctor_name} with {count} appointments."


def _format_monthly_appointments_result(result):
    if not result or "error" in result:
        return "I could not calculate monthly appointments."

    count = (
        result.get("appointments")
        or result.get("count")
        or result.get("appointment_count")
        or result.get("total")
        or 0
    )

    return f"There are {count} appointments."


def _format_department_load_result(result):
    if not result:
        return "I could not calculate department load."

    if isinstance(result, dict):
        result = (
            result.get("departments")
            or result.get("items")
            or result.get("data")
            or []
        )

    lines = ["Department load:"]

    for item in result:
        department = (
            item.get("department")
            or item.get("department_name")
            or item.get("name")
            or "Unknown department"
        )

        count = (
            item.get("appointments")
            or item.get("appointment_count")
            or item.get("count")
            or item.get("total")
            or 0
        )

        lines.append(f"• {department}: {count} appointments")

    return "\n".join(lines)


def _format_cancel_appointment_result(result):
    if not result or "error" in result:
        return "Could not cancel the appointment."

    appointment_id = result.get("id") or result.get("appointment_id")

    if appointment_id:
        return f"Appointment {appointment_id} was cancelled successfully."

    return "Appointment was cancelled successfully."


def _format_book_appointment_result(result):
    if not result or "error" in result:
        return "Could not book the appointment."

    return (
        f"Booked appointment for {result.get('patient_name')} "
        f"with Dr. {result.get('doctor_name')} "
        f"on {format_datetime(result.get('appointment_datetime'))}.\n"
        f"Appointment ID: {result.get('id')}"
    )


def _format_add_patient_result(result):
    if not result or "error" in result:
        return "Could not add the patient."

    patient_name = result.get("full_name") or result.get("name") or "Patient"
    patient_id = result.get("id")

    if patient_id:
        return f"{patient_name} was added successfully. Patient ID: {patient_id}"

    return f"{patient_name} was added successfully."


def _format_add_treatment_result(result):
    if not result or "error" in result:
        return "Could not add the treatment."

    treatment_id = result.get("id")

    if treatment_id:
        return f"Treatment was added successfully. Treatment ID: {treatment_id}"

    return "Treatment was added successfully."


def _safe_json(result):
    try:
        return json.dumps(result, indent=2, ensure_ascii=False)
    except TypeError:
        return str(result)