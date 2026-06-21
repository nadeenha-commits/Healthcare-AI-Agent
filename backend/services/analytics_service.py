from backend.db.database import SessionLocal
from backend.db.models import Appointment, Doctor
from sqlalchemy import func
from datetime import datetime
from sqlalchemy import text

def busiest_doctor(start=None, end=None):
    db = SessionLocal()
    try:
        qry = db.query(Doctor.full_name, func.count(Appointment.id).label('count')).join(Appointment, Appointment.doctor_id == Doctor.id)
        if start:
            try:
                s = datetime.fromisoformat(start)
                qry = qry.filter(Appointment.appointment_datetime >= s)
            except Exception:
                pass
        if end:
            try:
                e = datetime.fromisoformat(end)
                qry = qry.filter(Appointment.appointment_datetime <= e)
            except Exception:
                pass
        qry = qry.group_by(Doctor.id).order_by(func.count(Appointment.id).desc()).limit(1)
        row = qry.first()
        if not row:
            return {'message': 'no_data'}
        return {'doctor': row[0], 'appointments': row[1]}
    finally:
        db.close()


def monthly_appointments(month=None, year=None):
    db = SessionLocal()
    try:
        if not month or not year:
            now = datetime.utcnow()
            month = now.month
            year = now.year
        start = datetime(year, month, 1)
        # naive end: next month start
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        count = db.query(Appointment).filter(Appointment.appointment_datetime >= start, Appointment.appointment_datetime < end).count()
        return {'month': month, 'year': year, 'appointments': count}
    finally:
        db.close()


def department_load():
    db = SessionLocal()
    try:
        # count appointments per department
        res = db.execute(text("""

            SELECT d.name, count(a.id) as appts
            FROM departments d
            LEFT JOIN doctors doc on doc.department_id = d.id
            LEFT JOIN appointments a on a.doctor_id = doc.id
            GROUP BY d.id
        """))
        return [{'department': r[0], 'appointments': int(r[1])} for r in res]
    finally:
        db.close()

