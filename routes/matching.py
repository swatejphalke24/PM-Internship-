"""AI Matching Engine routes - trigger and retrieve match scores"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db
from services.ai_engine import (
    run_matching_engine, generate_recommendations,
    greedy_allocation, explain_match
)
import json

matching_bp = Blueprint('matching', __name__)


def is_admin(user_id):
    user = query_db('SELECT role FROM users WHERE id = %s', (user_id,), one=True)
    return user and user['role'] == 'admin'


@matching_bp.route('/run', methods=['POST'])
@jwt_required()
def run_matching():
    """Admin: trigger full matching engine for all students × internships."""
    user_id = int(get_jwt_identity())
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    # Fetch all active students with complete profiles
    students = query_db(
        '''SELECT id, gpa, cgpa_scale, skills, preferred_domains
           FROM student_profiles
           WHERE profile_complete = TRUE AND allocation_status IN ('pending', 'recommended')'''
    )

    # Fetch all active internships
    internships = query_db(
        '''SELECT id, required_skills, preferred_skills, domain,
                  min_gpa, is_active, (total_slots - filled_slots) as available_slots
           FROM internships
           WHERE is_active = TRUE AND (total_slots - filled_slots) > 0'''
    )

    if not students:
        return jsonify({'error': 'No eligible students found'}), 400
    if not internships:
        return jsonify({'error': 'No active internships found'}), 400

    # Run AI matching
    scores = run_matching_engine(students, internships)

    # Persist scores (upsert)
    for s in scores:
        query_db(
            '''INSERT INTO match_scores
               (student_id, internship_id, skill_similarity, gpa_score, preference_score, final_score)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               skill_similarity = VALUES(skill_similarity),
               gpa_score = VALUES(gpa_score),
               preference_score = VALUES(preference_score),
               final_score = VALUES(final_score),
               computed_at = CURRENT_TIMESTAMP''',
            (s['student_id'], s['internship_id'], s['skill_similarity'],
             s['gpa_score'], s['preference_score'], s['final_score']),
            commit=True
        )

    # Generate top-3 recommendations
    recommendations = generate_recommendations(scores, top_n=3)
    for student_id, recs in recommendations.items():
        # Delete old recommendations for this student
        query_db(
            'DELETE FROM recommendations WHERE student_id = %s', (student_id,), commit=True
        )
        for rec in recs:
            query_db(
                '''INSERT INTO recommendations
                   (student_id, internship_id, recommendation_rank, match_score)
                   VALUES (%s, %s, %s, %s)''',
                (student_id, rec['internship_id'], rec['rank'], rec['final_score']),
                commit=True
            )

        # Update student status
        query_db(
            '''UPDATE student_profiles SET allocation_status = 'recommended'
               WHERE id = %s''',
            (student_id,), commit=True
        )

        # Notify student
        profile = query_db('SELECT user_id FROM student_profiles WHERE id = %s',
                            (student_id,), one=True)
        if profile:
            query_db(
                '''INSERT INTO notifications (user_id, title, message, type)
                   VALUES (%s, %s, %s, %s)''',
                (profile['user_id'],
                 'Your internship recommendations are ready!',
                 'The AI matching engine has analysed your profile and found your top 3 internship matches. Log in to view them.',
                 'success'), commit=True
            )

    # Log the action
    query_db(
        '''INSERT INTO audit_logs (action, performed_by, target_type, details)
           VALUES (%s, %s, %s, %s)''',
        ('run_matching', user_id, 'all',
         f'Matched {len(students)} students against {len(internships)} internships. Generated {sum(len(v) for v in recommendations.values())} recommendations.'),
        commit=True
    )

    return jsonify({
        'message': 'Matching completed',
        'stats': {
            'students_processed': len(students),
            'internships_evaluated': len(internships),
            'total_scores': len(scores),
            'students_recommended': len(recommendations)
        }
    })


@matching_bp.route('/explain/<int:internship_id>', methods=['GET'])
@jwt_required()
def explain(internship_id):
    """Get detailed match explanation for the current student vs an internship."""
    user_id = int(get_jwt_identity())
    profile = query_db(
        'SELECT * FROM student_profiles WHERE user_id = %s', (user_id,), one=True
    )
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    internship = query_db(
        '''SELECT i.*, c.name as company_name FROM internships i
           JOIN companies c ON i.company_id = c.id
           WHERE i.id = %s''',
        (internship_id,), one=True
    )
    if not internship:
        return jsonify({'error': 'Internship not found'}), 404

    try:
        s_skills = json.loads(profile.get('skills') or '[]')
        s_prefs = json.loads(profile.get('preferred_domains') or '[]')
        req_skills = json.loads(internship.get('required_skills') or '[]')
        pref_skills = json.loads(internship.get('preferred_skills') or '[]')
    except json.JSONDecodeError:
        s_skills = s_prefs = req_skills = pref_skills = []

    explanation = explain_match(
        s_skills, req_skills, pref_skills, s_prefs,
        internship.get('domain', ''),
        float(profile.get('gpa') or 0),
        float(internship.get('min_gpa') or 0)
    )

    return jsonify({
        'internship': {
            'id': internship['id'],
            'title': internship['title'],
            'company': internship['company_name'],
            'domain': internship['domain']
        },
        'explanation': explanation
    })


@matching_bp.route('/scores', methods=['GET'])
@jwt_required()
def get_scores():
    """Admin: get all match scores with filtering."""
    user_id = int(get_jwt_identity())
    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    scores = query_db(
        '''SELECT ms.student_id, ms.internship_id, ms.final_score,
                  ms.skill_similarity, ms.gpa_score, ms.preference_score,
                  sp.full_name, sp.university, i.title, c.name as company
           FROM match_scores ms
           JOIN student_profiles sp ON ms.student_id = sp.id
           JOIN internships i ON ms.internship_id = i.id
           JOIN companies c ON i.company_id = c.id
           ORDER BY ms.final_score DESC
           LIMIT 100'''
    )
    return jsonify({'scores': scores, 'count': len(scores)})