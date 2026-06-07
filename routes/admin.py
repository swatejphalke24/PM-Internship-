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