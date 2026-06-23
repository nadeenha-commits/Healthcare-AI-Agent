import re
from datetime import datetime


MONTH_NAMES = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


SPECIALTY_MAP = {
    "cardiologist": "Cardiology",
    "cardiologists": "Cardiology",
    "cardiology": "Cardiology",
    "heart": "Cardiology",
    "heart doctor": "Cardiology",

    "neurologist": "Neurology",
    "neurologists": "Neurology",
    "neurology": "Neurology",
    "brain": "Neurology",
    "brain doctor": "Neurology",

    "pediatrician": "Pediatrics",
    "pediatricians": "Pediatrics",
    "pediatrics": "Pediatrics",
    "children": "Pediatrics",
    "child": "Pediatrics",
    "child doctor": "Pediatrics",

    "oncologist": "Oncology",
    "oncologists": "Oncology",
    "oncology": "Oncology",
    "cancer": "Oncology",
    "cancer doctor": "Oncology",

    "general medicine": "General",
    "general doctor": "General",
    "general physician": "General",
    "family doctor": "General",
    "general": "General",
}


def is_booking_request(message_lower: str) -> bool:
    text = str(message_lower or "").lower()

    booking_words = [
        "book",
        "schedule",
        "make",
        "create",
        "set up",
        "reserve",
    ]

    has_booking_word = any(word in text for word in booking_words)

    has_appointment_context = (
        "appointment" in text
        or "slot" in text
        or "visit" in text
        or "with a" in text
        or "with an" in text
        or "with dr" in text
        or "with doctor" in text
        or any(keyword in text for keyword in SPECIALTY_MAP.keys())
    )

    return has_booking_word and has_appointment_context


def extract_first_number(message: str):
    match = re.search(r"\d+", str(message or ""))
    return int(match.group()) if match else None


def extract_name_from_message(message: str):
    text = str(message or "").strip()

    patterns = [
        r"appointment\s+for\s+(.+?)\s+with\s+",
        r"book\s+an\s+appointment\s+for\s+(.+?)\s+with\s+",
        r"schedule\s+an\s+appointment\s+for\s+(.+?)\s+with\s+",
        r"make\s+an\s+appointment\s+for\s+(.+?)\s+with\s+",
        r"create\s+an\s+appointment\s+for\s+(.+?)\s+with\s+",
        r"book\s+(.+?)\s+with\s+",
        r"schedule\s+(.+?)\s+with\s+",
        r"reserve\s+(.+?)\s+with\s+",
        r"for\s+(.+?)\s+with\s+",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_extracted_value(match.group(1))

    return clean_extracted_value(text)


def extract_specialty_from_message(message: str):
    text = str(message or "").lower()

    for keyword, specialty in sorted(
        SPECIALTY_MAP.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if keyword in text:
            return specialty

    return None


def extract_date_range_from_message(message: str, default="next week"):
    text = str(message or "")
    text_lower = text.lower()

    iso_date_match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if iso_date_match:
        return iso_date_match.group(0)

    if "next week" in text_lower:
        return "next week"

    if "this week" in text_lower:
        return "this week"

    if "tomorrow" in text_lower:
        return "tomorrow"

    if "today" in text_lower:
        return "today"

    return default


def extract_month_year_from_message(message: str):
    text = str(message or "").lower()
    now = datetime.utcnow()

    if "this month" in text:
        return now.month, now.year

    month = None
    year = None

    for name, number in MONTH_NAMES.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            month = number
            break

    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    if year_match:
        year = int(year_match.group(1))

    if month and not year:
        year = now.year

    return month, year


def clean_extracted_value(value):
    if value is None:
        return None

    cleaned = str(value).strip()

    remove_phrases = [
        "book",
        "schedule",
        "make",
        "create",
        "set up",
        "reserve",
        "an appointment",
        "appointment",
        "a visit",
        "visit",
        "with a cardiologist",
        "with cardiologist",
        "with a neurologist",
        "with neurologist",
        "with a pediatrician",
        "with pediatrician",
        "with an oncologist",
        "with oncologist",
        "with a general doctor",
        "with general doctor",
        "with a doctor",
        "with doctor",
        "with dr",
        "next week",
        "this week",
        "tomorrow",
        "today",
    ]

    for phrase in remove_phrases:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.strip(" .,:;-")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned if cleaned else None


def extract_patient_history_query(message: str):
    text = str(message or "")
    text_lower = text.lower()

    patterns = [
        r"patient\s+history\s+for\s+(.+)$",
        r"history\s+for\s+(.+)$",
        r"show\s+history\s+of\s+(.+)$",
        r"medical\s+history\s+for\s+(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_extracted_value(match.group(1))

    if "patient history" in text_lower:
        original_index = text_lower.find("patient history") + len("patient history")
        return clean_extracted_value(text[original_index:]) or text.strip()

    return clean_extracted_value(text) or text.strip()


def choose_patient_match(patients, query):
    if len(patients) == 1:
        return patients[0]

    normalized_query = str(query or "").strip().lower()

    exact_matches = [
        patient
        for patient in patients
        if str(patient.get("full_name", "")).strip().lower() == normalized_query
    ]

    if len(exact_matches) == 1:
        return exact_matches[0]

    return None