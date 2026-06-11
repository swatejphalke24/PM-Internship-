"""
Company routes:
  - Public registration (no login)
  - Company dashboard (allocated students)
  - Company internship management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db

companies_bp = Blueprint('companies', __name__)


# ─── Public: Company self-registration ────────────────────────────────────────
@companies_bp.route('/register', methods=['POST'])
def register_company():
    """Public endpoint — no JWT required. Company submits details for admin review."""
    data = request.get_json()

    required = ['name', 'sector', 'location', 'contact_email']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Check duplicate by name or email
    existing = query_db(
        'SELECT id FROM companies WHERE name = %s OR contact_email = %s',
        (data['name'], data['contact_email']), one=True
    )
    if existing:
        return jsonify({'error': 'A company with this name or email already exists'}), 409

    # Insert as pending (unverified)
    company_id = query_db(
        '''INSERT INTO companies
           (name, sector, location, description, website, contact_email, verified, status)
           VALUES (%s, %s, %s, %s, %s, %s, FALSE, 'pending')''',
        (data['name'], data['sector'], data['location'],
         data.get('description', ''), data.get('website', ''),
         data['contact_email']),
        commit=True
    )

    query_db(
        '''INSERT INTO audit_logs (action, performed_by, target_type, target_id, details)
           VALUES (%s, %s, %s, %s, %s)''',
        ('company_registration_request', None, 'company', company_id,
         f'New registration request: {data["name"]} ({data["sector"]})'),
        commit=True
    )

    return jsonify({
        'message': 'Registration submitted. Awaiting admin approval. '
                   'Your login credentials will be sent to your contact email once approved.',
        'company_id': company_id
    }), 201


# ─── Company: Dashboard ────────────────────────────────────────────────────────
@companies_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def company_dashboard():
    """Company sees their internships and allocated students."""
    user_id = int(get_jwt_identity())

    user = query_db('SELECT role FROM users WHERE id = %s', (user_id,), one=True)
    if not user or user['role'] != 'company':
        return jsonify({'error': 'Company access required'}), 403

    # Get the company linked to this user
    company = query_db(
        'SELECT * FROM companies WHERE user_id = %s', (user_id,), one=True
    )
    if not company:
        return jsonify({'error': 'Company profile not found'}), 404

    # Get all internships for this company
    internships = query_db(
        '''SELECT i.id, i.title, i.domain, i.location, i.stipend,
                  i.duration_weeks, i.total_slots, i.filled_slots,
                  i.is_active, i.start_date,
                  (i.total_slots - i.filled_slots) as available_slots
           FROM internships i
           WHERE i.company_id = %s
           ORDER BY i.created_at DESC''',
        (company['id'],)
    )

    # Get all allocated students across all company internships
    allocated_students = query_db(
        '''SELECT
               sp.full_name, sp.student_id as student_code, sp.university,
               sp.degree_program, sp.year_of_study, sp.gpa, sp.skills,
               sp.phone, sp.state,
               u.email as student_email,
               i.title as internship_title, i.domain, i.location as internship_location,
               i.stipend, i.start_date, i.duration_weeks,
               a.allocation_score, a.allocation_method, a.allocated_at, a.status
           FROM allocations a
           JOIN student_profiles sp ON a.student_id = sp.id
           JOIN users u ON sp.user_id = u.id
           JOIN internships i ON a.internship_id = i.id
           WHERE i.company_id = %s
           ORDER BY i.title, a.allocation_score DESC''',
        (company['id'],)
    )

    # Stats
    total_slots = sum(i['total_slots'] for i in internships)
    filled_slots = sum(i['filled_slots'] for i in internships)

    return jsonify({
        'company': company,
        'internships': internships,
        'allocated_students': allocated_students,
        'stats': {
            'total_internships': len(internships),
            'total_slots': total_slots,
            'filled_slots': filled_slots,
            'available_slots': total_slots - filled_slots,
            'total_allocated': len(allocated_students)
        }
    })


# ─── Company: View students for a specific internship ─────────────────────────
@companies_bp.route('/internships/<int:internship_id>/students', methods=['GET'])
@jwt_required()
def internship_students(internship_id):
    user_id = int(get_jwt_identity())
    user = query_db('SELECT role FROM users WHERE id = %s', (user_id,), one=True)
    if not user or user['role'] != 'company':
        return jsonify({'error': 'Company access required'}), 403

    company = query_db('SELECT id FROM companies WHERE user_id = %s', (user_id,), one=True)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    # Verify this internship belongs to this company
    internship = query_db(
        'SELECT * FROM internships WHERE id = %s AND company_id = %s',
        (internship_id, company['id']), one=True
    )
    if not internship:
        return jsonify({'error': 'Internship not found or access denied'}), 404

    students = query_db(
        '''SELECT
               sp.full_name, sp.student_id as student_code, sp.university,
               sp.degree_program, sp.year_of_study, sp.gpa, sp.skills,
               sp.phone, u.email,
               a.allocation_score, a.allocation_method, a.allocated_at
           FROM allocations a
           JOIN student_profiles sp ON a.student_id = sp.id
           JOIN users u ON sp.user_id = u.id
           WHERE a.internship_id = %s
           ORDER BY a.allocation_score DESC''',
        (internship_id,)
    )

    return jsonify({
        'internship': internship,
        'students': students,
        'count': len(students)
    })