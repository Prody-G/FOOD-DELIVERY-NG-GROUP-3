from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from models import db, Admin, Customer, Rider, Vendor, Voucher, VoucherUsage, Order, PasswordResetRequest
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in as admin.', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


# ── AUTH ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Welcome back, ' + admin.username + '!', 'success')
            return redirect(url_for('admin.vendors'))
        flash('Invalid email or password.', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin.login'))


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return redirect(url_for('admin.vendors'))


# ── RIDER MANAGEMENT ──────────────────────────────────────────────────────────

@admin_bp.route('/riders')
@admin_required
def riders():
    tab = request.args.get('tab', 'all')
    if tab == 'pending':
        riders_list = Rider.query.filter_by(status='pending').order_by(Rider.created_at.desc()).all()
    elif tab == 'rejected':
        riders_list = Rider.query.filter_by(status='rejected').order_by(Rider.created_at.desc()).all()
    else:
        riders_list = Rider.query.order_by(Rider.created_at.desc()).all()
    return render_template('admin/riders.html', riders=riders_list, tab=tab)


@admin_bp.route('/riders/add', methods=['GET', 'POST'])
@admin_required
def rider_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        vehicle_type = request.form.get('vehicle_type', '')
        license_number = request.form.get('license_number', '').strip()
        password = request.form.get('password', '')
        if Rider.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('admin.rider_add'))
        rider = Rider(name=name, email=email, phone=phone,
                      vehicle_type=vehicle_type, license_number=license_number,
                      status='approved')
        rider.set_password(password)
        db.session.add(rider)
        db.session.commit()
        flash('Rider added successfully.', 'success')
        return redirect(url_for('admin.riders'))
    return render_template('admin/rider_add.html')


