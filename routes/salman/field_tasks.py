# Field Task Assignment

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, FieldTask, TaskLocationLog, Competitor, Business, User

field_tasks_bp = Blueprint('salman_field_tasks', __name__, url_prefix='/salman/field-tasks')

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

# Field Tasks
@field_tasks_bp.route('/')
@login_required
def index():
    if current_user.role == 'Field Agent':
        return redirect(url_for('salman_field_tasks.my_tasks'))

    business = get_user_business()
    tasks = FieldTask.query.filter_by(business_id=business.id).order_by(FieldTask.created_at.desc()).all()
    competitors = Competitor.query.filter_by(business_id=business.id).all()
    
    enrolled_users = User.query.filter_by(business_id=business.id).all()

    user_map = {u.id: u for u in enrolled_users}
    competitor_map = {c.id: c for c in competitors}

    assigned_count = sum(1 for t in tasks if t.status == 'Assigned')
    in_progress_count = sum(1 for t in tasks if t.status == 'In Progress')
    completed_count = sum(1 for t in tasks if t.status == 'Completed')

    return render_template(
        'salman/field_tasks.html',
        tasks=tasks,
        total_tasks=len(tasks),
        assigned_count=assigned_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        competitors=competitors,
        users=enrolled_users,
        user_map=user_map,
        competitor_map=competitor_map,
        business=business
    )

@field_tasks_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    business = get_user_business()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    assigned_to_id = request.form.get('assigned_to_id')
    competitor_id = request.form.get('competitor_id')

    if not title or not assigned_to_id or not competitor_id:
        flash('Task title, assigned user, and target competitor are required.', 'danger')
        return redirect(url_for('salman_field_tasks.index'))

    new_task = FieldTask(
        title=title,
        description=description,
        assigned_to_id=int(assigned_to_id),
        competitor_id=int(competitor_id),
        business_id=business.id,
        status='Assigned'
    )

    db.session.add(new_task)
    db.session.commit()

    flash(f'Field task "{title}" assigned successfully!', 'success')
    return redirect(url_for('salman_field_tasks.index'))

# Agent Portal
@field_tasks_bp.route('/my-tasks')
@login_required
def my_tasks():
    my_assigned_tasks = FieldTask.query.filter_by(assigned_to_id=current_user.id).order_by(FieldTask.created_at.desc()).all()
    competitors = Competitor.query.all()
    competitor_map = {c.id: c for c in competitors}

    return render_template(
        'salman/agent_portal.html',
        tasks=my_assigned_tasks,
        total_tasks=len(my_assigned_tasks),
        competitor_map=competitor_map
    )

@field_tasks_bp.route('/update-status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    task = FieldTask.query.filter_by(id=id).first_or_404()

    new_status = request.form.get('status')
    notes = request.form.get('onsite_notes', '').strip()

    if new_status in ['Assigned', 'In Progress', 'Completed']:
        task.status = new_status
    if notes:
        task.onsite_notes = notes

    db.session.commit()
    flash(f'Task "{task.title}" updated to {task.status}.', 'success')
    
    if current_user.role == 'Field Agent':
        return redirect(url_for('salman_field_tasks.my_tasks'))
    return redirect(url_for('salman_field_tasks.index'))
