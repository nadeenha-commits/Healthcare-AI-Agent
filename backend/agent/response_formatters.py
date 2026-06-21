from datetime import datetime


def format_datetime(value):
    if not value:
        return "Unknown date"

    try:
        return datetime.fromisoformat(str(value).replace("Z", "")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)


def format_patient_clarification(query, patients):
    lines = [
        f'I found multiple patients matching "{query}". Please specify which patient you mean:'
    ]

    for patient in patients[:5]:
        lines.append(
            f"• ID {patient.get('id')}: {patient.get('full_name')} | "
            f"Phone: {patient.get('phone')} | Age: {patient.get('age')}"
        )

    return "\n".join(lines)


def format_patient_history(patient: dict, history: dict):
    if not history or "error" in history:
        return f"No history found for {patient.get('full_name')}."

    patient_info = history.get("patient", {})
    appointments = history.get("appointments", [])
    treatments = history.get("treatments", [])

    active_appointments = [
        appointment
        for appointment in appointments
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
                f"• {format_datetime(appointment.get('datetime'))} | "
                f"Dr. {appointment.get('doctor_name')} ({appointment.get('specialty')}) | "
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


def format_doctor_schedule(doctor_id: int, schedule):
    if not schedule:
        return f"No appointments found for doctor {doctor_id}."

    if "error" in schedule:
        return f"Doctor {doctor_id} was not found."

    doctor = schedule.get("doctor", {})
    appointments = schedule.get("appointments", [])

    active_appointments = [
        appointment
        for appointment in appointments
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
                f"{format_datetime(appointment.get('datetime'))} "
                f"({appointment.get('status')})"
            )
    else:
        lines.append("• No scheduled appointments")

    lines.append("")
    lines.append(f"Total active appointments: {len(active_appointments)}")

    return "\n".join(lines)