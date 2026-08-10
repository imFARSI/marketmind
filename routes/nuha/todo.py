# ==============================================================================
# NUHA — Feature 3: To-Do & Quick Notes
# ==============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
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

# ==============================================================================
# RESTful JSON APIs
# ==============================================================================

@todo_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    """REST API: Returns JSON array of user's to-do notes/tasks grouped by status."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    notes = TodoNote.query.filter_by(business_id=business.id, owner_id=current_user.id).order_by(TodoNote.created_at.desc()).all()

    notes_data = [{
        'id': n.id,
        'title': n.title,
        'description': n.description,
        'status': n.status,
        'type': n.type,
        'created_at': n.created_at.isoformat() if n.created_at else None
    } for n in notes]

    grouped_by_status = {
        'Pending': [n for n in notes_data if n['status'] == 'Pending'],
        'In Progress': [n for n in notes_data if n['status'] == 'In Progress'],
        'Completed': [n for n in notes_data if n['status'] == 'Completed']
    }

    return jsonify({
        'status': 'success',
        'count': len(notes_data),
        'notes': notes_data,
        'grouped_by_status': grouped_by_status
    })

@todo_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """REST API: Accepts JSON payload or Form data to create a new task/note."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    payload = request.get_json(silent=True) or request.form

    title = payload.get('title', '').strip() if payload.get('title') is not None else ''
    description = payload.get('description', '')
    if not description and payload.get('content'):
        description = payload.get('content')
    if description is not None:
        description = str(description).strip()

    note_type = payload.get('type') or payload.get('category') or 'Task'
    if note_type is not None:
        note_type = str(note_type).strip()

    status = payload.get('status', 'Pending')
    if status is not None:
        status = str(status).strip()

    if not title:
        return jsonify({'status': 'error', 'message': 'Title is required.'}), 400

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

    return jsonify({
        'status': 'success',
        'message': f'{note_type} created successfully.',
        'note': {
            'id': new_note.id,
            'title': new_note.title,
            'description': new_note.description,
            'type': new_note.type,
            'status': new_note.status,
            'created_at': new_note.created_at.isoformat() if new_note.created_at else None
        }
    }), 201

@todo_bp.route('/api/edit/<int:note_id>', methods=['POST', 'PUT'])
@login_required
def api_edit(note_id):
    """REST API: Accepts JSON payload or Form data to update note attributes."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    note = TodoNote.query.get(note_id)
    if not note:
        return jsonify({'status': 'error', 'message': 'Note not found.'}), 404

    if note.owner_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    payload = request.get_json(silent=True) or request.form

    if payload.get('title') is not None:
        note.title = str(payload.get('title')).strip()
    if payload.get('description') is not None:
        note.description = str(payload.get('description')).strip()
    elif payload.get('content') is not None:
        note.description = str(payload.get('content')).strip()
    if payload.get('type') is not None:
        note.type = str(payload.get('type')).strip()
    if payload.get('status') is not None:
        note.status = str(payload.get('status')).strip()

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Updated successfully.',
        'note': {
            'id': note.id,
            'title': note.title,
            'description': note.description,
            'type': note.type,
            'status': note.status,
            'created_at': note.created_at.isoformat() if note.created_at else None
        }
    })

@todo_bp.route('/api/delete/<int:note_id>', methods=['POST', 'DELETE'])
@login_required
def api_delete(note_id):
    """REST API: Deletes a note by ID and returns JSON status."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    note = TodoNote.query.get(note_id)
    if not note:
        return jsonify({'status': 'error', 'message': 'Note not found.'}), 404

    if note.owner_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    db.session.delete(note)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Deleted successfully.'})

