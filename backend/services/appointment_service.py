from datetime import datetime

from backend.db.database import SessionLocal
from backend.db.models import Appointment, Doctor, Patient
from backend.services.serializers import (
    serialize_appointment,
    serialize_appointment_status,
)
from backend.services.service_utils import (
    error_response,
    parse_datetime,
    parse_positive_int,
    parse_required_positive_int,
    validate_appointment_status,
)

# Compatibility exports.
# These keep existing imports working while the project is being refactored.
from backend.services.department_service import list_departments
from backend.services.doctor_service import (
    get_doctor_by_id_service,
    get_doctor_schedule,
    list_doctors_service,
)
from backend.services.treatment_service import (
    add_treatment_service,
    get_patient_history,
)


def list_appointments(args):
    args = args or {}

    doctor_id = args.get("doctor_id")
    patient_id = args.get("patient_id")

    status, status_error = validate_appointment_status(args.get("status"))

    if status_error:
        return status_error

    if doctor_id:
        doctor_id, doctor_id_error = parse_positive_int(doctor_id, "doctor_id")

        if doctor_id_error:
            return doctor_id_error

    if patient_id:
        patient_id, patient_id_error = parse_positive_int(patient_id, "patient_id")

        if patient_id_error:
            return patient_id_error

    db = SessionLocal()

    try:
        query = db.query(Appointment)

        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)

        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)

        if status:
            query = query.filter(Appointment.status == status)

        appointments = query.order_by(Appointment.appointment_datetime).all()
        return [serialize_appointment(appointment) for appointment in appointments]

    finally:
        db.close()


def create_appointment(data):
    patient_id, patient_id_error = parse_required_positive_int(data, "patient_id")

    if patient_id_error:
        return patient_id_error

    doctor_id, doctor_id_error = parse_required_positive_int(data, "doctor_id")

    if doctor_id_error:
        return doctor_id_error

    appointment_datetime, datetime_error = parse_datetime(
        data.get("appointment_datetime"),
        "appointment_datetime",
        required=True,
    )

    if datetime_error:
        return datetime_error

    if appointment_datetime < datetime.utcnow():
        return error_response(
            "appointment_datetime_must_be_future",
            "appointment_datetime must be in the future.",
        )

    db = SessionLocal()

    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not patient:
            return error_response(
                "patient_not_found",
                "No patient exists with this patient_id.",
            )

        if not doctor:
            return error_response(
                "doctor_not_found",
                "No doctor exists with this doctor_id.",
            )

        doctor_slot_error = _validate_doctor_slot_available(
            db,
            doctor_id,
            appointment_datetime,
        )

        if doctor_slot_error:
            return doctor_slot_error

        patient_slot_error = _validate_patient_slot_available(
            db,
            patient_id,
            appointment_datetime,
        )

        if patient_slot_error:
            return patient_slot_error

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_datetime=appointment_datetime,
            status="scheduled",
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        return serialize_appointment(appointment)

    finally:
        db.close()


def cancel_appointment_service(appointment_id):
    return _update_appointment_status(
        appointment_id=appointment_id,
        new_status="cancelled",
    )


def complete_appointment_service(appointment_id):
    return _update_appointment_status(
        appointment_id=appointment_id,
        new_status="completed",
    )


def _validate_doctor_slot_available(db, doctor_id, appointment_datetime):
    existing = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_datetime == appointment_datetime,
            Appointment.status != "cancelled",
        )
        .first()
    )

    if existing:
        return error_response(
            "slot_already_booked",
            "This doctor already has an appointment at this time.",
            existing_appointment_id=existing.id,
        )

    return None


def _validate_patient_slot_available(db, patient_id, appointment_datetime):
    existing = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.appointment_datetime == appointment_datetime,
            Appointment.status != "cancelled",
        )
        .first()
    )

    if existing:
        return error_response(
            "patient_already_has_appointment",
            "This patient already has an appointment at this time.",
            existing_appointment_id=existing.id,
        )

    return None


def _update_appointment_status(appointment_id, new_status):
    appointment_id, appointment_id_error = parse_positive_int(
        appointment_id,
        "appointment_id",
    )

    if appointment_id_error:
        return appointment_id_error

    db = SessionLocal()

    try:
        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .first()
        )

        if not appointment:
            return error_response(
                "not_found",
                "Appointment was not found.",
            )

        status_error = _validate_status_transition(
            appointment.status,
            new_status,
        )

        if status_error:
            return status_error

        appointment.status = new_status
        db.commit()
        db.refresh(appointment)

        return serialize_appointment_status(appointment)

    finally:
        db.close()


def _validate_status_transition(current_status, new_status):
    if new_status == "cancelled" and current_status == "completed":
        return error_response(
            "appointment_already_completed",
            "Completed appointments cannot be cancelled.",
        )

    if new_status == "completed" and current_status == "cancelled":
        return error_response(
            "appointment_cancelled",
            "Cancelled appointments cannot be completed.",
        )

    return None