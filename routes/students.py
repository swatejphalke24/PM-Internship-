"""Student profile management routes"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db
import json

students_bp = Blueprint('students', __name__)


@students_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    profile = query_db(
        '''SELECT sp.*, u.email,
           (SELECT COUNT(*) FROM recommendations r WHERE r.student_id = sp.id) as rec_count,
           (SELECT COUNT(*) FROM allocations a WHERE a.student_id = sp.id) as allocated
           FROM student_profiles sp
           JOIN users u ON sp.user_id = u.id
           WHERE sp.user_id = %s''',
        (user_id,), one=True
    )
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(profile)


@students_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    allowed_fields = ['full_name', 'university', 'degree_program', 'year_of_study',
                      'gpa', 'phone', 'state', 'skills', 'preferred_domains']

    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    # Validate GPA
    if 'gpa' in updates:
        gpa = float(updates['gpa'])
        if not (0 <= gpa <= 4.0):
            return jsonify({'error': 'GPA must be between 0 and 4.0'}), 400

    # Build SET clause
    set_clause = ', '.join([f'{k} = %s' for k in updates])
    values = list(updates.values()) + [user_id]

    query_db(
        f'UPDATE student_profiles SET {set_clause}, profile_complete = TRUE WHERE user_id = %s',
        values, commit=True
    )

    # Add notification about profile update and reset allocation for re-matching
    query_db(
        '''INSERT INTO notifications (user_id, title, message, type)
           VALUES (%s, %s, %s, %s)''',
        (user_id, 'Profile updated',
         'Your profile has been updated. New AI recommendations will be generated shortly.',
         'info'), commit=True
    )

    return jsonify({'message': 'Profile updated successfully'})


@students_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = int(get_jwt_identity())
    profile = query_db(
        'SELECT * FROM student_profiles WHERE user_id = %s', (user_id,), one=True
    )
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    student_id = profile['id']

    # Get recommendations with internship details
    recommendations = query_db(
        '''SELECT r.*, i.title, i.domain, i.location, i.stipend, i.duration_weeks,
                  c.name as company_name, c.sector,
                  r.match_score, r.recommendation_rank
           FROM recommendations r
           JOIN internships i ON r.internship_id = i.id
           JOIN companies c ON i.company_id = c.id
           WHERE r.student_id = %s
           ORDER BY r.recommendation_rank''',
        (student_id,)
    )

    # Get allocation if any
    allocation = query_db(
        '''SELECT a.*, i.title, i.domain, i.location, i.stipend, i.start_date,
                  c.name as company_name, c.contact_email
           FROM allocations a
           JOIN internships i ON a.internship_id = i.id
           JOIN companies c ON i.company_id = c.id
           WHERE a.student_id = %s''',
        (student_id,), one=True
    )

    # Get match scores breakdown
    top_scores = query_db(
        '''SELECT ms.*, i.title, c.name as company_name
           FROM match_scores ms
           JOIN internships i ON ms.internship_id = i.id
           JOIN companies c ON i.company_id = c.id
           WHERE ms.student_id = %s
           ORDER BY ms.final_score DESC LIMIT 5''',
        (student_id,)
    )

    return jsonify({
        'profile': profile,
        'recommendations': recommendations,
        'allocation': allocation,
        'top_matches': top_scores,
        'stats': {
            'rec_count': len(recommendations),
            'allocated': allocation is not None,
            'profile_complete': profile.get('profile_complete', False)
        }
    })


@students_bp.route('/', methods=['GET'])
@jwt_required()
def list_students():
    """Admin: list all students with pagination."""
    user = query_db(
        'SELECT role FROM users WHERE id = %s', (int(get_jwt_identity()),), one=True
    )
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    status_filter = request.args.get('status', '')

    where = 'WHERE 1=1'
    params = []
    if status_filter:
        where += ' AND sp.allocation_status = %s'
        params.append(status_filter)

    students = query_db(
        f'''SELECT sp.id, sp.full_name, sp.student_id, sp.university,
                   sp.degree_program, sp.gpa, sp.allocation_status,
                   sp.profile_complete, u.email
            FROM student_profiles sp
            JOIN users u ON sp.user_id = u.id
            {where}
            ORDER BY sp.full_name
            LIMIT %s OFFSET %s''',
        params + [per_page, offset]
    )

    total = query_db(
        f'SELECT COUNT(*) as cnt FROM student_profiles sp {where}',
        params, one=True
    )

    return jsonify({
        'students': students,
        'total': total['cnt'],
        'page': page,
        'per_page': per_page
    })