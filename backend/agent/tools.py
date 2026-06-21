from datetime import datetime, timedelta

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
    busiest_doctor,
    monthly_appointments,
    department_load,
)


def search_patient(query):
    return list_patients(query, page=1, per=20)


def get_patient_details(patient_id):
    return get_patient(patient_id)


def add_patient(data):
    return create_patient(data)


def list_doctors(specialty=None, department=None):
    return list_doctors_service(specialty)


def doctor_schedule(doctor_id, date_range=None):
    start = None
    end = None

    if date_range == "next week":
        start = (datetime.utcnow() + timedelta(days=7)).isoformat()
        end = (datetime.utcnow() + timedelta(days=14)).isoformat()

    return get_doctor_schedule(doctor_id, start, end)


def available_slots(specialty=None, doctor_id=None, date=None):
    if doctor_id:
        doctors = [
            doctor for doctor in list_doctors_service(specialty)
            if doctor["id"] == int(doctor_id)
        ]
    else:
        doctors = list_doctors_service(specialty) if specialty else list_doctors_service()

    slots = []
    now = datetime.utcnow()

    for doctor in doctors:
        schedule_data = get_doctor_schedule(doctor["id"])

        if not schedule_data or "error" in schedule_data:
            continue

        appointments = schedule_data.get("appointments", [])

        occupied = {
            appointment["datetime"][:13]
            for appointment in appointments
            if appointment.get("status") != "cancelled"
        }

        found_slots = []

        for day_offset in range(1, 8):
            day = now + timedelta(days=day_offset)

            for hour in range(9, 17):
                candidate = day.replace(
                    hour=hour,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

                key = candidate.isoformat()[:13]

                if key not in occupied:
                    found_slots.append(candidate.isoformat())

                if len(found_slots) >= 3:
                    break

            if len(found_slots) >= 3:
                break

        if found_slots:
            slots.append({
                "doctor_id": doctor["id"],
                "doctor_name": doctor["full_name"],
                "specialty": doctor["specialty"],
                "slots": found_slots,
            })

    return slots


def book_appointment(patient_id, doctor_id, dt_iso):
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


def busiest_doctor_tool(start_date=None, end_date=None):
    return busiest_doctor(start_date, end_date)


def monthly_appointments_tool(month=None, year=None):
    return monthly_appointments(month, year)


def department_load_tool():
    return department_load()
