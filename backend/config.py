import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db')
SECRET_KEY = os.getenv('SECRET_KEY', 'change_this')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = os.getenv('GEMINI_API_URL')

