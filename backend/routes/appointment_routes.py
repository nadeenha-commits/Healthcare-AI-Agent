from flask import Blueprint, jsonify, request
from backend.services.appointment_service import list_appointments, create_appointment, cancel_appointment_service, complete_appointment_service

appointment_bp = Blueprint('appointments', __name__)


@appointment_bp.route('', methods=['GET'])
def appointments_list():
    args = request.args
    appts = list_appointments(args)
    return jsonify(appts)


@appointment_bp.route('', methods=['POST'])
def appointment_create():
    data = request.json or {}
    created = create_appointment(data)
    if 'error' in created:
        return jsonify(created), 400
    return jsonify(created), 201


@appointment_bp.route('/<int:appointment_id>/cancel', methods=['PUT'])
def appointment_cancel(appointment_id):
    res = cancel_appointment_service(appointment_id)
    if 'error' in res:
        return jsonify(res), 404
    return jsonify(res)


@appointment_bp.route('/<int:appointment_id>/complete', methods=['PUT'])
def appointment_complete(appointment_id):
    res = complete_appointment_service(appointment_id)
    if 'error' in res:
        return jsonify(res), 404
    return jsonify(res)

