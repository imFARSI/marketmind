# ==============================================================================
# NUHA — Feature 1: Workspace Configuration
# ==============================================================================

import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
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

# ==============================================================================
# RESTful JSON APIs
# ==============================================================================

@workspace_bp.route('/api/details', methods=['GET'])
@login_required
def api_details():
    """REST API: Returns current business workspace profile data as JSON."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No workspace found.'}), 404

    agent_count = User.query.filter_by(business_id=business.id).filter(User.id != current_user.id).count()

    return jsonify({
        'status': 'success',
        'business': {
            'id': business.id,
            'name': business.name,
            'industry': business.industry,
            'niche': business.niche,
            'contact_email': business.contact_email,
            'company_size': business.company_size,
            'founded_year': business.founded_year,
            'headquarters': business.headquarters,
            'description': business.description,
            'join_code': business.join_code,
            'owner_id': business.owner_id,
            'created_at': business.created_at.isoformat() if business.created_at else None
        },
        'agent_count': agent_count
    })

@workspace_bp.route('/api/update', methods=['POST', 'PUT'])
@login_required
def api_update():
    """REST API: Accepts JSON payload or form data to update business workspace attributes."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No workspace found.'}), 404

    payload = request.get_json(silent=True) or request.form

    name = payload.get('name', business.name)
    if name is not None:
        name = str(name).strip()
    else:
        name = business.name

    industry = payload.get('industry', business.industry)
    if industry is not None:
        industry = str(industry).strip()
    else:
        industry = business.industry

    niche = payload.get('niche', business.niche)
    if niche is not None:
        niche = str(niche).strip()

    contact_email = payload.get('contact_email', business.contact_email)
    if contact_email is not None:
        contact_email = str(contact_email).strip().lower()

    company_size = payload.get('company_size', business.company_size)
    if company_size is not None:
        company_size = str(company_size).strip()

    founded_year = payload.get('founded_year', business.founded_year)
    if founded_year is not None:
        founded_year = str(founded_year).strip()

    headquarters = payload.get('headquarters', business.headquarters)
    if headquarters is not None:
        headquarters = str(headquarters).strip()

    description = payload.get('description', business.description)
    if description is not None:
        description = str(description).strip()

    if not name:
        return jsonify({'status': 'error', 'message': 'Workspace / Business Name is required.'}), 400
    if not industry:
        return jsonify({'status': 'error', 'message': 'Industry is required.'}), 400
    if contact_email and not re.match(EMAIL_REGEX, contact_email):
        return jsonify({'status': 'error', 'message': 'Please enter a valid business contact email address.'}), 400

    business.name = name
    business.industry = industry
    business.niche = niche
    business.contact_email = contact_email
    business.company_size = company_size
    business.founded_year = founded_year
    business.headquarters = headquarters
    business.description = description

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Workspace updated successfully',
        'business': {
            'id': business.id,
            'name': business.name,
            'industry': business.industry,
            'niche': business.niche,
            'contact_email': business.contact_email,
            'company_size': business.company_size,
            'founded_year': business.founded_year,
            'headquarters': business.headquarters,
            'description': business.description,
            'join_code': business.join_code,
            'owner_id': business.owner_id
        }
    })


