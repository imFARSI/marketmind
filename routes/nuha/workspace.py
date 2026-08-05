# ==============================================================================
# NUHA — Feature 1: Workspace Configuration
# ==============================================================================

import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Business

workspace_bp = Blueprint('nuha_workspace', __name__, url_prefix='/nuha/workspace')

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

@workspace_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Only Business Owners are authorized to view or configure the workspace
    if current_user.role not in ['Business Owner', 'Business User']:
        flash('Access denied. Only Business Owners can access Workspace Configuration.', 'danger')
        return redirect(url_for('auth.dashboard'))

    business = current_user.user_business
    if not business:
        flash('No workspace found associated with your account.', 'warning')
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        industry = request.form.get('industry', '').strip()
        niche = request.form.get('niche', '').strip()
        contact_email = request.form.get('contact_email', '').strip().lower()
        company_size = request.form.get('company_size', '').strip()
        founded_year = request.form.get('founded_year', '').strip()
        headquarters = request.form.get('headquarters', '').strip()
        description = request.form.get('description', '').strip()

        # Validation
        if not name:
            flash('Workspace / Business Name is required.', 'danger')
        elif not industry:
            flash('Industry is required.', 'danger')
        elif contact_email and not re.match(EMAIL_REGEX, contact_email):
            flash('Please enter a valid business contact email address.', 'danger')
        else:
            # Update database attributes
            business.name = name
            business.industry = industry
            business.niche = niche
            business.contact_email = contact_email
            business.company_size = company_size
            business.founded_year = founded_year
            business.headquarters = headquarters
            business.description = description

            db.session.commit()
            flash('Workspace settings updated successfully!', 'success')
            return redirect(url_for('nuha_workspace.index'))

    # Count enrolled field agents linked to this business workspace
    agent_count = User.query.filter_by(business_id=business.id).filter(User.id != current_user.id).count()

    return render_template(
        'nuha/workspace.html', 
        business=business, 
        agent_count=agent_count
    )

