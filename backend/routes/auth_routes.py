from flask import Blueprint, request, jsonify, current_app
from backend.services.auth_service import register_user, authenticate_user, get_current_user, update_profile

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    user = register_user(data)
    if 'error' in user:
        return jsonify(user), 400
    return jsonify({'message': 'user_registered', 'user': {'id': user.id, 'email': user.email, 'full_name': user.full_name}}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    token = authenticate_user(data.get('email'), data.get('password'))
    if not token:
        return jsonify({'error': 'invalid_credentials'}), 401
    return jsonify({'access_token': token})


@auth_bp.route('/me', methods=['GET'])
def me():
    auth_header = request.headers.get('Authorization')
    user = get_current_user(auth_header)
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify({'id': user.id, 'email': user.email, 'full_name': user.full_name, 'role': user.role})


@auth_bp.route('/profile', methods=['PUT'])
def profile():
    auth_header = request.headers.get('Authorization')
    user = get_current_user(auth_header)
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    updated = update_profile(user.id, data)
    return jsonify({'message': 'profile_updated', 'user': {'id': updated.id, 'email': updated.email, 'full_name': updated.full_name}})

