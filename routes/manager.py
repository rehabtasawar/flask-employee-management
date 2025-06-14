from flask import Blueprint, request, jsonify
# from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, LeaveRequest, User, EmployeeProfile
from functools import wraps

manager_bp = Blueprint('manager', __name__)

def manager_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'manager':
            return jsonify({"error": "Manager access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

@manager_bp.route('/api/manager/leave-requests/<int:request_id>', methods=['PUT'])
@manager_required
def manager_update_leave_request(request_id):
    leave_request = LeaveRequest.query.get(request_id)
    if not leave_request:
        return jsonify({"error": "Leave request not found"}), 404

    # Only allow update if status is pending_manager
    if leave_request.status != 'pending_manager':
        return jsonify({"error": "Leave request is not pending manager approval"}), 400

    try:
        leave_request.status = 'pending_admin'
        db.session.commit()
        return jsonify({"message": "Leave request forwarded to admin"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500