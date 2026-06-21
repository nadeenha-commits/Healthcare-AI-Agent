from backend.db.database import SessionLocal
from backend.db.models import User
from backend.utils.security import hash_password, verify_password, create_access_token, decode_access_token


def register_user(data: dict):
    db = SessionLocal()
    try:
        if not data.get('email') or not data.get('password'):
            return {'error': 'email_and_password_required'}
        existing = db.query(User).filter(User.email == data['email']).first()
        if existing:
            return {'error': 'email_in_use'}
        hashed = hash_password(data['password'])
        u = User(full_name=data.get('full_name', ''), email=data['email'], password_hash=hashed, role=data.get('role', 'user'))
        db.add(u)
        db.commit()
        db.refresh(u)
        return u
    finally:
        db.close()


def authenticate_user(email, password):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            return None
        if not verify_password(password, u.password_hash):
            return None
        token = create_access_token({'user_id': u.id, 'email': u.email, 'role': u.role})
        return token
    finally:
        db.close()


def get_current_user(auth_header):
    if not auth_header:
        return None
    token = auth_header.replace('Bearer ', '')
    payload = decode_access_token(token)
    if not payload:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == payload.get('user_id')).first()
    finally:
        db.close()


def update_profile(user_id, data):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user_id).first()
        if not u:
            return None
        if data.get('full_name'):
            u.full_name = data['full_name']
        if data.get('email'):
            u.email = data['email']
        db.commit()
        db.refresh(u)
        return u
    finally:
        db.close()

