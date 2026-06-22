import json
from typing import Optional

from backend.agent.booking_flow import handle_book_flow
from backend.agent.gemini_client import generate_text
from backend.agent.message_parser import (
    choose_patient_match,
    extract_date_range_from_message,
    extract_first_number,
    extract_name_from_message,
    extract_patient_history_query,
    extract_specialty_from_message,
    is_booking_request,
)
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.registered_tool_handler import handle_registered_tool_action
from backend.agent.response_formatters import (
    format_patient_clarification,
    format_patient_history,
)
from backend.agent.tools import (
    list_departments,
    patient_history,
    search_patient,
)
from backend.agent.zep_memory import get_memory_context


class Agent:
    def __init__(self):
        self.histories = {}

    def get_history(self, session_id: Optional[str] = None):
        return self.histories.get(session_id or "default", [])

    def add_history(self, session_id: Optional[str], role: str, text: str):
        sid = session_id or "default"
        self.histories.setdefault(sid, [])
        self.histories[sid].append({
            "role": role,
            "text": text,
        })

    def _finish(self, session_id, reply, tools_called):
        self.add_history(session_id, "assistant", reply)
        return {
            "reply": reply,
            "tools_called": tools_called,
        }

    def handle_message(self, message: str, session_id: Optional[str] = None):
        self.add_history(session_id, "user", message)

        message_lower = message.lower().strip()
        tools_called = []

        if message_lower in ["hi", "hello", "hey"]:
            reply = (
                "Hello! I can help with patients, doctors, appointments, "
                "schedules, treatments, and clinic analytics."
            )
            return self._finish(session_id, reply, tools_called)

        # Booking must be checked before simple doctor/specialty listing.
        if is_booking_request(message_lower):
            payload = {
                "action": "book_flow",
                "args": {
                    "query": extract_name_from_message(message),
                    "specialty": extract_specialty_from_message(message),
                    "date_range": extract_date_range_from_message(message),
                },
            }
            return handle_book_flow(
                payload=payload,
                message=message,
                session_id=session_id,
                add_history=self.add_history,
            )

        if message_lower.startswith("find patient"):
            query = message.replace("Find patient", "").replace("find patient", "").strip()
            return self._run_tool_action(
                action="search_patient",
                args={"query": query},
                message=message,
                session_id=session_id,
            )

        if message_lower in ["list departments", "show departments", "departments"]:
            return self._handle_list_departments(session_id)

        if "department load" in message_lower:
            return self._run_tool_action(
                action="department_load",
                args={},
                message=message,
                session_id=session_id,
            )

        if "cardiologist" in message_lower or "cardiologists" in message_lower:
            return self._run_tool_action(
                action="list_doctors",
                args={"specialty": "Cardiology"},
                message=message,
                session_id=session_id,
            )

        if message_lower in ["list doctors", "show doctors"]:
            return self._run_tool_action(
                action="list_doctors",
                args={},
                message=message,
                session_id=session_id,
            )

        if "busiest doctor" in message_lower or "most appointments" in message_lower:
            return self._run_tool_action(
                action="busiest_doctor",
                args={},
                message=message,
                session_id=session_id,
            )

        if "appointments this month" in message_lower or "monthly appointments" in message_lower:
            return self._run_tool_action(
                action="monthly_appointments",
                args={},
                message=message,
                session_id=session_id,
            )

        if "cancel appointment" in message_lower:
            appointment_id = extract_first_number(message)

            if appointment_id is None:
                reply = "Please provide the appointment ID you want to cancel."
                return self._finish(session_id, reply, tools_called)

            return self._run_tool_action(
                action="cancel_appointment",
                args={"appointment_id": appointment_id},
                message=message,
                session_id=session_id,
            )

        if "patient history" in message_lower or "history for" in message_lower:
            return self._handle_patient_history(message, session_id)

        if "schedule" in message_lower and "doctor" in message_lower:
            doctor_id = extract_first_number(message)

            if doctor_id is None:
                reply = "Please provide the doctor ID to show the schedule."
                return self._finish(session_id, reply, tools_called)

            return self._run_tool_action(
                action="doctor_schedule",
                args={"doctor_id": doctor_id},
                message=message,
                session_id=session_id,
            )

        return self._handle_llm_fallback(message, session_id)

    def _run_tool_action(self, action, args, message, session_id):
        payload = {
            "action": action,
            "args": args,
        }

        return handle_registered_tool_action(
            payload=payload,
            session_id=session_id,
            add_history=self.add_history,
        )

    def _handle_list_departments(self, session_id):
        tools_called = []
        departments = list_departments()

        tools_called.append({
            "name": "list_departments",
            "args": {},
            "result_count": len(departments),
        })

        lines = ["Departments:"]

        for department in departments:
            lines.append(
                f"• {department.get('name')} - {department.get('description')}"
            )

        reply = "\n".join(lines)
        return self._finish(session_id, reply, tools_called)

    def _handle_patient_history(self, message, session_id):
        tools_called = []
        query = extract_patient_history_query(message)

        patients = search_patient(query)

        tools_called.append({
            "name": "search_patient",
            "args": {
                "query": query,
            },
            "result_count": len(patients),
        })

        if not patients:
            reply = f'No patient matched "{query}".'
            return self._finish(session_id, reply, tools_called)

        patient = choose_patient_match(patients, query)

        if patient is None:
            reply = format_patient_clarification(query, patients)
            return self._finish(session_id, reply, tools_called)

        result = patient_history(patient["id"])

        tools_called.append({
            "name": "patient_history",
            "args": {
                "patient_id": patient["id"],
            },
            "result": result,
        })

        reply = format_patient_history(patient, result)
        return self._finish(session_id, reply, tools_called)

    def _handle_llm_fallback(self, message, session_id):
        memory_context = get_memory_context(session_id)

        memory_section = ""
        if memory_context:
            memory_section = (
                "\nRelevant long-term memory from Zep:\n"
                f"{memory_context}\n"
            )

        prompt = f"{SYSTEM_PROMPT}{memory_section}\nUser: {message}\nAssistant:"
        llm_resp = generate_text(prompt)
        text = llm_resp.get("text", "")

        try:
            payload = json.loads(text)
        except Exception:
            return self._finish(session_id, text, [])

        action = payload.get("action")

        if action == "book_flow":
            return handle_book_flow(
                payload=payload,
                message=message,
                session_id=session_id,
                add_history=self.add_history,
            )

        return handle_registered_tool_action(
            payload=payload,
            session_id=session_id,
            add_history=self.add_history,
        )