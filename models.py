from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

#could add timestampMixin for automatic timestamping of created_at and updated_at fields
class User(db.Model, UserMixin):
    """User model for authentication and role management"""
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    # leave_balance = db.Column(db.Integer, nullable=False, default=20)
    
    profile = db.relationship('EmployeeProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True, cascade='all, delete-orphan')
    attendance = db.relationship('Attendance', backref='user', lazy=True, cascade='all, delete-orphan')
    # department = db.relationship('Department', backref='users', lazy=True)  
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)

    def leave_balance(self, year = None):
        """Calculate leave balance for the user"""
        approved_leaves = LeaveRequest.query.filter_by(employee_id=self.id, status='approved').all()
        days_taken = sum(
            (lr.end_date - lr.start_date).days + 1
            for lr in approved_leaves
            if lr.start_date.year == year
        )
        return 20 - days_taken
    
    def __repr__(self):
        return f'<User {self.emp_id}>'


class EmployeeProfile(db.Model):
    """Employee profile information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    def __repr__(self):
        return f'<EmployeeProfile {self.full_name}>'


class Department(db.Model):
    """Department model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relationships
    employees = db.relationship('User', backref='department', lazy=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'


class LeaveRequest(db.Model):
    """Leave request model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending_manager')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeaveRequest {self.id} - {self.status}>'
    
class Attendance(db.Model):
    """Attendance model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='present')  # 'present', 'absent', 'leave'
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    
    def __repr__(self):
        return f'<Attendance {self.user_id} - {self.date} - {self.status}>'