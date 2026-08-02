# ==============================================================================
# MUMTAHENAH BINTA HASHEM — Feature 1: Product Catalog Management
# ==============================================================================

from flask import Blueprint, render_template
from flask_login import login_required

products_bp = Blueprint('mumtahenah_products', __name__, url_prefix='/mumtahenah/products')

@products_bp.route('/')
@login_required
def index():
    return render_template('mumtahenah/products.html')
