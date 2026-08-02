# ==============================================================================
# NUHA — Feature 1: Workspace Configuration
# ==============================================================================

from flask import Blueprint, render_template
from flask_login import login_required

workspace_bp = Blueprint('nuha_workspace', __name__, url_prefix='/nuha/workspace')

@workspace_bp.route('/')
@login_required
def index():
    return render_template('nuha/workspace.html')
