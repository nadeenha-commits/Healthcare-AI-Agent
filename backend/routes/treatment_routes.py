from flask import Blueprint, jsonify, request

from backend.services.appointment_service import (
    get_patient_history,
    add_treatment_service,
)
from backend.utils.auth import login_required

treatment_bp = Blueprint("treatments", __name__)


def _status_code_for_error(error_code):
    if error_code in {"patient_not_found", "doctor_not_found", "not_found"}:
        return 404

    return 400


@treatment_bp.route("/patients/<int:patient_id>/history", methods=["GET"])
@login_required
def patient_history(patient_id):
    result = get_patient_history(patient_id)

    if result is None:
        return jsonify({"error": "not_found"}), 404

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), _status_code_for_error(result["error"])

    return jsonify(result), 200


@treatment_bp.route("/treatments", methods=["POST"])
@login_required
def add_treatment():
    data = request.get_json(silent=True) or {}

    result = add_treatment_service(data)

    if "error" in result:
        return jsonify(result), _status_code_for_error(result["error"])

    return jsonify(result), 201