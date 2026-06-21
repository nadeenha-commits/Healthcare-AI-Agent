import json
import re
from datetime import datetime
from typing import Optional

from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.gemini_client import generate_text
from backend.agent.tools import (
    search_patient,
    available_slots,
    book_appointment,
    busiest_doctor,
    monthly_appointments,
    patient_history,
    doctor_schedule,
    cancel_appointment,
)


class Agent:
    def __init__(self):
        self.histories = {}

    def get_history(self, session_id: Optional[str] = None):
        return self.histories.get(session_id or "default", [])

    def add_history(self, session_id: Optional[str], role: str, text: str):
        sid = session_id or "default"
        self.histories.setdefault(sid, [])
        self.histories[sid].append({"role": role, "text": text})

    def handle_message(self, message: str, session_id: Optional[str] = None):
        self.add_history(session_id, "user", message)

        message_lower = message.lower().strip()
        tools_called = []

        if message_lower in ["hi", "hello", "hey"]:
            reply = (
                "Hello! I can help with patients, doctors, appointments, "
                "schedules, treatments, and clinic analytics."
            )
            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        if "busiest doctor" in message_lower or "most appointments" in message_lower:
            result = busiest_doctor()
            tools_called.append({"name": "busiest_doctor", "args": {}, "result": result})

            if not result or "error" in result:
                reply = "I could not calculate the busiest doctor."
            else:
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

            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        if "appointments this month" in message_lower or "monthly appointments" in message_lower:
            result = monthly_appointments()
            tools_called.append({"name": "monthly_appointments", "args": {}, "result": result})

            if not result or "error" in result:
                reply = "I could not calculate this month's appointments."
            else:
                count = (
                    result.get("appointments")
                    or result.get("count")
                    or result.get("appointment_count")
                    or result.get("total")
                    or 0
                )
                reply = f"There are {count} appointments this month."

            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        if "cancel appointment" in message_lower:
            appointment_id = self._extract_first_number(message)

            if appointment_id is None:
                reply = "Please provide the appointment ID you want to cancel."
                self.add_history(session_id, "assistant", reply)
                return {"reply": reply, "tools_called": tools_called}

            result = cancel_appointment(appointment_id)
            tools_called.append({
                "name": "cancel_appointment",
                "args": {"appointment_id": appointment_id},
                "result": result,
            })

            if not result or "error" in result:
                reply = f"Could not cancel appointment {appointment_id}."
            else:
                patient_name = result.get("patient_name")
                doctor_name = result.get("doctor_name")
                appointment_time = self._format_datetime(result.get("appointment_datetime"))

                if patient_name and doctor_name:
                    reply = (
                        f"Appointment {appointment_id} was cancelled successfully.\n"
                        f"Patient: {patient_name}\n"
                        f"Doctor: Dr. {doctor_name}"
                    )
                    if appointment_time != "Unknown date":
                        reply += f"\nTime: {appointment_time}"
                else:
                    reply = f"Appointment {appointment_id} was cancelled successfully."

            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        if "patient history" in message_lower or "history for" in message_lower:
            query = self._extract_patient_history_query(message)

            patients = search_patient(query)
            tools_called.append({
                "name": "search_patient",
                "args": {"query": query},
                "result_count": len(patients),
            })

            if not patients:
                reply = f'No patient matched "{query}".'
                self.add_history(session_id, "assistant", reply)
                return {"reply": reply, "tools_called": tools_called}

            patient = patients[0]
            result = patient_history(patient["id"])
            tools_called.append({
                "name": "patient_history",
                "args": {"patient_id": patient["id"]},
                "result": result,
            })

            reply = self._format_patient_history(patient, result)
            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        if "schedule" in message_lower and "doctor" in message_lower:
            doctor_id = self._extract_first_number(message)

            if doctor_id is None:
                reply = "Please provide the doctor ID to show the schedule."
                self.add_history(session_id, "assistant", reply)
                return {"reply": reply, "tools_called": tools_called}

            result = doctor_schedule(doctor_id)
            tools_called.append({
                "name": "doctor_schedule",
                "args": {"doctor_id": doctor_id},
                "result": result,
            })

            reply = self._format_doctor_schedule(doctor_id, result)
            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        prompt = f"{SYSTEM_PROMPT}\nUser: {message}\nAssistant:"
        llm_resp = generate_text(prompt)
        text = llm_resp.get("text", "")

        try:
            payload = json.loads(text)
        except Exception:
            self.add_history(session_id, "assistant", text)
            return {"reply": text, "tools_called": []}

        action = payload.get("action")

        if action == "book_flow":
            return self._handle_book_flow(payload, message, session_id)

        reply = f"LLM requested unknown action: {action}. Raw: {payload}"
        self.add_history(session_id, "assistant", reply)
        return {"reply": reply, "tools_called": tools_called}

    def _handle_book_flow(self, payload: dict, message: str, session_id: Optional[str] = None):
        tools_called = []

        args = payload.get("args", {})
        query = args.get("query") or self._extract_name_from_message(message)
        specialty = args.get("specialty") or self._extract_specialty_from_message(message)
        date_range = args.get("date_range") or "next week"

        patients = search_patient(query)
        tools_called.append({
            "name": "search_patient",
            "args": {"query": query},
            "result_count": len(patients),
        })

        if len(patients) == 0:
            reply = f'No patient matched "{query}". Would you like to add a new patient?'
            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        if len(patients) > 1:
            reply = f'Multiple patients matched "{query}". Please provide more info like phone number.'
            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        patient = patients[0]
        patient_id = patient["id"]

        slots = available_slots(specialty=specialty, doctor_id=None, date=date_range)
        tools_called.append({
            "name": "available_slots",
            "args": {"specialty": specialty, "date_range": date_range},
            "result_count": len(slots),
        })

        if not slots:
            reply = f"No available slots found for {specialty} in {date_range}."
            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        booked = None
        last_error = None
        selected_doctor_name = None
        selected_doctor_specialty = None

        for choice in slots:
            doctor_id = choice["doctor_id"]
            selected_doctor_name = choice.get("doctor_name")
            selected_doctor_specialty = choice.get("specialty")

            for dt in choice.get("slots", []):
                attempt = book_appointment(patient_id, doctor_id, dt)

                tools_called.append({
                    "name": "book_appointment",
                    "args": {
                        "patient_id": patient_id,
                        "doctor_id": doctor_id,
                        "datetime": dt,
                    },
                    "result": attempt,
                })

                if "error" not in attempt:
                    booked = attempt
                    break

                last_error = attempt.get("error")

            if booked:
                break

        if not booked:
            reply = "Could not find any available appointment slot."
            if last_error:
                reply += f" Last error: {last_error}"
            self.add_history(session_id, "assistant", reply)
            return {"reply": reply, "tools_called": tools_called}

        reply = (
            f"Booked appointment for {booked.get('patient_name', patient['full_name'])} "
            f"with Dr. {booked.get('doctor_name', selected_doctor_name)} "
            f"({booked.get('specialty', selected_doctor_specialty)}) "
            f"on {self._format_datetime(booked.get('appointment_datetime'))}.\n"
            f"Appointment ID: {booked.get('id')}"
        )

        self.add_history(session_id, "assistant", reply)
        return {"reply": reply, "tools_called": tools_called}

    def _extract_first_number(self, message: str):
        match = re.search(r"\d+", message)
        if match:
            return int(match.group())
        return None

    def _extract_name_from_message(self, message: str):
        tokens = message.split(" for ")
        if len(tokens) > 1:
            candidate = tokens[1].split(" with ")[0]
            return candidate.strip()
        return message.strip()

    def _extract_specialty_from_message(self, message: str):
        for specialty in ["cardiology", "neurology", "pediatrics", "oncology", "general"]:
            if specialty in message.lower():
                return specialty.capitalize()

        if "heart" in message.lower() or "cardiologist" in message.lower():
            return "Cardiology"

        return None

    def _extract_patient_history_query(self, message: str):
        message_lower = message.lower()

        if "patient history for" in message_lower:
            return message.split("for")[-1].strip()

        if "history for" in message_lower:
            return message.split("for")[-1].strip()

        if "patient history" in message_lower:
            original_index = message_lower.find("patient history") + len("patient history")
            return message[original_index:].strip()

        return message.strip()

    def _format_datetime(self, value):
        if not value:
            return "Unknown date"

        try:
            return datetime.fromisoformat(str(value).replace("Z", "")).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(value)

    def _format_patient_history(self, patient: dict, history: dict):
        if not history or "error" in history:
            return f"No history found for {patient.get('full_name')}."

        patient_info = history.get("patient", {})
        appointments = history.get("appointments", [])
        treatments = history.get("treatments", [])

        active_appointments = [
            appointment for appointment in appointments
            if appointment.get("status") != "cancelled"
        ]

        lines = [
            f"Patient: {patient_info.get('full_name')}",
            f"Age: {patient_info.get('age')}",
            f"Phone: {patient_info.get('phone')}",
            f"Medical History: {patient_info.get('medical_history')}",
            "",
            "=== APPOINTMENTS ===",
        ]

        if active_appointments:
            for appointment in active_appointments:
                lines.append(
                    f"• {self._format_datetime(appointment.get('datetime'))} | "
                    f"Dr. {appointment.get('doctor_name')} "
                    f"({appointment.get('specialty')}) | "
                    f"Status: {appointment.get('status')}"
                )
        else:
            lines.append("• No active appointments")

        lines.extend(["", "=== TREATMENTS ==="])

        if treatments:
            for treatment in treatments:
                lines.append(
                    f"• Dr. {treatment.get('doctor_name')} | "
                    f"Diagnosis: {treatment.get('diagnosis')} | "
                    f"Plan: {treatment.get('plan')}"
                )
        else:
            lines.append("• No treatments")

        return "\n".join(lines)

    def _format_doctor_schedule(self, doctor_id: int, schedule):
        if not schedule:
            return f"No appointments found for doctor {doctor_id}."

        if "error" in schedule:
            return f"Doctor {doctor_id} was not found."

        doctor = schedule.get("doctor", {})
        appointments = schedule.get("appointments", [])

        active_appointments = [
            appointment for appointment in appointments
            if appointment.get("status") != "cancelled"
        ]

        lines = [
            f"Dr. {doctor.get('full_name')} ({doctor.get('specialty')})",
            "",
            "=== UPCOMING APPOINTMENTS ===",
        ]

        if active_appointments:
            for appointment in active_appointments:
                lines.append(
                    f"• {appointment.get('patient_name')} - "
                    f"{self._format_datetime(appointment.get('datetime'))} "
                    f"({appointment.get('status')})"
                )
        else:
            lines.append("• No scheduled appointments")

        lines.append("")
        lines.append(f"Total active appointments: {len(active_appointments)}")

        return "\n".join(lines)
