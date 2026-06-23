from datetime import datetime


ALLOWED_APPOINTMENT_STATUSES = {"scheduled", "cancelled", "completed"}


def clean_string(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value else None


def error_response(error, message, **extra):
    response = {
        "error": error,
        "message": message,
    }

    response.update(extra)
    return response


def parse_positive_int(value, field_name):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, error_response(
            f"invalid_{field_name}",
            f"{field_name} must be a positive integer.",
        )

    if number <= 0:
        return None, error_response(
            f"invalid_{field_name}",
            f"{field_name} must be greater than 0.",
        )

    return number, None


def parse_required_positive_int(data, field_name):
    raw_value = data.get(field_name)

    if raw_value in (None, ""):
        return None, error_response(
            f"{field_name}_required",
            f"{field_name} is required.",
        )

    return parse_positive_int(raw_value, field_name)


def parse_datetime(value, field_name="appointment_datetime", required=True):
    value = clean_string(value)

    if not value:
        if required:
            return None, error_response(
                f"{field_name}_required",
                f"{field_name} is required.",
            )

        return None, None

    try:
        normalized = value.replace("Z", "")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None, error_response(
            f"invalid_{field_name}",
            f"{field_name} must be a valid ISO datetime.",
        )

    return parsed, None


def validate_appointment_status(status):
    status = clean_string(status)

    if status and status not in ALLOWED_APPOINTMENT_STATUSES:
        return None, error_response(
            "invalid_status",
            "status must be one of: scheduled, cancelled, completed.",
        )

    return status, None