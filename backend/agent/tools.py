from datetime import datetime, timedelta, time

from backend.services.patient_service import (
    list_patients,
    get_patient,
    create_patient,
)

from backend.services.appointment_service import (
    list_doctors_service,
    get_doctor_schedule,
    create_appointment,
    get_patient_history,
    add_treatment_service,
    cancel_appointment_service,
    list_departments,
)

from backend.services.analytics_service import (
    busiest_doctor as busiest_doctor_service,
    monthly_appointments as monthly_appointments_service,
    department_load as department_load_service,
)


def search_patient(query):
    return list_patients(query, page=1, per=20)


def get_patient_details(patient_id):
    return get_patient(patient_id)


def add_patient(data):
    return create_patient(data)


def list_doctors(specialty=None, department=None):
    return list_doctors_service(specialty)


def _parse_date_window(date_value=None):
    """
    Converts natural date expressions into a start/end datetime window.

    Supported values:
    - today
    - tomorrow
    - this week
    - next week
    - YYYY-MM-DD
    - None/default: next 7 days
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    def window_from_days(start_days, duration_days, start_now=False):
        start = now if start_now else today_start + timedelta(days=start_days)
        end = today_start + timedelta(days=start_days + duration_days)
        return start, end

    if not date_value:
        return window_from_days(0, 8, start_now=True)

    value = str(date_value).strip().lower()

    date_windows = {
        "today": lambda: window_from_days(0, 1, start_now=True),
        "tomorrow": lambda: window_from_days(1, 1),
        "this week": lambda: window_from_days(0, 7, start_now=True),
        "next week": lambda: window_from_days(7, 7),
    }

    if value in date_windows:
        return date_windows[value]()

    try:
        exact_day = datetime.strptime(value, "%Y-%m-%d")
        start = exact_day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return start, end
    except ValueError:
        return window_from_days(0, 8, start_now=True)


def doctor_schedule(doctor_id, date_range=None):
    start = None
    end = None

    if date_range:
        start_dt, end_dt = _parse_date_window(date_range)
        start = start_dt.isoformat()
        end = end_dt.isoformat()

    return get_doctor_schedule(doctor_id, start, end)


def _get_doctors_for_slots(specialty=None, doctor_id=None):
    try:
        doctor_id = int(doctor_id) if doctor_id is not None else None
    except (TypeError, ValueError):
        return []

    doctors = list_doctors_service(specialty) if specialty else list_doctors_service()

    if doctor_id is None:
        return doctors

    return [
        doctor
        for doctor in doctors
        if int(doctor.get("id")) == doctor_id
    ]


def _appointment_hour_key(appointment):
    appointment_datetime = (
        appointment.get("datetime")
        or appointment.get("appointment_datetime")
    )

    if not appointment_datetime:
        return None

    return str(appointment_datetime)[:13]


def available_slots(specialty=None, doctor_id=None, date=None):
    """
    Finds available appointment slots according to the requested date window.
    This function is used by the Agent booking flow.
    """
    doctors = _get_doctors_for_slots(
        specialty=specialty,
        doctor_id=doctor_id,
    )

    slots = []
    now = datetime.utcnow()
    start_dt, end_dt = _parse_date_window(date)

    for doctor in doctors:
        schedule_data = get_doctor_schedule(
            doctor["id"],
            start_dt.isoformat(),
            end_dt.isoformat(),
        )

        if not schedule_data or "error" in schedule_data:
            continue

        appointments = schedule_data.get("appointments", [])

        occupied = {
            hour_key
            for hour_key in (
                _appointment_hour_key(appointment)
                for appointment in appointments
                if appointment.get("status") != "cancelled"
            )
            if hour_key
        }

        found_slots = []

        current_day = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        last_day = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        while current_day < last_day:
            for hour in range(9, 17):
                candidate = datetime.combine(
                    current_day.date(),
                    time(hour=hour, minute=0),
                )

                if candidate <= now:
                    continue

                if candidate < start_dt or candidate >= end_dt:
                    continue

                key = candidate.isoformat()[:13]

                if key not in occupied:
                    found_slots.append(candidate.isoformat())

                if len(found_slots) >= 3:
                    break

            if len(found_slots) >= 3:
                break

            current_day += timedelta(days=1)

        if found_slots:
            slots.append({
                "doctor_id": doctor["id"],
                "doctor_name": doctor["full_name"],
                "specialty": doctor["specialty"],
                "slots": found_slots,
            })

    return slots


def book_appointment(patient_id, doctor_id, dt_iso):
    """
    Creates an appointment through appointment_service.
    Duplicate prevention should be handled inside create_appointment(),
    because only the service has direct DB access.
    """
    return create_appointment({
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_datetime": dt_iso,
    })


def cancel_appointment(appointment_id):
    return cancel_appointment_service(appointment_id)


def patient_history(patient_id):
    return get_patient_history(patient_id)


def add_treatment(patient_id, doctor_id, diagnosis, treatment_plan):
    return add_treatment_service({
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "diagnosis": diagnosis,
        "treatment_plan": treatment_plan,
    })


def busiest_doctor(start_date=None, end_date=None):
    return busiest_doctor_service(start_date, end_date)


def monthly_appointments(month=None, year=None):
    return monthly_appointments_service(month, year)


def department_load_tool():
    return department_load_service()