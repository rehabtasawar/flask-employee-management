from flask import Flask
# from flask_login import LoginManager
from datetime import timedelta
import os
from models import db
from routes import auth_bp, admin_bp, employee_bp, manager_bp
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

# Import the register_routes function
# from routes import register_routes



def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres123@db:5432/employee_management')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')  # Change in production
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session timeout after 30 minutes
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

    # Configure secure cookies
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

    # Initialize extensions
    # login_manager = LoginManager()
    # login_manager.init_app(app)
    db.init_app(app)
    jwt = JWTManager(app)

    blacklist = set()

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        return jti in blacklist

    # Create database tables
    with app.app_context():
        db.create_all()

    # User loader function for Flask-Login
    # @login_manager.user_loader
    # def load_user(user_id):
    #     from models import User
    #     return User.query.get(int(user_id))

    # Register routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(manager_bp)

    return app

if __name__ == '__main__':
    app = create_app()

    app.run(debug=False)