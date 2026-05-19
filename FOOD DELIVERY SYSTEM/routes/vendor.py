from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, current_app)
from functools import wraps
from models import (db, Vendor, Category, MenuItem, Order, OrderItem,
                    ItemAddonGroup, ItemAddon)
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

vendor_bp = Blueprint('vendor', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, subfolder):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, unique_name))
        return f"uploads/{subfolder}/{unique_name}"
    return None


def vendor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'vendor_id' not in session:
            flash('Please log in as a vendor.', 'error')
            return redirect(url_for('vendor.login'))
        vendor = Vendor.query.get(session['vendor_id'])
        if not vendor or vendor.status in ('suspended', 'banned'):
            session.pop('vendor_id', None)
            flash('Your account has been suspended or banned.', 'error')
            return redirect(url_for('vendor.login'))
        return f(*args, **kwargs)
    return decorated


# ── AUTH ──────────────────────────────────────────────────────────────────────

ACCEPTED_CITIES = {'makati', 'taguig', 'makati city', 'taguig city'}

@vendor_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        address = request.form.get('address', '').strip()
        business_address = request.form.get('business_address', '').strip()
        business_city = request.form.get('business_city', '').strip().lower()
        vendor_barangay = request.form.get('vendor_barangay', '').strip()
        shop_type = request.form.get('shop_type', 'restaurant').strip()
        proposal = request.form.get('proposal', '').strip()

        if len(password) < 8 or len(password) > 16:
            flash('Password must be 8–16 characters.', 'error')
            return redirect(url_for('vendor.register'))
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('vendor.register'))
        if Vendor.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('vendor.register'))
        if business_city not in ACCEPTED_CITIES:
            flash('Business location must be in Makati City or Taguig City only.', 'error')
            return redirect(url_for('vendor.register'))
        if not proposal:
            flash('Please provide a reason / proposal for your application.', 'error')
            return redirect(url_for('vendor.register'))

        if phone and not (phone.isdigit() and len(phone) == 11 and phone.startswith('09')):
            flash('Invalid phone number. Must be 11 digits starting with 09.', 'error')
            return redirect(url_for('vendor.register'))

        vendor = Vendor(shop_name=shop_name, email=email, phone=phone,
                        address=address, business_address=business_address,
                        business_city=request.form.get('business_city', '').strip(),
                        vendor_barangay=vendor_barangay,
                        shop_type=shop_type,
                        proposal=proposal, status='pending')
        vendor.set_password(password)
        db.session.add(vendor)
        db.session.commit()
        flash('Application submitted! We will review your account shortly.', 'success')
        return redirect(url_for('vendor.application_status', email=email))
    return render_template('vendor/register.html')


@vendor_bp.route('/application-status')
def application_status():
    email = request.args.get('email', '').strip()
    vendor = None
    if email:
        vendor = Vendor.query.filter_by(email=email).first()
    return render_template('vendor/application_status.html', vendor=vendor, email=email)


