from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import json
import secrets
from time import time
import jwt
import os

# User model for authentication and authorization
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    discipline = db.Column(db.String(50))  # Engineering discipline
    role = db.Column(db.String(50))  # PM, PE, Sales, etc.
    business_unit = db.Column(db.String(50))  # Business Unit
    profile_photo = db.Column(db.String(255))  # Path to profile photo
    working_title = db.Column(db.String(100))  # Position/title
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # User preferences
    dashboard_theme = db.Column(db.String(50), default='default')  # Dashboard color theme preference
    
    # User attributes
    # Note: points and level attributes have been removed
    
    # Relationships
    projects_created = db.relationship('Project', backref='creator', lazy=True,
                                      foreign_keys='Project.created_by')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    project_ratings = db.relationship('ProjectRating', backref='rater', lazy=True)
    
    def is_ed_team(self):
        """Check if user is part of the E&D team or is a HOD"""
        return self.role == 'E&D' or self.role == 'HOD'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=3600):
        """Generate a password reset token valid for 1 hour"""
        payload = {
            'reset_password': self.id,
            'exp': time() + expires_in
        }
        # Use app secret key to sign the token
        return jwt.encode(
            payload, 
            os.environ.get('SECRET_KEY', 'dev-key-for-password-reset'),
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        """Verify a password reset token and return the associated user"""
        try:
            payload = jwt.decode(
                token,
                os.environ.get('SECRET_KEY', 'dev-key-for-password-reset'),
                algorithms=['HS256']
            )
            user_id = payload['reset_password']
        except Exception:
            return None
        return User.query.get(user_id)
    
    def has_discipline_access(self, discipline_field):
        # Admins have access to all disciplines
        if self.is_admin:
            return True
        
        # E&D role has access to all disciplines
        if self.role == 'E&D':
            return True
        
        # Engineering management can have multiple users
        if discipline_field == 'engineering_management_hours' and self.discipline == 'engineering_management':
            return True
        
        # Mapping form fields to discipline names
        discipline_map = {
            'process_sid_hours': 'process_sid',
            'civil_structure_hours': 'civil_structure',
            'piping_hours': 'piping',
            'mechanical_hours': 'mechanical',
            'electrical_hours': 'electrical',
            'instrumentation_control_hours': 'instrumentation_control',
            'digitalization_hours': 'digitalization',
            'engineering_management_hours': 'engineering_management',
            'environmental_hours': 'environmental',
            'tools_admin_hours': 'tools_admin',
            'construction_hours': 'construction',
        }
        
        # HODs can only access their specific discipline
        if discipline_field in discipline_map:
            if self.discipline == discipline_map[discipline_field]:
                return True
        
        return False

# Project model for storing project information and estimates
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    archived = db.Column(db.Boolean, default=False)
    archive_date = db.Column(db.DateTime, nullable=True)
    bp_code = db.Column(db.String(50), nullable=False)  # Budget Code
    wo_number = db.Column(db.String(50), nullable=False)  # Work Order
    business_unit = db.Column(db.String(100))  # Business Unit: Global phosphates, Water & Environment, etc.
    program = db.Column(db.String(100), nullable=True)  # Program: SP2M, Jorf & Safi Programs, etc.
    project_type = db.Column(db.String(10))  # OCP or Non-OCP
    project_tic = db.Column(db.String(50))  # Project TIC
    phase = db.Column(db.String(50))  # Phase subject of the estimate
    custom_phase = db.Column(db.String(100), nullable=True)  # Custom phase name when phase='Other'
    description = db.Column(db.Text)
    duration = db.Column(db.Float, default=1.0)  # Duration in months
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Draft')  # Draft, Pending Validation, Approved, Submitted, Rejected
    approval_date = db.Column(db.DateTime, nullable=True)
    submission_date = db.Column(db.DateTime, nullable=True)
    
    # Required project documents for validation
    func_heads_meeting_mom = db.Column(db.Text, default='[]')  # Functional heads meeting MOM
    bu_approval_to_bid = db.Column(db.Text, default='[]')  # BU Approval to bid
    expression_of_needs = db.Column(db.Text, default='[]')  # Expression of needs document
    scope_of_work = db.Column(db.Text, default='[]')  # Clear scope of work
    execution_schedule = db.Column(db.Text, default='[]')  # Schedule of execution
    execution_strategy = db.Column(db.Text, default='[]')  # Work execution strategy
    resource_mobilization = db.Column(db.Text, default='[]')  # Resource mobilization strategy
    
    # Additional timestamp for validation request
    validation_request_date = db.Column(db.DateTime, nullable=True)  # When submitted for validation
    
    # Revision tracking
    revision_number = db.Column(db.Integer, default=0)  # Changé de 1 à 0 (projets originaux = rev 0)
    is_revision = db.Column(db.Boolean, default=False)
    parent_project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    revisions = db.relationship('Project', backref=db.backref('parent_project', remote_side=[id]), lazy=True)
    revision_reason = db.Column(db.Text, nullable=True)
    
    # Hours by discipline
    process_sid_hours = db.Column(db.Float, default=0)
    civil_structure_hours = db.Column(db.Float, default=0)
    piping_hours = db.Column(db.Float, default=0)
    mechanical_hours = db.Column(db.Float, default=0)
    electrical_hours = db.Column(db.Float, default=0)
    instrumentation_control_hours = db.Column(db.Float, default=0)
    digitalization_hours = db.Column(db.Float, default=0)
    engineering_management_hours = db.Column(db.Float, default=0)
    environmental_hours = db.Column(db.Float, default=0)
    tools_admin_hours = db.Column(db.Float, default=0)
    construction_hours = db.Column(db.Float, default=0)
    
    # Backup files for hours estimates
    process_sid_files = db.Column(db.Text, default='[]')  # JSON array of filenames
    process_sid_files_date = db.Column(db.String(30), nullable=True)  # Last upload date
    civil_structure_files = db.Column(db.Text, default='[]')
    civil_structure_files_date = db.Column(db.String(30), nullable=True)
    piping_files = db.Column(db.Text, default='[]')
    piping_files_date = db.Column(db.String(30), nullable=True)
    mechanical_files = db.Column(db.Text, default='[]')
    mechanical_files_date = db.Column(db.String(30), nullable=True)
    electrical_files = db.Column(db.Text, default='[]')
    electrical_files_date = db.Column(db.String(30), nullable=True)
    instrumentation_control_files = db.Column(db.Text, default='[]')
    instrumentation_control_files_date = db.Column(db.String(30), nullable=True)
    digitalization_files = db.Column(db.Text, default='[]')
    digitalization_files_date = db.Column(db.String(30), nullable=True)
    engineering_management_files = db.Column(db.Text, default='[]')
    engineering_management_files_date = db.Column(db.String(30), nullable=True)
    environmental_files = db.Column(db.Text, default='[]')
    environmental_files_date = db.Column(db.String(30), nullable=True)
    tools_admin_files = db.Column(db.Text, default='[]')
    tools_admin_files_date = db.Column(db.String(30), nullable=True)
    construction_files = db.Column(db.Text, default='[]')
    construction_files_date = db.Column(db.String(30), nullable=True)
    
    # Estimate flags
    estimate_submitted = db.Column(db.Boolean, default=False)
    
    # Timeline tracking
    planned_start_date = db.Column(db.DateTime, nullable=True)
    planned_end_date = db.Column(db.DateTime, nullable=True)
    actual_start_date = db.Column(db.DateTime, nullable=True)
    actual_end_date = db.Column(db.DateTime, nullable=True)
    progress_percentage = db.Column(db.Float, default=0)  # 0-100
    
    # Change history
    history = db.relationship('ProjectHistory', backref='project', lazy=True, cascade="all, delete-orphan")
    
    def get_hourly_rate(self):
        """Get the current hourly rate from the latest historical rate"""
        latest_rate = HistoricalRate.query.order_by(HistoricalRate.effective_date.desc()).first()
        return latest_rate.rate if latest_rate else 500  # Default to 500 DH if no rate is set
    
    def calculate_estimated_cost(self):
        """Calculate total estimated cost based on hours and rate"""
        total_hours = sum([
            self.process_sid_hours, self.civil_structure_hours,
            self.piping_hours, self.mechanical_hours,
            self.electrical_hours, self.instrumentation_control_hours,
            self.digitalization_hours, self.engineering_management_hours,
            self.environmental_hours, self.tools_admin_hours,
            self.construction_hours
        ])
        return total_hours * self.get_hourly_rate()
    
    def get_phase_ratio(self):
        """Get ratio based on project phase"""
        # Try to get from database first
        from app import db
        
        # Check if ReferenceRatio exists in database
        ratio = None
        try:
            # Use db.session instead of raw connection
            reference_ratio = db.session.query(ReferenceRatio).filter_by(
                phase=self.phase,
                is_active=True
            ).first()
            
            if reference_ratio:
                ratio = {
                    'low': reference_ratio.low_ratio,
                    'avg': reference_ratio.avg_ratio,
                    'high': reference_ratio.high_ratio
                }
        except Exception as e:
            import logging
            logging.error(f"Error getting phase ratio from database: {str(e)}")
        
        # If not found in database, use default hardcoded values
        if not ratio:
            default_ratios = {
                'Identify': {'low': 0.002, 'avg': 0.003, 'high': 0.005},  # 0.20%, 0.30%, 0.50%
                'Evaluate': {'low': 0.008, 'avg': 0.01, 'high': 0.015},   # 0.80%, 1.00%, 1.50%
                'Define': {'low': 0.02, 'avg': 0.03, 'high': 0.05},       # 2.00%, 3.00%, 5.00%
                'Design': {'low': 0.10, 'avg': 0.17, 'high': 0.23},       # 10.00%, 17.00%, 23.00%
                'Build': {'low': 0.04, 'avg': 0.05, 'high': 0.07},        # 4.00%, 5.00%, 7.00%
                'Commissioning': {'low': 0.03, 'avg': 0.04, 'high': 0.06}, # 3.00%, 4.00%, 6.00%
                'Asset Management': {'low': 0.01, 'avg': 0.015, 'high': 0.025} # 1.00%, 1.50%, 2.50%
            }
            
            # For the "Other" phase, use default ratios
            default = {'low': 0.02, 'avg': 0.03, 'high': 0.05}  # Default to Define phase ratios
            ratio = default_ratios.get(self.phase, default)
            
        return ratio
    
    def calculate_reference_interval(self):
        """Calculate reference hours interval based on TIC and phase"""
        try:
            # Use TIC value directly without multiplying by 1000
            tic_value = float(self.project_tic or 1)  # Use 1 as default if TIC not set
            ratios = self.get_phase_ratio()
            return {
                'low': tic_value * ratios['low'],
                'avg': tic_value * ratios['avg'],
                'high': tic_value * ratios['high'],
                'tic_not_set': not self.project_tic
            }
        except (ValueError, TypeError):
            return {'low': 0, 'avg': 0, 'high': 0, 'tic_not_set': True}
    
    def calculate_discipline_reference_intervals(self):
        """Calculate reference hours intervals for each discipline based on TIC, phase, and discipline ratios"""
        try:
            # Get the standard phase ratios first
            phase_ratios = self.get_phase_ratio()
            
            # Calculate base TIC value - use directly without multiplying by 1000
            try:
                tic_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', self.project_tic or '0')))
            except ValueError:
                tic_value = 0
            
            # Calculate the reference hours (TIC × Ratio Phase)
            reference_hours = {
                'low': tic_value * phase_ratios['low'],
                'avg': tic_value * phase_ratios['avg'],
                'high': tic_value * phase_ratios['high']
            }
            
            # Dictionary to store reference intervals by discipline
            discipline_intervals = {}
            
            # Default disciplines list
            disciplines = [
                'Process & SID',
                'Civil & Structure',
                'Piping',
                'Mechanical',
                'Electrical',
                'Instrumentation & Control',
                'Digitalization',
                'Engineering Management',
                'Environmental',
                'Tools Admin',
                'Construction'
            ]
            
            # Get discipline ratios from database if available
            discipline_ratios = {}
            
            # If TIC is set and phase ratios exist
            if tic_value > 0 and self.phase:
                # Get discipline ratios from database
                try:
                    from app import db
                    
                    # First, get the reference ratio ID for this phase
                    reference_ratio_query = db.session.query(ReferenceRatio).filter_by(
                        phase=self.phase,
                        is_active=True
                    ).first()
                    
                    if reference_ratio_query:
                        # Now get the discipline ratios for this reference ratio
                        discipline_ratio_query = db.session.query(DisciplineReferenceRatio).filter_by(
                            reference_ratio_id=reference_ratio_query.id
                        ).all()
                        
                        # Store discipline-specific ratios
                        for dr in discipline_ratio_query:
                            discipline_ratios[dr.discipline] = {
                                'low': dr.low_ratio,
                                'avg': dr.avg_ratio,
                                'high': dr.high_ratio
                            }
                except Exception as e:
                    import logging
                    logging.error(f"Database error getting discipline ratios: {str(e)}")
            
            # Calculate reference interval for each discipline
            for discipline in disciplines:
                if discipline in discipline_ratios:
                    # Formula: Reference Range = Reference Hours * Ratio Discipline
                    dr = discipline_ratios[discipline]
                    discipline_intervals[discipline] = {
                        'low': reference_hours['low'] * dr['low'],
                        'avg': reference_hours['avg'] * dr['avg'],
                        'high': reference_hours['high'] * dr['high']
                    }
                else:
                    # Use reference hours directly if no discipline-specific ratio
                    discipline_intervals[discipline] = {
                        'low': reference_hours['low'],
                        'avg': reference_hours['avg'],
                        'high': reference_hours['high']
                    }
            
            # Add tic_not_set flag
            discipline_intervals['tic_not_set'] = not self.project_tic
            
            return discipline_intervals
        except Exception as e:
            import logging
            logging.error(f"Error calculating discipline reference intervals: {str(e)}")
            # Return default values with tic_not_set flag
            return {'tic_not_set': True}
    
    def calculate_progress(self):
        """Calculate project progress based on timeline"""
        if self.status == 'Completed':
            return 100
        
        if not self.planned_start_date or not self.planned_end_date:
            return self.progress_percentage
        
        if datetime.utcnow() < self.planned_start_date:
            return 0
        
        if datetime.utcnow() > self.planned_end_date:
            return 100
        
        total_days = (self.planned_end_date - self.planned_start_date).days
        days_passed = (datetime.utcnow() - self.planned_start_date).days
        
        if total_days <= 0:
            return 0
        
        return min(100, (days_passed / total_days) * 100)
        
    def calculate_status_based_progress(self):
        """Calculate progress based on project status"""
        if self.status == 'Completed':
            return 100
        elif self.status == 'Submitted':  # Final submission to PM
            return 75
        elif self.status == 'Approved':   # Admin approved the project
            return 50
        elif self.status == 'Pending Validation':  # Awaiting admin review
            return 30
        elif self.status == 'Draft' and self.estimate_submitted:
            return 25
        elif self.status == 'Draft':  # Initial state
            return 10
        elif self.status == 'Rejected':
            return 15  # Slightly more than initial draft
        else:
            return self.progress_percentage
    
    def get_hour_distribution(self):
        """Get hours distribution across disciplines"""
        return {
            'Process & SID': self.process_sid_hours,
            'Civil & Structure': self.civil_structure_hours,
            'Piping': self.piping_hours,
            'Mechanical': self.mechanical_hours,
            'Electrical': self.electrical_hours,
            'Instrumentation & Control': self.instrumentation_control_hours,
            'Digitalization': self.digitalization_hours,
            'Engineering Management': self.engineering_management_hours,
            'Environmental': self.environmental_hours,
            'Tools Admin': self.tools_admin_hours,
            'Construction': self.construction_hours
        }
    
    def get_total_hours(self):
        """Calculate total estimated hours"""
        return sum(self.get_hour_distribution().values())
    
    def calculate_reference_hours(self):
        """Calculate reference hours based on TIC value and project phase"""
        # Calculate using TIC directly (no multiplication by 1000)
        # Extract numeric value from project_tic field (which might contain currency symbols or formatting)
        try:
            tic_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', self.project_tic or '0')))
        except ValueError:
            tic_value = 0
            
        # Use TIC value directly
        base_hours = tic_value if tic_value > 0 else 0
        
        # Define phase ratios (these can be adjusted based on organizational standards)
        phase_ratios = {
            'Conceptual Design': {'low': 0.05, 'avg': 0.1, 'high': 0.15},
            'FEED': {'low': 0.15, 'avg': 0.25, 'high': 0.35},
            'Detailed Engineering': {'low': 0.35, 'avg': 0.50, 'high': 0.65},
            'Procurement Support': {'low': 0.05, 'avg': 0.1, 'high': 0.15},
            'Construction Support': {'low': 0.05, 'avg': 0.1, 'high': 0.15},
            'Commissioning': {'low': 0.05, 'avg': 0.1, 'high': 0.15},
            'As-Built': {'low': 0.05, 'avg': 0.1, 'high': 0.15},
            'Study': {'low': 0.05, 'avg': 0.1, 'high': 0.15},
        }
        
        # Get ratios for the current phase, default to FEED if not found
        current_phase = self.phase or 'FEED'
        ratios = phase_ratios.get(current_phase, phase_ratios['FEED'])
        
        # Calculate reference hours
        return {
            'low': base_hours * ratios['low'],
            'avg': base_hours * ratios['avg'],
            'high': base_hours * ratios['high']
        }
        
    def get_discipline_files(self, discipline):
        """Get files for a specific discipline"""
        import json
        file_field = f"{discipline.lower().replace(' & ', '_').replace(' ', '_')}_files"
        if hasattr(self, file_field):
            try:
                return json.loads(getattr(self, file_field))
            except (ValueError, TypeError):
                return []
        return []
        
    def get_document_files(self, field):
        """Get document files from a specified field"""
        import json
        if hasattr(self, field):
            try:
                return json.loads(getattr(self, field))
            except (ValueError, TypeError):
                return []
        return []
        
    def add_discipline_file(self, discipline, filename):
        """Add a file to a specific discipline"""
        import json
        from datetime import datetime
        
        field_name = f"{discipline.lower().replace(' & ', '_').replace(' ', '_')}_files"
        date_field = f"{discipline.lower().replace(' & ', '_').replace(' ', '_')}_files_date"
        
        if hasattr(self, field_name):
            try:
                files = json.loads(getattr(self, field_name))
            except (ValueError, TypeError):
                files = []
            
            if filename not in files:
                files.append(filename)
                setattr(self, field_name, json.dumps(files))
                
                # Update the file upload date
                current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
                setattr(self, date_field, current_date)
                
                return True
        return False
        
    def get_file_upload_date(self, discipline):
        """Get the date when files were last uploaded for a discipline"""
        date_field = f"{discipline.lower().replace(' & ', '_').replace(' ', '_')}_files_date"
        if hasattr(self, date_field):
            return getattr(self, date_field)
        return None
        
    def remove_discipline_file(self, discipline, filename):
        """Remove a file from a specific discipline"""
        import json
        field_name = f"{discipline.lower().replace(' & ', '_').replace(' ', '_')}_files"
        if hasattr(self, field_name):
            try:
                files = json.loads(getattr(self, field_name))
                if filename in files:
                    files.remove(filename)
                    setattr(self, field_name, json.dumps(files))
                    return True
            except (ValueError, TypeError):
                pass
        return False
        
    @classmethod
    def get_business_units(cls):
        """Get all unique business units"""
        return [bu[0] for bu in cls.query.with_entities(cls.business_unit).distinct().all() if bu[0]]
    
    @classmethod
    def get_programs(cls, business_unit=None):
        """Get all programs, optionally filtered by business unit"""
        if business_unit and business_unit != 'all':
            return [p[0] for p in cls.query.filter_by(business_unit=business_unit)
                   .with_entities(cls.program).distinct().all() if p[0]]
        return [p[0] for p in cls.query.with_entities(cls.program).distinct().all() if p[0]]
    
    @classmethod
    def filter_projects(cls, status='all', business_unit='all', program='all', 
                        search_term=None, start_date=None, end_date=None, 
                        archived=False, user_id=None):
        """Filter projects based on various criteria"""
        query = cls.query.filter_by(archived=archived)
        
        # Apply status filter
        if status and status != 'all':
            query = query.filter(cls.status == status)
        
        # Apply business unit filter
        if business_unit and business_unit != 'all':
            query = query.filter(cls.business_unit == business_unit)
        
        # Apply program filter
        if program and program != 'all':
            query = query.filter(cls.program == program)
        
        # Apply search term filter
        if search_term:
            search = f"%{search_term}%"
            query = query.filter(
                db.or_(
                    cls.title.ilike(search),
                    cls.bp_code.ilike(search),
                    cls.wo_number.ilike(search)
                )
            )
        
        # Apply date range filter
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            # Add one day to include the end date fully
            end_date_plus_one = end_date + timedelta(days=1)
            query = query.filter(cls.created_at < end_date_plus_one)
        
        # Filter by user if specified
        if user_id:
            query = query.filter(cls.created_by == user_id)
        
        return query.order_by(cls.created_at.desc())

# Project history tracking
class ProjectHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50))  # Created, Updated, Approved, etc.
    details = db.Column(db.Text)  # JSON string with changed fields
    
    user = db.relationship('User', backref='actions')

