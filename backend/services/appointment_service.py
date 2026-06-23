from datetime import datetime

from backend.db.database import SessionLocal
from backend.db.models import Appointment, Doctor, Patient, Department, Treatment


ALLOWED_APPOINTMENT_STATUSES = {"scheduled", "cancelled", "completed"}


def _clean_string(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value else None


def _parse_positive_int(value, field_name):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, {
            "error": f"invalid_{field_name}",
            "message": f"{field_name} must be a positive integer.",
        }

    if number <= 0:
        return None, {
            "error": f"invalid_{field_name}",
            "message": f"{field_name} must be greater than 0.",
        }

    return number, None


def _parse_datetime(value):
    value = _clean_string(value)

    if not value:
        return None, {
            "error": "invalid_datetime",
            "message": "appointment_datetime is required.",
        }

    try:
        normalized = value.replace("Z", "")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None, {
            "error": "invalid_datetime",
            "message": (
                "appointment_datetime must be a valid ISO datetime, "
                "for example 2026-06-25T10:00:00."
            ),
        }

    return parsed, None


def list_appointments(args):
    doctor_id = args.get("doctor_id")
    patient_id = args.get("patient_id")
    status = _clean_string(args.get("status"))

    if doctor_id:
        doctor_id, error = _parse_positive_int(doctor_id, "doctor_id")
        if error:
            return error

    if patient_id:
        patient_id, error = _parse_positive_int(patient_id, "patient_id")
        if error:
            return error

    if status and status not in ALLOWED_APPOINTMENT_STATUSES:
        return {
            "error": "invalid_status",
            "message": "status must be one of: scheduled, cancelled, completed.",
        }

    db = SessionLocal()

    try:
        qry = db.query(Appointment)

        if doctor_id:
            qry = qry.filter(Appointment.doctor_id == doctor_id)

        if patient_id:
            qry = qry.filter(Appointment.patient_id == patient_id)

        if status:
            qry = qry.filter(Appointment.status == status)

        appointments = qry.order_by(Appointment.appointment_datetime).all()

        return [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "patient_name": a.patient.full_name if a.patient else None,
                "doctor_id": a.doctor_id,
                "doctor_name": a.doctor.full_name if a.doctor else None,
                "specialty": a.doctor.specialty if a.doctor else None,
                "appointment_datetime": a.appointment_datetime.isoformat(),
                "status": a.status,
            }
            for a in appointments
        ]

    finally:
        db.close()


def create_appointment(data):
    patient_id_raw = data.get("patient_id")
    doctor_id_raw = data.get("doctor_id")
    datetime_raw = data.get("appointment_datetime")

    if patient_id_raw in (None, ""):
        return {
            "error": "patient_id_required",
            "message": "patient_id is required.",
        }

    if doctor_id_raw in (None, ""):
        return {
            "error": "doctor_id_required",
            "message": "doctor_id is required.",
        }

    if datetime_raw in (None, ""):
        return {
            "error": "appointment_datetime_required",
            "message": "appointment_datetime is required.",
        }

    patient_id, patient_id_error = _parse_positive_int(patient_id_raw, "patient_id")
    if patient_id_error:
        return patient_id_error

    doctor_id, doctor_id_error = _parse_positive_int(doctor_id_raw, "doctor_id")
    if doctor_id_error:
        return doctor_id_error

    dt_obj, datetime_error = _parse_datetime(datetime_raw)
    if datetime_error:
        return datetime_error

    if dt_obj < datetime.utcnow():
        return {
            "error": "appointment_datetime_must_be_future",
            "message": "appointment_datetime must be in the future.",
        }

    db = SessionLocal()

    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not patient:
            return {
                "error": "patient_not_found",
                "message": "No patient exists with this patient_id.",
            }

        if not doctor:
            return {
                "error": "doctor_not_found",
                "message": "No doctor exists with this doctor_id.",
            }

        existing_same_doctor_slot = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_datetime == dt_obj,
                Appointment.status != "cancelled",
            )
            .first()
        )

        if existing_same_doctor_slot:
            return {
                "error": "slot_already_booked",
                "message": "This doctor already has an appointment at this time.",
                "existing_appointment_id": existing_same_doctor_slot.id,
            }

        existing_same_patient_slot = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient_id,
                Appointment.appointment_datetime == dt_obj,
                Appointment.status != "cancelled",
            )
            .first()
        )

        if existing_same_patient_slot:
            return {
                "error": "patient_already_has_appointment",
                "message": "This patient already has an appointment at this time.",
                "existing_appointment_id": existing_same_patient_slot.id,
            }

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_datetime=dt_obj,
            status="scheduled",
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        return {
            "id": appointment.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "doctor_id": doctor.id,
            "doctor_name": doctor.full_name,
            "specialty": doctor.specialty,
            "appointment_datetime": appointment.appointment_datetime.isoformat(),
            "status": appointment.status,
        }

    finally:
        db.close()


