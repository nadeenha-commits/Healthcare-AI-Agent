from backend.db.database import SessionLocal
from backend.db.models import Patient


def _clean_string(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def _parse_age(value):
    if value is None or value == "":
        return None

    try:
        age = int(value)
    except (TypeError, ValueError):
        return None

    if age < 0 or age > 130:
        return None

    return age


def list_patients(q=None, page=1, per=50):
    db = SessionLocal()
    try:
        qry = db.query(Patient)

        if q:
            qlike = f"%{q}%"
            qry = qry.filter(
                (Patient.full_name.ilike(qlike)) |
                (Patient.phone.ilike(qlike))
            )

        patients = qry.offset((page - 1) * per).limit(per).all()

        return [
            {
                "id": p.id,
                "full_name": p.full_name,
                "phone": p.phone,
                "age": p.age,
                "gender": p.gender,
            }
            for p in patients
        ]

    finally:
        db.close()


def get_patient(patient_id):
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        if not patient:
            return None

        return {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "medical_history": patient.medical_history,
        }

    finally:
        db.close()


def create_patient(data):
    full_name = _clean_string(data.get("full_name"))
    phone = _clean_string(data.get("phone"))
    gender = _clean_string(data.get("gender"))
    medical_history = _clean_string(data.get("medical_history")) or ""
    age = _parse_age(data.get("age"))

    if not full_name:
        return {
            "error": "full_name_required",
            "message": "full_name is required."
        }

    if data.get("age") not in (None, "") and age is None:
        return {
            "error": "invalid_age",
            "message": "age must be a number between 0 and 130."
        }

    db = SessionLocal()
    try:
        patient = Patient(
            full_name=full_name,
            phone=phone,
            age=age,
            gender=gender,
            medical_history=medical_history,
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        return {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
        }

    finally:
        db.close()


def update_patient(patient_id, data):
    allowed_fields = {"full_name", "phone", "age", "gender", "medical_history"}

    if not any(field in data for field in allowed_fields):
        return {
            "error": "no_update_fields",
            "message": "At least one valid patient field is required."
        }

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        if not patient:
            return None

        if "full_name" in data:
            full_name = _clean_string(data.get("full_name"))
            if not full_name:
                return {
                    "error": "invalid_full_name",
                    "message": "full_name cannot be empty."
                }
            patient.full_name = full_name

        if "phone" in data:
            patient.phone = _clean_string(data.get("phone"))

        if "age" in data:
            age = _parse_age(data.get("age"))
            if data.get("age") not in (None, "") and age is None:
                return {
                    "error": "invalid_age",
                    "message": "age must be a number between 0 and 130."
                }
            patient.age = age

        if "gender" in data:
            patient.gender = _clean_string(data.get("gender"))

        if "medical_history" in data:
            patient.medical_history = _clean_string(data.get("medical_history")) or ""

        db.commit()
        db.refresh(patient)

        return {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "medical_history": patient.medical_history,
        }

    finally:
        db.close()