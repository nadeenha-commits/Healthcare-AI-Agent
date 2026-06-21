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
from backend.agent.response_formatters import (
    format_datetime,
    format_doctor_schedule,
    format_patient_clarification,
    format_patient_history,
)
from backend.agent.tools import (
    busiest_doctor,
    cancel_appointment,
    department_load_tool,
    doctor_schedule,
    list_departments,
    list_doctors,
    monthly_appointments,
    patient_history,
    search_patient,
)


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
            return self._handle_find_patient(message, session_id)

        if "department load" in message_lower:
            return self._handle_department_load(session_id)

        if message_lower in ["list departments", "show departments", "departments"]:
            return self._handle_list_departments(session_id)

        if "cardiologist" in message_lower or "cardiologists" in message_lower:
            return self._handle_cardiologists(session_id)

        if message_lower in ["list doctors", "show doctors"]:
            return self._handle_list_doctors(session_id)

        if "busiest doctor" in message_lower or "most appointments" in message_lower:
            return self._handle_busiest_doctor(session_id)

        if "appointments this month" in message_lower or "monthly appointments" in message_lower:
            return self._handle_monthly_appointments(session_id)

        if "cancel appointment" in message_lower:
            return self._handle_cancel_appointment(message, session_id)

        if "patient history" in message_lower or "history for" in message_lower:
            return self._handle_patient_history(message, session_id)

        if "schedule" in message_lower and "doctor" in message_lower:
            return self._handle_doctor_schedule(message, session_id)

        return self._handle_llm_fallback(message, session_id)

    def _handle_find_patient(self, message, session_id):
        tools_called = []
        query = message.replace("Find patient", "").replace("find patient", "").strip()

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

        lines = ["Patients found:"]

        for patient in patients:
            lines.append(
                f"• {patient.get('full_name')} | "
                f"Age: {patient.get('age')} | "
                f"Phone: {patient.get('phone')}"
            )

        reply = "\n".join(lines)
        return self._finish(session_id, reply, tools_called)

    def _handle_department_load(self, session_id):
        tools_called = []

        try:
            result = department_load_tool()

            tools_called.append({
                "name": "department_load",
                "args": {},
                "result": result,
            })

            if not result:
                reply = "I could not calculate department load."
                return self._finish(session_id, reply, tools_called)

            lines = ["Department load:"]

            if isinstance(result, dict):
                result = (
                    result.get("departments")
                    or result.get("items")
                    or result.get("data")
                    or []
                )

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

            reply = "\n".join(lines)

        except Exception as exc:
            tools_called.append({
                "name": "department_load",
                "args": {},
                "error": str(exc),
            })

            reply = "Department load is currently unavailable, but other analytics are working."

        return self._finish(session_id, reply, tools_called)

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

    def _handle_cardiologists(self, session_id):
        tools_called = []
        doctors = list_doctors(specialty="Cardiology")

        tools_called.append({
            "name": "list_doctors",
            "args": {
                "specialty": "Cardiology",
            },
            "result_count": len(doctors),
        })

        if not doctors:
            reply = "No cardiologists found."
            return self._finish(session_id, reply, tools_called)

        lines = ["Cardiologists:"]

        for doctor in doctors:
            lines.append(
                f"• Dr. {doctor.get('full_name')} | "
                f"Department: {doctor.get('department_name')}"
            )

        reply = "\n".join(lines)
        return self._finish(session_id, reply, tools_called)

    def _handle_list_doctors(self, session_id):
        tools_called = []
        doctors = list_doctors()

        tools_called.append({
            "name": "list_doctors",
            "args": {},
            "result_count": len(doctors),
        })

        lines = ["Doctors:"]

        for doctor in doctors:
            lines.append(
                f"• Dr. {doctor.get('full_name')} | "
                f"{doctor.get('specialty')} | "
                f"{doctor.get('department_name')}"
            )

        reply = "\n".join(lines)
        return self._finish(session_id, reply, tools_called)

    def _handle_busiest_doctor(self, session_id):
        tools_called = []
        result = busiest_doctor()

        tools_called.append({
            "name": "busiest_doctor",
            "args": {},
            "result": result,
        })

        if not result or "error" in result:
            reply = "I could not calculate the busiest doctor."
            return self._finish(session_id, reply, tools_called)

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

        reply = f"The busiest doctor is Dr. {doctor_name} with {count} appointments."
        return self._finish(session_id, reply, tools_called)

    def _handle_monthly_appointments(self, session_id):
        tools_called = []
        result = monthly_appointments()

        tools_called.append({
            "name": "monthly_appointments",
            "args": {},
            "result": result,
        })

        if not result or "error" in result:
            reply = "I could not calculate this month's appointments."
            return self._finish(session_id, reply, tools_called)

        count = (
            result.get("appointments")
            or result.get("count")
            or result.get("appointment_count")
            or result.get("total")
            or 0
        )

        reply = f"There are {count} appointments this month."
        return self._finish(session_id, reply, tools_called)

    def _handle_cancel_appointment(self, message, session_id):
        tools_called = []
        appointment_id = extract_first_number(message)

        if appointment_id is None:
            reply = "Please provide the appointment ID you want to cancel."
            return self._finish(session_id, reply, tools_called)

        result = cancel_appointment(appointment_id)

        tools_called.append({
            "name": "cancel_appointment",
            "args": {
                "appointment_id": appointment_id,
            },
            "result": result,
        })

        if not result or "error" in result:
            reply = f"Could not cancel appointment {appointment_id}."
            return self._finish(session_id, reply, tools_called)

        reply = f"Appointment {appointment_id} was cancelled successfully."

        if result.get("patient_name"):
            reply += f"\nPatient: {result.get('patient_name')}"

        if result.get("doctor_name"):
            reply += f"\nDoctor: Dr. {result.get('doctor_name')}"

        if result.get("appointment_datetime"):
            reply += f"\nTime: {format_datetime(result.get('appointment_datetime'))}"

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

    def _handle_doctor_schedule(self, message, session_id):
        tools_called = []
        doctor_id = extract_first_number(message)

        if doctor_id is None:
            reply = "Please provide the doctor ID to show the schedule."
            return self._finish(session_id, reply, tools_called)

        result = doctor_schedule(doctor_id)

        tools_called.append({
            "name": "doctor_schedule",
            "args": {
                "doctor_id": doctor_id,
            },
            "result": result,
        })

        reply = format_doctor_schedule(doctor_id, result)
        return self._finish(session_id, reply, tools_called)

    def _handle_llm_fallback(self, message, session_id):
        tools_called = []

        prompt = f"{SYSTEM_PROMPT}\nUser: {message}\nAssistant:"
        llm_resp = generate_text(prompt)
        text = llm_resp.get("text", "")

        try:
            payload = json.loads(text)
        except Exception:
            return self._finish(session_id, text, tools_called)

        action = payload.get("action")

        if action == "book_flow":
            return handle_book_flow(
                payload=payload,
                message=message,
                session_id=session_id,
                add_history=self.add_history,
            )

        reply = f"LLM requested unknown action: {action}. Raw: {payload}"
        return self._finish(session_id, reply, tools_called)