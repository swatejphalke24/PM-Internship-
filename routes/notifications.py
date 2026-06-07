"""Notification routes"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import query_db

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    notifs = query_db(
        '''SELECT id, title, message, type, is_read, created_at
           FROM notifications WHERE user_id = %s
           ORDER BY created_at DESC LIMIT 20''',
        (user_id,)
    )
    unread = sum(1 for n in notifs if not n['is_read'])
    return jsonify({'notifications': notifs, 'unread_count': unread})


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@jwt_required()
def mark_read(notif_id):
    user_id = int(get_jwt_identity())
    query_db(
        'UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s',
        (notif_id, user_id), commit=True
    )
    return jsonify({'message': 'Marked as read'})


@notifications_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    query_db(
        'UPDATE notifications SET is_read = TRUE WHERE user_id = %s',
        (user_id,), commit=True
    )
    return jsonify({'message': 'All notifications marked as read'})