# System settings configuration
class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), nullable=False, unique=True)
    setting_value = db.Column(db.Text, nullable=True)
    setting_type = db.Column(db.String(50), default='string')  # string, int, float, bool, json
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_value(cls, key, default=None):
        """Get a setting value by key"""
        setting = cls.query.filter_by(setting_key=key).first()
        if not setting:
            return default
        
        # Convert value based on type
        if setting.setting_type == 'int':
            try:
                return int(setting.setting_value)
            except (ValueError, TypeError):
                return default
        elif setting.setting_type == 'float':
            try:
                return float(setting.setting_value)
            except (ValueError, TypeError):
                return default
        elif setting.setting_type == 'bool':
            return setting.setting_value.lower() in ('true', 'yes', '1', 'on')
        elif setting.setting_type == 'json':
            try:
                return json.loads(setting.setting_value)
            except (json.JSONDecodeError, TypeError):
                return default
        else:  # string or unknown type
            return setting.setting_value
    
    @classmethod
    def set_value(cls, key, value, setting_type='string', description=None):
        """Set a setting value"""
        # Convert value to string based on type
        if setting_type == 'json' and not isinstance(value, str):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
        
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value_str
            setting.updated_at = datetime.utcnow()
            if description:
                setting.description = description
        else:
            setting = cls(
                setting_key=key,
                setting_value=value_str,
                setting_type=setting_type,
                description=description or f"Setting for {key}"
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting

# Historical hourly rates
class HistoricalRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.Float, nullable=False)  # Rate in DH
    effective_date = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User')

