# ==============================================================================
# NUHA — Feature 2: Competitor & Industry News Monitoring (NewsAPI)
# ==============================================================================

import os
import requests
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from models import db, NewsArticle, Competitor

news_bp = Blueprint('nuha_news', __name__, url_prefix='/nuha/news')

NEWS_API_KEY = os.getenv('NEWS_API_KEY') or '185e4dc47faf438c8f6d70be51b2dc7e'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

def fetch_and_save_news(query, business_id, competitor_id=None, page_size=12):
    """
    Helper function that calls the NewsAPI, clears old articles of the same type,
    and saves the new ones to the database.
    """
    if not NEWS_API_KEY:
        return False, "NEWS_API_KEY is missing from .env"

    try:
        params = {
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': page_size,
            'apiKey': NEWS_API_KEY
        }
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        data = response.json()

        if data.get('status') == 'ok':
            articles_data = data.get('articles', [])
            
            # Clear existing articles for this specific category (industry vs specific competitor)
            if competitor_id:
                NewsArticle.query.filter_by(business_id=business_id, competitor_id=competitor_id).delete()
            else:
                NewsArticle.query.filter_by(business_id=business_id, competitor_id=None).delete()
            
            # Save new articles
            for art in articles_data:
                # NewsAPI returns 'publishedAt' as ISO 8601 string, e.g., '2023-10-01T12:00:00Z'
                pub_date = None
                if art.get('publishedAt'):
                    try:
                        # Attempt to parse the date, fallback to now if it fails
                        pub_str = art.get('publishedAt').replace('Z', '+00:00')
                        pub_date = datetime.fromisoformat(pub_str)
                    except ValueError:
                        pub_date = datetime.utcnow()
                else:
                    pub_date = datetime.utcnow()
                
                new_article = NewsArticle(
                    title=art.get('title', 'No Title')[:255],
                    source=art.get('source', {}).get('name', 'Unknown')[:100],
                    url=art.get('url', '')[:500],
                    summary=art.get('description', ''),
                    published_at=pub_date,
                    competitor_id=competitor_id,
                    business_id=business_id
                )
                db.session.add(new_article)
            
            db.session.commit()
            return True, f"Successfully fetched and cached {len(articles_data)} articles."
        else:
            error_msg = data.get('message', 'Unknown API Error')
            return False, f"API Error: {error_msg}"
    except Exception as e:
        return False, f"Request Error: {str(e)}"

