from flask import Blueprint, jsonify, request
from backend.services.appointment_service import get_doctor_schedule, list_doctors_service

doctor_bp = Blueprint('doctors', __name__)


@doctor_bp.route('', methods=['GET'])
def doctors_list():
    specialty = request.args.get('specialty')
    doctors = list_doctors_service(specialty)
    return jsonify(doctors)


@doctor_bp.route('/<int:doctor_id>', methods=['GET'])
def doctor_detail(doctor_id):
    # simple lookup via appointment service that returns doctor info
    doctors = list_doctors_service()
    for d in doctors:
        if d['id'] == doctor_id:
            return jsonify(d)
    return jsonify({'error': 'not_found'}), 404


@doctor_bp.route('/<int:doctor_id>/schedule', methods=['GET'])
def doctor_schedule(doctor_id):
    start = request.args.get('start')
    end = request.args.get('end')
    schedule = get_doctor_schedule(doctor_id, start, end)
    return jsonify(schedule)

