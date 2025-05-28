from flask import request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps

from models import db, User, EmployeeProfile, Department, LeaveRequest
from werkzeug.security import check_password_hash

# Custom decorator for admin access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    login_user(user)
    session.permanent = True  # Use the permanent session lifetime
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "emp_id": user.emp_id,
            "email": user.email,
            "role": user.role
        }
    }), 200

@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

# Admin Routes
@login_required
@admin_required
def get_all_employees():
    employees = User.query.all()
    employee_list = []
    
    for employee in employees:
        profile = employee.profile
        employee_data = {
            "id": employee.id,
            "emp_id": employee.emp_id,
            "email": employee.email,
            "role": employee.role,
            "department_id": employee.department_id,
            "profile": None
        }
        
        if profile:
            employee_data["profile"] = {
                "full_name": profile.full_name,
                "salary": profile.salary,
                "contact_email": profile.contact_email,
                "phone": profile.phone
            }
        
        employee_list.append(employee_data)
    
    return jsonify({"employees": employee_list}), 200

@login_required
@admin_required
def add_employee():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['emp_id', 'email', 'password', 'role', 'department_id', 'full_name']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if employee already exists
    if User.query.filter_by(emp_id=data['emp_id']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Employee with this ID or email already exists"}), 409
    
    # Create new user
    new_user = User(
        emp_id=data['emp_id'],
        email=data['email'],
        role=data['role'],
        department_id=data['department_id']
    )
    new_user.set_password(data['password'])
    
    # Create employee profile
    new_profile = EmployeeProfile(
        full_name=data['full_name'],
        salary=data.get('salary', 0),
        contact_email=data.get('contact_email', data['email']),
        phone=data.get('phone', '')
    )
    
    # Save to database
    try:
        db.session.add(new_user)
        db.session.flush()  # To get the user ID
        
        new_profile.user_id = new_user.id
        db.session.add(new_profile)
        db.session.commit()
        
        return jsonify({"message": "Employee added successfully", "emp_id": new_user.emp_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@login_required
@admin_required
def update_employee(emp_id):
    data = request.get_json()
    user = User.query.filter_by(emp_id=emp_id).first()
    
    if not user:
        return jsonify({"error": "Employee not found"}), 404
    
    try:
        # Update user data
        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            user.role = data['role']
        if 'department_id' in data:
            user.department_id = data['department_id']
        if 'password' in data:
            user.set_password(data['password'])
        
        # Update profile data
        profile = user.profile
        if profile:
            if 'full_name' in data:
                profile.full_name = data['full_name']
            if 'salary' in data:
                profile.salary = data['salary']
            if 'contact_email' in data:
                profile.contact_email = data['contact_email']
            if 'phone' in data:
                profile.phone = data['phone']
        
        db.session.commit()
        return jsonify({"message": "Employee updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@login_required
@admin_required
def get_all_departments():
    departments = Department.query.all()
    department_list = []
    
    for dept in departments:
        employees = User.query.filter_by(department_id=dept.id).count()
        department_list.append({
            "id": dept.id,
            "name": dept.name,
            "employee_count": employees
        })
    
    return jsonify({"departments": department_list}), 200

@login_required
@admin_required
def add_department():
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({"error": "Department name is required"}), 400
    
    # Check if department already exists
    if Department.query.filter_by(name=data['name']).first():
        return jsonify({"error": "Department with this name already exists"}), 409
    
    new_department = Department(name=data['name'])
    
    try:
        db.session.add(new_department)
        db.session.commit()
        return jsonify({
            "message": "Department added successfully",
            "id": new_department.id,
            "name": new_department.name
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@login_required
@admin_required
def get_all_leave_requests():
    leave_requests = LeaveRequest.query.all()
    request_list = []
    
    for leave in leave_requests:
        employee = User.query.get(leave.employee_id)
        profile = employee.profile if employee else None
        
        request_list.append({
            "id": leave.id,
            "employee_id": leave.employee_id,
            "employee_name": profile.full_name if profile else "Unknown",
            "start_date": leave.start_date.strftime('%Y-%m-%d'),
            "end_date": leave.end_date.strftime('%Y-%m-%d'),
            "status": leave.status,
            "reason": leave.reason
        })
    
    return jsonify({"leave_requests": request_list}), 200

@login_required
@admin_required
def update_leave_request(request_id):
    data = request.get_json()
    leave_request = LeaveRequest.query.get(request_id)
    
    if not leave_request:
        return jsonify({"error": "Leave request not found"}), 404
    
    if 'status' not in data:
        return jsonify({"error": "Status is required"}), 400
    
    if data['status'] not in ['pending', 'approved', 'rejected']:
        return jsonify({"error": "Invalid status value"}), 400
    
    try:
        leave_request.status = data['status']
        db.session.commit()
        return jsonify({"message": "Leave request updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Employee Routes
@login_required
def get_profile():
    profile = current_user.profile
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    department = Department.query.get(current_user.department_id)
    
    return jsonify({
        "employee": {
            "id": current_user.id,
            "emp_id": current_user.emp_id,
            "email": current_user.email,
            "department": department.name if department else None,
            "profile": {
                "full_name": profile.full_name,
                "contact_email": profile.contact_email,
                "phone": profile.phone
            }
        }
    }), 200

@login_required
def update_contact_info():
    data = request.get_json()
    profile = current_user.profile
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    try:
        if 'contact_email' in data:
            profile.contact_email = data['contact_email']
        if 'phone' in data:
            profile.phone = data['phone']
        
        db.session.commit()
        return jsonify({"message": "Contact information updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@login_required
def submit_leave_request():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['start_date', 'end_date', 'reason']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if start_date > end_date:
            return jsonify({"error": "Start date cannot be after end date"}), 400
        
        leave_request = LeaveRequest(
            employee_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            reason=data['reason'],
            status='pending'
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({
            "message": "Leave request submitted successfully",
            "id": leave_request.id,
            "status": leave_request.status
        }), 201
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@login_required
def get_leave_requests():
    leave_requests = LeaveRequest.query.filter_by(employee_id=current_user.id).all()
    request_list = []
    
    for leave in leave_requests:
        request_list.append({
            "id": leave.id,
            "start_date": leave.start_date.strftime('%Y-%m-%d'),
            "end_date": leave.end_date.strftime('%Y-%m-%d'),
            "reason": leave.reason,
            "status": leave.status
        })
    
    return jsonify({"leave_requests": request_list}), 200

# Blueprint registration function
def register_routes(app):
    # Authentication routes
    app.route('/api/login', methods=['POST'])(login)
    app.route('/api/logout', methods=['POST'])(logout)
    
    # Admin routes
    app.route('/api/admin/employees', methods=['GET'])(get_all_employees)
    app.route('/api/admin/employees', methods=['POST'])(add_employee)
    app.route('/api/admin/employees/<emp_id>', methods=['PUT'])(update_employee)
    app.route('/api/admin/departments', methods=['GET'])(get_all_departments)
    app.route('/api/admin/departments', methods=['POST'])(add_department)
    app.route('/api/admin/leave-requests', methods=['GET'])(get_all_leave_requests)
    app.route('/api/admin/leave-requests/<int:request_id>', methods=['PUT'])(update_leave_request)
    
    # Employee routes
    app.route('/api/profile', methods=['GET'])(get_profile)
    app.route('/api/profile/contact', methods=['PATCH'])(update_contact_info)
    app.route('/api/leave', methods=['POST'])(submit_leave_request)
    app.route('/api/leave', methods=['GET'])(get_leave_requests)