# Notifications for users
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, warning, error, success
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    related_project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    
    related_project = db.relationship('Project')
    
    @classmethod
    def cleanup_old(cls):
        """Remove notifications older than 30 days"""
        cutoff = datetime.utcnow() - timedelta(days=30)
        cls.query.filter(cls.timestamp < cutoff).delete()
        db.session.commit()

# Business Unit and Program relationship
class BusinessUnitProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_unit = db.Column(db.String(100), nullable=False)
    program = db.Column(db.String(100), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('business_unit', 'program', name='uix_business_unit_program'),
    )
    
    @classmethod
    def get_programs_by_business_unit(cls, business_unit):
        """Get all programs for a given business unit"""
        if not business_unit or business_unit == 'all':
            return cls.query.with_entities(cls.program).distinct().all()
        return cls.query.filter_by(business_unit=business_unit).all()
    
    def __repr__(self):
        return f'<BusinessUnitProgram {self.business_unit} - {self.program}>'

# Bulk estimate import for CSV uploads
class BulkEstimateImport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Processing')  # Processing, Completed, Failed
    
    user = db.relationship('User')

# Achievement model has been removed

# UserAchievement model has been removed


# Project Clarity Rating model
class ProjectRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    documentation_completeness = db.Column(db.Integer, nullable=False)  # 1-5 rating
    documentation_clarity = db.Column(db.Integer, nullable=False)       # 1-5 rating
    documentation_quality = db.Column(db.Integer, nullable=False)       # 1-5 rating
    scope_definition = db.Column(db.Integer, nullable=False)            # 1-5 rating
    overall_rating = db.Column(db.Integer, nullable=False)              # 1-5 rating
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Establish relationship with Project
    project = db.relationship('Project', backref=db.backref('ratings', lazy=True))
    
    def __repr__(self):
        return f'<ProjectRating project_id={self.project_id} - rater_id={self.rater_id} - overall={self.overall_rating}>'


