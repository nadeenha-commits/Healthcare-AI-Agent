# Healthcare AI Agent

A university final project for the course **AI Agents in Python**.

This project is a clinic / hospital management system with an AI-powered chat interface. The Agent can understand free-text user requests, call backend tools, read/write from a PostgreSQL database, and return useful responses for clinic workflows such as searching patients, checking doctor availability, booking appointments, cancelling appointments, adding treatment records, and generating analytics.

---

## Project Overview

**System Flow**

```text
React / Chat UI
        ↓
Flask API
        ↓
AI Agent
        ↓
Function Tools
        ↓
PostgreSQL Database
        ↓
Final Response
```

The system demonstrates:

- AI Agent architecture with function/tool calling
- Multi-step agentic workflows
- REST API built with Flask
- PostgreSQL database with related tables
- SQLAlchemy ORM
- JWT authentication and hashed passwords
- Gemini API integration with local mock fallback
- Docker Compose setup
- React + TypeScript frontend bonus
- SSE-based workflow trace in the frontend

---

## Technology Stack

### Backend

- **Language:** Python
- **Framework:** Flask
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **LLM:** Gemini API
- **Auth:** JWT + bcrypt/passlib
- **Server:** Gunicorn

### Frontend

- **Framework:** React 18
- **Language:** TypeScript
- **HTTP:** Fetch API
- **Styling:** Bootstrap 5 components and utility classes

### DevOps

- **Containerization:** Docker
- **Orchestration:** Docker Compose

---

## Database Schema

The project uses **6 connected database tables**.

### 1. `users`

Stores system users and authentication data.

```text
id
full_name
email
password_hash
role
created_at
```

Important constraints:

```text
email is unique
role is limited to user / staff / admin
```

---

### 2. `departments`

Stores clinic departments.

```text
id
name
description
```

Important constraints:

```text
name is unique
```

---

### 3. `doctors`

Stores doctor information.

```text
id
full_name
specialty
department_id
```

Relationship:

```text
doctors.department_id → departments.id
```

---

### 4. `patients`

Stores patient records.

```text
id
full_name
phone
age
gender
medical_history
created_at
```

Important constraints:

```text
phone is unique
age must be non-negative
gender is limited to M / F / Other
```

---

### 5. `appointments`

Stores appointment bookings.

```text
id
patient_id
doctor_id
appointment_datetime
status
created_at
```

Relationships:

```text
appointments.patient_id → patients.id
appointments.doctor_id → doctors.id
```

Important constraints:

```text
status is limited to scheduled / cancelled / completed
active doctor slots are unique
active patient slots are unique
```

---

### 6. `treatments`

Stores treatment records.

```text
id
patient_id
doctor_id
diagnosis
treatment_plan
created_at
```

Relationships:

```text
treatments.patient_id → patients.id
treatments.doctor_id → doctors.id
```

---

## Entity Relationship Overview

```text
Departments
    ↓ one-to-many
Doctors
    ↓ one-to-many
Appointments
    ↑ many-to-one
Patients

Patients
    ↓ one-to-many
Treatments
    ↑ many-to-one
Doctors
```

### Text ERD

```text
departments
  id PK
  name UNIQUE
  description

doctors
  id PK
  full_name
  specialty
  department_id FK → departments.id

patients
  id PK
  full_name
  phone UNIQUE
  age
  gender
  medical_history
  created_at

appointments
  id PK
  patient_id FK → patients.id
  doctor_id FK → doctors.id
  appointment_datetime
  status
  created_at

treatments
  id PK
  patient_id FK → patients.id
  doctor_id FK → doctors.id
  diagnosis
  treatment_plan
  created_at

users
  id PK
  full_name
  email UNIQUE
  password_hash
  role
  created_at
```

---

## Project Structure