def cancel_appointment_service(appointment_id):
    appointment_id, appointment_id_error = _parse_positive_int(
        appointment_id,
        "appointment_id",
    )

    if appointment_id_error:
        return appointment_id_error

    db = SessionLocal()

    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

        if not appointment:
            return {
                "error": "not_found",
                "message": "Appointment was not found.",
            }

        if appointment.status == "completed":
            return {
                "error": "appointment_already_completed",
                "message": "Completed appointments cannot be cancelled.",
            }

        appointment.status = "cancelled"
        db.commit()
        db.refresh(appointment)

        return {
            "id": appointment.id,
            "status": appointment.status,
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient.full_name if appointment.patient else None,
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
            "appointment_datetime": appointment.appointment_datetime.isoformat(),
        }

    finally:
        db.close()


def complete_appointment_service(appointment_id):
    appointment_id, appointment_id_error = _parse_positive_int(
        appointment_id,
        "appointment_id",
    )

    if appointment_id_error:
        return appointment_id_error

    db = SessionLocal()

    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

        if not appointment:
            return {
                "error": "not_found",
                "message": "Appointment was not found.",
            }

        if appointment.status == "cancelled":
            return {
                "error": "appointment_cancelled",
                "message": "Cancelled appointments cannot be completed.",
            }

        appointment.status = "completed"
        db.commit()
        db.refresh(appointment)

        return {
            "id": appointment.id,
            "status": appointment.status,
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient.full_name if appointment.patient else None,
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
            "appointment_datetime": appointment.appointment_datetime.isoformat(),
        }

    finally:
        db.close()


def get_doctor_schedule(doctor_id, start=None, end=None):
    doctor_id, doctor_id_error = _parse_positive_int(doctor_id, "doctor_id")
    if doctor_id_error:
        return doctor_id_error

    start_dt = None
    end_dt = None

    if start:
        start_dt, start_error = _parse_datetime(start)
        if start_error:
            return {
                "error": "invalid_start",
                "message": "start must be a valid ISO datetime.",
            }

    if end:
        end_dt, end_error = _parse_datetime(end)
        if end_error:
            return {
                "error": "invalid_end",
                "message": "end must be a valid ISO datetime.",
            }

    if start_dt and end_dt and start_dt > end_dt:
        return {
            "error": "invalid_date_range",
            "message": "start must be before end.",
        }

    db = SessionLocal()

    try:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not doctor:
            return {
                "error": "doctor_not_found",
                "message": "No doctor exists with this doctor_id.",
            }

        qry = db.query(Appointment).filter(Appointment.doctor_id == doctor_id)

        if start_dt:
            qry = qry.filter(Appointment.appointment_datetime >= start_dt)

        if end_dt:
            qry = qry.filter(Appointment.appointment_datetime <= end_dt)

        appointments = qry.order_by(Appointment.appointment_datetime).all()

        return {
            "doctor": {
                "id": doctor.id,
                "full_name": doctor.full_name,
                "specialty": doctor.specialty,
            },
            "appointments": [
                {
                    "id": a.id,
                    "patient_id": a.patient_id,
                    "patient_name": a.patient.full_name if a.patient else None,
                    "datetime": a.appointment_datetime.isoformat(),
                    "status": a.status,
                }
                for a in appointments
            ],
        }

    finally:
        db.close()


