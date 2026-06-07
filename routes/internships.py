"""Internship listing routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db

internships_bp = Blueprint('internships', __name__)

@internships_bp.route('/', methods=['GET'])
@jwt_required()
def list_internships():
    domain = request.args.get('domain', '')
    search = request.args.get('search', '')
    active_only = request.args.get('active', 'true') == 'true'

    where = 'WHERE 1=1'
    params = []
    if active_only:
        where += ' AND i.is_active = TRUE'
    if domain:
        where += ' AND i.domain = %s'
        params.append(domain)
    if search:
        where += ' AND (i.title LIKE %s OR c.name LIKE %s)'
        params.extend([f'%{search}%', f'%{search}%'])

    internships = query_db(
        f'''SELECT i.*, c.name as company_name, c.sector, c.location as company_location,
                   (i.total_slots - i.filled_slots) as available_slots
            FROM internships i
            JOIN companies c ON i.company_id = c.id
            {where}
            ORDER BY i.created_at DESC''',
        params
    )
    return jsonify({'internships': internships, 'count': len(internships)})


@internships_bp.route('/<int:intern_id>', methods=['GET'])
@jwt_required()
def get_internship(intern_id):
    internship = query_db(
        '''SELECT i.*, c.name as company_name, c.sector, c.description as company_desc,
                  c.website, c.contact_email,
                  (i.total_slots - i.filled_slots) as available_slots
           FROM internships i
           JOIN companies c ON i.company_id = c.id
           WHERE i.id = %s''',
        (intern_id,), one=True
    )
    if not internship:
        return jsonify({'error': 'Internship not found'}), 404
    return jsonify(internship)


@internships_bp.route('/', methods=['POST'])
@jwt_required()
def create_internship():
    user_id = int(get_jwt_identity())
    user = query_db('SELECT role FROM users WHERE id = %s', (user_id,), one=True)
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    required = ['company_id', 'title', 'required_skills', 'domain', 'total_slots']
    for f in required:
        if not data.get(f):
            return jsonify({'error': f'{f} is required'}), 400

    intern_id = query_db(
        '''INSERT INTO internships (company_id, title, description, required_skills,
           preferred_skills, domain, location, stipend, duration_weeks, total_slots,
           min_gpa, min_year, start_date, application_deadline)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (data['company_id'], data['title'], data.get('description',''),
         data['required_skills'], data.get('preferred_skills','[]'),
         data['domain'], data.get('location',''), data.get('stipend',0),
         data.get('duration_weeks',12), data['total_slots'],
         data.get('min_gpa',0), data.get('min_year',1),
         data.get('start_date'), data.get('application_deadline')),
        commit=True
    )
    return jsonify({'message': 'Internship created', 'id': intern_id}), 201