# Reference hour ratios for project phases
class ReferenceRatio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phase = db.Column(db.String(50), nullable=False)  # Identify, Evaluate, Define, etc.
    low_ratio = db.Column(db.Float, nullable=False)   # Low reference ratio
    avg_ratio = db.Column(db.Float, nullable=False)   # Average reference ratio
    high_ratio = db.Column(db.Float, nullable=False)  # High reference ratio
    description = db.Column(db.Text)                  # Optional description of this ratio
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)   # Is this ratio currently active
    
    # Relationship to user who created it
    creator = db.relationship('User')
    
    # Discipline-specific reference ratios
    discipline_ratios = db.relationship('DisciplineReferenceRatio', backref='phase_ratio', 
                                       cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('phase', 'is_active', name='uix_phase_active'),
    )
    
    def __repr__(self):
        return f'<ReferenceRatio phase={self.phase} - low={self.low_ratio} - avg={self.avg_ratio} - high={self.high_ratio}>'


# Discipline-specific reference hour ratios
class DisciplineReferenceRatio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_ratio_id = db.Column(db.Integer, db.ForeignKey('reference_ratio.id'), nullable=False)
    discipline = db.Column(db.String(50), nullable=False)  # Process & SID, Civil & Structure, etc.
    low_ratio = db.Column(db.Float, nullable=False)   # Low reference ratio for this discipline
    avg_ratio = db.Column(db.Float, nullable=False)   # Average reference ratio for this discipline
    high_ratio = db.Column(db.Float, nullable=False)  # High reference ratio for this discipline
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('reference_ratio_id', 'discipline', name='uix_ratio_discipline'),
    )
    
    def __repr__(self):
        return f'<DisciplineReferenceRatio discipline={self.discipline} - low={self.low_ratio} - avg={self.avg_ratio} - high={self.high_ratio}>'

