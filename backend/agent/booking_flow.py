from typing import Callable, Optional

from backend.agent.message_parser import (
    clean_extracted_value,
    choose_patient_match,
    extract_date_range_from_message,
    extract_name_from_message,
    extract_specialty_from_message,
)
from backend.agent.response_formatters import (
    format_datetime,
    format_patient_clarification,
)
from backend.agent.tools import (
    available_slots,
    book_appointment,
    search_patient,
)


def handle_book_flow(
    payload: dict,
    message: str,
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

    args = payload.get("args", {})

    query = args.get("query") or extract_name_from_message(message)
    specialty = args.get("specialty") or extract_specialty_from_message(message)
    date_range = args.get("date_range") or extract_date_range_from_message(message)

    query = clean_extracted_value(query)

    if not query:
        return finish("Please provide the patient name for the appointment.")

    if not specialty:
        return finish("Please provide the doctor specialty for the appointment.")

    patients = search_patient(query)

    tools_called.append({
        "name": "search_patient",
        "args": {
            "query": query,
        },
        "result_count": len(patients),
    })

    if len(patients) == 0:
        return finish(f'No patient matched "{query}". Would you like to add a new patient?')

    patient = choose_patient_match(patients, query)

    if patient is None:
        return finish(format_patient_clarification(query, patients))

    patient_id = patient["id"]

    slots = available_slots(
        specialty=specialty,
        doctor_id=None,
        date=date_range,
    )

    tools_called.append({
        "name": "available_slots",
        "args": {
            "specialty": specialty,
            "date": date_range,
        },
        "result_count": len(slots),
    })

    if not slots:
        return finish(f"No available slots found for {specialty} in {date_range}.")

    booked = None
    last_error = None

    for doctor_option in slots:
        doctor_id = doctor_option.get("doctor_id")
        candidate_slots = doctor_option.get("slots", [])

        for slot_datetime in candidate_slots:
            attempt = book_appointment(
                patient_id,
                doctor_id,
                slot_datetime,
            )

            tools_called.append({
                "name": "book_appointment",
                "args": {
                    "patient_id": patient_id,
                    "doctor_id": doctor_id,
                    "datetime": slot_datetime,
                },
                "result": attempt,
            })

            if isinstance(attempt, dict) and "error" not in attempt:
                booked = attempt
                break

            if isinstance(attempt, dict):
                last_error = attempt.get("error")

        if booked:
            break

    if not booked:
        reply = "Could not find any available appointment slot."

        if last_error:
            reply += f" Last error: {last_error}"

        return finish(reply)

    reply = (
        f"Booked appointment for {booked.get('patient_name', patient.get('full_name'))} "
        f"with Dr. {booked.get('doctor_name')} "
        f"({booked.get('specialty')}) "
        f"on {format_datetime(booked.get('appointment_datetime'))}.\n"
        f"Appointment ID: {booked.get('id')}"
    )

    return finish(reply)