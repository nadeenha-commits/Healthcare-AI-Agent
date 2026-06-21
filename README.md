# Healthcare AI Agent

A university final project for the course "AI Agents in Python". A clinic/hospital management system with an AI-powered chat interface that can answer questions from the database and perform actions like booking appointments, searching patients, and providing analytics.

## 🏥 Project Overview

**User Flow:** React/Chat UI → Flask API → AI Agent → Function Tools → PostgreSQL → Final Response

The system demonstrates:
- AI Agent architecture with multi-step tool calling
- Function tools that interact with a PostgreSQL database
- RESTful API with Flask
- React + TypeScript frontend with real-time chat
- Authentication with JWT and bcrypt
- Comprehensive analytics and reporting

## 🔧 Technology Stack

### Backend
- **Framework:** Flask (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **LLM:** Gemini Free API (with mock mode for development)
- **Auth:** JWT + bcrypt (passlib)
- **Server:** Gunicorn

### Frontend
- **Framework:** React 18
- **Language:** TypeScript
- **Styling:** CSS3 with gradient designs
- **HTTP:** Fetch API

### DevOps
- **Containerization:** Docker
- **Orchestration:** Docker Compose

## 📊 Database Schema

### Tables
1. **users** - User accounts with authentication
   - id, full_name, email, password_hash, role, created_at

2. **departments** - Medical departments
   - id, name, description

3. **doctors** - Doctor information
   - id, full_name, specialty, department_id (FK → departments.id)

4. **patients** - Patient records
   - id, full_name, phone, age, gender, medical_history, created_at

5. **appointments** - Appointment bookings
   - id, patient_id (FK → patients.id), doctor_id (FK → doctors.id), appointment_datetime, status, created_at

6. **treatments** - Treatment records
   - id, patient_id (FK → patients.id), doctor_id (FK → doctors.id), diagnosis, treatment_plan, created_at

### Entity Relationship Diagram
```
Departments
    ↓ (one-to-many)
Doctors ←─────── Appointments ───────→ Patients
                      ↓
                 Treatments
```

## 🚀 Quick Start

### With Docker Compose (Recommended)
```bash
cd C:\Users\nadeenha\PycharmProjects\Healthcare-AI-Agent

# Copy environment file
copy .env.example .env

# Start all services
docker compose up --build

# In a new terminal, seed the database
docker compose exec backend python -m backend.db.seed

# Access the application
# Backend: http://localhost:8000
# Chat UI: http://localhost:8000/
```

### Local Development

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Seed database
python -m backend.db.seed

# Run server
cd ..
python main.py
```

#### Frontend (Optional)
```bash
cd frontend

# Install dependencies
npm install

# Create .env
copy .env.example .env

# Start development server
npm start
# Opens at http://localhost:3000
```

## 📋 API Endpoints (23 Total)

### Authentication (4 endpoints)
```
POST   /auth/register              - Register new user
POST   /auth/login                 - Login user (returns JWT)
GET    /auth/me                    - Get current user info
PUT    /auth/profile               - Update user profile
```

### Patients (4 endpoints)
```
GET    /patients                   - List all patients (with search)
GET    /patients/<id>              - Get patient details
POST   /patients                   - Create new patient
PUT    /patients/<id>              - Update patient info
```

### Doctors (3 endpoints)
```
GET    /doctors                    - List doctors (with specialty filter)
GET    /doctors/<id>               - Get doctor details
GET    /doctors/<id>/schedule      - Get doctor's appointment schedule
```

### Departments (1 endpoint)
```
GET    /departments                - List all departments
```

### Appointments (4 endpoints)
```
GET    /appointments               - List appointments (with filters)
POST   /appointments               - Book new appointment
PUT    /appointments/<id>/cancel   - Cancel appointment
PUT    /appointments/<id>/complete - Mark appointment as completed
```

### Treatments (2 endpoints)
```
GET    /patients/<id>/history      - Get patient's complete history
POST   /treatments                 - Add treatment record
```

### Analytics (3 endpoints)
```
GET    /analytics/busiest-doctor           - Find busiest doctor (time period)
GET    /analytics/monthly-appointments     - Count appointments for month
GET    /analytics/department-load          - Appointments per department
```

### Agent Chat (2 endpoints)
```
POST   /agent/chat                 - Send message to AI agent
GET    /agent/history              - Get conversation history
```

## 🤖 AI Agent Tools (13 Tools)

The AI Agent can call these tools to interact with the database:

1. **search_patient(query)** - Search patients by name or phone
2. **get_patient_details(patient_id)** - Get full patient information
3. **add_patient(data)** - Create new patient record
4. **list_doctors(specialty, department)** - List doctors with optional filters
5. **doctor_schedule(doctor_id, date_range)** - Get doctor's appointments
6. **available_slots(specialty, doctor_id, date)** - Find available appointment slots
7. **book_appointment(patient_id, doctor_id, datetime)** - Book appointment
8. **cancel_appointment(appointment_id)** - Cancel appointment
9. **patient_history(patient_id)** - Get patient history + treatments
10. **add_treatment(patient_id, doctor_id, diagnosis, plan)** - Add treatment record
11. **busiest_doctor(start_date, end_date)** - Find busiest doctor in period
12. **monthly_appointments(month, year)** - Count monthly appointments
13. **department_load()** - Get appointments per department

## 🔗 Multi-Step Agent Reasoning (3-Tool Scenario)

### User Request
```
"Book an appointment for Sarah Cohen with a cardiologist next week."
```

### Agent Execution Flow

**Step 1: Search for Patient**
```python
Tool Call: search_patient("Sarah Cohen")

DB Query Executed
Result: [
  {"id": 5, "full_name": "Sarah Cohen", "phone": "555-0101", "age": 34}
]
```

**Step 2: Find Available Slots**
```python
Tool Call: available_slots(specialty="Cardiology", date_range="next week")

DB Query Executed
Result: [
  {
    "doctor_id": 1,
    "doctor_name": "Amit Patel",
    "slots": [
      "2026-06-29T10:00:00",
      "2026-06-29T11:00:00",
      "2026-06-30T09:00:00"
    ]
  }
]
```

**Step 3: Book the Appointment**
```python
Tool Call: book_appointment(patient_id=5, doctor_id=1, datetime="2026-06-29T10:00:00")

DB INSERT Query Executed
Result: {
  "id": 123,
  "patient_id": 5,
  "doctor_id": 1,
  "appointment_datetime": "2026-06-29T10:00:00",
  "status": "scheduled"
}
```

**Final Response to User**
```
"✅ Booked! Sarah Cohen has an appointment with Dr. Amit Patel 
(Cardiology) on June 29, 2026 at 10:00 AM. 
Appointment ID: #123"
```

### API Response
```json
{
  "reply": "Booked appointment for Sarah Cohen...",
  "tools_called": [
    {
      "name": "search_patient",
      "args": {"query": "Sarah Cohen"},
      "result_count": 1
    },
    {
      "name": "available_slots",
      "args": {"specialty": "Cardiology", "date_range": "next week"},
      "result_count": 1
    },
    {
      "name": "book_appointment",
      "args": {
        "patient_id": 5,
        "doctor_id": 1,
        "datetime": "2026-06-29T10:00:00"
      },
      "result": {"id": 123, "status": "scheduled"}
    }
  ]
}
```

## 💬 Example Chat Conversations

### Example 1: Show Available Cardiology Appointments
```
User: "Show available cardiology appointments."

Agent Query Process:
1. Extract specialty: "Cardiology"
2. Call available_slots(specialty="Cardiology")
3. Query doctors WHERE specialty LIKE '%Cardiology%'
4. Check appointments for each doctor
5. Return free slots

Response: "Available cardiology appointments:
- Dr. Amit Patel: June 29 at 10:00 AM, 11:00 AM
- Dr. Lina Chen: June 30 at 09:00 AM, 02:00 PM"
```

### Example 2: Patient Medical History
```
User: "Show patient history for David Levi."

Agent Query Process:
1. search_patient("David Levi")
2. patient_history(patient_id=21)
3. Fetch appointments + treatments

Response: "David Levi (Patient #21)
Medical History:
- Age: 45, Gender: Male
- Main Condition: Hypertension

Recent Appointments:
- May 15, 2026: Follow-up with Dr. Brown
- April 10, 2026: Initial consultation

Treatments:
- Diagnosis: Hypertension
- Plan: Daily Lisinopril 10mg + blood pressure monitoring"
```

### Example 3: Analytics Query
```
User: "Who has the most appointments next week?"

Agent Query Process:
1. busiest_doctor(start_date, end_date)
2. GROUP BY doctor COUNT appointments
3. ORDER BY count DESC LIMIT 1

Response: "Dr. Amit Patel (Cardiology) has the most appointments 
next week with 12 scheduled appointments."
```

### Example 4: Cancel Appointment
```
User: "Cancel appointment #104."

Agent Query Process:
1. cancel_appointment(104)
2. UPDATE appointments SET status='cancelled'

Response: "✅ Appointment #104 has been cancelled.
Would you like me to help reschedule?"
```

## 🔐 Authentication & Security

### Password Storage
- Uses bcrypt via passlib library
- Passwords hashed with salt: `passlib.context.CryptContext`
- Never stored in plain text

### JWT Tokens
- 24-hour expiration
- Payload: `{user_id, email, role}`
- Used for all protected endpoints

### SQL Safety
- SQLAlchemy ORM prevents SQL injection
- Parameterized queries for all DB operations

### Sample Auth Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "password": "secure_password"
  }'

Response: 
{
  "message": "user_registered",
  "user": {"id": 1, "email": "john@example.com", "full_name": "John Doe"}
}

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "secure_password"
  }'

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# 3. Use token in protected requests
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  http://localhost:8000/auth/me
```

## 📁 Project Structure

```
healthcare-ai-agent/
├── backend/
│   ├── app.py                    # Flask app factory
│   ├── config.py                 # Configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── __init__.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── database.py           # DB session management
│   │   └── seed.py               # Seed demo data
│   │
│   ├── routes/                   # Flask blueprints (7 files)
│   │   ├── auth_routes.py        # JWT auth endpoints
│   │   ├── patient_routes.py     # Patient CRUD
│   │   ├── doctor_routes.py      # Doctor endpoints
│   │   ├── appointment_routes.py # Appointment CRUD
│   │   ├── treatment_routes.py   # Treatment records
│   │   ├── analytics_routes.py   # Analytics queries
│   │   └── agent_routes.py       # Chat endpoints
│   │
│   ├── services/                 # Business logic (4 files)
│   │   ├── auth_service.py
│   │   ├── patient_service.py
│   │   ├── appointment_service.py
│   │   └── analytics_service.py
│   │
│   ├── agent/                    # AI agent layer (4 files)
│   │   ├── agent.py              # Main orchestrator
│   │   ├── tools.py              # 13 tool wrappers
│   │   ├── prompts.py            # System prompts
│   │   └── gemini_client.py      # LLM client
│   │
│   ├── utils/                    # Utilities (2 files)
│   │   ├── security.py           # JWT & bcrypt
│   │   └── responses.py          # Response helpers
│   │
│   └── static/
│       └── index.html            # Fallback UI
│
├── frontend/                     # React + TypeScript
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.tsx               # Root component
│   │   ├── index.tsx             # Entry point
│   │   ├── api.ts                # API client
│   │   ├── App.css
│   │   ├── styles.css            # Chat styles
│   │   └── components/
│   │       └── Chat.tsx          # Chat UI component
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
│
├── main.py                       # Root entry point
├── docker-compose.yml            # Docker services
├── .env                          # Environment vars
├── .env.example
├── .gitignore
└── README.md
```

## 🌐 Gemini LLM Integration

### Development Mode (Default - No Key Required)
The system ships with mock LLM that simulates responses based on the user message. Perfect for development and testing.

**File:** `backend/agent/gemini_client.py`

### Production Mode (Real Gemini API)
To use the real Gemini Free API:

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update `.env`:
   ```
   GEMINI_API_KEY=AIzaSy...your_key...
   GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
   ```
3. The client automatically switches to real API if keys are configured

## 👥 Team Contribution Guide

### Suggested Git Commits Split

**Member A: Database & Data Layer**
```
Commit 1: "feat: Add SQLAlchemy models and DB schema"
- backend/db/models.py
- backend/db/database.py

Commit 2: "feat: Add seed data script"
- backend/db/seed.py
```

**Member B: API & Authentication**
```
Commit 1: "feat: Add auth service and security utils"
- backend/services/auth_service.py
- backend/utils/security.py

Commit 2: "feat: Implement auth routes"
- backend/routes/auth_routes.py

Commit 3: "feat: Implement patient and doctor routes"
- backend/routes/patient_routes.py
- backend/routes/doctor_routes.py
- backend/routes/appointment_routes.py
- backend/services/patient_service.py
- backend/services/appointment_service.py
```

**Member C: Agent & Frontend**
```
Commit 1: "feat: Implement AI agent orchestrator"
- backend/agent/agent.py
- backend/agent/tools.py
- backend/agent/prompts.py
- backend/agent/gemini_client.py

Commit 2: "feat: Add analytics service and routes"
- backend/services/analytics_service.py
- backend/routes/analytics_routes.py
- backend/routes/agent_routes.py

Commit 3: "feat: Create React + TypeScript frontend"
- frontend/src/*
- frontend/public/index.html

Commit 4: "docs: Add comprehensive README and Docker setup"
- README.md
- docker-compose.yml
- Dockerfile
- .env.example
```

## 🧪 Testing & Validation

### Test Database Connection
```bash
# From backend directory
python -c "from backend.db.database import engine; print('✅ DB Connected!')"
```

### Test API Endpoints
```bash
# Start backend
python main.py

# In another terminal
# Get all patients
curl http://localhost:8000/patients

# Get patient #1
curl http://localhost:8000/patients/1

# Get all doctors
curl http://localhost:8000/doctors

# Get doctors by specialty
curl "http://localhost:8000/doctors?specialty=Cardiology"

# Test analytics
curl http://localhost:8000/analytics/busiest-doctor
curl http://localhost:8000/analytics/monthly-appointments
curl http://localhost:8000/analytics/department-load
```

### Test Agent Chat
```bash
# Book appointment scenario
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Book an appointment for Sarah Cohen with a cardiologist next week.",
    "session_id": "test-session-1"
  }'

# Get conversation history
curl "http://localhost:8000/agent/history?session_id=test-session-1"
```

### Test Multi-Step Tool Calling
Watch the tools_called array in the response to see all 3 steps:
1. search_patient
2. available_slots
3. book_appointment

## 📊 Database Seed Data

The seed script populates:
- **5 Departments:** Cardiology, Neurology, Pediatrics, Oncology, General Medicine
- **8 Doctors:** 2 per major department
- **10 Patients:** Various ages, genders, medical histories
- **20 Appointments:** Distributed across patients/doctors
- **10 Treatments:** Various diagnoses and treatment plans
- **2 Users:** admin@example.com, reception@example.com (password: password)

Access them immediately after seeding!

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| `ERROR: could not connect to database` | Ensure PostgreSQL is running and DATABASE_URL in .env is correct |
| `ERROR: Address already in use` | Kill process on port 8000: `netstat -ano` + `taskkill /PID <pid>` |
| `ModuleNotFoundError: No module named 'backend'` | Make sure you're in the project root directory |
| `Gemini API Key not found` | Normal - system falls back to mock mode. Set key in .env to use real API |
| `frontend: npm: not found` | Install Node.js from nodejs.org |

## ✅ Course Requirements Checklist

- [x] Backend in Flask Python
- [x] 10+ meaningful API endpoints (23 total)
- [x] PostgreSQL database (not SQLite)
- [x] 5+ connected tables with foreign keys (6 tables)
- [x] ERD or schema documentation (in this README)
- [x] 8+ meaningful agent tools (13 total)
- [x] Gemini free API integration (with mock fallback)
- [x] AI Agent shows multi-step reasoning
- [x] Demonstrates 3-tool booking scenario
- [x] User management (registration, login, hashed passwords, JWT, profile update)
- [x] Docker Compose setup (one command to run)
- [x] React + TypeScript frontend (bonus)
- [x] Clean layered architecture (routes → services → db)
- [x] Code divided for 3-person team commits
- [x] Comprehensive README with examples

## 📚 References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [React TypeScript Guide](https://www.typescriptlang.org/docs/handbook/react.html)
- [Docker Compose](https://docs.docker.com/compose/)
- [JWT Authentication](https://jwt.io/)
- [Bcrypt Security](https://en.wikipedia.org/wiki/Bcrypt)

## 📄 License

University Project - © 2026

---

**Project Status:** ✅ Complete & Ready for Demonstration
**Last Updated:** June 2026