```text
Healthcare-AI-Agent/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── __init__.py
│   │
│   ├── agent/
│   │   ├── agent.py
│   │   ├── booking_flow.py
│   │   ├── gemini_client.py
│   │   ├── message_parser.py
│   │   ├── prompts.py
│   │   ├── registered_tool_handler.py
│   │   ├── response_formatters.py
│   │   ├── tool_registry.py
│   │   └── tools.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── seed.py
│   │
│   ├── routes/
│   │   ├── agent_routes.py
│   │   ├── analytics_routes.py
│   │   ├── appointment_routes.py
│   │   ├── auth_routes.py
│   │   ├── department_routes.py
│   │   ├── doctor_routes.py
│   │   ├── patient_routes.py
│   │   └── treatment_routes.py
│   │
│   ├── services/
│   │   ├── analytics_service.py
│   │   ├── appointment_service.py
│   │   ├── auth_service.py
│   │   ├── department_service.py
│   │   ├── doctor_service.py
│   │   ├── patient_service.py
│   │   ├── serializers.py
│   │   ├── service_utils.py
│   │   └── treatment_service.py
│   │
│   ├── static/
│   │   └── index.html
│   │
│   └── utils/
│       ├── auth.py
│       ├── responses.py
│       └── security.py
│
├── frontend/
├── manual-tests/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Service Layer Design

The backend uses a layered structure to separate responsibilities.

```text
routes/      → receive HTTP requests and return JSON responses
services/    → business logic and database operations
agent/       → AI Agent reasoning, tool selection, and tool execution
db/          → SQLAlchemy models, database connection, and seed data
utils/       → authentication, security, and shared response helpers
```

The service layer is split into focused files:

```text
appointment_service.py     → appointment listing, booking, cancellation, completion
doctor_service.py          → doctor list, doctor details, doctor schedules
department_service.py      → department listing
treatment_service.py       → treatment records and patient history
analytics_service.py       → clinic analytics
auth_service.py            → registration, login, user profile
patient_service.py         → patient CRUD
service_utils.py           → shared validation helpers
serializers.py             → shared response formatting
```

This improves code readability and avoids putting all business logic into one large service file.

---

## Environment Variables

The real `.env` file is local only and must **not** be committed.

Create it from the example file:

```powershell
copy .env.example .env
```

Example root `.env`:

```env
DATABASE_URL=postgresql://healthcare_user:healthcare_pass@db:5432/healthcare_db
SECRET_KEY=replace_with_secure_secret

GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_URL=

PYTHON_ENV=development
```

Important:

```text
.env contains secrets and must not be committed.
.env.example is safe to commit.
```

---

## Docker Setup

### 1. Start Docker services

From the project root:

```powershell
docker compose up --build
```

Backend URL:

```text
http://localhost:8000
```

The simple backend demo page is available at:

```text
http://localhost:8000/
```

---

### 2. Seed the database

In a second terminal:

```powershell
docker compose exec backend python -m backend.db.seed
```

The seed script is idempotent and safe to run multiple times.

---

### 3. Verify Python inside Docker

```powershell
docker compose exec backend python --version
```

Expected example:

```text
Python 3.11.x
```

---

### 4. Verify Gemini environment safely

Do not paste `docker compose config` output publicly because it may show secrets.

Use this safe command instead:

```powershell
docker compose exec backend python -c "import os; print('key_loaded=', bool(os.getenv('GEMINI_API_KEY'))); print('model=', os.getenv('GEMINI_MODEL')); print('custom_url=', bool(os.getenv('GEMINI_API_URL')))"
```

Expected example:

```text
key_loaded= True
model= gemini-2.5-flash
custom_url= False
```

---

## Local Development Run

This is the recommended way to run the project during development and demo testing.

### Required versions

```text
Python 3.12.x
Node.js / npm
Docker Desktop
```

Python 3.14 is not recommended for this project because some pinned backend dependencies may not support it correctly.

---

### 1. Start Docker database

From the project root:

```powershell
cd C:\Users\nadeenha\PycharmProjects\Healthcare-AI-Agent
docker compose up -d
```

---

### 2. Create and activate Python virtual environment

From the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r backend\requirements.txt
```

If the virtual environment already exists, only activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### 3. Seed the database

