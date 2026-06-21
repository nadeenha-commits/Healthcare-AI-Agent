from flask import Blueprint, jsonify, request
from backend.services.patient_service import list_patients, get_patient, create_patient, update_patient

patient_bp = Blueprint('patients', __name__)


@patient_bp.route('', methods=['GET'])
def patients_list():
    q = request.args.get('q')
    page = int(request.args.get('page', 1))
    per = int(request.args.get('per', 50))
    patients = list_patients(q, page, per)
    return jsonify([p for p in patients])


@patient_bp.route('/<int:patient_id>', methods=['GET'])
def patient_detail(patient_id):
    p = get_patient(patient_id)
    if not p:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(p)


@patient_bp.route('', methods=['POST'])
def patient_create():
    data = request.json or {}
    created = create_patient(data)
    return jsonify(created), 201


@patient_bp.route('/<int:patient_id>', methods=['PUT'])
def patient_update(patient_id):
    data = request.json or {}
    updated = update_patient(patient_id, data)
    if not updated:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(updated)