def list_doctors_service(specialty=None):
    db = SessionLocal()

    try:
        qry = db.query(Doctor)

        specialty = _clean_string(specialty)

        if specialty:
            qry = qry.filter(Doctor.specialty.ilike(f"%{specialty}%"))

        doctors = qry.order_by(Doctor.id).all()

        return [
            {
                "id": d.id,
                "full_name": d.full_name,
                "specialty": d.specialty,
                "department_id": d.department_id,
                "department_name": d.department.name if d.department else None,
            }
            for d in doctors
        ]

    finally:
        db.close()


def get_doctor_by_id_service(doctor_id):
    doctor_id, doctor_id_error = _parse_positive_int(doctor_id, "doctor_id")

    if doctor_id_error:
        return doctor_id_error

    db = SessionLocal()

    try:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not doctor:
            return None

        return {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "specialty": doctor.specialty,
            "department_id": doctor.department_id,
            "department_name": doctor.department.name if doctor.department else None,
        }

    finally:
        db.close()


def list_departments():
    db = SessionLocal()

    try:
        departments = db.query(Department).order_by(Department.id).all()

        return [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
            }
            for d in departments
        ]

    finally:
        db.close()


def get_patient_history(patient_id):
    patient_id, patient_id_error = _parse_positive_int(patient_id, "patient_id")
    if patient_id_error:
        return patient_id_error

    db = SessionLocal()

    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        if not patient:
            return None

        appointments = [
            {
                "id": a.id,
                "datetime": a.appointment_datetime.isoformat(),
                "doctor_id": a.doctor_id,
                "doctor_name": a.doctor.full_name if a.doctor else None,
                "specialty": a.doctor.specialty if a.doctor else None,
                "status": a.status,
            }
            for a in sorted(patient.appointments, key=lambda item: item.appointment_datetime)
        ]

        treatments = [
            {
                "id": t.id,
                "doctor_id": t.doctor_id,
                "doctor_name": t.doctor.full_name if t.doctor else None,
                "diagnosis": t.diagnosis,
                "plan": t.treatment_plan,
            }
            for t in sorted(patient.treatments, key=lambda item: item.created_at)
        ]

        return {
            "patient": {
                "id": patient.id,
                "full_name": patient.full_name,
                "phone": patient.phone,
                "age": patient.age,
                "gender": patient.gender,
                "medical_history": patient.medical_history,
            },
            "appointments": appointments,
            "treatments": treatments,
        }

    finally:
        db.close()


def add_treatment_service(data):
    patient_id_raw = data.get("patient_id")
    doctor_id_raw = data.get("doctor_id")
    diagnosis = _clean_string(data.get("diagnosis"))
    plan = _clean_string(data.get("treatment_plan")) or ""

    if patient_id_raw in (None, ""):
        return {
            "error": "patient_id_required",
            "message": "patient_id is required.",
        }

    if doctor_id_raw in (None, ""):
        return {
            "error": "doctor_id_required",
            "message": "doctor_id is required.",
        }

    if not diagnosis:
        return {
            "error": "diagnosis_required",
            "message": "diagnosis is required.",
        }

    patient_id, patient_id_error = _parse_positive_int(patient_id_raw, "patient_id")
    if patient_id_error:
        return patient_id_error

    doctor_id, doctor_id_error = _parse_positive_int(doctor_id_raw, "doctor_id")
    if doctor_id_error:
        return doctor_id_error

    db = SessionLocal()

    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not patient:
            return {
                "error": "patient_not_found",
                "message": "No patient exists with this patient_id.",
            }

        if not doctor:
            return {
                "error": "doctor_not_found",
                "message": "No doctor exists with this doctor_id.",
            }

        treatment = Treatment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            diagnosis=diagnosis,
            treatment_plan=plan,
        )

        db.add(treatment)
        db.commit()
        db.refresh(treatment)

        return {
            "id": treatment.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "doctor_id": doctor.id,
            "doctor_name": doctor.full_name,
            "diagnosis": treatment.diagnosis,
            "plan": treatment.treatment_plan,
        }

    finally:
        db.close()  