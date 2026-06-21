# Healthcare AI Agent

A university final project for the course **AI Agents in Python**.

This project is a clinic / hospital management system with an AI-powered chat interface. The Agent can answer questions from the database and perform real actions such as searching patients, checking doctor availability, booking appointments, cancelling appointments, adding treatment records, and generating clinic analytics.

---

## Project Overview

**System Flow:**

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

* AI Agent architecture with function/tool calling
* Multi-step agentic workflows
* REST API built with Flask
* PostgreSQL database with related tables
* JWT authentication and hashed passwords
* Gemini API integration with local mock fallback
* Docker Compose setup
* React + TypeScript frontend bonus

---

## Technology Stack

### Backend

* **Language:** Python
* **Framework:** Flask
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **LLM:** Gemini API
* **Auth:** JWT + bcrypt/passlib
* **Server:** Gunicorn

### Frontend

* **Framework:** React 18
* **Language:** TypeScript
* **HTTP:** Fetch API
* **Styling:** CSS

### DevOps

* **Containerization:** Docker
* **Orchestration:** Docker Compose

---

## Database Schema

The project uses **6 connected database tables**.

### 1. users

Stores system users and authentication data.

```text
id
full_name
email
password_hash
role
created_at
```

### 2. departments

Stores clinic departments.

```text
id
name
description
```

### 3. doctors

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

### 4. patients

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

### 5. appointments

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

### 6. treatments

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
│   │   ├── doctor_routes.py
│   │   ├── patient_routes.py
│   │   └── treatment_routes.py
│   │
│   ├── services/
│   │   ├── analytics_service.py
│   │   ├── appointment_service.py
│   │   ├── auth_service.py
│   │   └── patient_service.py
│   │
│   ├── static/
│   │   └── index.html
│   │
│   └── utils/
│       ├── auth.py
│       ├── responses.py
│       └── security.py
│
├── docs/
├── frontend/
├── manual-tests/
├── main.py
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── test_imports.py
```

---

## Environment Variables

The real `.env` file is local only and must **not** be committed.

Create it from the example file:

```powershell
copy .env.example .env
```

Your root `.env` should look like this:

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

### 1. Start the project

From the project root:

```powershell
docker compose up --build
```

The backend will run at:

```text
http://localhost:8000
```

The default chat UI is available at:

```text
http://localhost:8000/
```

---

### 2. Seed the database

In a second terminal:

```powershell
docker compose exec backend python -m backend.db.seed
```

The seed script is safe to run multiple times.

---

### 3. Verify Python inside Docker

```powershell
docker compose exec backend python --version
```

Expected:

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

Expected:

```text
key_loaded= True
model= gemini-2.5-flash
custom_url= False
```

---

## Gemini API Integration

The project supports two modes.

### 1. Real Gemini mode

When `GEMINI_API_KEY` exists in `.env`, the backend calls Gemini through:

```text
https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

The model is controlled by:

```env
GEMINI_MODEL=gemini-2.5-flash
```

The client builds the URL automatically when:

```env
GEMINI_API_URL=
```

is empty.

### 2. Mock mode

When `GEMINI_API_KEY` is missing, the system uses a local mock fallback.

This keeps the project demo working even without an external API key.

File:

```text
backend/agent/gemini_client.py
```

---

## API Endpoints

The project contains **23 meaningful API endpoints**.

---

### Authentication

```text
POST   /auth/register
POST   /auth/login
GET    /auth/me
PUT    /auth/profile
```

Purpose:

* Register a user
* Login and receive JWT
* Read current user profile
* Update user profile

---

### Patients

```text
GET    /patients
GET    /patients/<id>
POST   /patients
PUT    /patients/<id>
```

Purpose:

* List/search patients
* View patient details
* Create patients
* Update patient data

---

### Doctors

```text
GET    /doctors
GET    /doctors/<id>
GET    /doctors/<id>/schedule
```

Purpose:

* List doctors
* Filter doctors by specialty
* View doctor schedule

---

### Departments

```text
GET    /departments
```

Purpose:

* List all departments

---

### Appointments

```text
GET    /appointments
POST   /appointments
PUT    /appointments/<id>/cancel
PUT    /appointments/<id>/complete
```

Purpose:

* List appointments
* Book appointments
* Cancel appointments
* Mark appointments as completed

---

### Treatments

```text
GET    /patients/<id>/history
POST   /treatments
```

Purpose:

* View patient history
* Add treatment records

---

### Analytics

```text
GET    /analytics/busiest-doctor
GET    /analytics/monthly-appointments
GET    /analytics/department-load
```

Purpose:

* Find busiest doctor
* Get monthly appointment statistics
* Show department workload

---

### Agent

```text
POST   /agent/chat
GET    /agent/history
```

Purpose:

* Send a message to the AI Agent
* Read conversation history

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
Booked appointment for Sarah Cohen with Dr. Amit Patel (Cardiology) on 2026-06-28 09:00.
Appointment ID: 22
```

### Example tools_called output

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
        "datetime": "2026-06-28T09:00:00",
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
curl.exe http://localhost:8000/doctors
```

### List cardiologists

```powershell
curl.exe "http://localhost:8000/doctors?specialty=Cardiology"
```

### List departments

```powershell
curl.exe http://localhost:8000/departments
```

### Agent chat

```powershell
curl.exe -i -X POST "http://localhost:8000/agent/chat" -H "Content-Type: application/json" -d "{\"message\":\"Who is the busiest doctor?\",\"session_id\":\"demo\"}"
```

---

## Demo Script for Lecturer

A recommended demonstration flow:

### 1. Start Docker

```powershell
docker compose up --build
```

### 2. Seed the database

```powershell
docker compose exec backend python -m backend.db.seed
```

### 3. Open the chat UI

```text
http://localhost:8000/
```

### 4. Ask a free-text question

```text
What can you help me with?
```

Expected:

```text
Gemini responds with a natural explanation.
```

### 5. Ask an analytics question

```text
Who is the busiest doctor?
```

Expected:

```text
The Agent calls busiest_doctor.
```

### 6. Ask a multi-step booking question

```text
Book Sarah Cohen with a cardiologist next week
```

Expected:

```text
The Agent calls:
search_patient → available_slots → book_appointment
```

### 7. Show tools_called in the API response

This proves the Agent is not only chatting, but also performing structured tool calls.

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

---

## Troubleshooting

| Problem                        | Solution                                                           |
| ------------------------------ | ------------------------------------------------------------------ |
| Docker does not start          | Make sure Docker Desktop is running                                |
| Database connection error      | Run `docker compose up --build` and wait for database health check |
| `ModuleNotFoundError: backend` | Run commands from the project root                                 |
| Gemini returns mock message    | Make sure `GEMINI_API_KEY` exists in `.env`                        |
| Gemini returns 403             | Create a new Gemini API key/project and replace the key in `.env`  |
| `curl` cannot open JSON file   | Recreate the file inside `manual-tests/`                           |
| Port 8000 already in use       | Stop the process using port 8000 or change the port mapping        |

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
✅ Layered architecture
✅ README with setup and demo instructions
```

---

## Important Submission Notes

Before submitting:

```text
Do not include .env
Do not include real API keys
Do not include node_modules
Do not include .venv
Do not include __pycache__
Do not include .git in the final submission zip unless required
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

---

## License

University project — 2026.

---

## Project Status

```text
Complete and ready for demonstration.
```
