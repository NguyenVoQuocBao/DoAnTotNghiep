"""Flask application factory with enhanced features"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config import SECRET_KEY, STATIC_DIR, TEMPLATES_DIR, ensure_directories
from .routes import auth, student, teacher, advanced
from .simple_socketio import init_socketio

def create_app():
    """Create and configure Flask application with SocketIO"""
    ensure_directories()
    
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        template_folder=str(TEMPLATES_DIR)
    )
    
    app.secret_key = SECRET_KEY
    
    # Enable CSRF protection
    csrf = CSRFProtect(app)
    
    # Exempt upload routes from CSRF
    from .routes.teacher import upload_excel, import_data
    csrf.exempt(upload_excel)
    csrf.exempt(import_data)
    
    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(teacher.bp)
    app.register_blueprint(advanced.bp, url_prefix='/advanced')
    
    # Initialize SocketIO
    socketio = init_socketio(app)
    app.config['SOCKETIO'] = socketio
    
    return app
