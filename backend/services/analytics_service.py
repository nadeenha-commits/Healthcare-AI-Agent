from datetime import datetime

from sqlalchemy import and_, func

from backend.db.database import SessionLocal
from backend.db.models import Appointment, Department, Doctor


def _parse_datetime(value, field_name):
    if value in (None, ""):
        return None, None

    try:
        return datetime.fromisoformat(str(value).replace("Z", "")), None
    except ValueError:
        return None, {
            "error": f"invalid_{field_name}",
            "message": f"{field_name} must be a valid ISO datetime.",
        }


def _parse_month_year(month, year):
    now = datetime.utcnow()

    try:
        month = int(month) if month not in (None, "") else now.month
        year = int(year) if year not in (None, "") else now.year
    except (TypeError, ValueError):
        return None, None, {
            "error": "invalid_month_or_year",
            "message": "month and year must be valid numbers.",
        }

    if not 1 <= month <= 12:
        return None, None, {
            "error": "invalid_month",
            "message": "month must be between 1 and 12.",
        }

    return month, year, None


def busiest_doctor(start=None, end=None):
    start_dt, start_error = _parse_datetime(start, "start")
    if start_error:
        return start_error

    end_dt, end_error = _parse_datetime(end, "end")
    if end_error:
        return end_error

    if start_dt and end_dt and start_dt > end_dt:
        return {
            "error": "invalid_date_range",
            "message": "start must be before end.",
        }

    db = SessionLocal()

    try:
        query = (
            db.query(
                Doctor.full_name.label("doctor_name"),
                func.count(Appointment.id).label("appointment_count"),
            )
            .join(Appointment, Appointment.doctor_id == Doctor.id)
            .filter(Appointment.status != "cancelled")
        )

        if start_dt:
            query = query.filter(Appointment.appointment_datetime >= start_dt)

        if end_dt:
            query = query.filter(Appointment.appointment_datetime <= end_dt)

        row = (
            query
            .group_by(Doctor.id, Doctor.full_name)
            .order_by(func.count(Appointment.id).desc())
            .first()
        )

        if not row:
            return {
                "doctor": None,
                "appointments": 0,
                "message": "no_data",
            }

        return {
            "doctor": row.doctor_name,
            "appointments": int(row.appointment_count),
        }

    finally:
        db.close()


def monthly_appointments(month=None, year=None):
    month, year, error = _parse_month_year(month, year)

    if error:
        return error

    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

    db = SessionLocal()

    try:
        count = (
            db.query(Appointment)
            .filter(
                Appointment.appointment_datetime >= start,
                Appointment.appointment_datetime < end,
                Appointment.status != "cancelled",
            )
            .count()
        )

        return {
            "month": month,
            "year": year,
            "appointments": int(count),
        }

    finally:
        db.close()


def department_load():
    db = SessionLocal()

    try:
        rows = (
            db.query(
                Department.name.label("department_name"),
                func.count(Appointment.id).label("appointment_count"),
            )
            .outerjoin(Doctor, Doctor.department_id == Department.id)
            .outerjoin(
                Appointment,
                and_(
                    Appointment.doctor_id == Doctor.id,
                    Appointment.status != "cancelled",
                ),
            )
            .group_by(Department.id, Department.name)
            .order_by(Department.id)
            .all()
        )

        return [
            {
                "department": row.department_name,
                "appointments": int(row.appointment_count),
            }
            for row in rows
        ]

    finally:
        db.close()