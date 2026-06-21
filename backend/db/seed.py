"""Seed script to populate DB with sample data for demo.

This script is idempotent:
- It can be executed more than once.
- It does not duplicate departments, doctors, patients, users, appointments, or treatments.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, func

from backend.db.database import SessionLocal, init_db
from backend.db.models import User, Department, Doctor, Patient, Appointment, Treatment
from backend.utils.security import hash_password


def get_or_create_department(db, name, description):
    department = db.execute(
        select(Department).where(Department.name == name)
    ).scalar_one_or_none()

    if department:
        return department

    department = Department(name=name, description=description)
    db.add(department)
    db.flush()
    return department


def get_or_create_doctor(db, full_name, specialty, department_id):
    doctor = db.execute(
        select(Doctor).where(Doctor.full_name == full_name)
    ).scalar_one_or_none()

    if doctor:
        return doctor

    doctor = Doctor(
        full_name=full_name,
        specialty=specialty,
        department_id=department_id
    )
    db.add(doctor)
    db.flush()
    return doctor


def get_or_create_patient(db, full_name, phone, age, gender, medical_history):
    patient = db.execute(
        select(Patient).where(Patient.phone == phone)
    ).scalar_one_or_none()

    if patient:
        return patient

    patient = Patient(
        full_name=full_name,
        phone=phone,
        age=age,
        gender=gender,
        medical_history=medical_history
    )
    db.add(patient)
    db.flush()
    return patient


def get_or_create_user(db, full_name, email, password, role):
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if user:
        return user

    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role=role
    )
    db.add(user)
    db.flush()
    return user


def seed_departments(db):
    department_data = [
        ("Cardiology", "Heart related"),
        ("Neurology", "Brain and nerves"),
        ("Pediatrics", "Children"),
        ("Oncology", "Cancer care"),
        ("General Medicine", "Primary care"),
    ]

    return [
        get_or_create_department(db, name, description)
        for name, description in department_data
    ]


def seed_doctors(db, departments):
    doctor_data = [
        ("Amit Patel", "Cardiology", departments[0].id),
        ("Lina Chen", "Cardiology", departments[0].id),
        ("Robert Jones", "Neurology", departments[1].id),
        ("Maria Gonzalez", "Pediatrics", departments[2].id),
        ("Wei Zhang", "Oncology", departments[3].id),
        ("Olivia Brown", "General", departments[4].id),
        ("Samuel Lee", "Cardiology", departments[0].id),
        ("Fatima Khan", "General", departments[4].id),
    ]

    return [
        get_or_create_doctor(db, full_name, specialty, department_id)
        for full_name, specialty, department_id in doctor_data
    ]


def seed_patients(db):
    patient_data = [
        ("Sarah Cohen", "555-0101", 34, "F", "No major issues"),
        ("David Levi", "555-0102", 45, "M", "Hypertension"),
        ("John Smith", "555-0103", 29, "M", "Asthma"),
        ("Emily Davis", "555-0104", 52, "F", "Diabetes"),
        ("Michael Brown", "555-0105", 60, "M", "Heart disease"),
        ("Angela White", "555-0106", 39, "F", "None"),
        ("Chris Green", "555-0107", 27, "M", "Allergy"),
        ("Nora Black", "555-0108", 22, "F", "None"),
        ("Liam Moore", "555-0109", 48, "M", "High cholesterol"),
        ("Olga Ivanova", "555-0110", 55, "F", "Arthritis"),
    ]

    return [
        get_or_create_patient(db, full_name, phone, age, gender, medical_history)
        for full_name, phone, age, gender, medical_history in patient_data
    ]


def seed_appointments(db, patients, doctors):
    appointment_count = db.execute(
        select(func.count(Appointment.id))
    ).scalar_one()

    if appointment_count > 0:
        return

    now = datetime.utcnow()

    appointments = []
    for i in range(20):
        appointments.append(
            Appointment(
                patient_id=patients[i % len(patients)].id,
                doctor_id=doctors[i % len(doctors)].id,
                appointment_datetime=now + timedelta(days=(i - 5)),
                status="scheduled"
            )
        )

    db.add_all(appointments)


def seed_treatments(db, patients, doctors):
    treatment_count = db.execute(
        select(func.count(Treatment.id))
    ).scalar_one()

    if treatment_count > 0:
        return

    treatments = []
    for i in range(10):
        treatments.append(
            Treatment(
                patient_id=patients[i % len(patients)].id,
                doctor_id=doctors[i % len(doctors)].id,
                diagnosis="Diagnosis example",
                treatment_plan="Treatment plan example"
            )
        )

    db.add_all(treatments)


def seed_users(db):
    users = [
        ("Admin User", "admin@example.com", "password", "admin"),
        ("Reception", "reception@example.com", "password", "staff"),
    ]

    for full_name, email, password, role in users:
        get_or_create_user(db, full_name, email, password, role)


def seed():
    init_db()
    db = SessionLocal()

    try:
        departments = seed_departments(db)
        doctors = seed_doctors(db, departments)
        patients = seed_patients(db)

        seed_appointments(db, patients, doctors)
        seed_treatments(db, patients, doctors)
        seed_users(db)

        db.commit()
        print("Seed complete")

    except Exception as e:
        db.rollback()
        print("Seed failed:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()