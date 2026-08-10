# Finance & Meetings Management (HTML Routes + RESTful JSON APIs)

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Meeting, Expense, Business

finance_meetings_bp = Blueprint('salman_finance_meetings', __name__, url_prefix='/salman/finance-meetings')

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
YEARS = [2026, 2025, 2024]

def get_user_business():
    if current_user.role == 'Field Agent' and current_user.business_id:
        return Business.query.get(current_user.business_id)
    business = Business.query.filter_by(owner_id=current_user.id).first()
    if not business:
        import secrets
        code = f"BIZ{secrets.randbelow(8999) + 1000}"
        business = Business(name=f"{current_user.username}'s Business", industry="General", join_code=code, owner_id=current_user.id)
        db.session.add(business)
        db.session.commit()
    return business

# ==============================================================================
# HTML WEB PAGE ROUTES (Server-Side Jinja2 Rendering)
# ==============================================================================

@finance_meetings_bp.route('/')
@login_required
def index():
    business = get_user_business()
    
    # Filter params
    selected_year = request.args.get('year', type=int, default=2026)
    selected_month = request.args.get('month', default='All') # 'All' or 'Jan', 'Feb', etc.

    # Fetch Meetings
    meetings = Meeting.query.filter_by(business_id=business.id).order_by(Meeting.created_at.desc()).all()

    # Query Expenses / Revenues
    expense_query = Expense.query.filter_by(business_id=business.id, year=selected_year)
    if selected_month != 'All':
        expense_query = expense_query.filter_by(month=selected_month)
    
    financial_items = expense_query.order_by(Expense.created_at.desc()).all()

    # Calculate Totals for Selected Year & Month Filter
    total_revenue = sum(item.amount for item in financial_items if item.type == 'Revenue')
    total_expense = sum(item.amount for item in financial_items if item.type == 'Expense')
    net_profit = total_revenue - total_expense

    # Monthly breakdown dictionary for chart/summary
    monthly_data = {}
    for m in MONTHS:
        m_items = Expense.query.filter_by(business_id=business.id, year=selected_year, month=m).all()
        m_rev = sum(i.amount for i in m_items if i.type == 'Revenue')
        m_exp = sum(i.amount for i in m_items if i.type == 'Expense')
        monthly_data[m] = {
            'revenue': m_rev,
            'expense': m_exp,
            'profit': m_rev - m_exp
        }

    return render_template(
        'salman/finance_meetings.html',
        meetings=meetings,
        financial_items=financial_items,
        total_revenue=total_revenue,
        total_expense=total_expense,
        net_profit=net_profit,
        selected_year=selected_year,
        selected_month=selected_month,
        months=MONTHS,
        years=YEARS,
        monthly_data=monthly_data
    )

# --- MEETING MANAGEMENT ---

@finance_meetings_bp.route('/meetings/add', methods=['POST'])
@login_required
def add_meeting():
    business = get_user_business()
    title = request.form.get('title', '').strip()
    date_time_raw = request.form.get('date_time', '').strip()
    location = request.form.get('location', 'Online Meeting').strip()
    agenda = request.form.get('agenda', '').strip()

    formatted_date_time = date_time_raw
    if 'T' in date_time_raw:
        try:
            dt_obj = datetime.strptime(date_time_raw, '%Y-%m-%dT%H:%M')
            formatted_date_time = dt_obj.strftime('%b %d, %Y at %I:%M %p')
        except Exception:
            pass

    if not title or not date_time_raw:
        flash('Meeting title and date/time are required.', 'danger')
        return redirect(url_for('salman_finance_meetings.index'))

    new_meeting = Meeting(
        title=title,
        date_time=formatted_date_time,
        location=location,
        agenda=agenda,
        status='Upcoming',
        business_id=business.id
    )
    db.session.add(new_meeting)
    db.session.commit()
    flash(f'Meeting "{title}" scheduled successfully!', 'success')
    return redirect(url_for('salman_finance_meetings.index'))

