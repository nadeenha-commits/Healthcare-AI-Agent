from flask import Blueprint, jsonify, request

from backend.services.patient_service import (
    list_patients,
    get_patient,
    create_patient,
    update_patient,
)
from backend.utils.auth import login_required

patient_bp = Blueprint("patients", __name__)


def _parse_positive_int(value, default, field_name, max_value=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, {
            "error": f"invalid_{field_name}",
            "message": f"{field_name} must be a positive integer."
        }

    if number <= 0:
        return None, {
            "error": f"invalid_{field_name}",
            "message": f"{field_name} must be greater than 0."
        }

    if max_value is not None and number > max_value:
        return None, {
            "error": f"invalid_{field_name}",
            "message": f"{field_name} cannot be greater than {max_value}."
        }

    return number, None


@patient_bp.route("", methods=["GET"])
@login_required
def patients_list():
    q = request.args.get("q")

    page, page_error = _parse_positive_int(
        request.args.get("page", 1),
        1,
        "page",
    )
    if page_error:
        return jsonify(page_error), 400

    per, per_error = _parse_positive_int(
        request.args.get("per", 50),
        50,
        "per",
        max_value=100,
    )
    if per_error:
        return jsonify(per_error), 400

    patients = list_patients(q, page, per)
    return jsonify(patients), 200


@patient_bp.route("/<int:patient_id>", methods=["GET"])
@login_required
def patient_detail(patient_id):
    patient = get_patient(patient_id)

    if not patient:
        return jsonify({"error": "not_found"}), 404

    return jsonify(patient), 200


@patient_bp.route("", methods=["POST"])
@login_required
def patient_create():
    data = request.get_json(silent=True) or {}

    created = create_patient(data)

    if "error" in created:
        return jsonify(created), 400

    return jsonify(created), 201


@patient_bp.route("/<int:patient_id>", methods=["PUT"])
@login_required
def patient_update(patient_id):
    data = request.get_json(silent=True) or {}

    updated = update_patient(patient_id, data)

    if updated is None:
        return jsonify({"error": "not_found"}), 404

    if "error" in updated:
        return jsonify(updated), 400

    return jsonify(updated), 200