```powershell
python -m backend.db.seed
```

Expected output:

```text
Seed complete
```

---

### 4. Run backend

Always run the backend from the project root:

```powershell
python -m backend.app
```

Backend URL:

```text
http://127.0.0.1:8000
```

---

### 5. Run frontend

Open a new PowerShell terminal:

```powershell
cd C:\Users\nadeenha\PycharmProjects\Healthcare-AI-Agent\frontend
npm install
npm start
```

Frontend URL:

```text
http://localhost:3000
```

---

## Gemini API Integration

The project supports two modes.

### 1. Real Gemini mode

When `GEMINI_API_KEY` exists in `.env`, the backend calls Gemini through the configured Gemini model.

The model is controlled by:

```env
GEMINI_MODEL=gemini-2.5-flash
```

The client builds the URL automatically when:

```env
GEMINI_API_URL=
```

is empty.

File:

```text
backend/agent/gemini_client.py
```

---

### 2. Mock mode

When `GEMINI_API_KEY` is missing, the system uses a local mock fallback.

This keeps the project demo working even without an external API key.

File:

```text
backend/agent/gemini_client.py
```

---

## API Endpoints

The project contains more than 10 meaningful Flask API endpoints.

The project supports both legacy routes and `/api/...` aliases.  
The `/api/...` routes are recommended for documentation and testing.

---

### Authentication

```text
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
PUT    /api/auth/profile
```

Legacy equivalents:

```text
/auth/register
/auth/login
/auth/me
/auth/profile
```

Purpose:

- Register a user
- Login and receive JWT
- Read current user profile
- Update user profile

---

### Patients

```text
GET    /api/patients
GET    /api/patients/<id>
POST   /api/patients
PUT    /api/patients/<id>
```

Legacy equivalents:

```text
/patients
/patients/<id>
```

Purpose:

- List/search patients
- View patient details
- Create patients
- Update patient data

---

### Doctors

```text
GET    /api/doctors
GET    /api/doctors/<id>
GET    /api/doctors/<id>/schedule
```

Legacy equivalents:

```text
/doctors
/doctors/<id>
/doctors/<id>/schedule
```

Purpose:

- List doctors
- Filter doctors by specialty
- View doctor details
- View doctor schedule

Test examples:

```text
http://127.0.0.1:8000/api/doctors
http://127.0.0.1:8000/api/doctors/1
http://127.0.0.1:8000/api/doctors/999
```

---

### Departments

```text
GET    /api/departments
```

Legacy equivalent:

```text
/departments
```

Purpose:

- List all departments

Test example:

```text
http://127.0.0.1:8000/api/departments
```

---

### Appointments

```text
GET    /api/appointments
POST   /api/appointments
PUT    /api/appointments/<id>/cancel
PUT    /api/appointments/<id>/complete
```

Legacy equivalents:

```text
/appointments
/appointments/<id>/cancel
/appointments/<id>/complete
```

Purpose:

- List appointments
- Book appointments
- Cancel appointments
- Mark appointments as completed

---

### Treatments

```text
GET    /api/patients/<id>/history
POST   /api/treatments
```

Legacy equivalents:

```text
/patients/<id>/history
/treatments
```

Purpose:

- View patient history
- Add treatment records

---

### Analytics

```text
GET    /api/analytics/busiest-doctor
GET    /api/analytics/monthly-appointments
GET    /api/analytics/department-load
```

Legacy equivalents:

```text
/analytics/busiest-doctor
/analytics/monthly-appointments
/analytics/department-load
```

Purpose:

- Find busiest doctor
- Get monthly appointment statistics
- Show department workload

---

### Agent

```text
POST   /api/agent/chat
GET    /api/agent/history
```

Legacy equivalents:

```text
/agent/chat
/agent/history
```

Purpose:

- Send a free-text message to the AI Agent
- Read conversation history

---

## Authentication and Security

The project includes user management.

### Password security

Passwords are never stored in plain text.

The system uses:

```text
bcrypt / passlib
```

### JWT authentication

