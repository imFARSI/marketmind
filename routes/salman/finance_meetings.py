# Business Expense & Finance Management (HTML Routes + RESTful JSON APIs)

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Expense, Business

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
    flash(f'{entry_type} entry "৳{amount:,.2f}" logged for {month} {year}!', 'success')
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


