def _isoformat(value):
    return value.isoformat() if value else None


def serialize_doctor(doctor):
    return {
        "id": doctor.id,
        "full_name": doctor.full_name,
        "specialty": doctor.specialty,
        "department_id": doctor.department_id,
        "department_name": doctor.department.name if doctor.department else None,
    }


def serialize_department(department):
    return {
        "id": department.id,
        "name": department.name,
        "description": department.description,
    }


def serialize_appointment(appointment):
    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": appointment.patient.full_name if appointment.patient else None,
        "doctor_id": appointment.doctor_id,
        "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
        "specialty": appointment.doctor.specialty if appointment.doctor else None,
        "appointment_datetime": _isoformat(appointment.appointment_datetime),
        "status": appointment.status,
    }


def serialize_appointment_status(appointment):
    return {
        "id": appointment.id,
        "status": appointment.status,
        "patient_id": appointment.patient_id,
        "patient_name": appointment.patient.full_name if appointment.patient else None,
        "doctor_id": appointment.doctor_id,
        "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
        "appointment_datetime": _isoformat(appointment.appointment_datetime),
    }


def serialize_doctor_schedule(doctor, appointments):
    return {
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "specialty": doctor.specialty,
        },
        "appointments": [
            {
                "id": appointment.id,
                "patient_id": appointment.patient_id,
                "patient_name": appointment.patient.full_name if appointment.patient else None,
                "datetime": _isoformat(appointment.appointment_datetime),
                "status": appointment.status,
            }
            for appointment in appointments
        ],
    }


def serialize_treatment(treatment, patient=None, doctor=None):
    patient = patient or treatment.patient
    doctor = doctor or treatment.doctor

    return {
        "id": treatment.id,
        "patient_id": treatment.patient_id,
        "patient_name": patient.full_name if patient else None,
        "doctor_id": treatment.doctor_id,
        "doctor_name": doctor.full_name if doctor else None,
        "diagnosis": treatment.diagnosis,
        "plan": treatment.treatment_plan,
    }


def serialize_patient_history(patient):
    appointments = [
        {
            "id": appointment.id,
            "datetime": _isoformat(appointment.appointment_datetime),
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
            "specialty": appointment.doctor.specialty if appointment.doctor else None,
            "status": appointment.status,
        }
        for appointment in sorted(
            patient.appointments,
            key=lambda item: item.appointment_datetime,
        )
    ]

    treatments = [
        {
            "id": treatment.id,
            "doctor_id": treatment.doctor_id,
            "doctor_name": treatment.doctor.full_name if treatment.doctor else None,
            "diagnosis": treatment.diagnosis,
            "plan": treatment.treatment_plan,
        }
        for treatment in sorted(
            patient.treatments,
            key=lambda item: item.created_at,
        )
    ]

    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "medical_history": patient.medical_history,
        },
        "appointments": appointments,
        "treatments": treatments,
    }