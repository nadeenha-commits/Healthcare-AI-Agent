from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(50), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text)
    doctors = relationship('Doctor', back_populates='department')


class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    specialty = Column(String(128), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'))
    department = relationship('Department', back_populates='doctors')
    appointments = relationship('Appointment', back_populates='doctor')


class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    phone = Column(String(32))
    age = Column(Integer)
    gender = Column(String(16))
    medical_history = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    appointments = relationship('Appointment', back_populates='patient')
    treatments = relationship('Treatment', back_populates='patient')


class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    appointment_datetime = Column(DateTime, nullable=False)
    status = Column(String(32), default='scheduled')
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship('Patient', back_populates='appointments')
    doctor = relationship('Doctor', back_populates='appointments')


class Treatment(Base):
    __tablename__ = 'treatments'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship('Patient', back_populates='treatments')
    doctor = relationship('Doctor')

