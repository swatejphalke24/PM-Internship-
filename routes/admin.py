"""Admin dashboard routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db

admin_bp = Blueprint('admin', __name__)

def require_admin(user_id):
    u = query_db('SELECT role FROM users WHERE id = %s', (user_id,), one=True)
    return u and u['role'] == 'admin'


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    stats = {}

    total_students = query_db('SELECT COUNT(*) as cnt FROM student_profiles', one=True)
    stats['total_students'] = total_students['cnt']

    status_counts = query_db(
        '''SELECT allocation_status, COUNT(*) as cnt
           FROM student_profiles GROUP BY allocation_status'''
    )
    stats['by_status'] = {r['allocation_status']: r['cnt'] for r in status_counts}

    total_internships = query_db('SELECT COUNT(*) as cnt FROM internships WHERE is_active=TRUE', one=True)
    stats['total_internships'] = total_internships['cnt']

    total_allocations = query_db('SELECT COUNT(*) as cnt FROM allocations', one=True)
    stats['total_allocations'] = total_allocations['cnt']

    total_slots = query_db('SELECT SUM(total_slots) as t, SUM(filled_slots) as f FROM internships WHERE is_active=TRUE', one=True)
    stats['total_slots'] = int(total_slots['t'] or 0)
    stats['filled_slots'] = int(total_slots['f'] or 0)
    stats['fill_rate'] = round((stats['filled_slots'] / max(stats['total_slots'], 1)) * 100, 1)

    domain_dist = query_db(
        '''SELECT i.domain, COUNT(*) as internships, SUM(i.total_slots) as slots
           FROM internships i WHERE i.is_active=TRUE GROUP BY i.domain ORDER BY slots DESC'''
    )
    stats['domain_distribution'] = domain_dist

    top_matches = query_db(
        '''SELECT sp.full_name, i.title, c.name as company, a.allocation_score
           FROM allocations a
           JOIN student_profiles sp ON a.student_id = sp.id
           JOIN internships i ON a.internship_id = i.id
           JOIN companies c ON i.company_id = c.id
           ORDER BY a.allocation_score DESC LIMIT 10'''
    )
    stats['top_allocations'] = top_matches

    avg_score = query_db('SELECT AVG(final_score) as avg FROM match_scores', one=True)
    stats['avg_match_score'] = round(float(avg_score['avg'] or 0), 3)

    recent_activity = query_db(
        '''SELECT action, details, created_at FROM audit_logs
           ORDER BY created_at DESC LIMIT 10'''
    )
    stats['recent_activity'] = recent_activity

    unallocated = query_db(
        "SELECT COUNT(*) as cnt FROM student_profiles WHERE allocation_status NOT IN ('allocated')",
        one=True
    )
    stats['unallocated_students'] = unallocated['cnt']

    return jsonify(stats)


@admin_bp.route('/companies', methods=['GET'])
@jwt_required()
def list_companies():
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    companies = query_db(
        '''SELECT c.*, COUNT(i.id) as internship_count, SUM(i.total_slots) as total_slots
           FROM companies c
           LEFT JOIN internships i ON c.id = i.company_id AND i.is_active = TRUE
           GROUP BY c.id ORDER BY c.name'''
    )
    return jsonify({'companies': companies})


@admin_bp.route('/companies', methods=['POST'])
@jwt_required()
def add_company():
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if not data.get('name'):
        return jsonify({'error': 'Company name is required'}), 400

    company_id = query_db(
        '''INSERT INTO companies (name, sector, location, description, website, contact_email, verified)
           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        (data['name'], data.get('sector', ''), data.get('location', ''),
         data.get('description', ''), data.get('website', ''),
         data.get('contact_email', ''), data.get('verified', False)),
        commit=True
    )

    query_db(
        '''INSERT INTO audit_logs (action, performed_by, target_type, target_id, details)
           VALUES (%s, %s, %s, %s, %s)''',
        ('add_company', user_id, 'company', company_id, f'Added company: {data["name"]}'),
        commit=True
    )

    return jsonify({'message': 'Company added successfully', 'id': company_id}), 201


@admin_bp.route('/companies/<int:company_id>', methods=['PUT'])
@jwt_required()
def update_company(company_id):
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    allowed = ['name', 'sector', 'location', 'description', 'website', 'contact_email', 'verified']
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    set_clause = ', '.join([f'{k} = %s' for k in updates])
    query_db(
        f'UPDATE companies SET {set_clause} WHERE id = %s',
        list(updates.values()) + [company_id], commit=True
    )
    return jsonify({'message': 'Company updated successfully'})


@admin_bp.route('/companies/<int:company_id>', methods=['DELETE'])
@jwt_required()
def delete_company(company_id):
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    # Check if company has internships
    has_internships = query_db(
        'SELECT COUNT(*) as cnt FROM internships WHERE company_id = %s', (company_id,), one=True
    )
    if has_internships['cnt'] > 0:
        return jsonify({'error': 'Cannot delete company with existing internships'}), 400

    query_db("UPDATE companies SET status = 'rejected', verified = FALSE WHERE id = %s", (company_id,), commit=True)
    return jsonify({'message': 'Company deleted successfully'})


@admin_bp.route('/companies/pending', methods=['GET'])
@jwt_required()
def pending_companies():
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    companies = query_db(
        'SELECT * FROM companies WHERE verified = FALSE ORDER BY created_at DESC'
    )
    return jsonify({'companies': companies, 'count': len(companies)})


@admin_bp.route('/companies/<int:company_id>/approve', methods=['POST'])
@jwt_required()
def approve_company(company_id):
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    company = query_db('SELECT * FROM companies WHERE id = %s', (company_id,), one=True)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    # Check if company already has a user account
    if company.get('user_id'):
        return jsonify({'error': 'Company already approved'}), 400

    from werkzeug.security import generate_password_hash
    import random, string

    # Auto-generate login credentials
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    pw_hash = generate_password_hash(temp_password)
    login_email = company['contact_email']

    # Check if email already in users
    existing_user = query_db('SELECT id FROM users WHERE email = %s', (login_email,), one=True)
    if existing_user:
        login_email = f"company.{company_id}@pm-internship.gov.my"

    # Create user account for the company
    new_user_id = query_db(
        "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'company')",
        (login_email, pw_hash), commit=True
    )

    # Link user to company and mark verified
    query_db(
        "UPDATE companies SET verified = TRUE, status = 'approved', user_id = %s WHERE id = %s",
        (new_user_id, company_id), commit=True
    )

    # Auto-create a default internship so approved company appears in student listings
    existing_internship = query_db(
        'SELECT id FROM internships WHERE company_id = %s LIMIT 1',
        (company_id,), one=True
    )

    if not existing_internship:
        query_db(
            '''INSERT INTO internships
               (company_id, title, required_skills, preferred_skills, domain, location,
                stipend, duration_weeks, total_slots, filled_slots, min_gpa, min_year,
                is_active, start_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, CURDATE())''',
            (
                company_id,
                f'{company["name"]} Internship Opportunity',
                '["Communication","Basic Computer Skills"]',
                '["Teamwork","Problem Solving"]',
                company.get('sector') or 'General',
                company.get('location') or 'Remote',
                1000,
                12,
                5,
                0,
                2.5,
                1
            ),
            commit=True
        )

    query_db(
        '''INSERT INTO audit_logs (action, performed_by, target_type, target_id, details)
           VALUES (%s, %s, %s, %s, %s)''',
        ('approve_company', user_id, 'company', company_id,
         f'Approved: {company["name"]} | Login: {login_email} | Temp password: {temp_password}'),
        commit=True
    )

    return jsonify({
        'message': f'{company["name"]} approved successfully',
        'login_email': login_email,
        'temp_password': temp_password,
        'note': 'Share these credentials with the company to access their portal'
    })


@admin_bp.route('/companies/<int:company_id>/reject', methods=['POST'])
@jwt_required()
def reject_company(company_id):
    user_id = int(get_jwt_identity())
    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    company = query_db('SELECT * FROM companies WHERE id = %s', (company_id,), one=True)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    query_db("UPDATE companies SET status = 'rejected', verified = FALSE WHERE id = %s", (company_id,), commit=True)

    query_db(
        '''INSERT INTO audit_logs (action, performed_by, target_type, target_id, details)
           VALUES (%s, %s, %s, %s, %s)''',
        ('reject_company', user_id, 'company', company_id,
         f'Rejected and removed company: {company["name"]}'),
        commit=True
    )
    return jsonify({'message': f'{company["name"]} rejected and removed'})