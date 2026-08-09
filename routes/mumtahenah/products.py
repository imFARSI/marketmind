# ==============================================================================
# MUMTAHENAH BINTA HASHEM — Feature 1: Product & Price Catalog Management
# ==============================================================================

import re
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Product, Price, PriceHistory, Competitor

products_bp = Blueprint('mumtahenah_products', __name__, url_prefix='/mumtahenah/products')


# ------------------------------------------------------------------------------
# HELPER FUNCTION: Extract product metadata from webpage URL link
# ------------------------------------------------------------------------------
def parse_product_url(url):
    data = {'name': '', 'price': 0.0, 'currency': 'USD', 'category': 'General', 'description': ''}
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            # Extract webpage title
            title_tag = soup.find('meta', property='og:title') or soup.find('h1') or soup.find('title')
            if title_tag:
                data['name'] = re.split(r' [|\-–] ', title_tag.get('content', title_tag.get_text()).strip())[0]
            # Extract meta description
            desc_tag = soup.find('meta', property='og:description') or soup.find('meta', name='description')
            if desc_tag:
                data['description'] = desc_tag.get('content', '').strip()[:150]
            # Extract price & currency
            price_tag = soup.find('meta', property='og:price:amount') or soup.find('meta', name='price')
            if price_tag and price_tag.get('content'):
                data['price'] = float(price_tag.get('content').replace(',', ''))
            elif match := re.search(r'(\$|USD|BDT|৳)\s?([0-9]+(?:\.[0-9]{2})?)', soup.get_text()):
                if match.group(1) in ['BDT', '৳']:
                    data['currency'] = 'BDT'
                data['price'] = float(match.group(2))
    except Exception:
        pass

    if not data['name']:
        data['name'] = "Imported Product"
    return data


# ------------------------------------------------------------------------------
# ROUTE 1: View Product Catalog (Dashboard, Search & Competitor Filter)
# ------------------------------------------------------------------------------
@products_bp.route('/')
@login_required
def index():
    business = current_user.user_business
    if not business:
        flash('Please configure your business workspace first.', 'warning')
        return redirect(url_for('nuha_workspace.index'))

    competitors = Competitor.query.filter_by(business_id=business.id).all()
    comp_ids = [c.id for c in competitors]
    selected_comp = request.args.get('competitor_id', type=int)
    search = request.args.get('search', '', type=str).strip()

    # Filter products by competitor and search keyword
    query = Product.query.filter(Product.competitor_id.in_(comp_ids)) if comp_ids else Product.query.filter_by(id=-1)
    if selected_comp:
        query = query.filter(Product.competitor_id == selected_comp)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.category.ilike(f'%{search}%'))

    products_list = query.order_by(Product.created_at.desc()).all()

    # Calculate summary statistics
    products_data = []
    total_price = 0.0
    highest_price = 0.0

    for prod in products_list:
        latest_price = Price.query.filter_by(product_id=prod.id).order_by(Price.created_at.desc()).first()
        price_val = latest_price.amount if latest_price else 0.0
        total_price += price_val
        if price_val > highest_price:
            highest_price = price_val

        comp = Competitor.query.get(prod.competitor_id)
        products_data.append({
            'product': prod,
            'competitor_name': comp.name if comp else 'Unknown',
            'latest_price': price_val,
            'currency': latest_price.currency if latest_price else 'USD',
            'source': latest_price.source if latest_price else 'Manual',
            'history_count': PriceHistory.query.filter_by(product_id=prod.id).count()
        })

    avg_price = total_price / len(products_data) if products_data else 0.0
    kpis = {
        'total': len(products_data),
        'avg': round(avg_price, 2),
        'highest': round(highest_price, 2),
        'competitors_count': len(competitors)
    }

    return render_template(
        'mumtahenah/products.html',
        products=products_data,
        competitors=competitors,
        selected_competitor_id=selected_comp,
        search_query=search,
        kpis=kpis
    )


