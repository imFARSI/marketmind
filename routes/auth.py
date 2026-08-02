from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Business
import secrets
import re

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('home.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Strict Email Format Validation on Login
        if not email or not re.match(EMAIL_REGEX, email):
            flash('Please enter a valid email address (e.g. name@company.com).', 'danger')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with this email address.', 'danger')
            return redirect(url_for('auth.login'))
        elif user.password != password:
            flash('Incorrect password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        else:
            login_user(user)
            if user.role == 'Field Agent':
                return redirect(url_for('salman_field_tasks.my_tasks'))
            return redirect(url_for('auth.dashboard'))
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        account_type = request.form.get('account_type', 'owner') # 'owner' or 'agent'
        join_code = request.form.get('join_code', '').strip().upper()

        # Strict Email Format Validation on Register
        if not email or not re.match(EMAIL_REGEX, email):
            flash('Please enter a valid email address (e.g. name@company.com).', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email address is already registered.', 'warning')
            return redirect(url_for('auth.register'))

        if account_type == 'agent':
            # Field Agent Registration with Business Join Code
            target_business = Business.query.filter_by(join_code=join_code).first()
            if not target_business:
                flash('Invalid Business Join Code. Please check with your business owner.', 'danger')
                return redirect(url_for('auth.register'))

            new_user = User(
                username=username,
                email=email,
                password=password,
                role='Field Agent',
                business_id=target_business.id
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            flash(f'Successfully joined {target_business.name} as a Field Agent!', 'success')
            return redirect(url_for('salman_field_tasks.my_tasks'))
        else:
            # Business Owner Registration
            new_user = User(
                username=username,
                email=email,
                password=password,
                role='Business Owner'
            )
            db.session.add(new_user)
            db.session.commit()

            # Generate clean Business Join Code (e.g. BIZ8842)
            code = f"BIZ{secrets.randbelow(8999) + 1000}"
            default_business = Business(
                name=f"{username}'s Enterprise",
                industry="General",
                join_code=code,
                owner_id=new_user.id
            )
            db.session.add(default_business)
            db.session.commit()

            new_user.business_id = default_business.id
            db.session.commit()

            login_user(new_user)
            flash(f'Business workspace created! Your Business Join Code is {code}', 'success')
            return redirect(url_for('auth.dashboard'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.index'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'Field Agent':
        return redirect(url_for('salman_field_tasks.my_tasks'))
    
    business = Business.query.filter_by(owner_id=current_user.id).first()
    return render_template('auth/dashboard.html', business=business)
