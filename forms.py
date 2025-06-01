from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms import SelectField, FloatField, DateField, HiddenField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError, NumberRange
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')
    
class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('', 'Select Role'),
        ('PM', 'Project Manager'),
        ('PE', 'Project Engineer'),
        ('Sales', 'Sales'),
        ('HOD', 'Head of Discipline'),
        ('E&D', 'Engineering & Design'),
        ('Admin', 'Administrator')
    ], validators=[DataRequired()])
    discipline = SelectField('Discipline', choices=[
        ('', 'Select Discipline'),
        ('process_sid', 'Process & SID'),
        ('civil_structure', 'Civil & Structure'),
        ('piping', 'Piping'),
        ('mechanical', 'Mechanical'),
        ('electrical', 'Electrical'),
        ('instrumentation_control', 'Instrumentation & Control'),
        ('digitalization', 'Digitalization'),
        ('engineering_management', 'Engineering Management'),
        ('environmental', 'Environmental'),
        ('tools_admin', 'Tools Admin'),
        ('construction', 'Construction'),
        ('none', 'None')
    ])
    business_unit = SelectField('Business Unit', choices=[
        ('', 'Select Business Unit'),
        ('BU1', 'Business Unit 1'),
        ('BU2', 'Business Unit 2'),
        ('BU3', 'Business Unit 3'),
        ('BU4', 'Business Unit 4'),
        ('none', 'None')
    ])
    working_title = StringField('Working Title', validators=[Length(max=100)])
    submit = SubmitField('Register')

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=100)])
    bp_code = StringField('BP Code', validators=[DataRequired(), Length(max=50)])
    wo_number = StringField('WO Number', validators=[DataRequired(), Length(max=50)])
    business_unit = SelectField('Business Unit', validators=[DataRequired()])
    program = SelectField('Program', validators=[Optional()])
    project_type = SelectField('Project Type', choices=[
        ('OCP', 'OCP'),
        ('Non-OCP', 'Non-OCP')
    ], validators=[DataRequired()])
    project_tic = StringField('Project TIC', validators=[Optional()])
    phase = SelectField('Project Phase', choices=[
        ('Identify', 'Identify (Phase 1)'),
        ('Evaluate', 'Evaluate (Phase 2)'),
        ('Define', 'Define (Phase 3)'),
        ('Design', 'Design (Phase 4)'),
        ('Build', 'Build (Phase 5)'),
        ('Commissioning', 'Commissioning and Handover (Phase 6)'),
        ('Asset Management', 'Asset Management (Phase 7)'),
        ('Other', 'Other (For special cases)')
    ], validators=[DataRequired()])
    
    custom_phase = StringField('Custom Phase Name', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Project Description', validators=[DataRequired()])
    duration = FloatField('Duration (months)', validators=[DataRequired()])
    planned_start_date = DateField('Planned Start Date', format='%Y-%m-%d', validators=[Optional()])
    planned_end_date = DateField('Planned End Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Required project documents
    func_heads_meeting_mom = FileField('Functional Heads Meeting MOM', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    bu_approval_to_bid = FileField('BU Approval to Bid', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    expression_of_needs = FileField('Expression of Needs Document', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    scope_of_work = FileField('Clear Scope of Work', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    execution_schedule = FileField('Schedule of Execution', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx'], 'Only PDF, Word, and Excel documents are allowed')
    ])
    execution_strategy = FileField('Work Execution Strategy', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    resource_mobilization = FileField('Resource Mobilization Strategy', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        # Populate business units from the centralized mapping
        from utils.business_units import get_all_business_units, get_all_programs
        business_units = get_all_business_units()
        
        self.business_unit.choices = [('', 'Select Business Unit')] + [(bu, bu) for bu in sorted(business_units)]
        
        # Get all programs for dropdown, regardless of selected BU
        all_programs = get_all_programs()
        self.program.choices = [('', 'Select Program (Optional)')] + [(p, p) for p in sorted(all_programs)]
    submit = SubmitField('Create Project')
    
    def validate_planned_end_date(self, planned_end_date):
        if self.planned_start_date.data and planned_end_date.data:
            if planned_end_date.data < self.planned_start_date.data:
                raise ValidationError('End date must be after start date')

class DocumentUploadForm(FlaskForm):
    """Form for uploading required project documents"""
    func_heads_meeting_mom = FileField('Functional Heads Meeting MOM', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    bu_approval_to_bid = FileField('BU Approval to Bid', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    expression_of_needs = FileField('Expression of Needs Document', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    scope_of_work = FileField('Clear Scope of Work', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    execution_schedule = FileField('Schedule of Execution', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx'], 'Only PDF, Word, and Excel documents are allowed')
    ])
    execution_strategy = FileField('Work Execution Strategy', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    resource_mobilization = FileField('Resource Mobilization Strategy', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    submit = SubmitField('Save Documents')


class EstimateForm(FlaskForm):
    process_sid_hours = FloatField('Process & SID Hours', default=0)
    civil_structure_hours = FloatField('Civil & Structure Hours', default=0)
    piping_hours = FloatField('Piping Hours', default=0)
    mechanical_hours = FloatField('Mechanical Hours', default=0)
    electrical_hours = FloatField('Electrical Hours', default=0)
    instrumentation_control_hours = FloatField('Instrumentation & Control Hours', default=0)
    digitalization_hours = FloatField('Digitalization Hours', default=0)
    engineering_management_hours = FloatField('Engineering Management Hours', default=0)
    environmental_hours = FloatField('Environmental Hours', default=0)
    tools_admin_hours = FloatField('Tools Admin Hours', default=0)
    construction_hours = FloatField('Construction Hours', default=0)
    
    # File upload fields for supporting documentation by discipline
    process_sid_files = FileField('Process & SID Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    civil_structure_files = FileField('Civil & Structure Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    piping_files = FileField('Piping Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    mechanical_files = FileField('Mechanical Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    electrical_files = FileField('Electrical Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    instrumentation_control_files = FileField('Instrumentation & Control Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    digitalization_files = FileField('Digitalization Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    engineering_management_files = FileField('Engineering Management Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    environmental_files = FileField('Environmental Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    tools_admin_files = FileField('Tools Admin Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    construction_files = FileField('Construction Documentation', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'Allowed file types: PDF, Word, Excel, Text')
    ])
    
    # Required project document fields
    func_heads_meeting_mom = FileField('Functional Heads Meeting MOM', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    bu_approval_to_bid = FileField('BU Approval to Bid', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    expression_of_needs = FileField('Expression of Needs Document', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    scope_of_work = FileField('Clear Scope of Work', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    execution_schedule = FileField('Schedule of Execution', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx'], 'Only PDF, Word, and Excel documents are allowed')
    ])
    execution_strategy = FileField('Work Execution Strategy', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    resource_mobilization = FileField('Resource Mobilization Strategy', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed')
    ])
    
    submit = SubmitField('Save Estimate')

class RevisionForm(FlaskForm):
    revision_reason = TextAreaField('Reason for Revision', validators=[DataRequired()])
    submit = SubmitField('Create Revision')

class ApprovalForm(FlaskForm):
    action = RadioField('Action', choices=[
        ('approve', 'Approve Project'),
        ('reject', 'Reject Project')
    ], validators=[DataRequired()])
    comments = TextAreaField('Comments')
    submit = SubmitField('Submit Decision')

class ProjectFilterForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('all', 'All'),
        ('Draft', 'Draft'),
        ('Pending Validation', 'Pending Validation'),
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Archived', 'Archived')
    ])
    business_unit = SelectField('Business Unit', choices=[('all', 'All')])
    program = SelectField('Program', choices=[('all', 'All')])
    project_type = SelectField('Project Type', choices=[
        ('all', 'All'),
        ('OCP', 'OCP'),
        ('Non-OCP', 'Non-OCP')
    ])
    search = StringField('Search', validators=[Optional()])
    start_date = DateField('From Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('To Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Filter')
    
    def __init__(self, *args, **kwargs):
        super(ProjectFilterForm, self).__init__(*args, **kwargs)
        # Use the centralized business units mapping
        from utils.business_units import get_all_business_units, get_all_programs
        business_units = get_all_business_units()
        all_programs = get_all_programs()
        
        self.business_unit.choices = [('all', 'All')] + [(bu, bu) for bu in sorted(business_units)]
        # Show all programs in the dropdown
        self.program.choices = [('all', 'All')] + [(p, p) for p in sorted(all_programs)]

class ProfileUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    working_title = StringField('Working Title', validators=[Length(max=100)])
    dashboard_theme = SelectField('Dashboard Theme', choices=[
        ('default', 'JESA Blue (Default)'),
        ('ocean', 'Ocean Blue'),
        ('emerald', 'Emerald Green'),
        ('sunset', 'Sunset Orange'),
        ('royal', 'Royal Purple'),
        ('charcoal', 'Charcoal Dark')
    ])
    profile_photo = FileField('Update Profile Photo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                    validators=[EqualTo('new_password')])
    submit = SubmitField('Update Profile')

class HourlyRateForm(FlaskForm):
    rate = FloatField('Hourly Rate (DH)', validators=[DataRequired()])
    effective_date = DateField('Effective Date', format='%Y-%m-%d', 
                              default=datetime.today, validators=[DataRequired()])
    submit = SubmitField('Set Rate')

class BulkImportForm(FlaskForm):
    file = FileField('CSV File', validators=[
        DataRequired(), 
        FileAllowed(['csv'], 'CSV files only!')
    ])
    submit = SubmitField('Upload')

class ReportForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('pdf', 'PDF Report'),
        ('ppt', 'PowerPoint Presentation')
    ], validators=[DataRequired()])
    include_charts = BooleanField('Include Charts', default=True)
    include_cost = BooleanField('Include Cost Information', default=True)
    include_messages = BooleanField('Include Important Messages', default=True)
    submit = SubmitField('Generate Report')
    
    
class ProjectRatingForm(FlaskForm):
    documentation_completeness = RadioField('Documentation Completeness', 
        choices=[(1, '1 - Poor'), (2, '2 - Needs Improvement'), (3, '3 - Adequate'), (4, '4 - Good'), (5, '5 - Excellent')],
        validators=[DataRequired()], coerce=int)
    documentation_clarity = RadioField('Documentation Clarity',
        choices=[(1, '1 - Poor'), (2, '2 - Needs Improvement'), (3, '3 - Adequate'), (4, '4 - Good'), (5, '5 - Excellent')],
        validators=[DataRequired()], coerce=int)
    documentation_quality = RadioField('Documentation Quality',
        choices=[(1, '1 - Poor'), (2, '2 - Needs Improvement'), (3, '3 - Adequate'), (4, '4 - Good'), (5, '5 - Excellent')],
        validators=[DataRequired()], coerce=int)
    scope_definition = RadioField('Scope Definition',
        choices=[(1, '1 - Poor'), (2, '2 - Needs Improvement'), (3, '3 - Adequate'), (4, '4 - Good'), (5, '5 - Excellent')],
        validators=[DataRequired()], coerce=int)
    overall_rating = RadioField('Overall Rating',
        choices=[(1, '1 - Poor'), (2, '2 - Needs Improvement'), (3, '3 - Adequate'), (4, '4 - Good'), (5, '5 - Excellent')],
        validators=[DataRequired()], coerce=int)
    comments = TextAreaField('Additional Comments')
    submit = SubmitField('Submit Rating')


class ReferenceRatioForm(FlaskForm):
    phase = SelectField('Project Phase', choices=[
        ('Identify', 'Identify (Phase 1)'),
        ('Evaluate', 'Evaluate (Phase 2)'),
        ('Define', 'Define (Phase 3)'),
        ('Design', 'Design (Phase 4)'),
        ('Build', 'Build (Phase 5)'),
        ('Commissioning', 'Commissioning and Handover (Phase 6)'),
        ('Asset Management', 'Asset Management (Phase 7)'),
        ('Other', 'Other (For special cases)')
    ], validators=[DataRequired()])
    low_ratio = FloatField('Low Ratio (as decimal, e.g. 0.02 for 2%)', 
                           validators=[DataRequired(), NumberRange(min=0, max=1)])
    avg_ratio = FloatField('Average Ratio (as decimal, e.g. 0.03 for 3%)', 
                           validators=[DataRequired(), NumberRange(min=0, max=1)])
    high_ratio = FloatField('High Ratio (as decimal, e.g. 0.05 for 5%)', 
                            validators=[DataRequired(), NumberRange(min=0, max=1)])
    description = TextAreaField('Description/Notes')
    submit = SubmitField('Save Reference Ratio')
    
    def validate_high_ratio(self, high_ratio):
        if self.low_ratio.data is not None and self.avg_ratio.data is not None and self.low_ratio.data > self.avg_ratio.data:
            raise ValidationError("Low ratio must be less than or equal to average ratio")
        if self.avg_ratio.data is not None and high_ratio.data is not None and self.avg_ratio.data > high_ratio.data:
            raise ValidationError("Average ratio must be less than or equal to high ratio")


class DisciplineReferenceRatioForm(FlaskForm):
    discipline = SelectField('Discipline', choices=[
        ('Process & SID', 'Process & SID'),
        ('Civil & Structure', 'Civil & Structure'),
        ('Piping', 'Piping'),
        ('Mechanical', 'Mechanical'),
        ('Electrical', 'Electrical'),
        ('Instrumentation & Control', 'Instrumentation & Control'),
        ('Digitalization', 'Digitalization'),
        ('Engineering Management', 'Engineering Management'),
        ('Environmental', 'Environmental'),
        ('Tools Admin', 'Tools Admin'),
        ('Construction', 'Construction'),
    ], validators=[DataRequired()])
    low_ratio = FloatField('Low Ratio (as decimal)', 
                           validators=[DataRequired(), NumberRange(min=0, max=1)])
    avg_ratio = FloatField('Average Ratio (as decimal)', 
                           validators=[DataRequired(), NumberRange(min=0, max=1)])
    high_ratio = FloatField('High Ratio (as decimal)', 
                            validators=[DataRequired(), NumberRange(min=0, max=1)])
    submit = SubmitField('Save Discipline Ratio')

class HourlyRateForm(FlaskForm):
    """Form for creating and editing hourly rates"""
    name = StringField('Rate Name', validators=[DataRequired(), Length(max=100)])
    rate = FloatField('Rate (DH)', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description')
    is_default = BooleanField('Set as Default Rate')
    submit = SubmitField('Save Hourly Rate')

class SystemSettingForm(FlaskForm):
    """Form for managing system settings"""
    setting_key = StringField('Setting Key', validators=[DataRequired(), Length(max=100)])
    setting_value = TextAreaField('Setting Value', validators=[Optional()])
    setting_type = SelectField('Setting Type', choices=[
        ('string', 'Text'),
        ('int', 'Integer'),
        ('float', 'Decimal'),
        ('bool', 'Boolean'),
        ('json', 'JSON')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Setting')

class ProjectMessageForm(FlaskForm):
    """Form for project chat messages"""
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=1000)])
    is_important = BooleanField('Mark as Important for Reports', default=False)
    submit = SubmitField('Send Message')


class ProjectAssumptionForm(FlaskForm):
    """Form for project assumptions"""
    assumption_text = TextAreaField('Assumption', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Save Assumption')


class RequestPasswordResetForm(FlaskForm):
    """Form for requesting a password reset"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    """Form for resetting a password"""
    password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')
