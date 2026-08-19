# ==============================================================================
# NUHA — Feature 4: Strategic Recommendation Report (SWOT & PESTEL + Marketing)
# ==============================================================================

import os
import requests
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from models import db, AiAnalysis, Report, Competitor, Product

strategic_bp = Blueprint('nuha_strategic', __name__, url_prefix='/nuha/strategic')

GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-1.5-pro"
]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_gemini_api(prompt):
    """
    Calls Google Gemini API to generate strategic recommendations.
    Tries stable Gemini endpoints (1.5-flash, 2.0-flash, etc.).
    Returns generated content string or None if unconfigured/failed.
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    for model_name in GEMINI_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', '').strip()
        except Exception:
            continue
    return None


GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound-mini",
    "qwen/qwen3.6-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]


def clean_ai_markdown(text):
    """Strips internal thought tags from reasoning models if present."""
    if not text:
        return ""
    import re
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    return cleaned


def call_groq_api(prompt):
    """
    Calls Groq Cloud API for AI strategic reports.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return None

    for model in GROQ_MODELS:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are MarketMind Strategic AI, an expert business analyst specializing in SWOT analysis, PESTEL frameworks, competitive market positioning, and strategic growth marketing for small businesses."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2048
            }
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                content = data['choices'][0]['message']['content'].strip()
                return clean_ai_markdown(content)
        except Exception:
            continue
    return None


@strategic_bp.route('/')
@login_required
def index():
    """Main view: Lists saved strategic reports and provides generator controls."""
    if current_user.role not in ['Business Owner', 'Business User']:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.dashboard'))

    business = current_user.user_business
    if not business:
        flash('No business workspace found. Please configure your workspace first.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    # Fetch stored strategic reports
    saved_reports = AiAnalysis.query.filter_by(
        business_id=business.id,
        analysis_type='STRATEGIC_REPORT'
    ).order_by(AiAnalysis.created_at.desc()).all()

    # Fetch competitors for context
    competitors = Competitor.query.filter_by(business_id=business.id).all()

    return render_template(
        'nuha/strategic.html',
        business=business,
        competitors=competitors,
        saved_reports=saved_reports
    )


@strategic_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Form route: Generates a new Strategic Recommendation Report via Gemini AI."""
    if current_user.role not in ['Business Owner', 'Business User']:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.dashboard'))

    business = current_user.user_business
    if not business:
        flash('Please configure your business workspace first.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    focus_area = request.form.get('focus_area', 'Comprehensive Growth Strategy').strip()
    competitors = Competitor.query.filter_by(business_id=business.id).all()
    comp_summary = "\n".join([f"- {c.name} ({c.industry}): {c.description or 'No desc'} (Visibility Score: {c.search_visibility_score})" for c in competitors])

    prompt = f"""
You are MarketMind Strategic AI. Generate a comprehensive, executive Strategic Recommendation Report for the following business:

**Business Name:** {business.name}
**Industry:** {business.industry}
**Niche:** {business.niche or 'General'}
**Company Size:** {business.company_size or 'Small Business'}
**Description:** {business.description or 'N/A'}

**Tracked Competitors:**
{comp_summary or 'No specific competitors registered yet.'}

**Strategic Focus Requested:** {focus_area}

Please output a beautifully structured Markdown report with:
1. Executive Summary
2. Detailed SWOT Analysis (Strengths, Weaknesses, Opportunities, Threats) tailored to competing against the listed competitors.
3. PESTEL Analysis (Political, Economic, Social, Technological, Environmental, Legal factors impacting this industry).
4. Strategic Marketing Recommendations & Actionable Steps (High Priority, Medium Term, Defensive Positioning).
"""

    # 1. Try Gemini API
    ai_content = call_gemini_api(prompt)

    # 2. Try Groq Cloud API
    if not ai_content:
        ai_content = call_groq_api(prompt)

    if not ai_content:
        flash('Failed to generate report. Please ensure your Gemini or Groq API key is valid.', 'danger')
        return redirect(url_for('nuha_strategic.index'))

    # Save to AiAnalysis model
    analysis = AiAnalysis(
        analysis_type='STRATEGIC_REPORT',
        content=ai_content,
        business_id=business.id
    )
    db.session.add(analysis)

    # Also save to Report model for standard reporting records
    report_record = Report(
        title=f"Strategic Report - {focus_area} ({datetime.utcnow().strftime('%b %d')})",
        report_type='SWOT & PESTEL',
        file_path='',
        business_id=business.id
    )
    db.session.add(report_record)

    db.session.commit()

    flash('Strategic Recommendation Report generated successfully!', 'success')
    return redirect(url_for('nuha_strategic.index'))


@strategic_bp.route('/view/<int:analysis_id>')
@login_required
def view_report(analysis_id):
    """View details of a specific saved strategic report."""
    analysis = AiAnalysis.query.get_or_404(analysis_id)
    business = current_user.user_business

    if not business or analysis.business_id != business.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('nuha_strategic.index'))

    return jsonify({
        'status': 'success',
        'id': analysis.id,
        'analysis_type': analysis.analysis_type,
        'content': analysis.content,
        'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })


@strategic_bp.route('/delete/<int:analysis_id>', methods=['POST'])
@login_required
def delete(analysis_id):
    """Deletes a saved strategic report."""
    analysis = AiAnalysis.query.get_or_404(analysis_id)
    business = current_user.user_business

    if not business or analysis.business_id != business.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('nuha_strategic.index'))

    db.session.delete(analysis)
    db.session.commit()

    flash('Strategic report deleted successfully.', 'success')
    return redirect(url_for('nuha_strategic.index'))


# ==============================================================================
# RESTful JSON APIs (Module 3 Integration & Grading)
# ==============================================================================

@strategic_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    """REST API: Returns JSON array of saved strategic recommendation reports."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    reports = AiAnalysis.query.filter_by(
        business_id=business.id,
        analysis_type='STRATEGIC_REPORT'
    ).order_by(AiAnalysis.created_at.desc()).all()

    data = [{
        'id': r.id,
        'analysis_type': r.analysis_type,
        'content': r.content,
        'created_at': r.created_at.isoformat() if r.created_at else None
    } for r in reports]

    return jsonify({
        'status': 'success',
        'count': len(data),
        'reports': data
    })


