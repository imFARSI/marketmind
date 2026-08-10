# Competitor Management (HTML Routes + RESTful JSON APIs)

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Competitor, Business

competitors_bp = Blueprint('salman_competitors', __name__, url_prefix='/salman/competitors')

def get_user_business():
    """Helper to retrieve or create current user's business context."""
    user_id = current_user.id if (current_user and current_user.is_authenticated) else 1
    username = current_user.username if (current_user and current_user.is_authenticated) else "farsi"

    business = Business.query.filter_by(owner_id=user_id).first()
    if not business:
        business = Business(name=f"{username}'s Business", industry="General", owner_id=user_id)
        db.session.add(business)
        db.session.commit()
    return business

# ==============================================================================
# HTML WEB PAGE ROUTES (Server-Side Jinja2 Rendering)
# ==============================================================================

@competitors_bp.route('/')
@login_required
def index():
    business = get_user_business()
    search_query = request.args.get('search', '').strip()
    selected_industry = request.args.get('industry', '').strip()

    query = Competitor.query.filter_by(business_id=business.id)

    if search_query:
        query = query.filter(Competitor.name.ilike(f"%{search_query}%"))
    if selected_industry:
        query = query.filter_by(industry=selected_industry)

    competitors = query.order_by(Competitor.created_at.desc()).all()
    
    # Get distinct list of industries for filtering dropdown
    all_industries = db.session.query(Competitor.industry).filter_by(business_id=business.id).distinct().all()
    industries_list = [i[0] for i in all_industries if i[0]]

    return render_template(
        'salman/competitors.html',
        competitors=competitors,
        total_count=len(competitors),
        search_query=search_query,
        selected_industry=selected_industry,
        industries=industries_list
    )

@competitors_bp.route('/add', methods=['POST'])
@login_required
def add_competitor():
    business = get_user_business()
    name = request.form.get('name', '').strip()
    industry = request.form.get('industry', '').strip()
    website = request.form.get('website', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not industry:
        flash('Competitor name and industry are required.', 'danger')
        return redirect(url_for('salman_competitors.index'))

    # Auto-format website URL if missing http/https
    if website and not (website.startswith('http://') or website.startswith('https://')):
        website = f"https://{website}"

    new_competitor = Competitor(
        name=name,
        industry=industry,
        website=website,
        location=location,
        description=description,
        search_visibility_score=85.0, # Default visibility score
        business_id=business.id
    )

    db.session.add(new_competitor)
    db.session.commit()

    flash(f'Competitor "{name}" added successfully!', 'success')
    return redirect(url_for('salman_competitors.index'))

@competitors_bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_competitor(id):
    business = get_user_business()
    competitor = Competitor.query.filter_by(id=id, business_id=business.id).first_or_404()

    competitor.name = request.form.get('name', '').strip()
    competitor.industry = request.form.get('industry', '').strip()
    website = request.form.get('website', '').strip()
    if website and not (website.startswith('http://') or website.startswith('https://')):
        website = f"https://{website}"
    competitor.website = website
    competitor.location = request.form.get('location', '').strip()
    competitor.description = request.form.get('description', '').strip()

    db.session.commit()
    flash(f'Competitor "{competitor.name}" updated successfully!', 'success')
    return redirect(url_for('salman_competitors.index'))

@competitors_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_competitor(id):
    business = get_user_business()
    competitor = Competitor.query.filter_by(id=id, business_id=business.id).first_or_404()
    name = competitor.name

    db.session.delete(competitor)
    db.session.commit()

    flash(f'Competitor "{name}" deleted.', 'info')
    return redirect(url_for('salman_competitors.index'))

# ==============================================================================
# RESTFUL JSON API ENDPOINTS (Postman & Asynchronous JSON API Calls)
# ==============================================================================

@competitors_bp.route('/api/list', methods=['GET'])
def api_list_competitors():
    """REST API: Returns JSON array of user's competitors."""
    business = get_user_business()
    search_query = request.args.get('search', '').strip()
    selected_industry = request.args.get('industry', '').strip()

    query = Competitor.query.filter_by(business_id=business.id)
    if search_query:
        query = query.filter(Competitor.name.ilike(f"%{search_query}%"))
    if selected_industry:
        query = query.filter_by(industry=selected_industry)

    competitors = query.order_by(Competitor.created_at.desc()).all()

    data = [{
        'id': c.id,
        'name': c.name,
        'industry': c.industry,
        'website': c.website,
        'location': c.location,
        'description': c.description,
        'search_visibility_score': c.search_visibility_score,
        'created_at': c.created_at.isoformat() if c.created_at else None
    } for c in competitors]

    return jsonify({'status': 'success', 'count': len(data), 'competitors': data})

@competitors_bp.route('/api/add', methods=['POST'])
def api_add_competitor():
    """REST API: Accepts JSON payload or Form data to add a competitor."""
    business = get_user_business()
    payload = request.get_json(silent=True) or request.form

    name = payload.get('name', '').strip()
    industry = payload.get('industry', '').strip()
    website = payload.get('website', '').strip()
    location = payload.get('location', '').strip()
    description = payload.get('description', '').strip()

    if not name or not industry:
        return jsonify({'status': 'error', 'message': 'Competitor name and industry are required.'}), 400

    if website and not (website.startswith('http://') or website.startswith('https://')):
        website = f"https://{website}"

    new_competitor = Competitor(
        name=name,
        industry=industry,
        website=website,
        location=location,
        description=description,
        search_visibility_score=85.0,
        business_id=business.id
    )

    db.session.add(new_competitor)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Competitor "{name}" created successfully.',
        'competitor': {
            'id': new_competitor.id,
            'name': new_competitor.name,
            'industry': new_competitor.industry,
            'website': new_competitor.website,
            'location': new_competitor.location,
            'description': new_competitor.description
        }
    }), 201

@competitors_bp.route('/api/edit/<int:id>', methods=['POST', 'PUT'])
def api_edit_competitor(id):
    """REST API: Accepts JSON payload or Form data to update a competitor."""
    business = get_user_business()
    competitor = Competitor.query.filter_by(id=id, business_id=business.id).first()
    if not competitor:
        return jsonify({'status': 'error', 'message': 'Competitor not found.'}), 404

    payload = request.get_json(silent=True) or request.form

    competitor.name = payload.get('name', competitor.name).strip()
    competitor.industry = payload.get('industry', competitor.industry).strip()
    website = payload.get('website', competitor.website).strip()
    if website and not (website.startswith('http://') or website.startswith('https://')):
        website = f"https://{website}"
    competitor.website = website
    competitor.location = payload.get('location', competitor.location).strip()
    competitor.description = payload.get('description', competitor.description).strip()

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Competitor "{competitor.name}" updated successfully.',
        'competitor': {
            'id': competitor.id,
            'name': competitor.name,
            'industry': competitor.industry,
            'website': competitor.website,
            'location': competitor.location,
            'description': competitor.description
        }
    })

@competitors_bp.route('/api/delete/<int:id>', methods=['POST', 'DELETE'])
def api_delete_competitor(id):
    """REST API: Deletes a competitor and returns JSON status."""
    business = get_user_business()
    competitor = Competitor.query.filter_by(id=id, business_id=business.id).first()
    if not competitor:
        return jsonify({'status': 'error', 'message': 'Competitor not found.'}), 404

    name = competitor.name
    db.session.delete(competitor)
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Competitor "{name}" deleted successfully.'})
