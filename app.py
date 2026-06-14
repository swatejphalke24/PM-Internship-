"""
PM Internship Scheme - AI-Based Smart Allocation & Recommendation Engine
Backend: Flask + MySQL + scikit-learn
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from datetime import timedelta

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'pm-internship-secret-key-2025'
app.config['JWT_SECRET_KEY'] = 'jwt-pm-internship-2025'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'root123')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'pm_internship')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

# Uploads
app.config['UPLOAD_FOLDER'] = 'uploads/resumes'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# Extensions
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "https://pm-internship-blond.vercel.app",
            "https://pm-internship-6sw1yfal1-swatej-s-projects.vercel.app"
        ]
    }
}, supports_credentials=True)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        origin = request.headers.get("Origin")

        allowed_origins = [
            "http://localhost:5173",
            "https://pm-internship-blond.vercel.app",
            "https://pm-internship-6sw1yfal1-swatej-s-projects.vercel.app",
        ]

        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"

        return response, 200

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    allowed_origins = [
        "http://localhost:5173",
        "https://pm-internship-blond.vercel.app",
        "https://pm-internship-6sw1yfal1-swatej-s-projects.vercel.app",
    ]

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response

jwt = JWTManager(app)

# Register blueprints
from routes.auth import auth_bp
from routes.students import students_bp
from routes.internships import internships_bp
from routes.matching import matching_bp
from routes.recommendations import recommendations_bp
from routes.allocations import allocations_bp
from routes.admin import admin_bp
from routes.notifications import notifications_bp
from routes.companies import companies_bp


app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(students_bp, url_prefix='/api/students')
app.register_blueprint(internships_bp, url_prefix='/api/internships')
app.register_blueprint(matching_bp, url_prefix='/api/matching')
app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
app.register_blueprint(allocations_bp, url_prefix='/api/allocations')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
app.register_blueprint(companies_bp, url_prefix='/api/companies')

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'version': '1.0.0', 'service': 'PM Internship AI Engine'})

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)