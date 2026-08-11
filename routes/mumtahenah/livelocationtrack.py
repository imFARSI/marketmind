# ==============================================================================
# MUMTAHENAH BINTA HASHEM — Feature 2: Live Field Agent Location Tracking
# (Includes Dual HTML / Internal REST API Response & Endpoint Support)
# ==============================================================================

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, FieldTask, TaskLocationLog, User, Competitor, Business

tracking_bp = Blueprint('mumtahenah_tracking', __name__, url_prefix='/mumtahenah/tracking')


# ------------------------------------------------------------------------------
# HELPER: Check if client requests JSON REST response
# ------------------------------------------------------------------------------
def wants_json_response():
    return (
        request.is_json or
        request.headers.get('Accept') == 'application/json' or
        request.args.get('format') == 'json'
    )


# ------------------------------------------------------------------------------
# ROUTE 1: Location Tracking Dashboard & Assigner Map Portal (HTML + REST API)
# ------------------------------------------------------------------------------
@tracking_bp.route('/')
@login_required
def index():
    business = current_user.user_business
    if not business:
        if wants_json_response():
            return jsonify({'success': False, 'error': 'Please configure your business workspace first.'}), 400
        flash('Please configure your business workspace first.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    # Fetch tasks and location logs based on user role
    if current_user.role == 'Field Agent':
        assigned_tasks = FieldTask.query.filter_by(assigned_to_id=current_user.id, business_id=business.id).all()
        task_ids = [t.id for t in assigned_tasks]
        location_logs = TaskLocationLog.query.filter(TaskLocationLog.task_id.in_(task_ids)).order_by(TaskLocationLog.logged_at.desc()).limit(20).all() if task_ids else []
    else:
        assigned_tasks = FieldTask.query.filter_by(business_id=business.id).all()
        task_ids = [t.id for t in assigned_tasks]
        location_logs = TaskLocationLog.query.filter(TaskLocationLog.task_id.in_(task_ids)).order_by(TaskLocationLog.logged_at.desc()).limit(50).all() if task_ids else []

    # Map location logs with task, agent, and competitor details
    logs_data = []
    active_agent_ids = set()

    for log in location_logs:
        task = FieldTask.query.get(log.task_id)
        if task:
            agent = User.query.get(task.assigned_to_id)
            comp = Competitor.query.get(task.competitor_id)
            if agent:
                active_agent_ids.add(agent.id)

            logs_data.append({
                'log_id': log.id,
                'task_id': task.id,
                'task_title': task.title,
                'agent_name': agent.username if agent else 'Field Agent',
                'competitor_name': comp.name if comp else 'Target Store',
                'latitude': log.latitude,
                'longitude': log.longitude,
                'address': log.address or f"{log.latitude:.4f}, {log.longitude:.4f}",
                'logged_at': log.logged_at.strftime('%b %d, %Y %I:%M %p'),
                'task_status': task.status
            })

    # Prepare Tasks Data for REST API AND DROPDOWN   
    tasks_data = []
    for t in assigned_tasks:
        agent = User.query.get(t.assigned_to_id)
        comp = Competitor.query.get(t.competitor_id)
        tasks_data.append({
            'task_id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'assigned_agent': agent.username if agent else None,
            'competitor_name': comp.name if comp else None
        })

    # Summary KPI Statistics
    in_progress_count = FieldTask.query.filter_by(business_id=business.id, status='In Progress').count()
    kpis = {
        'total_tasks': len(assigned_tasks),
        'in_progress': in_progress_count,
        'active_agents': len(active_agent_ids),
        'total_logs': len(location_logs)
    }

    # Internal REST API JSON Response if requested
    if wants_json_response():
        return jsonify({
            'success': True,
            'kpis': kpis,
            'tasks': tasks_data,
            'logs': logs_data
        })

    return render_template(
        'mumtahenah/livelocationtrack.html',
        tasks=assigned_tasks,
        logs=logs_data,
        kpis=kpis,
        is_agent=(current_user.role == 'Field Agent')
    )


# ------------------------------------------------------------------------------
# ROUTE 2: Receive GPS Coordinates from Browser Geolocation (REST API)
# ------------------------------------------------------------------------------
@tracking_bp.route('/update-location', methods=['POST'])
@login_required
def update_location():
    if request.is_json:
        data = request.get_json() or {}
        task_id = int(data.get('task_id')) if data.get('task_id') is not None else None
        latitude = float(data.get('latitude')) if data.get('latitude') is not None else None
        longitude = float(data.get('longitude')) if data.get('longitude') is not None else None
        address = str(data.get('address') or '').strip()
    else:
        task_id = request.form.get('task_id', type=int)
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        address = request.form.get('address', '').strip()

    if not task_id or latitude is None or longitude is None:
        return jsonify({'success': False, 'error': 'Task ID, Latitude, and Longitude are required.'}), 400

    task = FieldTask.query.get_or_404(task_id)

    # Save GPS Location Log into SQLite Database
    new_log = TaskLocationLog(
        task_id=task.id,
        latitude=latitude,
        longitude=longitude,
        address=address or f"Lat: {latitude:.4f}, Lng: {longitude:.4f}",
        logged_at=datetime.utcnow()
    )
    db.session.add(new_log)

    # Automatically update task status to 'In Progress' if newly started
    if task.status == 'Assigned':
        task.status = 'In Progress'

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Live GPS location recorded successfully.',
        'log_id': new_log.id,
        'latitude': latitude,
        'longitude': longitude,
        'task_status': task.status,
        'logged_at': new_log.logged_at.strftime('%b %d, %Y %I:%M %p')
    })


