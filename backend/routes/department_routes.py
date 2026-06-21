from flask import Blueprint, jsonify
from backend.services.appointment_service import list_departments

department_bp = Blueprint('departments', __name__)


@department_bp.route('', methods=['GET'])
def list_depts():
    return jsonify(list_departments())

