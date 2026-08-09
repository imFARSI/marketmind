# Competitor Management

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Competitor, Business

competitors_bp = Blueprint('salman_competitors', __name__, url_prefix='/salman/competitors')

def get_user_business():
    """Helper to retrieve or create current user's business context."""
    business = Business.query.filter_by(owner_id=current_user.id).first()
    if not business:
        business = Business(name=f"{current_user.username}'s Business", industry="General", owner_id=current_user.id)
        db.session.add(business)
        db.session.commit()
    return business

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
    #ADDING COMPETITORS
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
