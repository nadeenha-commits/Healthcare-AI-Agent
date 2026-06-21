from backend.db.database import SessionLocal
from backend.db.models import User
from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def _clean_string(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value else None


def register_user(data: dict):
    full_name = _clean_string(data.get("full_name")) or "New User"
    email = _clean_string(data.get("email"))
    password = data.get("password")

    if not email or not password:
        return {
            "error": "email_and_password_required",
            "message": "email and password are required."
        }

    if len(str(password)) < 6:
        return {
            "error": "password_too_short",
            "message": "password must contain at least 6 characters."
        }

    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            return {
                "error": "email_in_use",
                "message": "This email is already registered."
            }

        hashed = hash_password(password)

        # Security rule:
        # Public registration must always create a normal user.
        # Admin/staff users should only come from seed data or protected admin logic.
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hashed,
            role="user",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    finally:
        db.close()


def authenticate_user(email, password):
    email = _clean_string(email)

    if not email or not password:
        return None

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        })

        return token

    finally:
        db.close()


def get_current_user(auth_header):
    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "", 1).strip()

    if not token:
        return None

    payload = decode_access_token(token)

    if not payload:
        return None

    db = SessionLocal()

    try:
        return db.query(User).filter(User.id == payload.get("user_id")).first()

    finally:
        db.close()


def update_profile(user_id, data):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return None

        if "full_name" in data:
            full_name = _clean_string(data.get("full_name"))

            if not full_name:
                return {
                    "error": "invalid_full_name",
                    "message": "full_name cannot be empty."
                }

            user.full_name = full_name

        if "email" in data:
            email = _clean_string(data.get("email"))

            if not email:
                return {
                    "error": "invalid_email",
                    "message": "email cannot be empty."
                }

            existing = (
                db.query(User)
                .filter(User.email == email, User.id != user_id)
                .first()
            )

            if existing:
                return {
                    "error": "email_in_use",
                    "message": "This email is already used by another user."
                }

            user.email = email

        db.commit()
        db.refresh(user)

        return user

    finally:
        db.close()