@admin_bp.route('/riders/<int:rider_id>/edit', methods=['GET', 'POST'])
@admin_required
def rider_edit(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    if request.method == 'POST':
        rider.name = request.form.get('name', rider.name).strip()
        rider.email = request.form.get('email', rider.email).strip()
        rider.phone = request.form.get('phone', rider.phone or '').strip()
        rider.vehicle_type = request.form.get('vehicle_type', rider.vehicle_type or '')
        rider.license_number = request.form.get('license_number', rider.license_number or '').strip()
        rider.status = request.form.get('status', rider.status)
        new_password = request.form.get('password', '')
        if new_password:
            rider.set_password(new_password)
        db.session.commit()
        flash('Rider updated.', 'success')
        return redirect(url_for('admin.riders'))
    return render_template('admin/rider_edit.html', rider=rider)


@admin_bp.route('/riders/<int:rider_id>/approve', methods=['POST'])
@admin_required
def rider_approve(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    rider.status = 'approved'
    # Set a temporary password if none set
    if not rider.password_hash:
        temp_pw = 'Rider' + str(rider_id) + '!'
        rider.set_password(temp_pw)
        flash(f'Rider approved. Temporary password: {temp_pw}', 'success')
    else:
        flash('Rider approved.', 'success')
    db.session.commit()
    return redirect(url_for('admin.riders', tab='pending'))


@admin_bp.route('/riders/<int:rider_id>/reject', methods=['POST'])
@admin_required
def rider_reject(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    reason = request.form.get('reason', 'Application not approved.')
    rider.status = 'rejected'
    rider.rejection_reason = reason
    db.session.commit()
    flash('Rider application rejected.', 'success')
    return redirect(url_for('admin.riders', tab='pending'))


@admin_bp.route('/riders/<int:rider_id>/delete', methods=['POST'])
@admin_required
def rider_delete(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    # Unlink orders
    for order in rider.orders:
        order.rider_id = None
    db.session.delete(rider)
    db.session.commit()
    flash('Rider deleted.', 'success')
    return redirect(url_for('admin.riders'))


# ── CUSTOMER MANAGEMENT ───────────────────────────────────────────────────────

@admin_bp.route('/customers')
@admin_required
def customers():
    customers_list = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('admin/customers.html', customers=customers_list)


@admin_bp.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@admin_required
def customer_edit(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form.get('name', customer.name).strip()
        customer.email = request.form.get('email', customer.email).strip()
        customer.phone = request.form.get('phone', customer.phone or '').strip()
        customer.address = request.form.get('address', customer.address or '').strip()
        customer.province = request.form.get('province', customer.province or '').strip()
        customer.region = request.form.get('region', customer.region or '').strip()
        customer.city = request.form.get('city', customer.city or '').strip()
        customer.barangay = request.form.get('barangay', customer.barangay or '').strip()
        customer.status = request.form.get('status', customer.status)
        new_password = request.form.get('password', '')
        if new_password:
            customer.set_password(new_password)
        db.session.commit()
        flash('Customer updated.', 'success')
        return redirect(url_for('admin.customers'))
    return render_template('admin/customer_edit.html', customer=customer)


@admin_bp.route('/customers/<int:customer_id>/suspend', methods=['POST'])
@admin_required
def customer_suspend(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.status = 'suspended'
    db.session.commit()
    flash('Customer suspended.', 'success')
    return redirect(url_for('admin.customers'))


@admin_bp.route('/customers/<int:customer_id>/ban', methods=['POST'])
@admin_required
def customer_ban(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.status = 'banned'
    db.session.commit()
    flash('Customer banned.', 'success')
    return redirect(url_for('admin.customers'))


@admin_bp.route('/customers/<int:customer_id>/activate', methods=['POST'])
@admin_required
def customer_activate(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.status = 'active'
    db.session.commit()
    flash('Customer reactivated.', 'success')
    return redirect(url_for('admin.customers'))


@admin_bp.route('/customers/<int:customer_id>/delete', methods=['POST'])
@admin_required
def customer_delete(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted.', 'success')
    return redirect(url_for('admin.customers'))


# ── VENDOR MANAGEMENT ─────────────────────────────────────────────────────────

@admin_bp.route('/vendors')
@admin_required
def vendors():
    tab = request.args.get('tab', 'pending')
    if tab == 'active':
        vendors_list = Vendor.query.filter_by(status='active').order_by(Vendor.created_at.desc()).all()
    elif tab == 'all':
        vendors_list = Vendor.query.order_by(Vendor.created_at.desc()).all()
    else:
        vendors_list = Vendor.query.filter(
            Vendor.status.in_(['pending', 'under_review'])
        ).order_by(Vendor.created_at.desc()).all()
    return render_template('admin/vendors.html', vendors=vendors_list, tab=tab)


@admin_bp.route('/vendors/<int:vendor_id>/approve', methods=['POST'])
@admin_required
def vendor_approve(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'active'
    db.session.commit()
    flash(f'{vendor.shop_name} has been approved and activated.', 'success')
    return redirect(url_for('admin.vendors'))


@admin_bp.route('/vendors/<int:vendor_id>/reject', methods=['POST'])
@admin_required
def vendor_reject(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'rejected'
    db.session.commit()
    flash(f'{vendor.shop_name} application has been rejected.', 'success')
    return redirect(url_for('admin.vendors'))


@admin_bp.route('/vendors/<int:vendor_id>/review', methods=['POST'])
@admin_required
def vendor_set_review(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'under_review'
    db.session.commit()
    flash(f'{vendor.shop_name} marked as Under Review.', 'success')
    return redirect(url_for('admin.vendors'))


@admin_bp.route('/vendors/<int:vendor_id>/suspend', methods=['POST'])
@admin_required
def vendor_suspend(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'suspended'
    db.session.commit()
    flash('Vendor suspended.', 'success')
    return redirect(url_for('admin.vendors'))


@admin_bp.route('/vendors/<int:vendor_id>/ban', methods=['POST'])
@admin_required
def vendor_ban(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'banned'
    db.session.commit()
    flash('Vendor banned.', 'success')
    return redirect(url_for('admin.vendors'))


@admin_bp.route('/vendors/<int:vendor_id>/activate', methods=['POST'])
@admin_required
def vendor_activate(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'active'
    db.session.commit()
    flash('Vendor reactivated.', 'success')
    return redirect(url_for('admin.vendors'))


@admin_bp.route('/vendors/<int:vendor_id>/delete', methods=['POST'])
@admin_required
def vendor_delete(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    for order in list(vendor.orders):
        for item in list(order.items):
            db.session.delete(item)
        db.session.delete(order)
    db.session.delete(vendor)
    db.session.commit()
    flash('Vendor deleted.', 'success')
    return redirect(url_for('admin.vendors'))


@admin_bp.route('/vendors/<int:vendor_id>/view')
@admin_required
def vendor_view(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    return render_template('admin/vendor_view.html', vendor=vendor)


# ── VOUCHER MANAGEMENT ────────────────────────────────────────────────────────

@admin_bp.route('/vouchers')
@admin_required
def vouchers():
    vouchers_list = Voucher.query.order_by(Voucher.created_at.desc()).all()
    return render_template('admin/vouchers.html', vouchers=vouchers_list, now=datetime.utcnow())


@admin_bp.route('/vouchers/add', methods=['GET', 'POST'])
@admin_required
def voucher_add():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        discount_value = float(request.form.get('discount_value', 0))
        max_discount = request.form.get('max_discount', '')
        discount_type = request.form.get('discount_type', 'percentage')
        expiration_str = request.form.get('expiration_date', '')
        global_limit = request.form.get('global_usage_limit', '')
        per_user = int(request.form.get('per_user_limit', 1))

        if Voucher.query.filter_by(code=code).first():
            flash('Voucher code already exists.', 'error')
            return redirect(url_for('admin.vouchers'))

        voucher = Voucher(
            code=code,
            discount_value=discount_value,
            max_discount=float(max_discount) if max_discount else None,
            discount_type=discount_type,
            expiration_date=datetime.strptime(expiration_str, '%Y-%m-%d') if expiration_str else None,
            global_usage_limit=int(global_limit) if global_limit else None,
            per_user_limit=per_user,
        )
        db.session.add(voucher)
        db.session.commit()
        flash('Voucher created.', 'success')
        return redirect(url_for('admin.vouchers'))
    return redirect(url_for('admin.vouchers'))


@admin_bp.route('/vouchers/<int:voucher_id>/edit', methods=['GET', 'POST'])
@admin_required
def voucher_edit(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    if request.method == 'POST':
        voucher.code = request.form.get('code', voucher.code).strip().upper()
        voucher.discount_value = float(request.form.get('discount_value', voucher.discount_value))
        max_discount = request.form.get('max_discount', '')
        voucher.max_discount = float(max_discount) if max_discount else None
        voucher.discount_type = request.form.get('discount_type', voucher.discount_type)
        expiration_str = request.form.get('expiration_date', '')
        voucher.expiration_date = datetime.strptime(expiration_str, '%Y-%m-%d') if expiration_str else None
        global_limit = request.form.get('global_usage_limit', '')
        voucher.global_usage_limit = int(global_limit) if global_limit else None
        voucher.per_user_limit = int(request.form.get('per_user_limit', voucher.per_user_limit))
        db.session.commit()
        flash('Voucher updated.', 'success')
        return redirect(url_for('admin.vouchers'))
    return redirect(url_for('admin.vouchers'))


@admin_bp.route('/vouchers/<int:voucher_id>/disable', methods=['POST'])
@admin_required
def voucher_disable(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    voucher.is_active = not voucher.is_active
    db.session.commit()
    flash('Voucher ' + ('enabled' if voucher.is_active else 'disabled') + '.', 'success')
    return redirect(url_for('admin.vouchers'))


@admin_bp.route('/vouchers/<int:voucher_id>/delete', methods=['POST'])
@admin_required
def voucher_delete(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    db.session.delete(voucher)
    db.session.commit()
    flash('Voucher deleted.', 'success')
    return redirect(url_for('admin.vouchers'))


# ── PASSWORD RESET MANAGEMENT ─────────────────────────────────────────────────

@admin_bp.route('/password-resets')
@admin_required
def password_resets():
    requests_list = PasswordResetRequest.query.order_by(
        PasswordResetRequest.requested_at.desc()).all()
    return render_template('admin/password_resets.html', requests=requests_list,
                           base_url=request.host_url.rstrip('/'))


@admin_bp.route('/password-resets/<int:req_id>/approve', methods=['POST'])
@admin_required
def password_reset_approve(req_id):
    reset_req = PasswordResetRequest.query.get_or_404(req_id)
    reset_req.generate_token()
    reset_req.status = 'approved'
    reset_req.processed_at = datetime.utcnow()
    db.session.commit()
    flash(f'Reset approved. Token link generated for {reset_req.user_email}.', 'success')
    return redirect(url_for('admin.password_resets'))


@admin_bp.route('/password-resets/<int:req_id>/deny', methods=['POST'])
@admin_required
def password_reset_deny(req_id):
    reset_req = PasswordResetRequest.query.get_or_404(req_id)
    reset_req.status = 'denied'
    reset_req.processed_at = datetime.utcnow()
    db.session.commit()
    flash('Reset request denied.', 'success')
    return redirect(url_for('admin.password_resets'))


# ── ORDER MANAGEMENT ──────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@admin_required
def orders():
    orders_list = Order.query.order_by(Order.created_at.desc()).all()
    riders_list = Rider.query.filter_by(status='approved').all()
    return render_template('admin/orders.html', orders=orders_list, riders=riders_list)


@admin_bp.route('/orders/<int:order_id>/assign-rider', methods=['POST'])
@admin_required
def assign_rider(order_id):
    order = Order.query.get_or_404(order_id)
    rider_id = request.form.get('rider_id')
    order.rider_id = int(rider_id) if rider_id else None
    if rider_id:
        order.status = 'out_for_delivery'
    db.session.commit()
    flash('Rider assigned.', 'success')
    return redirect(url_for('admin.orders'))