# ------------------------------------------------------------------------------
# ROUTE 3: Dedicated REST API Endpoint for Assigner Live Map Markers
# ------------------------------------------------------------------------------
@tracking_bp.route('/api/live-locations')
@login_required
def api_live_locations():
    business = current_user.user_business
    if not business:
        return jsonify({'success': False, 'error': 'No workspace found'}), 400

    tasks = FieldTask.query.filter_by(business_id=business.id).all()
    latest_markers = []

    for task in tasks:
        # Find latest GPS location log for each field task
        latest_log = TaskLocationLog.query.filter_by(task_id=task.id).order_by(TaskLocationLog.logged_at.desc()).first()
        if latest_log:
            agent = User.query.get(task.assigned_to_id)
            comp = Competitor.query.get(task.competitor_id)
            latest_markers.append({
                'task_id': task.id,
                'task_title': task.title,
                'agent_name': agent.username if agent else 'Field Agent',
                'competitor_name': comp.name if comp else 'Target Store',
                'latitude': latest_log.latitude,
                'longitude': latest_log.longitude,
                'logged_at': latest_log.logged_at.strftime('%I:%M %p'),
                'status': task.status
            })

    return jsonify({'success': True, 'markers': latest_markers})


# ------------------------------------------------------------------------------
# ROUTE 4: Dedicated REST API Endpoint for Dashboard Metrics
# ------------------------------------------------------------------------------
@tracking_bp.route('/api/dashboard')
@login_required
def api_dashboard():
    business = current_user.user_business
    if not business:
        return jsonify({'success': False, 'error': 'No workspace found'}), 400

    assigned_tasks = FieldTask.query.filter_by(business_id=business.id).all()
    task_ids = [t.id for t in assigned_tasks]
    location_logs = TaskLocationLog.query.filter(TaskLocationLog.task_id.in_(task_ids)).all() if task_ids else []

    active_agents = set()
    for task in assigned_tasks:
        if task.assigned_to_id:
            active_agents.add(task.assigned_to_id)

    in_progress_count = sum(1 for t in assigned_tasks if t.status == 'In Progress')

    return jsonify({
        'success': True,
        'kpis': {
            'total_tasks': len(assigned_tasks),
            'in_progress': in_progress_count,
            'active_agents': len(active_agents),
            'total_logs': len(location_logs)
        }
    })


# ------------------------------------------------------------------------------
# ROUTE 5: Dedicated REST API Endpoint for Location Logs History
# ------------------------------------------------------------------------------
@tracking_bp.route('/api/logs')
@login_required
def api_logs():
    business = current_user.user_business
    if not business:
        return jsonify({'success': False, 'error': 'No workspace found'}), 400

    tasks = FieldTask.query.filter_by(business_id=business.id).all()
    task_ids = [t.id for t in tasks]
    logs = TaskLocationLog.query.filter(TaskLocationLog.task_id.in_(task_ids)).order_by(TaskLocationLog.logged_at.desc()).all() if task_ids else []

    logs_list = []
    for l in logs:
        task = FieldTask.query.get(l.task_id)
        agent = User.query.get(task.assigned_to_id) if task else None
        logs_list.append({
            'log_id': l.id,
            'task_id': l.task_id,
            'task_title': task.title if task else None,
            'agent_name': agent.username if agent else None,
            'latitude': l.latitude,
            'longitude': l.longitude,
            'address': l.address,
            'logged_at': l.logged_at.isoformat()
        })

    return jsonify({'success': True, 'count': len(logs_list), 'logs': logs_list})


# ------------------------------------------------------------------------------
# ROUTE 6: Manual Location Logger (Dual HTML Redirect / REST API Response)
# ------------------------------------------------------------------------------
@tracking_bp.route('/manual-log', methods=['POST'])
@login_required
def manual_log():
    if request.is_json:
        data = request.get_json() or {}
        task_id = int(data.get('task_id')) if data.get('task_id') is not None else None
        latitude = float(data.get('latitude')) if data.get('latitude') is not None else None
        longitude = float(data.get('longitude')) if data.get('longitude') is not None else None
        address = str(data.get('address') or '').strip()
    else:
        task_id = request.form.get('task_id', type=int)
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        address = request.form.get('address', '').strip()

    if not task_id or latitude is None or longitude is None:
        if wants_json_response():
            return jsonify({'success': False, 'error': 'Task ID, Latitude, and Longitude are required.'}), 400
        flash('Task, Latitude, and Longitude are required.', 'danger')
        return redirect(url_for('mumtahenah_tracking.index'))

    task = FieldTask.query.get_or_404(task_id)

    log = TaskLocationLog(
        task_id=task.id,
        latitude=latitude,
        longitude=longitude,
        address=address or f"Lat: {latitude:.4f}, Lng: {longitude:.4f}"
    )
    db.session.add(log)
    if task.status == 'Assigned':
        task.status = 'In Progress'
    db.session.commit()

    if wants_json_response():
        return jsonify({
            'success': True,
            'message': 'Location coordinate logged successfully.',
            'log_id': log.id,
            'task_id': task.id,
            'latitude': latitude,
            'longitude': longitude
        })

    flash('Location coordinate logged successfully.', 'success')
    return redirect(url_for('mumtahenah_tracking.index'))
