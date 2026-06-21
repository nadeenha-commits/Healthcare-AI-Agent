from flask import Blueprint, jsonify, request
from backend.services.appointment_service import (
    get_patient_history,
    add_treatment_service
)

treatment_bp = Blueprint("treatments", __name__)


# Correct final route:
# GET /patients/<patient_id>/history
@treatment_bp.route("/patients/<int:patient_id>/history", methods=["GET"])
def patient_history(patient_id):
    res = get_patient_history(patient_id)

    if res is None:
        return jsonify({"error": "not_found"}), 404

    return jsonify(res), 200


# Correct final route:
# POST /treatments
@treatment_bp.route("/treatments", methods=["POST"])
def add_treatment():
    data = request.get_json(silent=True) or {}

    res = add_treatment_service(data)

    if "error" in res:
        return jsonify(res), 400

    return jsonify(res), 201