@strategic_bp.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    """REST API: Triggers strategic report generation via JSON request."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    payload = request.get_json(silent=True) or request.form
    focus_area = payload.get('focus_area', 'Comprehensive Growth Strategy')

    competitors = Competitor.query.filter_by(business_id=business.id).all()
    comp_summary = "\n".join([f"- {c.name} ({c.industry}): {c.description or 'No desc'}" for c in competitors])

    prompt = f"""
Generate an executive Strategic Recommendation Report (SWOT, PESTEL, and Marketing Strategy) for:
Business: {business.name} ({business.industry}, Niche: {business.niche or 'General'})
Description: {business.description or 'N/A'}
Competitors: {comp_summary or 'General market rivals'}
Focus Area: {focus_area}
"""

    ai_content = call_gemini_api(prompt) or call_groq_api(prompt)
    if not ai_content:
        return jsonify({'status': 'error', 'message': 'AI report generation failed. Ensure your Gemini or Groq API key is configured and valid.'}), 502

    analysis = AiAnalysis(
        analysis_type='STRATEGIC_REPORT',
        content=ai_content,
        business_id=business.id
    )
    db.session.add(analysis)

    report_record = Report(
        title=f"Strategic Report - {focus_area}",
        report_type='SWOT & PESTEL',
        file_path='',
        business_id=business.id
    )
    db.session.add(report_record)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Strategic report generated successfully.',
        'report': {
            'id': analysis.id,
            'analysis_type': analysis.analysis_type,
            'content': analysis.content,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None
        }
    }), 201


@strategic_bp.route('/api/get/<int:analysis_id>', methods=['GET'])
@login_required
def api_get(analysis_id):
    """REST API: Returns JSON details of a single report."""
    analysis = AiAnalysis.query.get(analysis_id)
    if not analysis:
        return jsonify({'status': 'error', 'message': 'Report not found.'}), 404

    business = current_user.user_business
    if not business or analysis.business_id != business.id:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    return jsonify({
        'status': 'success',
        'report': {
            'id': analysis.id,
            'analysis_type': analysis.analysis_type,
            'content': analysis.content,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None
        }
    })


@strategic_bp.route('/api/delete/<int:analysis_id>', methods=['POST', 'DELETE'])
@login_required
def api_delete(analysis_id):
    """REST API: Deletes a strategic report."""
    analysis = AiAnalysis.query.get(analysis_id)
    if not analysis:
        return jsonify({'status': 'error', 'message': 'Report not found.'}), 404

    business = current_user.user_business
    if not business or analysis.business_id != business.id:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    db.session.delete(analysis)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Report deleted successfully.'})
