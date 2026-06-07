"""Allocations routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db
from services.ai_engine import greedy_allocation

allocations_bp = Blueprint('allocations', __name__)

def is_admin(uid):
    u = query_db('SELECT role FROM users WHERE id = %s', (uid,), one=True)
    return u and u['role'] == 'admin'


@allocations_bp.route('/run', methods=['POST'])
@jwt_required()
def run_allocation():
    """Admin: execute greedy allocation algorithm."""
    user_id = int(get_jwt_identity())
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    # Get all match scores for eligible students
    scores = query_db(
        '''SELECT ms.student_id, ms.internship_id, ms.final_score,
                  ms.skill_similarity, ms.gpa_score, ms.preference_score
           FROM match_scores ms
           JOIN student_profiles sp ON ms.student_id = sp.id
           JOIN internships i ON ms.internship_id = i.id
           WHERE sp.allocation_status IN ('recommended', 'pending')
             AND i.is_active = TRUE
             AND (i.total_slots - i.filled_slots) > 0'''
    )

    # Get available slots per internship
    internship_slots_data = query_db(
        'SELECT id, (total_slots - filled_slots) as slots FROM internships WHERE is_active = TRUE'
    )
    internship_slots = {r['id']: r['slots'] for r in internship_slots_data}

    # Get student choices (accepted recommendations)
    student_choices_data = query_db(
        '''SELECT r.student_id, r.internship_id FROM recommendations r
           WHERE r.student_choice = 'accepted' '''
    )
    student_choices = {r['student_id']: r['internship_id'] for r in student_choices_data}

    if not scores:
        return jsonify({'error': 'No match scores found. Run matching first.'}), 400

    # Run greedy algorithm
    allocations = greedy_allocation(scores, internship_slots, student_choices)

    allocated_count = 0
    for student_id, alloc in allocations.items():
        # Insert allocation
        existing = query_db('SELECT id FROM allocations WHERE student_id = %s', (student_id,), one=True)
        if existing:
            continue  # Skip already allocated

        query_db(
            '''INSERT INTO allocations (student_id, internship_id, allocation_score, allocation_method)
               VALUES (%s, %s, %s, %s)''',
            (student_id, alloc['internship_id'], alloc['score'],
             'student_choice' if alloc['method'] == 'student_choice' else 'ai_recommended'),
            commit=True
        )

        # Update filled_slots
        query_db(
            'UPDATE internships SET filled_slots = filled_slots + 1 WHERE id = %s',
            (alloc['internship_id'],), commit=True
        )

        # Update student status
        query_db(
            "UPDATE student_profiles SET allocation_status = 'allocated' WHERE id = %s",
            (student_id,), commit=True
        )

        # Notify student
        profile = query_db(
            'SELECT user_id FROM student_profiles WHERE id = %s', (student_id,), one=True
        )
        internship = query_db(
            '''SELECT i.title, c.name FROM internships i
               JOIN companies c ON i.company_id = c.id WHERE i.id = %s''',
            (alloc['internship_id'],), one=True
        )
        if profile and internship:
            query_db(
                '''INSERT INTO notifications (user_id, title, message, type)
                   VALUES (%s, %s, %s, %s)''',
                (profile['user_id'],
                 'Internship placement confirmed!',
                 f'Congratulations! You have been allocated to {internship["title"]} at {internship["name"]}.',
                 'success'), commit=True
            )
        allocated_count += 1

    query_db(
        '''INSERT INTO audit_logs (action, performed_by, target_type, details)
           VALUES (%s, %s, %s, %s)''',
        ('run_allocation', user_id, 'all',
         f'Allocated {allocated_count} students using greedy algorithm.'),
        commit=True
    )

    return jsonify({
        'message': 'Allocation completed',
        'allocated_count': allocated_count,
        'total_processed': len(allocations)
    })


@allocations_bp.route('/', methods=['GET'])
@jwt_required()
def list_allocations():
    user_id = int(get_jwt_identity())
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    allocs = query_db(
        '''SELECT a.*, sp.full_name, sp.student_id as student_code,
                  sp.university, sp.gpa, i.title, c.name as company_name,
                  i.domain, i.location
           FROM allocations a
           JOIN student_profiles sp ON a.student_id = sp.id
           JOIN internships i ON a.internship_id = i.id
           JOIN companies c ON i.company_id = c.id
           ORDER BY a.allocated_at DESC'''
    )
    return jsonify({'allocations': allocs, 'count': len(allocs)})