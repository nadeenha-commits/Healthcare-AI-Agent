from backend.db.database import SessionLocal
from backend.db.models import Patient


def list_patients(q=None, page=1, per=50):
    db = SessionLocal()
    try:
        qry = db.query(Patient)
        if q:
            qlike = f"%{q}%"
            qry = qry.filter((Patient.full_name.ilike(qlike)) | (Patient.phone.ilike(qlike)))
        patients = qry.offset((page - 1) * per).limit(per).all()
        result = []
        for p in patients:
            result.append({'id': p.id, 'full_name': p.full_name, 'phone': p.phone, 'age': p.age, 'gender': p.gender})
        return result
    finally:
        db.close()


def get_patient(patient_id):
    db = SessionLocal()
    try:
        p = db.query(Patient).filter(Patient.id == patient_id).first()
        if not p:
            return None
        return {'id': p.id, 'full_name': p.full_name, 'phone': p.phone, 'age': p.age, 'gender': p.gender, 'medical_history': p.medical_history}
    finally:
        db.close()


def create_patient(data):
    db = SessionLocal()
    try:
        p = Patient(full_name=data.get('full_name'), phone=data.get('phone'), age=data.get('age'), gender=data.get('gender'), medical_history=data.get('medical_history', ''))
        db.add(p)
        db.commit()
        db.refresh(p)
        return {'id': p.id, 'full_name': p.full_name}
    finally:
        db.close()


def update_patient(patient_id, data):
    db = SessionLocal()
    try:
        p = db.query(Patient).filter(Patient.id == patient_id).first()
        if not p:
            return None
        for field in ('full_name', 'phone', 'age', 'gender', 'medical_history'):
            if data.get(field) is not None:
                setattr(p, field, data.get(field))
        db.commit()
        db.refresh(p)
        return {'id': p.id, 'full_name': p.full_name, 'phone': p.phone}
    finally:
        db.close()

