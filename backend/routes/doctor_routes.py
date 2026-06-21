from flask import Blueprint, jsonify, request

from backend.services.appointment_service import (
    get_doctor_schedule,
    list_doctors_service,
)
from backend.utils.auth import login_required

doctor_bp = Blueprint("doctors", __name__)


@doctor_bp.route("", methods=["GET"])
def doctors_list():
    specialty = request.args.get("specialty")
    doctors = list_doctors_service(specialty)
    return jsonify(doctors), 200


@doctor_bp.route("/<int:doctor_id>", methods=["GET"])
def doctor_detail(doctor_id):
    doctors = list_doctors_service()

    for doctor in doctors:
        if doctor["id"] == doctor_id:
            return jsonify(doctor), 200

    return jsonify({"error": "not_found"}), 404


@doctor_bp.route("/<int:doctor_id>/schedule", methods=["GET"])
@login_required
def doctor_schedule(doctor_id):
    start = request.args.get("start")
    end = request.args.get("end")

    schedule = get_doctor_schedule(doctor_id, start, end)

    if isinstance(schedule, dict) and "error" in schedule:
        if schedule["error"] == "doctor_not_found":
            return jsonify(schedule), 404

        return jsonify(schedule), 400

    return jsonify(schedule), 200