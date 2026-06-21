from flask import Blueprint, jsonify, request
from backend.services.analytics_service import busiest_doctor, monthly_appointments, department_load

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/busiest-doctor', methods=['GET'])
def busiest_doctor_route():
    start = request.args.get('start')
    end = request.args.get('end')
    res = busiest_doctor(start, end)
    return jsonify(res)


@analytics_bp.route('/monthly-appointments', methods=['GET'])
def monthly_appointments_route():
    month = int(request.args.get('month')) if request.args.get('month') else None
    year = int(request.args.get('year')) if request.args.get('year') else None
    res = monthly_appointments(month, year)
    return jsonify(res)


@analytics_bp.route('/department-load', methods=['GET'])
def department_load_route():
    res = department_load()
    return jsonify(res)

