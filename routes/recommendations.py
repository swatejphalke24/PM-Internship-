"""Recommendations routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    user_id = int(get_jwt_identity())
    profile = query_db('SELECT id FROM student_profiles WHERE user_id = %s', (user_id,), one=True)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    recs = query_db(
        '''SELECT r.id, r.recommendation_rank, r.match_score, r.student_choice,
                  i.id as internship_id, i.title, i.description, i.domain, i.location,
                  i.stipend, i.duration_weeks, i.required_skills, i.preferred_skills,
                  i.min_gpa, i.start_date, i.application_deadline,
                  c.name as company_name, c.sector, c.location as company_location
           FROM recommendations r
           JOIN internships i ON r.internship_id = i.id
           JOIN companies c ON i.company_id = c.id
           WHERE r.student_id = %s
           ORDER BY r.recommendation_rank''',
        (profile['id'],)
    )
    return jsonify({'recommendations': recs})


@recommendations_bp.route('/<int:rec_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_recommendation(rec_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    choice = data.get('choice')  # 'accepted' or 'declined'

    if choice not in ['accepted', 'declined']:
        return jsonify({'error': 'Choice must be accepted or declined'}), 400

    profile = query_db('SELECT id FROM student_profiles WHERE user_id = %s', (user_id,), one=True)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    # Verify rec belongs to this student
    rec = query_db(
        'SELECT id FROM recommendations WHERE id = %s AND student_id = %s',
        (rec_id, profile['id']), one=True
    )
    if not rec:
        return jsonify({'error': 'Recommendation not found'}), 404

    query_db(
        'UPDATE recommendations SET student_choice = %s WHERE id = %s',
        (choice, rec_id), commit=True
    )

    return jsonify({'message': f'Recommendation {choice}'})