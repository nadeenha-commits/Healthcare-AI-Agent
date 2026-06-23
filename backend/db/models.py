from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "role IN ('user', 'staff', 'admin')",
            name="ck_users_role_valid",
        ),
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
    )


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)

    doctors = relationship("Doctor", back_populates="department")

    __table_args__ = (
        UniqueConstraint("name", name="uq_departments_name"),
        Index("ix_departments_name", "name"),
    )


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    specialty = Column(String(128), nullable=False)
    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
    )

    department = relationship("Department", back_populates="doctors")
    appointments = relationship("Appointment", back_populates="doctor")
    treatments = relationship("Treatment", back_populates="doctor")

    __table_args__ = (
        Index("ix_doctors_specialty", "specialty"),
        Index("ix_doctors_department_id", "department_id"),
        Index("ix_doctors_full_name", "full_name"),
    )


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    phone = Column(String(32))
    age = Column(Integer)
    gender = Column(String(16))
    medical_history = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient")
    treatments = relationship("Treatment", back_populates="patient")

    __table_args__ = (
        UniqueConstraint("phone", name="uq_patients_phone"),
        CheckConstraint(
            "age IS NULL OR age >= 0",
            name="ck_patients_age_non_negative",
        ),
        CheckConstraint(
            "gender IS NULL OR gender IN ('M', 'F', 'Other')",
            name="ck_patients_gender_valid",
        ),
        Index("ix_patients_full_name", "full_name"),
        Index("ix_patients_phone", "phone"),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
    )
    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False,
    )
    appointment_datetime = Column(DateTime, nullable=False)
    status = Column(String(32), nullable=False, default="scheduled")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'cancelled', 'completed')",
            name="ck_appointments_status_valid",
        ),

        # Speeds up doctor schedule queries.
        Index(
            "ix_appointments_doctor_datetime",
            "doctor_id",
            "appointment_datetime",
        ),

        # Speeds up patient history queries.
        Index(
            "ix_appointments_patient_datetime",
            "patient_id",
            "appointment_datetime",
        ),

        # Speeds up monthly analytics and availability checks.
        Index("ix_appointments_datetime", "appointment_datetime"),
        Index("ix_appointments_status", "status"),

        # Prevents double-booking the same active doctor slot.
        # Cancelled appointments do not block the slot.
        Index(
            "uq_active_doctor_slot",
            "doctor_id",
            "appointment_datetime",
            unique=True,
            postgresql_where=text("status <> 'cancelled'"),
        ),

        # Prevents a patient from having two active appointments at the same time.
        # Cancelled appointments do not block the patient from booking again.
        Index(
            "uq_active_patient_slot",
            "patient_id",
            "appointment_datetime",
            unique=True,
            postgresql_where=text("status <> 'cancelled'"),
        ),
    )


class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
    )
    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False,
    )
    diagnosis = Column(Text, nullable=False)
    treatment_plan = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="treatments")
    doctor = relationship("Doctor", back_populates="treatments")

    __table_args__ = (
        Index("ix_treatments_patient_id", "patient_id"),
        Index("ix_treatments_doctor_id", "doctor_id"),
        Index("ix_treatments_created_at", "created_at"),
    )