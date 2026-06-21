import re


def is_booking_request(message_lower: str) -> bool:
    booking_words = ["book", "schedule", "make", "create", "set up"]
    has_booking_word = any(word in message_lower for word in booking_words)

    has_appointment_context = (
        "appointment" in message_lower
        or "with a" in message_lower
        or "with dr" in message_lower
        or "with doctor" in message_lower
        or "with cardiologist" in message_lower
        or "with neurologist" in message_lower
        or "with pediatrician" in message_lower
        or "with oncologist" in message_lower
    )

    return has_booking_word and has_appointment_context


def extract_first_number(message: str):
    match = re.search(r"\d+", message)
    return int(match.group()) if match else None


def extract_name_from_message(message: str):
    patterns = [
        r"appointment\s+for\s+(.+?)\s+with\s+",
        r"book\s+an\s+appointment\s+for\s+(.+?)\s+with\s+",
        r"schedule\s+an\s+appointment\s+for\s+(.+?)\s+with\s+",
        r"book\s+(.+?)\s+with\s+",
        r"schedule\s+(.+?)\s+with\s+",
        r"for\s+(.+?)\s+with\s+",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            return clean_extracted_value(match.group(1))

    return clean_extracted_value(message)


def extract_specialty_from_message(message: str):
    message_lower = message.lower()

    specialty_map = {
        "cardiologist": "Cardiology",
        "cardiologists": "Cardiology",
        "cardiology": "Cardiology",
        "heart": "Cardiology",

        "neurologist": "Neurology",
        "neurologists": "Neurology",
        "neurology": "Neurology",
        "brain": "Neurology",

        "pediatrician": "Pediatrics",
        "pediatricians": "Pediatrics",
        "pediatrics": "Pediatrics",
        "children": "Pediatrics",
        "child": "Pediatrics",

        "oncologist": "Oncology",
        "oncologists": "Oncology",
        "oncology": "Oncology",
        "cancer": "Oncology",

        "general medicine": "General",
        "general doctor": "General",
        "general physician": "General",
        "general": "General",
    }

    for keyword, specialty in specialty_map.items():
        if keyword in message_lower:
            return specialty

    return None


def extract_date_range_from_message(message: str):
    message_lower = message.lower()

    iso_date_match = re.search(r"\d{4}-\d{2}-\d{2}", message)
    if iso_date_match:
        return iso_date_match.group(0)

    if "next week" in message_lower:
        return "next week"

    if "tomorrow" in message_lower:
        return "tomorrow"

    if "today" in message_lower:
        return "today"

    if "this week" in message_lower:
        return "this week"

    return "next week"


def clean_extracted_value(value):
    if value is None:
        return None

    value = str(value).strip()

    remove_phrases = [
        "book",
        "schedule",
        "make",
        "create",
        "set up",
        "an appointment",
        "appointment",
        "with a cardiologist",
        "with cardiologist",
        "with a neurologist",
        "with neurologist",
        "with a pediatrician",
        "with pediatrician",
        "with an oncologist",
        "with oncologist",
        "with a doctor",
        "with doctor",
        "with dr",
        "next week",
        "this week",
        "tomorrow",
        "today",
    ]

    cleaned = value

    for phrase in remove_phrases:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.strip(" .,:;-")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned if cleaned else None


def extract_patient_history_query(message: str):
    message_lower = message.lower()

    if "patient history for" in message_lower:
        return message.split("for")[-1].strip()

    if "history for" in message_lower:
        return message.split("for")[-1].strip()

    if "patient history" in message_lower:
        original_index = message_lower.find("patient history") + len("patient history")
        return message[original_index:].strip()

    return message.strip()


def choose_patient_match(patients, query):
    if len(patients) == 1:
        return patients[0]

    normalized_query = str(query).strip().lower()

    exact_matches = [
        patient
        for patient in patients
        if str(patient.get("full_name", "")).strip().lower() == normalized_query
    ]

    if len(exact_matches) == 1:
        return exact_matches[0]

    return None