@news_bp.route('/')
@login_required
def index():
    if current_user.role not in ['Business Owner', 'Business User']:
        flash('Access denied. Only Business Owners can access News Monitoring.', 'danger')
        return redirect(url_for('auth.dashboard'))

    business = current_user.user_business
    if not business:
        flash('No business workspace found. Please configure your workspace first.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    # Load all cached industry news
    industry_articles = NewsArticle.query.filter_by(business_id=business.id, competitor_id=None).order_by(NewsArticle.published_at.desc()).all()
    
    # Load all cached competitor news
    competitor_articles = NewsArticle.query.filter(NewsArticle.business_id == business.id, NewsArticle.competitor_id != None).order_by(NewsArticle.published_at.desc()).all()
    
    # Load list of competitors for the dropdown selector
    competitors = Competitor.query.filter_by(business_id=business.id).all()

    # Get active tab from URL (defaults to industry)
    active_tab = request.args.get('tab', 'industry')

    return render_template(
        'nuha/news.html',
        business=business,
        industry_articles=industry_articles,
        competitor_articles=competitor_articles,
        competitors=competitors,
        active_tab=active_tab
    )

@news_bp.route('/fetch', methods=['POST'])
@login_required
def fetch():
    if current_user.role not in ['Business Owner', 'Business User']:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.dashboard'))

    business = current_user.user_business
    if not business:
        flash('No business workspace found.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    category = request.form.get('category')
    
    if category == 'industry':
        # Build query for industry news
        industry = business.industry or ''
        niche = business.niche or ''
        query = f"{niche} {industry}".strip()
        if not query:
            query = "business" # Fallback if they haven't configured their workspace
            
        success, msg = fetch_and_save_news(query, business.id, competitor_id=None)
        if success:
            flash(msg, 'success')
        else:
            flash(msg, 'danger')
            
    elif category == 'competitor':
        competitor_id = request.form.get('competitor_id')
        if not competitor_id:
            flash('Please select a competitor to fetch news for.', 'warning')
            return redirect(url_for('nuha_news.index'))
            
        competitor = Competitor.query.filter_by(id=competitor_id, business_id=business.id).first()
        if not competitor:
            flash('Competitor not found.', 'danger')
            return redirect(url_for('nuha_news.index'))
            
        query = competitor.name
        success, msg = fetch_and_save_news(query, business.id, competitor_id=competitor.id)
        if success:
            flash(msg, 'success')
        else:
            flash(msg, 'danger')
    
    else:
        flash('Invalid category selected.', 'danger')
        category = 'industry' # fallback

    return redirect(url_for('nuha_news.index', tab=category))

# ==============================================================================
# RESTful JSON APIs
# ==============================================================================

@news_bp.route('/api/articles', methods=['GET'])
@login_required
def api_articles():
    """REST API: Returns JSON array of cached news articles for the user's business workspace."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    industry_articles = NewsArticle.query.filter_by(business_id=business.id, competitor_id=None).order_by(NewsArticle.published_at.desc()).all()
    competitor_articles = NewsArticle.query.filter(NewsArticle.business_id == business.id, NewsArticle.competitor_id != None).order_by(NewsArticle.published_at.desc()).all()

    industry_data = [{
        'id': a.id,
        'title': a.title,
        'source': a.source,
        'url': a.url,
        'summary': a.summary,
        'published_at': a.published_at.isoformat() if a.published_at else None,
        'competitor_id': a.competitor_id
    } for a in industry_articles]

    competitor_data = [{
        'id': a.id,
        'title': a.title,
        'source': a.source,
        'url': a.url,
        'summary': a.summary,
        'published_at': a.published_at.isoformat() if a.published_at else None,
        'competitor_id': a.competitor_id
    } for a in competitor_articles]

    all_articles = industry_data + competitor_data

    return jsonify({
        'status': 'success',
        'count': len(all_articles),
        'industry_articles': industry_data,
        'competitor_articles': competitor_data,
        'articles': all_articles
    })

@news_bp.route('/api/fetch', methods=['POST'])
@login_required
def api_fetch():
    """REST API: Accepts JSON payload or Form data to fetch latest news via NewsAPI and update cache."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    payload = request.get_json(silent=True) or request.form
    category = payload.get('category')

    if category == 'industry':
        industry = business.industry or ''
        niche = business.niche or ''
        query = f"{niche} {industry}".strip()
        if not query:
            query = "business"

        success, msg = fetch_and_save_news(query, business.id, competitor_id=None)
        if success:
            count = NewsArticle.query.filter_by(business_id=business.id, competitor_id=None).count()
            return jsonify({
                'status': 'success',
                'message': msg,
                'articles_count': count
            })
        else:
            return jsonify({'status': 'error', 'message': msg}), 400

    elif category == 'competitor':
        competitor_id = payload.get('competitor_id')
        if not competitor_id:
            return jsonify({'status': 'error', 'message': 'Please select a competitor to fetch news for.'}), 400

        competitor = Competitor.query.filter_by(id=competitor_id, business_id=business.id).first()
        if not competitor:
            return jsonify({'status': 'error', 'message': 'Competitor not found.'}), 404

        query = competitor.name
        success, msg = fetch_and_save_news(query, business.id, competitor_id=competitor.id)
        if success:
            count = NewsArticle.query.filter_by(business_id=business.id, competitor_id=competitor.id).count()
            return jsonify({
                'status': 'success',
                'message': msg,
                'articles_count': count
            })
        else:
            return jsonify({'status': 'error', 'message': msg}), 400
    else:
        return jsonify({'status': 'error', 'message': 'Invalid category selected. Use "industry" or "competitor".'}), 400