@vendor_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'vendor_id' in session:
        return redirect(url_for('vendor.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        vendor = Vendor.query.filter_by(email=email).first()
        if vendor and vendor.check_password(password):
            if vendor.status == 'pending':
                flash('Your application is under review.', 'error')
                return redirect(url_for('vendor.application_status', email=email))
            elif vendor.status == 'under_review':
                flash('Your application is being reviewed by our team.', 'error')
                return redirect(url_for('vendor.application_status', email=email))
            elif vendor.status == 'rejected':
                flash('Your application was not approved. Please contact support.', 'error')
                return redirect(url_for('vendor.application_status', email=email))
            elif vendor.status in ('suspended', 'banned'):
                flash('Your account is ' + vendor.status + '.', 'error')
            else:
                session['vendor_id'] = vendor.id
                session['vendor_name'] = vendor.shop_name
                session['vendor_logo'] = vendor.shop_logo or ''
                return redirect(url_for('vendor.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('vendor/login.html')


@vendor_bp.route('/logout')
def logout():
    session.pop('vendor_id', None)
    session.pop('vendor_name', None)
    return redirect(url_for('vendor.login'))


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@vendor_bp.route('/dashboard')
@vendor_required
def dashboard():
    vendor = Vendor.query.get(session['vendor_id'])
    recent_orders = Order.query.filter_by(vendor_id=vendor.id).order_by(
        Order.created_at.desc()).limit(10).all()
    stats = {
        'pending': Order.query.filter_by(vendor_id=vendor.id, status='pending').count(),
        'preparing': Order.query.filter_by(vendor_id=vendor.id, status='preparing').count(),
        'ready': Order.query.filter_by(vendor_id=vendor.id, status='ready_for_pickup').count(),
        'delivered': Order.query.filter_by(vendor_id=vendor.id, status='delivered').count(),
        'total_items': MenuItem.query.filter_by(vendor_id=vendor.id).count(),
    }
    return render_template('vendor/dashboard.html', vendor=vendor,
                           recent_orders=recent_orders, stats=stats)


# ── SHOP SETTINGS ─────────────────────────────────────────────────────────────

@vendor_bp.route('/shop', methods=['GET', 'POST'])
@vendor_required
def shop():
    ACCEPTED_CITIES = {'makati', 'taguig', 'makati city', 'taguig city'}
    vendor = Vendor.query.get(session['vendor_id'])
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        if phone and not (phone.isdigit() and len(phone) == 11 and phone.startswith('09')):
            flash('Invalid phone number. Must be 11 digits starting with 09.', 'error')
            return redirect(url_for('vendor.shop'))
        vendor.shop_name    = request.form.get('shop_name', vendor.shop_name).strip()
        vendor.phone        = phone
        vendor.address      = request.form.get('address', vendor.address or '').strip()
        vendor.description  = request.form.get('description', vendor.description or '').strip()
        vendor.shop_type    = request.form.get('shop_type', vendor.shop_type or 'restaurant').strip()

        # Business location
        new_city    = request.form.get('business_city', '').strip()
        new_barangay = request.form.get('vendor_barangay', '').strip()
        new_baddr   = request.form.get('business_address', '').strip()
        if new_city and new_city.lower() not in ACCEPTED_CITIES:
            flash('Business location must be in Makati City or Taguig City.', 'error')
            return redirect(url_for('vendor.shop'))
        if new_city:
            vendor.business_city = new_city
        if new_barangay:
            vendor.vendor_barangay = new_barangay
        if new_baddr:
            vendor.business_address = new_baddr

        # Cover banner upload
        banner_file = request.files.get('cover_banner')
        if banner_file and banner_file.filename:
            path = save_upload(banner_file, 'banners')
            if path:
                vendor.cover_banner = path

        # Shop logo upload
        logo_file = request.files.get('shop_logo')
        if logo_file and logo_file.filename:
            path = save_upload(logo_file, 'logos')
            if path:
                vendor.shop_logo = path

        session['vendor_name'] = vendor.shop_name
        session['vendor_logo'] = vendor.shop_logo or ''
        db.session.commit()
        flash('Shop settings updated.', 'success')
        return redirect(url_for('vendor.shop'))
    return render_template('vendor/shop.html', vendor=vendor)


# ── CATEGORIES ────────────────────────────────────────────────────────────────

@vendor_bp.route('/categories')
@vendor_required
def categories():
    return redirect(url_for('vendor.menu'))


@vendor_bp.route('/menu')
@vendor_required
def menu():
    vendor = Vendor.query.get(session['vendor_id'])
    cats = Category.query.filter_by(vendor_id=vendor.id).all()
    uncategorized = MenuItem.query.filter_by(vendor_id=vendor.id, category_id=None).all()
    return render_template('vendor/menu.html', vendor=vendor, categories=cats, uncategorized=uncategorized)


@vendor_bp.route('/categories/add', methods=['POST'])
@vendor_required
def category_add():
    name = request.form.get('name', '').strip()
    if name:
        cat = Category(vendor_id=session['vendor_id'], name=name)
        db.session.add(cat)
        db.session.commit()
        flash('Category added.', 'success')
    return redirect(url_for('vendor.menu'))


@vendor_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@vendor_required
def category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.categories'))
    # Unlink items from this category
    for item in cat.items:
        item.category_id = None
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('vendor.menu'))


# ── MENU ITEMS ────────────────────────────────────────────────────────────────

@vendor_bp.route('/items')
@vendor_required
def items():
    vendor = Vendor.query.get(session['vendor_id'])
    items_list = MenuItem.query.filter_by(vendor_id=vendor.id).order_by(
        MenuItem.category_id, MenuItem.name).all()
    cats = Category.query.filter_by(vendor_id=vendor.id).all()
    return render_template('vendor/items.html', vendor=vendor, items=items_list, categories=cats)


@vendor_bp.route('/items/add', methods=['GET', 'POST'])
@vendor_required
def item_add():
    vendor = Vendor.query.get(session['vendor_id'])
    cats = Category.query.filter_by(vendor_id=vendor.id).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = float(request.form.get('price', 0))
        category_id = request.form.get('category_id', '')

        item = MenuItem(
            vendor_id=vendor.id,
            name=name,
            description=description,
            price=price,
            category_id=int(category_id) if category_id else None,
        )

        img_file = request.files.get('image')
        if img_file and img_file.filename:
            path = save_upload(img_file, 'items')
            if path:
                item.image = path

        db.session.add(item)
        db.session.commit()
        flash('Item added.', 'success')
        return redirect(url_for('vendor.menu'))
    return render_template('vendor/item_form.html', item=None, categories=cats, vendor=vendor)


@vendor_bp.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@vendor_required
def item_edit(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.menu'))
    vendor = Vendor.query.get(session['vendor_id'])
    cats = Category.query.filter_by(vendor_id=vendor.id).all()
    if request.method == 'POST':
        item.name = request.form.get('name', item.name).strip()
        item.description = request.form.get('description', item.description or '').strip()
        item.price = float(request.form.get('price', item.price))
        cat_id = request.form.get('category_id', '')
        item.category_id = int(cat_id) if cat_id else None

        img_file = request.files.get('image')
        if img_file and img_file.filename:
            path = save_upload(img_file, 'items')
            if path:
                item.image = path

        db.session.commit()
        flash('Item updated.', 'success')
        return redirect(url_for('vendor.menu'))
    return render_template('vendor/item_form.html', item=item, categories=cats, vendor=vendor)


@vendor_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@vendor_required
def item_delete(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.items'))
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', 'success')
    return redirect(url_for('vendor.menu'))


@vendor_bp.route('/items/<int:item_id>/toggle', methods=['POST'])
@vendor_required
def item_toggle(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.items'))
    item.is_available = not item.is_available
    db.session.commit()
    return redirect(url_for('vendor.menu'))


# ── ORDERS ────────────────────────────────────────────────────────────────────

@vendor_bp.route('/orders')
@vendor_required
def orders():
    vendor = Vendor.query.get(session['vendor_id'])
    orders_list = Order.query.filter_by(vendor_id=vendor.id).order_by(
        Order.created_at.desc()).all()
    return render_template('vendor/orders.html', vendor=vendor, orders=orders_list)


@vendor_bp.route('/orders/<int:order_id>/confirm', methods=['POST'])
@vendor_required
def order_confirm(order_id):
    order = Order.query.get_or_404(order_id)
    if order.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.orders'))
    order.status = 'preparing'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Order accepted — start preparing the food!', 'success')
    return redirect(url_for('vendor.orders'))


@vendor_bp.route('/orders/<int:order_id>/prepare', methods=['POST'])
@vendor_required
def order_prepare(order_id):
    order = Order.query.get_or_404(order_id)
    if order.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.orders'))
    order.status = 'preparing'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Order is now being prepared.', 'success')
    return redirect(url_for('vendor.orders'))


@vendor_bp.route('/orders/<int:order_id>/ready', methods=['POST'])
@vendor_required
def order_ready(order_id):
    order = Order.query.get_or_404(order_id)
    if order.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.orders'))
    if order.status in ('confirmed', 'preparing'):
        order.status = 'ready_for_pickup'
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Order is ready — seeking a rider!', 'success')
    return redirect(url_for('vendor.orders'))


# ── REMITTANCES ─────────────────────────────────────────────────────────────

@vendor_bp.route('/remittances')
@vendor_required
def remittances():
    from models import RiderCashout
    vendor_id = session['vendor_id']
    vendor = Vendor.query.get(vendor_id)
    cashouts = RiderCashout.query.filter_by(vendor_id=vendor_id).order_by(RiderCashout.requested_at.desc()).all()
    return render_template('vendor/remittances.html', cashouts=cashouts, vendor=vendor)

@vendor_bp.route('/remittances/<int:cashout_id>/approve', methods=['POST'])
@vendor_required
def approve_remittance(cashout_id):
    from models import RiderCashout
    cashout = RiderCashout.query.get_or_404(cashout_id)
    if cashout.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.remittances'))
    cashout.status = 'completed'
    cashout.processed_at = datetime.utcnow()
    db.session.commit()
    flash(f'Remittance of ₱{cashout.amount:.2f} approved.', 'success')
    return redirect(url_for('vendor.remittances'))

@vendor_bp.route('/remittances/<int:cashout_id>/reject', methods=['POST'])
@vendor_required
def reject_remittance(cashout_id):
    from models import RiderCashout
    cashout = RiderCashout.query.get_or_404(cashout_id)
    if cashout.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.remittances'))
    cashout.status = 'rejected'
    cashout.processed_at = datetime.utcnow()
    db.session.commit()
    flash(f'Remittance of ₱{cashout.amount:.2f} rejected.', 'success')
    return redirect(url_for('vendor.remittances'))


# ── ANALYTICS ────────────────────────────────────────────────────────────────

@vendor_bp.route('/analytics')
@vendor_required
def analytics():
    from sqlalchemy import func
    vendor = Vendor.query.get(session['vendor_id'])
    period = request.args.get('period', 'daily')  # daily | weekly | monthly

    delivered_orders = Order.query.filter_by(
        vendor_id=vendor.id, status='delivered').all()

    # ── time-series revenue ───────────────────────────────────────────────────
    from collections import defaultdict
    rev_map = defaultdict(float)
    for o in delivered_orders:
        if period == 'daily':
            key = o.created_at.strftime('%b %d')
        elif period == 'weekly':
            # ISO week number
            key = 'W' + o.created_at.strftime('%U') + ' ' + o.created_at.strftime('%Y')
        else:
            key = o.created_at.strftime('%b %Y')
        rev_map[key] += float(o.total_amount or 0)

    sorted_keys  = sorted(rev_map.keys(),
                          key=lambda k: list(rev_map.keys()).index(k))[:30]
    chart_labels = sorted_keys
    chart_values = [round(rev_map[k], 2) for k in sorted_keys]

    # ── top items ─────────────────────────────────────────────────────────────
    item_rev = defaultdict(float)
    item_qty = defaultdict(int)
    for o in delivered_orders:
        for oi in o.items:
            item_rev[oi.name] += oi.price * oi.quantity
            item_qty[oi.name] += oi.quantity
    top_items = sorted(item_rev.items(), key=lambda x: x[1], reverse=True)[:10]

    # ── category revenue ──────────────────────────────────────────────────────
    cat_rev = defaultdict(float)
    cats    = {c.id: c.name for c in Category.query.filter_by(vendor_id=vendor.id).all()}
    for o in delivered_orders:
        for oi in o.items:
            mi = MenuItem.query.filter_by(name=oi.name, vendor_id=vendor.id).first()
            cat_name = cats.get(mi.category_id, 'Uncategorized') if mi else 'Uncategorized'
            cat_rev[cat_name] += oi.price * oi.quantity

    # ── summary stats ─────────────────────────────────────────────────────────
    total_revenue = sum(float(o.total_amount or 0) for o in delivered_orders)
    total_orders  = len(delivered_orders)
    avg_order     = (total_revenue / total_orders) if total_orders else 0

    return render_template('vendor/analytics.html',
        vendor=vendor,
        period=period,
        chart_labels=chart_labels,
        chart_values=chart_values,
        top_items=top_items,
        cat_labels=[k for k, v in sorted(cat_rev.items(), key=lambda x: x[1], reverse=True)],
        cat_values=[round(v, 2) for k, v in sorted(cat_rev.items(), key=lambda x: x[1], reverse=True)],
        cat_rev=sorted(cat_rev.items(), key=lambda x: x[1], reverse=True),
        total_revenue=total_revenue,
        total_orders=total_orders,
        avg_order=avg_order,
    )


# ── ADD-ONS ───────────────────────────────────────────────────────────────────

@vendor_bp.route('/items/<int:item_id>/addon-groups/add', methods=['POST'])
@vendor_required
def addon_group_add(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.items'))
    name = request.form.get('name', '').strip()
    if not name:
        flash('Group name is required.', 'error')
        return redirect(url_for('vendor.item_edit', item_id=item_id))
    required      = request.form.get('required') == '1'
    max_sel       = int(request.form.get('max_selections', 1) or 1)
    group = ItemAddonGroup(item_id=item_id, name=name,
                           required=required, max_selections=max_sel)
    db.session.add(group)
    db.session.commit()
    flash('Add-on group added.', 'success')
    return redirect(url_for('vendor.item_edit', item_id=item_id))


@vendor_bp.route('/addon-groups/<int:group_id>/delete', methods=['POST'])
@vendor_required
def addon_group_delete(group_id):
    group = ItemAddonGroup.query.get_or_404(group_id)
    if group.item.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.items'))
    item_id = group.item_id
    db.session.delete(group)
    db.session.commit()
    flash('Group deleted.', 'success')
    return redirect(url_for('vendor.item_edit', item_id=item_id))


@vendor_bp.route('/addon-groups/<int:group_id>/addons/add', methods=['POST'])
@vendor_required
def addon_add(group_id):
    group = ItemAddonGroup.query.get_or_404(group_id)
    if group.item.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.items'))
    name  = request.form.get('name', '').strip()
    price = float(request.form.get('price', 0) or 0)
    if not name:
        flash('Option name is required.', 'error')
        return redirect(url_for('vendor.item_edit', item_id=group.item_id))
    addon = ItemAddon(group_id=group_id, name=name, price=price)
    db.session.add(addon)
    db.session.commit()
    flash('Option added.', 'success')
    return redirect(url_for('vendor.item_edit', item_id=group.item_id))


@vendor_bp.route('/addons/<int:addon_id>/delete', methods=['POST'])
@vendor_required
def addon_delete(addon_id):
    addon = ItemAddon.query.get_or_404(addon_id)
    if addon.group.item.vendor_id != session['vendor_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('vendor.items'))
    item_id = addon.group.item_id
    db.session.delete(addon)
    db.session.commit()
    flash('Option deleted.', 'success')
    return redirect(url_for('vendor.item_edit', item_id=item_id))
