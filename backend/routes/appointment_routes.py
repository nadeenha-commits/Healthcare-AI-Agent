from flask import Blueprint, jsonify, request

from backend.services.appointment_service import (
    list_appointments,
    create_appointment,
    cancel_appointment_service,
    complete_appointment_service,
)
from backend.utils.auth import login_required

appointment_bp = Blueprint("appointments", __name__)


def _status_code_for_error(error_code):
    if error_code in {"patient_not_found", "doctor_not_found", "not_found"}:
        return 404

    if error_code in {
        "slot_already_booked",
        "patient_already_has_appointment",
        "appointment_already_completed",
        "appointment_cancelled",
    }:
        return 409

    return 400


@appointment_bp.route("", methods=["GET"])
@login_required
def appointments_list():
    result = list_appointments(request.args)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 400

    return jsonify(result), 200


@appointment_bp.route("", methods=["POST"])
@login_required
def appointment_create():
    data = request.get_json(silent=True) or {}

    created = create_appointment(data)

    if "error" in created:
        return jsonify(created), _status_code_for_error(created["error"])

    return jsonify(created), 201


@appointment_bp.route("/<int:appointment_id>/cancel", methods=["PUT"])
@login_required
def appointment_cancel(appointment_id):
    result = cancel_appointment_service(appointment_id)

    if "error" in result:
        return jsonify(result), _status_code_for_error(result["error"])

    return jsonify(result), 200


@appointment_bp.route("/<int:appointment_id>/complete", methods=["PUT"])
@login_required
def appointment_complete(appointment_id):
    result = complete_appointment_service(appointment_id)

    if "error" in result:
        return jsonify(result), _status_code_for_error(result["error"])

    return jsonify(result), 200