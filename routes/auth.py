"""Authentication routes - register, login, logout, profile"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import query_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['email', 'password', 'full_name', 'student_id',
                 'university', 'degree_program', 'year_of_study', 'gpa']

    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Check email uniqueness
    existing = query_db('SELECT id FROM users WHERE email = %s', (data['email'],), one=True)
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    # Create user
    pw_hash = generate_password_hash(data['password'])
    user_id = query_db(
        'INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)',
        (data['email'], pw_hash, 'student'), commit=True
    )

# Create student profile
gpa = float(data['gpa'])

query_db(
    '''INSERT INTO student_profiles
       (user_id, full_name, student_id, university, degree_program,
        year_of_study, gpa, phone, state, skills,
        preferred_domains, profile_complete, allocation_status)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
    (
        user_id,
        data['full_name'],
        data['student_id'],
        data['university'],
        data['degree_program'],
        data['year_of_study'],
        gpa,
        data.get('phone', ''),
        data.get('state', ''),
        data.get('skills', '[]'),
        data.get('preferred_domains', '[]'),
        True,          # profile_complete
        'pending'      # allocation_status
    ),
    commit=True
)

    # Welcome notification
    query_db(
        '''INSERT INTO notifications (user_id, title, message, type)
           VALUES (%s, %s, %s, %s)''',
        (user_id, 'Welcome to PM Internship Scheme!',
         'Your profile has been created. Complete your profile to get AI-powered internship recommendations.',
         'info'), commit=True
    )

    token = create_access_token(identity=str(user_id))
    return jsonify({'token': token, 'message': 'Registration successful', 'user_id': user_id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    user = query_db(
        'SELECT id, email, password_hash, role FROM users WHERE email = %s',
        (data['email'],), one=True
    )

    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user['id']))

    # Fetch profile if student
    profile = None
    if user['role'] == 'student':
        profile = query_db(
            '''SELECT sp.*, u.email FROM student_profiles sp
               JOIN users u ON sp.user_id = u.id
               WHERE sp.user_id = %s''',
            (user['id'],), one=True
        )

    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'role': user['role'],
            'profile': profile
        }
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = query_db(
        'SELECT id, email, role FROM users WHERE id = %s', (user_id,), one=True
    )
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user['role'] == 'student':
        profile = query_db(
            'SELECT * FROM student_profiles WHERE user_id = %s', (user_id,), one=True
        )
        user['profile'] = profile

    return jsonify(user)