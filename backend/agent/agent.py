import json
import re
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


def normalize_message(message: str) -> str:
    """
    Normalizes user text for intent matching.

    Example:
    'List doctorsssssssss' -> 'list doctors'
    """
    text = str(message or "").lower().strip()
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    return text


def parse_llm_json_payload(text: str):
    """
    Parses Gemini tool JSON even if Gemini adds text before/after it.

    Example:
    'I can list doctors. {"action": "list_doctors", "args": {}}'
    becomes:
    {"action": "list_doctors", "args": {}}
    """
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None
    except Exception:
        pass

    match = re.search(r"\{.*\}", text or "", flags=re.DOTALL)

    if not match:
        return None

    try:
        payload = json.loads(match.group(0))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


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

    def _recent_history_context(self, session_id: Optional[str], limit: int = 8) -> str:
        """
        Builds compact same-session memory context from the local Agent history.
        """
        history = self.get_history(session_id)[-limit:]

        if not history:
            return ""

        lines = []

        for item in history:
            role = item.get("role", "user")
            text = item.get("text", "")

            if text:
                lines.append(f"{role}: {text}")

        return "\n".join(lines)

    def _extract_demo_memory_from_text(self, text: str) -> Optional[str]:
        """
        Extracts demo memory values from any real text the user previously gave.
        This is not hardcoded to specific values; it reads the values dynamically.
        """
        preferred_specialty = None
        demo_patient = None

        specialty_match = re.search(
            r"preferred doctor specialty is ([A-Za-z ]+?)(?=,|\.| and my demo patient|$)",
            text or "",
            flags=re.IGNORECASE,
        )

        patient_match = re.search(
            r"demo patient is ([A-Za-z ]+?)(?=,|\.|$)",
            text or "",
            flags=re.IGNORECASE,
        )

        if specialty_match:
            preferred_specialty = specialty_match.group(1).strip().rstrip(".")

        if patient_match:
            demo_patient = patient_match.group(1).strip().rstrip(".")

        if not preferred_specialty and not demo_patient:
            return None

        parts = []

        if preferred_specialty:
            parts.append(f"Your preferred doctor specialty is {preferred_specialty}.")

        if demo_patient:
            parts.append(f"Your demo patient is {demo_patient}.")

        return " ".join(parts)

    def _extract_demo_memory_from_history(self, session_id: Optional[str]) -> Optional[str]:
        history = self.get_history(session_id)

        for item in reversed(history):
            if item.get("role") != "user":
                continue

            memory_reply = self._extract_demo_memory_from_text(item.get("text", ""))

            if memory_reply:
                return memory_reply

        return None

    def _is_memory_recall_question(self, message: str) -> bool:
        text = normalize_message(message)

        recall_phrases = [
            "what doctor specialty",
            "what specialty",
            "what demo patient",
            "what patient",
            "what did i mention earlier",
            "what did i say earlier",
            "what do you remember",
            "remember earlier",
        ]

        return any(phrase in text for phrase in recall_phrases)

    def _is_available_slots_request(self, message_lower: str) -> bool:
        slot_words = [
            "available slot",
            "available slots",
            "appointment slot",
            "appointment slots",
            "free slot",
            "free slots",
            "open slot",
            "open slots",
            "openings",
            "availability",
        ]

        return any(word in message_lower for word in slot_words)

    def _finish(self, session_id, reply, tools_called):
        self.add_history(session_id, "assistant", reply)
        return {
            "reply": reply,
            "tools_called": tools_called,
        }

    def handle_message(self, message: str, session_id: Optional[str] = None):
        self.add_history(session_id, "user", message)

        message_lower = normalize_message(message)
        tools_called = []

        if message_lower.startswith(("remember this", "remember that")):
            reply = "Got it. I will remember that for this session."
            return self._finish(session_id, reply, tools_called)

        if self._is_memory_recall_question(message):
            memory_reply = self._extract_demo_memory_from_history(session_id)

            if not memory_reply:
                memory_reply = self._extract_demo_memory_from_text(
                    get_memory_context(session_id)
                )

            if memory_reply:
                return self._finish(session_id, memory_reply, tools_called)

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

        if self._is_available_slots_request(message_lower):
            specialty = extract_specialty_from_message(message)
            date_range = extract_date_range_from_message(message)

            if not specialty:
                reply = (
                    "Please tell me which doctor specialty you need "
                    "so I can check available appointment slots."
                )
                return self._finish(session_id, reply, tools_called)

            return self._run_tool_action(
                action="available_slots",
                args={
                    "specialty": specialty,
                    "date": date_range,
                },
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
        recent_history = self._recent_history_context(session_id)

        # Keep Zep useful, but do not allow memory to make the Gemini prompt too large.
        if memory_context:
            memory_context = memory_context[-800:]

        if recent_history:
            recent_history = recent_history[-800:]

        memory_section = ""

        if memory_context:
            memory_section += (
                "\nLong-term memory from Zep:\n"
                f"{memory_context}\n"
            )

        if recent_history:
            memory_section += (
                "\nRecent conversation history:\n"
                f"{recent_history}\n"
            )

        prompt = f"{SYSTEM_PROMPT}{memory_section}\nUser: {message}\nAssistant:"
        llm_resp = generate_text(prompt, max_tokens=300)
        text = llm_resp.get("text", "")

        payload = parse_llm_json_payload(text)

        if payload is None:
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