# ------------------------------------------------------------------------------
# ROUTE 2: Add Product Manually
# ------------------------------------------------------------------------------
@products_bp.route('/add-manual', methods=['POST'])
@login_required
def add_manual():
    comp_id = request.form.get('competitor_id', type=int)
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'General').strip()
    amount = float(request.form.get('amount', 0))
    currency = request.form.get('currency', 'USD').strip()
    description = request.form.get('description', '').strip()

    # Save new Product
    product = Product(name=name, category=category, description=description, competitor_id=comp_id)
    db.session.add(product)
    db.session.flush()

    # Save initial Price
    price = Price(product_id=product.id, amount=amount, currency=currency, source='Manual')
    db.session.add(price)
    db.session.commit()

    flash(f'Product "{name}" added successfully.', 'success')
    return redirect(url_for('mumtahenah_products.index'))


# ------------------------------------------------------------------------------
# ROUTE 3: Add Product via Link (URL Import)
# ------------------------------------------------------------------------------
@products_bp.route('/add-url', methods=['POST'])
@login_required
def add_url():
    comp_id = request.form.get('competitor_id', type=int)
    url = request.form.get('url', '').strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    scraped = parse_product_url(url)

    name = request.form.get('name') or scraped['name']
    category = request.form.get('category') or scraped['category']
    amount = float(request.form.get('amount') or scraped['price'])
    currency = request.form.get('currency') or scraped['currency']
    description = request.form.get('description') or scraped['description']

    # Save Product & Price
    product = Product(name=name, category=category, description=description, competitor_id=comp_id)
    db.session.add(product)
    db.session.flush()

    price = Price(product_id=product.id, amount=amount, currency=currency, source='URL Link Import')
    db.session.add(price)
    db.session.commit()

    flash(f'Product "{name}" imported via link successfully.', 'success')
    return redirect(url_for('mumtahenah_products.index'))


# ------------------------------------------------------------------------------
# ROUTE 4: Update Price & Log History
# ------------------------------------------------------------------------------
@products_bp.route('/update-price/<int:product_id>', methods=['POST'])
@login_required
def update_price(product_id):
    product = Product.query.get_or_404(product_id)
    new_amount = float(request.form.get('amount', 0))
    source = request.form.get('source', 'Manual Update')

    latest = Price.query.filter_by(product_id=product.id).order_by(Price.created_at.desc()).first()
    old_amount = latest.amount if latest else 0.0
    currency = latest.currency if latest else 'USD'

    # Save new Price entry & log to PriceHistory table
    db.session.add(Price(product_id=product.id, amount=new_amount, currency=currency, source=source))
    db.session.add(PriceHistory(product_id=product.id, old_amount=old_amount, new_amount=new_amount, changed_by_source=source))
    db.session.commit()

    flash(f'Price for "{product.name}" updated to {currency} {new_amount:.2f}.', 'success')
    return redirect(url_for('mumtahenah_products.index'))


# ------------------------------------------------------------------------------
# ROUTE 5: Delete Product
# ------------------------------------------------------------------------------
@products_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    PriceHistory.query.filter_by(product_id=product.id).delete()
    Price.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()

    flash(f'Product "{product.name}" deleted.', 'info')
    return redirect(url_for('mumtahenah_products.index'))


# ------------------------------------------------------------------------------
# ROUTE 6: Price Audit History API for Modal
# ------------------------------------------------------------------------------
@products_bp.route('/api/price-history/<int:product_id>')
@login_required
def api_price_history(product_id):
    product = Product.query.get_or_404(product_id)
    history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.recorded_at.desc()).all()
    logs = [{'old': h.old_amount, 'new': h.new_amount, 'source': h.changed_by_source, 'date': h.recorded_at.strftime('%b %d, %Y')} for h in history]

    return jsonify({'product_name': product.name, 'history': logs})
