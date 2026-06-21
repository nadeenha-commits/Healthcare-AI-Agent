from flask import Blueprint, jsonify, request

from backend.services.analytics_service import (
    busiest_doctor,
    monthly_appointments,
    department_load,
)
from backend.utils.auth import role_required

analytics_bp = Blueprint("analytics", __name__)


def _parse_optional_int(name, min_value=None, max_value=None):
    value = request.args.get(name)

    if value is None or value == "":
        return None, None

    try:
        number = int(value)
    except ValueError:
        return None, {
            "error": f"invalid_{name}",
            "message": f"{name} must be a valid integer."
        }

    if min_value is not None and number < min_value:
        return None, {
            "error": f"invalid_{name}",
            "message": f"{name} must be at least {min_value}."
        }

    if max_value is not None and number > max_value:
        return None, {
            "error": f"invalid_{name}",
            "message": f"{name} must be at most {max_value}."
        }

    return number, None


@analytics_bp.route("/busiest-doctor", methods=["GET"])
@role_required("admin", "staff")
def busiest_doctor_route():
    start = request.args.get("start")
    end = request.args.get("end")

    result = busiest_doctor(start, end)
    return jsonify(result), 200


@analytics_bp.route("/monthly-appointments", methods=["GET"])
@role_required("admin", "staff")
def monthly_appointments_route():
    month, month_error = _parse_optional_int("month", 1, 12)
    if month_error:
        return jsonify(month_error), 400

    year, year_error = _parse_optional_int("year", 2000, 2100)
    if year_error:
        return jsonify(year_error), 400

    if (month is None and year is not None) or (month is not None and year is None):
        return jsonify({
            "error": "month_and_year_required_together",
            "message": "month and year must be provided together."
        }), 400

    result = monthly_appointments(month, year)
    return jsonify(result), 200


@analytics_bp.route("/department-load", methods=["GET"])
@role_required("admin", "staff")
def department_load_route():
    result = department_load()
    return jsonify(result), 200