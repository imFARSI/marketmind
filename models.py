from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ==============================================================================
# DATABASE MODELS (Shared schema for Modules 1, 2, and 3)
# ==============================================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='Business Owner') # 'Business Owner' or 'Field Agent'
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def user_business(self):
        b_id = getattr(self, 'business_id', None)
        if b_id:
            return Business.query.get(b_id)
        return Business.query.filter_by(owner_id=self.id).first()

class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(80), nullable=False)
    company_size = db.Column(db.String(50))
    founded_year = db.Column(db.String(10))
    headquarters = db.Column(db.String(150))
    description = db.Column(db.Text)
    niche = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    join_code = db.Column(db.String(20), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Competitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(80), nullable=False)
    website = db.Column(db.String(200))
    location = db.Column(db.String(150))
    description = db.Column(db.Text)
    search_visibility_score = db.Column(db.Float, default=0.0)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Price(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    source = db.Column(db.String(50), default='Manual')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    old_amount = db.Column(db.Float)
    new_amount = db.Column(db.Float, nullable=False)
    changed_by_source = db.Column(db.String(50))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class FieldTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    status = db.Column(db.String(30), default='Assigned')
    onsite_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TaskLocationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('field_task.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255))
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

class TodoNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default='Pending') # Pending, In Progress, Completed
    type = db.Column(db.String(30), default='Task') # Task, Reminder, Note
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(100))
    url = db.Column(db.String(500))
    summary = db.Column(db.Text)
    published_at = db.Column(db.DateTime)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'))
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)

class AiAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'))
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    report_type = db.Column(db.String(30), default='PDF')
    file_path = db.Column(db.String(255))
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CompanionMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_proactive = db.Column(db.Boolean, default=False)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    date_time = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(120), default='Online Meeting')
    agenda = db.Column(db.Text)
    status = db.Column(db.String(20), default='Scheduled') # 'Scheduled', 'In Progress', 'Ended'
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), default='General') # Marketing, Operations, Payroll, Software, Sales, General
    type = db.Column(db.String(20), default='Expense') # 'Expense' vs 'Revenue'
    amount = db.Column(db.Float, nullable=False, default=0.0)
    month = db.Column(db.String(10), nullable=False, default='Jan') # Jan, Feb, Mar, etc.
    year = db.Column(db.Integer, nullable=False, default=2026)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
