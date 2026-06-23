from backend.db.database import SessionLocal
from backend.db.models import Appointment, Doctor
from backend.services.serializers import (
    serialize_doctor,
    serialize_doctor_schedule,
)
from backend.services.service_utils import (
    clean_string,
    error_response,
    parse_datetime,
    parse_positive_int,
)


def list_doctors_service(specialty=None):
    db = SessionLocal()

    try:
        query = db.query(Doctor)
        specialty = clean_string(specialty)

        if specialty:
            query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))

        doctors = query.order_by(Doctor.id).all()
        return [serialize_doctor(doctor) for doctor in doctors]

    finally:
        db.close()


def get_doctor_by_id_service(doctor_id):
    doctor_id, doctor_id_error = parse_positive_int(doctor_id, "doctor_id")

    if doctor_id_error:
        return doctor_id_error

    db = SessionLocal()

    try:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not doctor:
            return None

        return serialize_doctor(doctor)

    finally:
        db.close()


def get_doctor_schedule(doctor_id, start=None, end=None):
    doctor_id, doctor_id_error = parse_positive_int(doctor_id, "doctor_id")

    if doctor_id_error:
        return doctor_id_error

    start_dt, start_error = parse_datetime(start, "start", required=False)

    if start_error:
        return error_response(
            "invalid_start",
            "start must be a valid ISO datetime.",
        )

    end_dt, end_error = parse_datetime(end, "end", required=False)

    if end_error:
        return error_response(
            "invalid_end",
            "end must be a valid ISO datetime.",
        )

    if start_dt and end_dt and start_dt > end_dt:
        return error_response(
            "invalid_date_range",
            "start must be before end.",
        )

    db = SessionLocal()

    try:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not doctor:
            return error_response(
                "doctor_not_found",
                "No doctor exists with this doctor_id.",
            )

        query = db.query(Appointment).filter(Appointment.doctor_id == doctor_id)

        if start_dt:
            query = query.filter(Appointment.appointment_datetime >= start_dt)

        if end_dt:
            query = query.filter(Appointment.appointment_datetime <= end_dt)

        appointments = query.order_by(Appointment.appointment_datetime).all()
        return serialize_doctor_schedule(doctor, appointments)

    finally:
        db.close()