Login returns a JWT access token.

Protected endpoints require:

```text
Authorization: Bearer <token>
```

### Role protection

Some endpoints are protected by user role.

Analytics endpoints require:

```text
admin or staff
```

---

## AI Agent Tools

The AI Agent has **13 registered tools**.

```text
1. search_patient
2. get_patient_details
3. add_patient
4. list_doctors
5. doctor_schedule
6. available_slots
7. book_appointment
8. cancel_appointment
9. patient_history
10. add_treatment
11. busiest_doctor
12. monthly_appointments
13. department_load
```

These tools allow the Agent to interact with the database and perform real actions.

---

## Multi-Step Agent Reasoning

The project demonstrates a required multi-step Agent flow using **3 tools**.

### Example user message

```text
Book Sarah Cohen with a cardiologist next week
```

### Agent execution

```text
Step 1: search_patient
Step 2: available_slots
Step 3: book_appointment
```

### Example response

```text
Booked appointment for Sarah Cohen with Dr. Amit Patel (Cardiology) on 2026-06-30 10:00.
Appointment ID: 22
```

### Example tools-called output

```json
{
  "tools_called": [
    {
      "name": "search_patient",
      "args": {
        "query": "Sarah Cohen"
      },
      "result_count": 1
    },
    {
      "name": "available_slots",
      "args": {
        "date": "next week",
        "specialty": "Cardiology"
      },
      "result_count": 3
    },
    {
      "name": "book_appointment",
      "args": {
        "datetime": "2026-06-30T10:00:00",
        "doctor_id": 1,
        "patient_id": 1
      },
      "result": {
        "status": "scheduled"
      }
    }
  ]
}
```

---

## Manual Test Commands

The `manual-tests/` directory contains JSON request files used to test Agent behavior.

### 1. Gemini free-text Agent test

Create the test file:

```powershell
@'
{"message":"What can you help me with?","session_id":"phase8-gemini"}
'@ | Set-Content -Path manual-tests/agent-gemini-test.json
```

Run:

```powershell
curl.exe -i -X POST "http://localhost:8000/agent/chat" -H "Content-Type: application/json" --data-binary "@manual-tests/agent-gemini-test.json"
```

Expected:

```text
HTTP/1.1 200 OK
tools_called: []
```

---

### 2. Agent tool test

Create the test file:

```powershell
@'
{"message":"Who is the busiest doctor?","session_id":"phase8-tool-check"}
'@ | Set-Content -Path manual-tests/agent-tool-check.json
```

Run:

```powershell
curl.exe -i -X POST "http://localhost:8000/agent/chat" -H "Content-Type: application/json" --data-binary "@manual-tests/agent-tool-check.json"
```

Expected:

```text
tools_called includes busiest_doctor
```

---

### 3. Required 3-tool booking flow test

Create the test file:

```powershell
@'
{"message":"Book Sarah Cohen with a cardiologist next week","session_id":"phase8-booking-check"}
'@ | Set-Content -Path manual-tests/agent-booking-check.json
```

Run:

```powershell
curl.exe -i -X POST "http://localhost:8000/agent/chat" -H "Content-Type: application/json" --data-binary "@manual-tests/agent-booking-check.json"
```

Expected:

```text
tools_called includes:
1. search_patient
2. available_slots
3. book_appointment
```

---

## Additional API Test Examples

### List doctors

```powershell
curl.exe http://localhost:8000/api/doctors
```

### Doctor details

```powershell
curl.exe http://localhost:8000/api/doctors/1
```

### Invalid doctor

```powershell
curl.exe http://localhost:8000/api/doctors/999
```

Expected:

```json
{
  "error": "not_found",
  "message": "Doctor was not found."
}
```

### List cardiologists

```powershell
curl.exe "http://localhost:8000/api/doctors?specialty=Cardiology"
```

### List departments

```powershell
curl.exe http://localhost:8000/api/departments
```

### Agent chat

