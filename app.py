import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Custom logger setup
logger = logging.getLogger('app')

def debug_log(message, error=None, level='info'):
    """Enhanced debug logging with traceback support
    
    Args:
        message (str): Message to log
        error (Exception, optional): Exception to log stacktrace
        level (str): Log level ('info', 'warning', 'error')
    """
    if error:
        logger.error(f"{message}: {str(error)}")
        import traceback
        logger.error(traceback.format_exc())
    elif level == 'warning':
        logger.warning(message)
    else:
        logger.info(message)

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", "your-secret-key-for-dev")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Make session available to templates
@app.context_processor
def inject_session():
    from flask import session
    return dict(session=session)

@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_date(date):
        if date:
            return date.strftime('%Y-%m-%d')
        return "Not specified"
        
    def format_currency(amount):
        if amount is None:
            return "Not specified"
        return f"{amount:.2f} DH"
        
    return dict(
        format_date=format_date,
        format_currency=format_currency
    )

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Create a list of endpoints that should be exempt from CSRF protection
csrf_exempt_endpoints = ['update_program_options']

# Configure CSRF exemption for specific endpoints
@app.before_request
def csrf_exempt_routes():
    from flask import request
    if request.endpoint in csrf_exempt_endpoints:
        csrf.exempt(request)
        
# Exempt public file routes from login requirements
@app.before_request
def public_routes_exempt():
    from flask import request
    # If the endpoint starts with 'public_excel', skip login check
    if request.endpoint and request.endpoint.startswith('public_excel.'):
        # This avoids the login redirect for routes in the public_excel blueprint
        return None

# Database configuration
db_url = os.environ.get("DATABASE_URL", 'sqlite:///project_estimation.db')

# Fix for PostgreSQL URLs from Heroku/render (if they start with postgres://, not postgresql://)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,  # recycle connections after 5 minutes
    "pool_pre_ping": True,  # verify connections before using them
    "pool_size": 10,  # maximum number of connections to keep persistently
    "max_overflow": 20,  # maximum number of connections to create above pool_size
}

# Upload folder configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Configure login manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Import models to ensure they're loaded before creating tables
from models import User, Project, ProjectHistory, Notification, HistoricalRate, BulkEstimateImport
from models import Discipline, Deliverable, EstimationInput, DeliverableUpload

# Initialize database tables
with app.app_context():
    db.create_all()
    
    # Create default admin user if it doesn't exist
    from models import User
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@estimatetracker.com',
            role='Admin',
            discipline='tools_admin',
            business_unit='BU1',
            working_title='System Administrator',
            is_admin=True
        )
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Default admin user created.")
    
    # Update all project progress values based on their status
    from models import Project
    try:
        projects = Project.query.all()
        updated_count = 0
        
        for project in projects:
            old_progress = project.progress_percentage
            new_progress = project.calculate_status_based_progress()
            
            # Only update if progress is different
            if abs(old_progress - new_progress) > 0.1:  # Small threshold to avoid floating point issues
                project.progress_percentage = new_progress
                updated_count += 1
        
        # Commit all changes at once
        if updated_count > 0:
            db.session.commit()
            app.logger.info(f"Successfully updated progress for {updated_count} projects")
        
    except Exception as e:
        app.logger.error(f"Error updating project progress: {str(e)}")

# Import and register blueprints
from routes.auth import auth_bp
from routes.projects import projects_bp
from routes.admin import admin_bp
from routes.reports import reports_bp
from routes.users import users_bp
from routes.api import api_bp
from routes.deliverables import deliverables_bp
from routes.excel_templates import excel_templates_bp
from routes.deliverable_lists import deliverable_lists_bp
from routes.standard_templates import standard_templates_bp
from routes.public_excel import public_excel_bp

app.register_blueprint(auth_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(users_bp)
app.register_blueprint(api_bp)
app.register_blueprint(deliverables_bp)
app.register_blueprint(excel_templates_bp)
app.register_blueprint(deliverable_lists_bp)
app.register_blueprint(standard_templates_bp)
app.register_blueprint(public_excel_bp)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register custom template filters
import json
@app.template_filter('fromjson')
def fromjson_filter(value):
    """Parse a JSON string and return a Python object"""
    if not value:
        return {}
    if isinstance(value, dict):
        return value  # Already decoded
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return {}

@app.template_filter('datetime')
def datetime_filter(value):
    """Format a datetime object to string"""
    if not value:
        return ''
    return value.strftime('%Y-%m-%d %H:%M')

@app.template_filter('basename')
def basename_filter(value):
    """Extract the base filename from a path"""
    if not value:
        return ''
    import os
    return os.path.basename(value)

# Global error handling for database transactions
from flask import request, g
from sqlalchemy.exc import SQLAlchemyError

@app.before_request
def before_request():
    """Setup for each request, ensure clean transaction state"""
    g.db_errors = False

@app.after_request
def after_request(response):
    """Clean up after each request"""
    # If we had a database error during the request
    if hasattr(g, 'db_errors') and g.db_errors:
        try:
            db.session.rollback()
            app.logger.info("Transaction rolled back due to errors")
        except Exception as e:
            app.logger.error(f"Error rolling back transaction: {e}")
    
    # If we have a 500 error, try to recover the database connection
    if response.status_code >= 500:
        try:
            db.session.rollback()
            app.logger.info("Transaction rolled back due to 500 error")
        except Exception as e:
            app.logger.error(f"Error rolling back transaction: {e}")
    
    return response

@app.errorhandler(SQLAlchemyError)
def handle_db_exception(error):
    """Handle database exceptions globally"""
    app.logger.error(f"Database error: {str(error)}")
    g.db_errors = True
    db.session.rollback()
    return "A database error occurred. Please try again later.", 500

# Import routes after app is initialized
from routes import *