@finance_meetings_bp.route('/meetings/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_meeting_status(id):
    business = get_user_business()
    meeting = Meeting.query.filter_by(id=id, business_id=business.id).first_or_404()
    meeting.status = 'Done' if meeting.status == 'Upcoming' else 'Upcoming'
    db.session.commit()
    flash(f'Meeting status updated to "{meeting.status}".', 'success')
    return redirect(url_for('salman_finance_meetings.index'))

@finance_meetings_bp.route('/meetings/<int:id>/edit', methods=['POST'])
@login_required
def edit_meeting(id):
    business = get_user_business()
    meeting = Meeting.query.filter_by(id=id, business_id=business.id).first_or_404()
    meeting.title = request.form.get('title', meeting.title).strip()
    meeting.date_time = request.form.get('date_time', meeting.date_time).strip()
    meeting.location = request.form.get('location', meeting.location).strip()
    meeting.agenda = request.form.get('agenda', meeting.agenda).strip()
    meeting.status = request.form.get('status', meeting.status).strip()
    db.session.commit()
    flash('Meeting updated successfully.', 'success')
    return redirect(url_for('salman_finance_meetings.index'))

@finance_meetings_bp.route('/meetings/<int:id>/delete', methods=['POST'])
@login_required
def delete_meeting(id):
    business = get_user_business()
    meeting = Meeting.query.filter_by(id=id, business_id=business.id).first_or_404()
    db.session.delete(meeting)
    db.session.commit()
    flash('Meeting deleted.', 'info')
    return redirect(url_for('salman_finance_meetings.index'))

# --- EXPENSE & REVENUE MANAGEMENT ---

@finance_meetings_bp.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    business = get_user_business()
    title = request.form.get('title', '').strip()
    entry_type = request.form.get('type', 'Expense').strip()
    category = request.form.get('category', 'General').strip()
    amount = request.form.get('amount', type=float, default=0.0)
    month = request.form.get('month', 'Jan').strip()
    year = request.form.get('year', type=int, default=2026)

    if not title or amount <= 0:
        flash('Valid title and amount greater than 0 are required.', 'danger')
        return redirect(url_for('salman_finance_meetings.index'))

    new_entry = Expense(
        title=title,
        category=category,
        type=entry_type,
        amount=amount,
        month=month,
        year=year,
        business_id=business.id
    )
    db.session.add(new_entry)
    db.session.commit()
    flash(f'{entry_type} entry "${amount:,.2f}" logged for {month} {year}!', 'success')
    return redirect(url_for('salman_finance_meetings.index', year=year, month=month))

@finance_meetings_bp.route('/expenses/<int:id>/delete', methods=['POST'])
@login_required
def delete_expense(id):
    business = get_user_business()
    entry = Expense.query.filter_by(id=id, business_id=business.id).first_or_404()
    year = entry.year
    month = entry.month
    db.session.delete(entry)
    db.session.commit()
    flash('Financial record deleted.', 'info')
    return redirect(url_for('salman_finance_meetings.index', year=year, month=month))

# ==============================================================================
# RESTFUL JSON API ENDPOINTS (For Postman & AJAX API calls)
# ==============================================================================

@finance_meetings_bp.route('/api/summary', methods=['GET'])
@login_required
def api_finance_summary():
    """REST API: Returns JSON summary of financial math calculation & meetings list."""
    business = get_user_business()
    selected_year = request.args.get('year', type=int, default=2026)
    selected_month = request.args.get('month', default='All')

    expense_query = Expense.query.filter_by(business_id=business.id, year=selected_year)
    if selected_month != 'All':
        expense_query = expense_query.filter_by(month=selected_month)
    
    financial_items = expense_query.order_by(Expense.created_at.desc()).all()

    total_revenue = sum(item.amount for item in financial_items if item.type == 'Revenue')
    total_expense = sum(item.amount for item in financial_items if item.type == 'Expense')
    net_profit = total_revenue - total_expense

    meetings = Meeting.query.filter_by(business_id=business.id).order_by(Meeting.created_at.desc()).all()

    return jsonify({
        'status': 'success',
        'selected_year': selected_year,
        'selected_month': selected_month,
        'summary': {
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'net_profit': net_profit
        },
        'meetings': [{
            'id': m.id,
            'title': m.title,
            'date_time': m.date_time,
            'location': m.location,
            'agenda': m.agenda,
            'status': m.status
        } for m in meetings],
        'financial_items': [{
            'id': f.id,
            'title': f.title,
            'category': f.category,
            'type': f.type,
            'amount': f.amount,
            'month': f.month,
            'year': f.year
        } for f in financial_items]
    })

@finance_meetings_bp.route('/api/meetings/add', methods=['POST'])
@login_required
def api_add_meeting():
    """REST API: Accepts JSON payload or Form data to schedule a meeting."""
    business = get_user_business()
    payload = request.get_json(silent=True) or request.form

    title = payload.get('title', '').strip()
    date_time_raw = payload.get('date_time', '').strip()
    location = payload.get('location', 'Online Meeting').strip()
    agenda = payload.get('agenda', '').strip()

    formatted_date_time = date_time_raw
    if 'T' in date_time_raw:
        try:
            dt_obj = datetime.strptime(date_time_raw, '%Y-%m-%dT%H:%M')
            formatted_date_time = dt_obj.strftime('%b %d, %Y at %I:%M %p')
        except Exception:
            pass

    if not title or not date_time_raw:
        return jsonify({'status': 'error', 'message': 'Meeting title and date/time are required.'}), 400

    new_meeting = Meeting(
        title=title,
        date_time=formatted_date_time,
        location=location,
        agenda=agenda,
        status='Upcoming',
        business_id=business.id
    )
    db.session.add(new_meeting)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Meeting "{title}" scheduled successfully.',
        'meeting': {
            'id': new_meeting.id,
            'title': new_meeting.title,
            'date_time': new_meeting.date_time,
            'location': new_meeting.location,
            'agenda': new_meeting.agenda,
            'status': new_meeting.status
        }
    }), 201

@finance_meetings_bp.route('/api/expenses/add', methods=['POST'])
@login_required
def api_add_expense():
    """REST API: Accepts JSON payload or Form data to log an expense or revenue."""
    business = get_user_business()
    payload = request.get_json(silent=True) or request.form

    title = payload.get('title', '').strip()
    entry_type = payload.get('type', 'Expense').strip()
    category = payload.get('category', 'General').strip()
    amount = float(payload.get('amount', 0.0))
    month = payload.get('month', 'Jan').strip()
    year = int(payload.get('year', 2026))

    if not title or amount <= 0:
        return jsonify({'status': 'error', 'message': 'Valid title and amount > 0 are required.'}), 400

    new_entry = Expense(
        title=title,
        category=category,
        type=entry_type,
        amount=amount,
        month=month,
        year=year,
        business_id=business.id
    )
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'{entry_type} entry "${amount:,.2f}" logged for {month} {year}.',
        'entry': {
            'id': new_entry.id,
            'title': new_entry.title,
            'type': new_entry.type,
            'category': new_entry.category,
            'amount': new_entry.amount,
            'month': new_entry.month,
            'year': new_entry.year
        }
    }), 201
