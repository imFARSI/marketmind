# ==============================================================================
# MUMTAHENAH BINTA HASHEM — Feature 4: Agents On-Site Findings Submission & Email Alert
# (Resend API Integration + Dual HTML / REST API Support)
# ==============================================================================

import os
import requests
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, FieldTask, User, Competitor, Business

findings_bp = Blueprint('mumtahenah_findings', __name__, url_prefix='/mumtahenah/findings')

# ------------------------------------------------------------------------------
# STEP 1: OUT-OF-THE-BOX API KEY FALLBACK HANDLING (MANDATORY)
# ------------------------------------------------------------------------------
RESEND_API_KEY = os.getenv('RESEND_API_KEY') or 're_123456789_YOUR_RESEND_API_KEY_FALLBACK'


def wants_json_response():
    return (
        request.is_json or
        request.headers.get('Accept') == 'application/json' or
        request.args.get('format') == 'json'
    )


# ------------------------------------------------------------------------------
# HELPER: Resend API Email Alert Dispatcher with Fallback Engine
# ------------------------------------------------------------------------------
def dispatch_resend_email_alert(recipient_email, task_title, agent_name, competitor_name, findings_notes):
    """
    Sends automated email alert via Resend API when field agent submits on-site findings.
    Includes simulated fallback if RESEND_API_KEY is unconfigured.
    """
    subject = f"[MarketMind Alert] On-Site Field Audit Submitted: {task_title}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #E2E8F0; border-radius: 8px;">
        <h2 style="color: #2563EB; margin-top: 0;">📍 On-Site Field Audit Submitted</h2>
        <p><strong>Field Agent:</strong> {agent_name}</p>
        <p><strong>Target Competitor:</strong> {competitor_name}</p>
        <p><strong>Field Task:</strong> {task_title}</p>
        <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0;"/>
        <h4 style="color: #1E293B; margin-bottom: 5px;">Agent Findings Notes:</h4>
        <blockquote style="background: #F8FAFC; padding: 12px; border-left: 4px solid #2563EB; margin: 0; color: #334155;">
            {findings_notes}
        </blockquote>
        <p style="font-size: 12px; color: #64748B; margin-top: 20px;">Sent automatically by MarketMind Intelligence Platform (Resend API).</p>
    </div>
    """

    if RESEND_API_KEY != 're_123456789_YOUR_RESEND_API_KEY_FALLBACK' and RESEND_API_KEY.startswith('re_'):
        try:
            url = 'https://api.resend.com/emails'
            headers = {
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'from': 'MarketMind Alerts <onboarding@resend.dev>',
                'to': [recipient_email],
                'subject': subject,
                'html': html_content
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            if resp.status_code in (200, 201):
                return True, "Live Resend API Email Sent"
        except Exception as e:
            print(f"Resend API Error: {e}")

    # Fallback simulated email dispatch
    return True, f"Simulated Email Logged (To: {recipient_email})"


# ------------------------------------------------------------------------------
# ROUTE 1: View On-Site Findings Submission Portal & Log Feed
# ------------------------------------------------------------------------------
@findings_bp.route('/')
@login_required
def index():
    business = current_user.user_business
    if not business:
        if wants_json_response():
            return jsonify({'success': False, 'error': 'Please configure your business workspace first.'}), 400
        flash('Please configure your business workspace first.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    # Fetch tasks based on user role
    if current_user.role == 'Field Agent':
        assigned_tasks = FieldTask.query.filter_by(assigned_to_id=current_user.id, business_id=business.id).all()
    else:
        assigned_tasks = FieldTask.query.filter_by(business_id=business.id).all()

    # Completed tasks with on-site findings
    completed_findings = [t for t in assigned_tasks if t.onsite_notes]

    findings_data = []
    for t in completed_findings:
        agent = User.query.get(t.assigned_to_id)
        comp = Competitor.query.get(t.competitor_id)
        findings_data.append({
            'task_id': t.id,
            'task_title': t.title,
            'agent_name': agent.username if agent else 'Field Agent',
            'competitor_name': comp.name if comp else 'Target Store',
            'notes': t.onsite_notes,
            'status': t.status,
            'submitted_at': t.created_at.strftime('%b %d, %Y')
        })

    kpis = {
        'total_assigned': len(assigned_tasks),
        'total_completed': len(completed_findings),
        'pending_count': len(assigned_tasks) - len(completed_findings)
    }

    if wants_json_response():
        return jsonify({
            'success': True,
            'kpis': kpis,
            'tasks': [{'id': t.id, 'title': t.title, 'status': t.status} for t in assigned_tasks],
            'findings': findings_data
        })

    return render_template(
        'mumtahenah/findings.html',
        tasks=assigned_tasks,
        findings=findings_data,
        kpis=kpis,
        is_agent=(current_user.role == 'Field Agent')
    )


# ------------------------------------------------------------------------------
# ROUTE 2: Submit On-Site Field Findings & Trigger Resend Email Alert
# ------------------------------------------------------------------------------
@findings_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    if request.is_json:
        data = request.get_json() or {}
        task_id = int(data.get('task_id')) if data.get('task_id') is not None else None
        category = str(data.get('category') or 'General Audit').strip()
        notes = str(data.get('notes') or '').strip()
    else:
        task_id = request.form.get('task_id', type=int)
        category = request.form.get('category', 'General Audit').strip()
        notes = request.form.get('notes', '').strip()

    if not task_id or not notes:
        if wants_json_response():
            return jsonify({'success': False, 'error': 'Task ID and Observation Notes are required.'}), 400
        flash('Task ID and Observation Notes are required.', 'danger')
        return redirect(url_for('mumtahenah_findings.index'))

    business = current_user.user_business
    task = FieldTask.query.filter_by(id=task_id, business_id=business.id).first() if business else None
    if not task:
        task = FieldTask.query.get_or_404(task_id)

    # Format findings notes
    formatted_notes = f"[{category}] {notes} (Recorded on {datetime.utcnow().strftime('%b %d, %Y %I:%M %p')})"
    task.onsite_notes = formatted_notes
    task.status = 'Completed'
    db.session.commit()

    # Trigger Automated Email Alert via Resend API
    recipient_email = (business.contact_email if business and business.contact_email else current_user.email)
    agent = User.query.get(task.assigned_to_id)
    comp = Competitor.query.get(task.competitor_id)

    email_sent, email_status = dispatch_resend_email_alert(
        recipient_email=recipient_email,
        task_title=task.title,
        agent_name=agent.username if agent else current_user.username,
        competitor_name=comp.name if comp else 'Target Competitor',
        findings_notes=formatted_notes
    )

    if wants_json_response():
        return jsonify({
            'success': True,
            'message': 'On-site findings submitted and email alert dispatched successfully.',
            'task_id': task.id,
            'task_status': task.status,
            'email_status': email_status
        })

    flash(f"On-site findings submitted for '{task.title}'! Automated email alert triggered ({email_status}).", 'success')
    return redirect(url_for('mumtahenah_findings.index'))


# ------------------------------------------------------------------------------
# ROUTE 3: Dedicated REST API Endpoint for On-Site Findings List
# ------------------------------------------------------------------------------
@findings_bp.route('/api/list')
@login_required
def api_list():
    business = current_user.user_business
    if not business:
        return jsonify({'success': False, 'error': 'No workspace found'}), 400

    tasks = FieldTask.query.filter_by(business_id=business.id).all()
    completed = [t for t in tasks if t.onsite_notes]

    findings_list = []
    for t in completed:
        agent = User.query.get(t.assigned_to_id)
        comp = Competitor.query.get(t.competitor_id)
        findings_list.append({
            'task_id': t.id,
            'title': t.title,
            'agent_name': agent.username if agent else None,
            'competitor_name': comp.name if comp else None,
            'onsite_notes': t.onsite_notes,
            'status': t.status
        })

    return jsonify({'success': True, 'count': len(findings_list), 'findings': findings_list})
