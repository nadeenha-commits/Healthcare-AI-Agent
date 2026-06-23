import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from backend.db.database import init_db
from backend.routes.auth_routes import auth_bp
from backend.routes.patient_routes import patient_bp
from backend.routes.doctor_routes import doctor_bp
from backend.routes.appointment_routes import appointment_bp
from backend.routes.treatment_routes import treatment_bp
from backend.routes.analytics_routes import analytics_bp
from backend.routes.agent_routes import agent_bp
from backend.routes.department_routes import department_bp


def create_app():
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(backend_dir, "static"),
        template_folder=os.path.join(backend_dir, "static"),
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret")
    CORS(app)

    init_db(app)

    # ------------------------------------------------------------------
    # Legacy routes
    # These keep the current frontend working.
    # Examples:
    # /auth
    # /patients
    # /doctors
    # /appointments
    # /agent
    # ------------------------------------------------------------------
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(patient_bp, url_prefix="/patients")
    app.register_blueprint(doctor_bp, url_prefix="/doctors")
    app.register_blueprint(appointment_bp, url_prefix="/appointments")

    # treatment_routes.py already defines:
    # GET /patients/<patient_id>/history
    # POST /treatments
    app.register_blueprint(treatment_bp)

    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(agent_bp, url_prefix="/agent")
    app.register_blueprint(department_bp, url_prefix="/departments")

    # ------------------------------------------------------------------
    # API aliases
    # These add clean /api/... endpoints for README/demo/API testing.
    # Examples:
    # /api/auth
    # /api/patients
    # /api/doctors
    # /api/appointments
    # /api/agent
    # ------------------------------------------------------------------
    app.register_blueprint(auth_bp, url_prefix="/api/auth", name="api_auth")
    app.register_blueprint(patient_bp, url_prefix="/api/patients", name="api_patients")
    app.register_blueprint(doctor_bp, url_prefix="/api/doctors", name="api_doctors")
    app.register_blueprint(
        appointment_bp,
        url_prefix="/api/appointments",
        name="api_appointments",
    )

    # Creates:
    # GET /api/patients/<patient_id>/history
    # POST /api/treatments
    app.register_blueprint(treatment_bp, url_prefix="/api", name="api_treatments")

    app.register_blueprint(analytics_bp, url_prefix="/api/analytics", name="api_analytics")
    app.register_blueprint(agent_bp, url_prefix="/api/agent", name="api_agent")
    app.register_blueprint(
        department_bp,
        url_prefix="/api/departments",
        name="api_departments",
    )

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)