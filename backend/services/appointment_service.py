from backend.db.database import SessionLocal
from backend.db.models import Appointment, Doctor, Patient, Department, Treatment
from datetime import datetime


def list_appointments(args):
    db = SessionLocal()
    try:
        qry = db.query(Appointment)

        if args.get("doctor_id"):
            qry = qry.filter(Appointment.doctor_id == int(args.get("doctor_id")))
        if args.get("patient_id"):
            qry = qry.filter(Appointment.patient_id == int(args.get("patient_id")))
        if args.get("status"):
            qry = qry.filter(Appointment.status == args.get("status"))

        appointments = qry.order_by(Appointment.appointment_datetime).all()

        return [
            {
                "id": appointment.id,
                "patient_id": appointment.patient_id,
                "patient_name": appointment.patient.full_name if appointment.patient else None,
                "doctor_id": appointment.doctor_id,
                "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
                "specialty": appointment.doctor.specialty if appointment.doctor else None,
                "appointment_datetime": appointment.appointment_datetime.isoformat(),
                "status": appointment.status,
            }
            for appointment in appointments
        ]
    finally:
        db.close()


def create_appointment(data):
    db = SessionLocal()
    try:
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        dt = data.get("appointment_datetime")

        if not (patient_id and doctor_id and dt):
            return {"error": "missing_fields"}

        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not patient:
            return {"error": "patient_not_found"}
        if not doctor:
            return {"error": "doctor_not_found"}

        try:
            dt_obj = datetime.fromisoformat(str(dt).replace("Z", ""))
        except Exception:
            return {"error": "invalid_datetime"}

        existing = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_datetime == dt_obj,
                Appointment.status == "scheduled",
            )
            .first()
        )

        if existing:
            return {
                "error": "slot_already_booked",
                "existing_appointment_id": existing.id,
                "doctor_id": doctor.id,
                "doctor_name": doctor.full_name,
                "appointment_datetime": existing.appointment_datetime.isoformat(),
            }

        appt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_datetime=dt_obj,
            status="scheduled",
        )

        db.add(appt)
        db.commit()
        db.refresh(appt)

        return {
            "id": appt.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "doctor_id": doctor.id,
            "doctor_name": doctor.full_name,
            "specialty": doctor.specialty,
            "appointment_datetime": appt.appointment_datetime.isoformat(),
            "status": appt.status,
        }
    finally:
        db.close()


def cancel_appointment_service(appointment_id):
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

        if not appointment:
            return {"error": "not_found"}

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
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

        if not appointment:
            return {"error": "not_found"}

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
    db = SessionLocal()
    try:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not doctor:
            return {"error": "doctor_not_found"}

        qry = db.query(Appointment).filter(Appointment.doctor_id == doctor_id)

        if start:
            try:
                start_dt = datetime.fromisoformat(str(start).replace("Z", ""))
                qry = qry.filter(Appointment.appointment_datetime >= start_dt)
            except Exception:
                pass

        if end:
            try:
                end_dt = datetime.fromisoformat(str(end).replace("Z", ""))
                qry = qry.filter(Appointment.appointment_datetime <= end_dt)
            except Exception:
                pass

        appointments = qry.order_by(Appointment.appointment_datetime).all()

        return {
            "doctor": {
                "id": doctor.id,
                "full_name": doctor.full_name,
                "specialty": doctor.specialty,
            },
            "appointments": [
                {
                    "id": appointment.id,
                    "patient_id": appointment.patient_id,
                    "patient_name": appointment.patient.full_name if appointment.patient else None,
                    "datetime": appointment.appointment_datetime.isoformat(),
                    "status": appointment.status,
                }
                for appointment in appointments
            ],
        }
    finally:
        db.close()


def list_doctors_service(specialty=None):
    db = SessionLocal()
    try:
        qry = db.query(Doctor)

        if specialty:
            qry = qry.filter(Doctor.specialty.ilike(f"%{specialty}%"))

        doctors = qry.all()

        return [
            {
                "id": doctor.id,
                "full_name": doctor.full_name,
                "specialty": doctor.specialty,
                "department_id": doctor.department_id,
                "department_name": doctor.department.name if doctor.department else None,
            }
            for doctor in doctors
        ]
    finally:
        db.close()


def list_departments():
    db = SessionLocal()
    try:
        departments = db.query(Department).all()

        return [
            {
                "id": department.id,
                "name": department.name,
                "description": department.description,
            }
            for department in departments
        ]
    finally:
        db.close()


def get_patient_history(patient_id):
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        if not patient:
            return None

        appointments = [
            {
                "id": appointment.id,
                "datetime": appointment.appointment_datetime.isoformat(),
                "doctor_id": appointment.doctor_id,
                "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
                "specialty": appointment.doctor.specialty if appointment.doctor else None,
                "status": appointment.status,
            }
            for appointment in sorted(patient.appointments, key=lambda a: a.appointment_datetime)
        ]

        treatments = [
            {
                "id": treatment.id,
                "doctor_id": treatment.doctor_id,
                "doctor_name": treatment.doctor.full_name if treatment.doctor else None,
                "diagnosis": treatment.diagnosis,
                "plan": treatment.treatment_plan,
            }
            for treatment in sorted(patient.treatments, key=lambda t: t.created_at)
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
    db = SessionLocal()
    try:
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        diagnosis = data.get("diagnosis")
        plan = data.get("treatment_plan")

        if not (patient_id and doctor_id and diagnosis):
            return {"error": "missing_fields"}

        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

        if not patient:
            return {"error": "patient_not_found"}
        if not doctor:
            return {"error": "doctor_not_found"}

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