```powershell
curl.exe -i -X POST "http://localhost:8000/api/agent/chat" -H "Content-Type: application/json" -d "{\"message\":\"Who is the busiest doctor?\",\"session_id\":\"demo\"}"
```

---

## Final Demo Test Flow

Use this order during the lecturer demo.

### 1. Start Docker database

```powershell
docker compose up -d
```

### 2. Run backend

```powershell
.\.venv\Scripts\Activate.ps1
python -m backend.app
```

### 3. Run frontend

```powershell
cd frontend
npm start
```

### 4. Open the frontend

```text
http://localhost:3000
```

Make sure the UI shows:

```text
Gemini Connected
SSE Enabled
```

---

### 5. Required multi-tool Agent flow

Ask:

```text
Book Sarah Cohen with a cardiologist next week
```

Expected tool workflow:

```text
search_patient → available_slots → book_appointment
```

Expected result:

```text
The Agent books an appointment and returns the appointment ID.
```

---

### 6. Analytics workflow

Ask:

```text
Who is the busiest doctor next week?
```

Expected tool:

```text
busiest_doctor
```

---

### 7. Doctor schedule workflow

Ask:

```text
Show doctor 1 schedule this week
```

Expected tool:

```text
doctor_schedule
```

---

### 8. Availability workflow

Ask:

```text
Are there cardiology slots tomorrow?
```

Expected tool:

```text
available_slots
```

---

### 9. Department list workflow

Ask:

```text
Show departments
```

Expected tool:

```text
list_departments
```

---

### 10. Department analytics workflow

Ask:

```text
department load
```

Expected tool:

```text
department_load
```

---

### 11. Show API endpoint proof

Open:

```text
http://127.0.0.1:8000/api/doctors
http://127.0.0.1:8000/api/departments
```

This proves the Flask API and PostgreSQL database are working.

---

## Seed Data

The seed script creates demo data:

```text
5 departments
8 doctors
10 patients
20 appointments
10 treatments
2 users
```

Default demo users:

```text
admin@example.com
reception@example.com
```

Default password:

```text
password
```

After a clean database reset, seeded doctor IDs are usually:

```text
1–8
```

Recommended demo doctor:

```text
Doctor ID 1: Amit Patel
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Docker does not start | Make sure Docker Desktop is running |
| Database connection error | Run `docker compose up -d` and wait for the database to start |
| `ModuleNotFoundError: backend` | Run backend commands from the project root |
| Gemini returns mock message | Make sure `GEMINI_API_KEY` exists in `.env` |
| Gemini returns 403 | Create a new Gemini API key/project and replace the key in `.env` |
| `curl` cannot open JSON file | Recreate the file inside `manual-tests/` |
| Port 8000 already in use | Stop the process using port 8000 or change the port mapping |
| `psycopg2-binary` install fails | Use Python 3.12 and `psycopg2-binary==2.9.12` |
| `npm run dev` fails | This frontend uses `npm start`, not `npm run dev` |

---

## Course Requirements Checklist

```text
✅ Flask backend
✅ PostgreSQL database
✅ 10+ meaningful API endpoints
✅ 5+ related database tables
✅ SQLAlchemy ORM
✅ JWT authentication
✅ Hashed passwords
✅ 8+ meaningful Agent tools
✅ 3+ tool multi-step Agent flow
✅ Gemini API integration
✅ Mock fallback for development
✅ Docker Compose setup
✅ React + TypeScript frontend bonus
✅ SSE workflow trace
✅ Layered architecture
✅ README with setup and demo instructions
✅ Database schema and ERD-style documentation
```

---

## Final Submission Cleanup

Before creating the final ZIP, remove files and folders that should not be submitted.

Do not include:

```text
.env
.venv
node_modules
.git
.idea
__pycache__
frontend/build
dist
```

Safe to include:

```text
.env.example
README.md
docker-compose.yml
backend/
frontend/
manual-tests/
docs/
```

A clean ZIP should contain the source code and documentation only, not local environments or generated dependency folders.

---

## License

University project — 2026.

---

## Project Status

```text
Complete and ready for demonstration.
```
