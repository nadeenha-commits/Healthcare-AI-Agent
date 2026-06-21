"""Seed script to populate DB with sample data for demo."""
from datetime import datetime, timedelta
from backend.db.database import SessionLocal, init_db
from backend.db.models import User, Department, Doctor, Patient, Appointment, Treatment
from backend.utils.security import hash_password


def seed():
    init_db()
    db = SessionLocal()
    try:
        # Add departments
        depts = [
            Department(name='Cardiology', description='Heart related'),
            Department(name='Neurology', description='Brain and nerves'),
            Department(name='Pediatrics', description='Children'),
            Department(name='Oncology', description='Cancer care'),
            Department(name='General Medicine', description='Primary care')
        ]
        db.add_all(depts)
        db.flush()

        # Add doctors
        doctors = [
            Doctor(full_name='Amit Patel', specialty='Cardiology', department_id=depts[0].id),
            Doctor(full_name='Lina Chen', specialty='Cardiology', department_id=depts[0].id),
            Doctor(full_name='Robert Jones', specialty='Neurology', department_id=depts[1].id),
            Doctor(full_name='Maria Gonzalez', specialty='Pediatrics', department_id=depts[2].id),
            Doctor(full_name='Wei Zhang', specialty='Oncology', department_id=depts[3].id),
            Doctor(full_name='Olivia Brown', specialty='General', department_id=depts[4].id),
            Doctor(full_name='Samuel Lee', specialty='Cardiology', department_id=depts[0].id),
            Doctor(full_name='Fatima Khan', specialty='General', department_id=depts[4].id),
        ]
        db.add_all(doctors)
        db.flush()

        # Add patients
        patients = [
            Patient(full_name='Sarah Cohen', phone='555-0101', age=34, gender='F', medical_history='No major issues'),
            Patient(full_name='David Levi', phone='555-0102', age=45, gender='M', medical_history='Hypertension'),
            Patient(full_name='John Smith', phone='555-0103', age=29, gender='M', medical_history='Asthma'),
            Patient(full_name='Emily Davis', phone='555-0104', age=52, gender='F', medical_history='Diabetes'),
            Patient(full_name='Michael Brown', phone='555-0105', age=60, gender='M', medical_history='Heart disease'),
            Patient(full_name='Angela White', phone='555-0106', age=39, gender='F', medical_history='None'),
            Patient(full_name='Chris Green', phone='555-0107', age=27, gender='M', medical_history='Allergy'),
            Patient(full_name='Nora Black', phone='555-0108', age=22, gender='F', medical_history='None'),
            Patient(full_name='Liam Moore', phone='555-0109', age=48, gender='M', medical_history='High cholesterol'),
            Patient(full_name='Olga Ivanova', phone='555-0110', age=55, gender='F', medical_history='Arthritis'),
        ]
        db.add_all(patients)
        db.flush()

        # Add appointments (20)
        now = datetime.utcnow()
        appts = []
        for i in range(20):
            appts.append(Appointment(
                patient_id=patients[i % len(patients)].id,
                doctor_id=doctors[i % len(doctors)].id,
                appointment_datetime=now + timedelta(days=(i - 5)),
                status='scheduled'
            ))
        db.add_all(appts)

        # Add treatments (10)
        treatments = []
        for i in range(10):
            treatments.append(Treatment(
                patient_id=patients[i % len(patients)].id,
                doctor_id=doctors[i % len(doctors)].id,
                diagnosis='Diagnosis example',
                treatment_plan='Treatment plan example'
            ))
        db.add_all(treatments)

        # Add two users
        users = [
            User(full_name='Admin User', email='admin@example.com', password_hash=hash_password('password'), role='admin'),
            User(full_name='Reception', email='reception@example.com', password_hash=hash_password('password'), role='staff')
        ]
        db.add_all(users)

        db.commit()
        print('Seed complete')
    except Exception as e:
        db.rollback()
        print('Seed failed:', e)
    finally:
        db.close()


if __name__ == '__main__':
    seed()


