# ==============================================================================
# NUHA — Feature 3: To-Do & Quick Notes
# ==============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, TodoNote

todo_bp = Blueprint('nuha_todo', __name__, url_prefix='/nuha/todo')

@todo_bp.route('/')
@login_required
def index():
    if current_user.role not in ['Business Owner', 'Business User']:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.dashboard'))

    business = current_user.user_business
    if not business:
        flash('No business workspace found. Please configure your workspace first.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    # Fetch notes for this user's business
    notes = TodoNote.query.filter_by(business_id=business.id, owner_id=current_user.id).order_by(TodoNote.created_at.desc()).all()
    
    # Filter for frontend convenience
    tasks = [n for n in notes if n.type == 'Task']
    reminders = [n for n in notes if n.type == 'Reminder']
    quick_notes = [n for n in notes if n.type == 'Note']

    return render_template(
        'nuha/todo.html',
        business=business,
        tasks=tasks,
        reminders=reminders,
        quick_notes=quick_notes
    )

@todo_bp.route('/create', methods=['POST'])
@login_required
def create():
    if current_user.role not in ['Business Owner', 'Business User']:
        return redirect(url_for('auth.dashboard'))

    business = current_user.user_business
    if not business:
        return redirect(url_for('nuha_workspace.index'))

    title = request.form.get('title')
    description = request.form.get('description')
    note_type = request.form.get('type') # Task, Reminder, Note
    status = request.form.get('status', 'Pending')

    if not title:
        flash('Title is required.', 'danger')
        return redirect(url_for('nuha_todo.index'))

    new_note = TodoNote(
        title=title,
        description=description,
        type=note_type,
        status=status,
        business_id=business.id,
        owner_id=current_user.id
    )
    db.session.add(new_note)
    db.session.commit()
    flash(f'{note_type} created successfully.', 'success')

    return redirect(url_for('nuha_todo.index'))

@todo_bp.route('/update/<int:note_id>', methods=['POST'])
@login_required
def update(note_id):
    note = TodoNote.query.get_or_404(note_id)
    
    # Security check
    if note.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('nuha_todo.index'))

    # Quick status toggle OR full update
    new_status = request.form.get('status')
    if new_status:
        note.status = new_status
        db.session.commit()
        return redirect(url_for('nuha_todo.index'))

    # Full update from modal
    title = request.form.get('title')
    description = request.form.get('description')
    if title:
        note.title = title
    note.description = description
    db.session.commit()
    flash('Updated successfully.', 'success')

    return redirect(url_for('nuha_todo.index'))

@todo_bp.route('/delete/<int:note_id>', methods=['POST'])
@login_required
def delete(note_id):
    note = TodoNote.query.get_or_404(note_id)
    
    if note.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('nuha_todo.index'))

    db.session.delete(note)
    db.session.commit()
    flash('Deleted successfully.', 'success')

    return redirect(url_for('nuha_todo.index'))
