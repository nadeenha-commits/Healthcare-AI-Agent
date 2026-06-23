from backend.db.database import SessionLocal
from backend.db.models import Doctor, Patient, Treatment
from backend.services.serializers import (
    serialize_patient_history,
    serialize_treatment,
)
from backend.services.service_utils import (
    clean_string,
    error_response,
    parse_positive_int,
    parse_required_positive_int,
)


def get_patient_history(patient_id):
    patient_id, patient_id_error = parse_positive_int(patient_id, "patient_id")

    if patient_id_error:
        return patient_id_error

    db = SessionLocal()

    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        if not patient:
            return None

        return serialize_patient_history(patient)

    finally:
        db.close()


def add_treatment_service(data):
    patient_id, patient_id_error = parse_required_positive_int(data, "patient_id")

    if patient_id_error:
        return patient_id_error

    doctor_id, doctor_id_error = parse_required_positive_int(data, "doctor_id")

    if doctor_id_error:
        return doctor_id_error

    diagnosis = clean_string(data.get("diagnosis"))
    treatment_plan = clean_string(data.get("treatment_plan")) or ""

    if not diagnosis:
        return error_response(
            "diagnosis_required",
            "diagnosis is required.",
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

        treatment = Treatment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            diagnosis=diagnosis,
            treatment_plan=treatment_plan,
        )

        db.add(treatment)
        db.commit()
        db.refresh(treatment)

        return serialize_treatment(treatment, patient, doctor)

    finally:
        db.close()