from backend.db.database import SessionLocal
from backend.db.models import Department
from backend.services.serializers import serialize_department


def list_departments():
    db = SessionLocal()

    try:
        departments = db.query(Department).order_by(Department.id).all()
        return [serialize_department(department) for department in departments]

    finally:
        db.close()