# Hourly rate model for cost calculations
class HourlyRate(db.Model):
    """Model for hourly rates used in cost calculations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Float, nullable=False)  # Rate in Moroccan Dirham (DH)
    description = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HourlyRate {self.name}: {self.rate} DH>'


class ProjectMessage(db.Model):
    """Model for chat messages related to a project"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_important = db.Column(db.Boolean, default=False)  # Flag for messages to include in reports
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('messages', lazy=True, cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    
    def __repr__(self):
        return f'<ProjectMessage {self.id} from user {self.user_id}>'


class ProjectAssumption(db.Model):
    """Model for project assumptions added by users"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assumption_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('assumptions', lazy=True, cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('assumptions', lazy=True))
    
    def __repr__(self):
        return f'<ProjectAssumption {self.id} by user {self.user_id}>'

# Deliverables Estimation Module Models
class Discipline(db.Model):
    """Discipline model for storing engineering disciplines"""
    __tablename__ = 'discipline'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - only keep the EstimationInput relationship
    estimation_inputs = db.relationship('EstimationInput', backref='discipline', lazy=True)
    
    def __repr__(self):
        return f'<Discipline {self.name}>'

class Deliverable(db.Model):
    """Deliverable model for storing project deliverables"""
    __tablename__ = 'deliverable'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    phase = db.Column(db.String(100))
    discipline = db.Column(db.String(100))  # Store discipline name instead of ID
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    estimation_inputs = db.relationship('EstimationInput', backref='deliverable', lazy=True)
    
    def __repr__(self):
        return f'<Deliverable {self.name}>'

class EstimationInput(db.Model):
    """EstimationInput model for storing project-specific deliverable estimates"""
    __tablename__ = 'estimation_input'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    deliverable_id = db.Column(db.Integer, db.ForeignKey('deliverable.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    norm_hours = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('estimation_inputs', lazy=True, cascade="all, delete-orphan"))
    user = db.relationship('User', foreign_keys=[created_by], backref='estimation_inputs')
    
    def __repr__(self):
        return f'<EstimationInput Project:{self.project_id} Deliverable:{self.deliverable_id}>'

# Excel Template model defined below with DeliverableUpload

class ExcelTemplate(db.Model):
    """Excel template model for storing discipline-specific Excel templates"""
    __tablename__ = 'excel_template'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    discipline = db.Column(db.String(100), nullable=False)  # Store discipline name
    phase = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.Integer, default=1)  # Template version number
    
    # Relationships
    user = db.relationship('User', foreign_keys=[created_by], backref='excel_templates')
    
    def __repr__(self):
        return f'<ExcelTemplate {self.name} ({self.discipline}/{self.phase}) v{self.version}>'
        
    def is_user_authorized(self, user):
        """Check if user is authorized to manage this template"""
        # Only Admin and HHO users can manage templates
        return user.is_admin or user.role == 'HHO'


class DeliverableUpload(db.Model):
    """DeliverableUpload model for tracking deliverable file uploads"""
    __tablename__ = 'deliverable_upload'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=True)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)  # Project is now required
    discipline = db.Column(db.String(100), nullable=False)  # Discipline is now required
    phase = db.Column(db.String(100), nullable=False)  # Store project phase
    is_estimate_sheet = db.Column(db.Boolean, default=False)  # Flag for estimate sheets
    template_id = db.Column(db.Integer, db.ForeignKey('excel_template.id'), nullable=True)
    version = db.Column(db.Integer, default=1)  # Version of this estimate file
    
    # Relationships
    user = db.relationship('User', foreign_keys=[uploaded_by], backref='deliverable_uploads')
    project = db.relationship('Project', backref='deliverable_uploads', lazy=True)
    template = db.relationship('ExcelTemplate', backref='generated_files', lazy=True)
    
    def __repr__(self):
        return f'<DeliverableUpload {self.filename} v{self.version}>'
        
    def is_user_authorized(self, user):
        """Check if user is authorized to access this file"""
        # Admins and HHO can access any file
        if user.is_admin or user.role == 'HHO':
            return True
            
        # Users can access their own uploads
        if self.uploaded_by == user.id:
            return True
            
        # Users can access files for their discipline
        if self.discipline == user.discipline:
            return True
            
        return False


class DeliverableList(db.Model):
    """Model for tracking project deliverable lists"""
    __tablename__ = 'deliverable_list'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    discipline = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('deliverable_upload.id'), nullable=True)
    status = db.Column(db.String(50), default='Draft')  # Draft, In Progress, Completed, Approved
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completion_percentage = db.Column(db.Float, default=0.0)  # 0-100% completion
    estimated_hours = db.Column(db.Float, default=0.0)  # Total hours estimated
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('deliverable_lists', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', foreign_keys=[created_by], backref='deliverable_lists')
    file = db.relationship('DeliverableUpload', backref='deliverable_list', uselist=False)
    
    def __repr__(self):
        return f'<DeliverableList {self.name} - {self.discipline} - {self.status}>'
        
    def is_user_authorized(self, user):
        """Check if user can manage this deliverable list"""
        # Admins and HHO users can manage any list
        if user.is_admin or user.role == 'HHO':
            return True
            
        # Users can manage lists they created
        if self.created_by == user.id:
            return True
            
        # Users can manage lists for their discipline
        if self.discipline == user.discipline:
            return True
            
        return False


class DeliverableListItem(db.Model):
    """Model for tracking individual deliverables within a deliverable list"""
    __tablename__ = 'deliverable_list_item'
    
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('deliverable_list.id'), nullable=False)
    deliverable_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deliverable_type = db.Column(db.String(100), nullable=True)  # Drawing, Report, etc.
    estimated_hours = db.Column(db.Float, default=0.0)
    complexity = db.Column(db.String(50), default='Medium')  # Low, Medium, High
    status = db.Column(db.String(50), default='Not Started')  # Not Started, In Progress, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_template_item = db.Column(db.Boolean, default=False)  # Whether this is a standard template item
    sequence = db.Column(db.Integer, default=0)  # Order in the list
    
    # Relationships
    deliverable_list = db.relationship('DeliverableList', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<DeliverableListItem {self.deliverable_name} - {self.status}>'


class StandardDeliverableTemplate(db.Model):
    """Model for standard deliverable templates for different disciplines and phases"""
    __tablename__ = 'standard_deliverable_template'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    discipline = db.Column(db.String(100), nullable=False)
    phase = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[created_by], backref='standard_templates')
    
    def __repr__(self):
        return f'<StandardDeliverableTemplate {self.name} ({self.discipline}/{self.phase})>'
        
    @staticmethod
    def get_templates_for_discipline_phase(discipline, phase):
        """Get all active standard templates for a specific discipline and phase"""
        return StandardDeliverableTemplate.query.filter_by(
            discipline=discipline,
            phase=phase,
            is_active=True
        ).all()


class StandardDeliverableItem(db.Model):
    """Model for standard deliverable items in a template"""
    __tablename__ = 'standard_deliverable_item'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('standard_deliverable_template.id'), nullable=False)
    deliverable_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deliverable_type = db.Column(db.String(100), nullable=True)  # Drawing, Report, etc.
    estimated_hours = db.Column(db.Float, default=0.0)
    complexity = db.Column(db.String(50), default='Medium')  # Low, Medium, High
    sequence = db.Column(db.Integer, default=0)  # Order in the template
    
    # Relationships
    template = db.relationship('StandardDeliverableTemplate', 
                              backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<StandardDeliverableItem {self.deliverable_name} ({self.deliverable_type})>'
