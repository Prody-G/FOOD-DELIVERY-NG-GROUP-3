from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, jsonify)
from functools import wraps
from models import (db, Customer, Vendor, MenuItem, Category, Order, OrderItem,
                    Voucher, VoucherUsage, PasswordResetRequest, RiderRating, ChatMessage,
                    get_shipping_fee)
from datetime import datetime

customer_bp = Blueprint('customer', __name__)


def customer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'customer_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('customer.login'))
        customer = Customer.query.get(session['customer_id'])
        if not customer or customer.status in ('suspended', 'banned'):
            session.pop('customer_id', None)
            flash('Your account is not active.', 'error')
            return redirect(url_for('customer.login'))
        return f(*args, **kwargs)
    return decorated


# ── AUTH ──────────────────────────────────────────────────────────────────────

@customer_bp.route('/customer/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 8 or len(password) > 16:
            flash('Password must be 8–16 characters.', 'error')
            return redirect(url_for('customer.register'))
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('customer.register'))
        if Customer.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('customer.register'))

        customer = Customer(name=name, email=email, phone=phone)
        customer.set_password(password)
        db.session.add(customer)
        db.session.commit()
        session['customer_id'] = customer.id
        session['customer_name'] = customer.name
        flash('Account created! Welcome, ' + name + '!', 'success')
        return redirect(url_for('customer.landing'))
    return render_template('customer/register.html')


@customer_bp.route('/customer/login', methods=['GET', 'POST'])
def login():
    if 'customer_id' in session:
        return redirect(url_for('customer.landing'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        customer = Customer.query.filter_by(email=email).first()
        if customer and customer.check_password(password):
            if customer.status in ('suspended', 'banned'):
                flash('Your account is ' + customer.status + '.', 'error')
            else:
                session['customer_id'] = customer.id
                session['customer_name'] = customer.name
                next_url = request.args.get('next', url_for('customer.landing'))
                return redirect(next_url)
        else:
            flash('Invalid email or password.', 'error')
    return render_template('customer/login.html')


@customer_bp.route('/customer/logout')
def logout():
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    return redirect(url_for('customer.landing'))


@customer_bp.route('/customer/profile', methods=['GET', 'POST'])
@customer_required
def profile():
    customer = Customer.query.get(session['customer_id'])
    if request.method == 'POST':
        customer.name = request.form.get('name', customer.name).strip()
        customer.phone = request.form.get('phone', customer.phone or '').strip()
        customer.address = request.form.get('address', customer.address or '').strip()
        customer.province = request.form.get('province', customer.province or '').strip()
        customer.region = request.form.get('region', customer.region or '').strip()
        customer.city = request.form.get('city', customer.city or '').strip()
        customer.barangay = request.form.get('barangay', customer.barangay or '').strip()
        new_pw = request.form.get('new_password', '')
        if new_pw:
            old_pw = request.form.get('current_password', '')
            if not customer.check_password(old_pw):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('customer.profile'))
            customer.set_password(new_pw)
        session['customer_name'] = customer.name
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('customer.profile'))
    return render_template('customer/profile.html', customer=customer)


# ── LANDING PAGE ──────────────────────────────────────────────────────────────

@customer_bp.route('/')
def landing():
    search = request.args.get('search', '').strip()
    query = Vendor.query.filter_by(status='active')
    if search:
        query = query.filter(Vendor.shop_name.ilike(f'%{search}%'))
    vendors = query.order_by(Vendor.created_at.desc()).all()
    return render_template('customer/landing.html', vendors=vendors, search=search)


# ── RESTAURANT / MENU ─────────────────────────────────────────────────────────

@customer_bp.route('/restaurant/<int:vendor_id>')
def restaurant(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    if vendor.status != 'active':
        flash('This restaurant is currently unavailable.', 'error')
        return redirect(url_for('customer.landing'))
    categories = Category.query.filter_by(vendor_id=vendor_id).all()
    uncategorized = MenuItem.query.filter_by(
        vendor_id=vendor_id, category_id=None, is_available=True).all()
    return render_template('customer/restaurant.html', vendor=vendor,
                           categories=categories, uncategorized=uncategorized)


# ── CHECKOUT ──────────────────────────────────────────────────────────────────

@customer_bp.route('/customer/estimate-shipping', methods=['POST'])
@customer_required
def estimate_shipping():
    data = request.get_json(silent=True) or {}
    vendor_id         = data.get('vendor_id')
    customer_barangay = data.get('customer_barangay', '').strip()
    item_count        = int(data.get('item_count', 1) or 1)
    vendor = Vendor.query.get(vendor_id) if vendor_id else None
    vendor_barangay = (vendor.vendor_barangay or '') if vendor else ''
    dist_km, fee = get_shipping_fee(vendor_barangay, customer_barangay, item_count)
    return jsonify({'shipping_fee': fee, 'distance_km': dist_km,
                    'vendor_barangay': vendor_barangay})


@customer_bp.route('/customer/checkout')
@customer_required
def checkout():
    customer = Customer.query.get(session['customer_id'])
    return render_template('customer/checkout.html', customer=customer)


@customer_bp.route('/customer/place-order', methods=['POST'])
@customer_required
def place_order():
    customer = Customer.query.get(session['customer_id'])
    data = request.get_json()

    if not data or not data.get('items'):
        return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

    vendor_id = data.get('vendor_id')
    vendor = Vendor.query.get(vendor_id)
    if not vendor or vendor.status != 'active':
        return jsonify({'success': False, 'message': 'Restaurant unavailable.'}), 400

    # Build order items and calculate subtotal
    subtotal = 0.0
    order_items = []
    for cart_item in data['items']:
        menu_item = MenuItem.query.get(cart_item.get('id'))
        if not menu_item or menu_item.vendor_id != vendor_id or not menu_item.is_available:
            return jsonify({'success': False, 'message': f"Item '{cart_item.get('name')}' unavailable."}), 400
        qty = int(cart_item.get('quantity', 1))
        line_price = menu_item.price * qty
        subtotal += line_price
        order_items.append(OrderItem(
            menu_item_id=menu_item.id,
            name=menu_item.name,
            quantity=qty,
            price=menu_item.price,
        ))

    # Validate voucher
    discount = 0.0
    voucher_id = None
    voucher_code = data.get('voucher_code', '').strip().upper()
    if voucher_code:
        voucher = Voucher.query.filter_by(code=voucher_code, is_active=True).first()
        if voucher:
            now = datetime.utcnow()
            if voucher.expiration_date and voucher.expiration_date < now:
                return jsonify({'success': False, 'message': 'Voucher has expired.'}), 400
            # Check global usage
            if voucher.global_usage_limit is not None:
                used_count = VoucherUsage.query.filter_by(voucher_id=voucher.id).count()
                if used_count >= voucher.global_usage_limit:
                    return jsonify({'success': False, 'message': 'Voucher usage limit reached.'}), 400
            # Check per-user usage
            user_usage = VoucherUsage.query.filter_by(
                voucher_id=voucher.id, customer_id=customer.id).count()
            if user_usage >= (voucher.per_user_limit or 1):
                return jsonify({'success': False, 'message': 'You have already used this voucher.'}), 400

            if voucher.discount_type == 'percentage':
                discount = subtotal * (voucher.discount_value / 100)
                if voucher.max_discount:
                    discount = min(discount, voucher.max_discount)
            else:
                discount = min(voucher.discount_value, subtotal)
            voucher_id = voucher.id
        else:
            return jsonify({'success': False, 'message': 'Invalid or inactive voucher.'}), 400

    total = max(0, subtotal - discount)
    # Calculate shipping fee based on vendor barangay vs customer barangay + item count
    customer_barangay = data.get('barangay', '').strip()
    vendor_barangay   = vendor.vendor_barangay or ''
    total_item_qty    = sum(int(i.get('quantity', 1)) for i in data['items'])
    distance_km, shipping_fee = get_shipping_fee(vendor_barangay, customer_barangay, total_item_qty)
    grand_total = round(total + shipping_fee, 2)
    payment_method = data.get('payment_method', 'cod')

    order = Order(
        customer_id=customer.id,
        vendor_id=vendor_id,
        voucher_id=voucher_id,
        status='pending',
        payment_method=payment_method,
        payment_status='pending',
        subtotal=subtotal,
        discount=discount,
        shipping_fee=shipping_fee,
        distance_km=distance_km,
        total=grand_total,
        delivery_address=data.get('delivery_address', ''),
        city=data.get('city', ''),
        barangay=customer_barangay,
        notes=data.get('notes', ''),
    )
    db.session.add(order)
    db.session.flush()  # get order.id

    for oi in order_items:
        oi.order_id = order.id
        db.session.add(oi)

    if voucher_id:
        usage = VoucherUsage(voucher_id=voucher_id, customer_id=customer.id, order_id=order.id)
        db.session.add(usage)

    # Remember customer's delivery location for next time
    if customer_barangay:
        customer.barangay = customer_barangay
    if data.get('city'):
        customer.city = data.get('city')
    if data.get('delivery_address'):
        customer.address = data.get('delivery_address')

    db.session.commit()
    return jsonify({'success': True, 'order_id': order.id})


# ── ORDERS ────────────────────────────────────────────────────────────────────

@customer_bp.route('/customer/orders')
@customer_required
def orders():
    customer = Customer.query.get(session['customer_id'])
    orders_list = Order.query.filter_by(customer_id=customer.id).order_by(
        Order.created_at.desc()).all()
    return render_template('customer/orders.html', customer=customer, orders=orders_list)


@customer_bp.route('/customer/orders/<int:order_id>')
@customer_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != session['customer_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('customer.orders'))
    has_rated = RiderRating.query.filter_by(
        order_id=order_id, customer_id=session['customer_id']).first() is not None
    can_rate = order.status == 'delivered' and order.rider_id and not has_rated
    return render_template('customer/order_detail.html', order=order,
                           has_rated=has_rated, can_rate=can_rate)


@customer_bp.route('/customer/orders/<int:order_id>/cancel', methods=['POST'])
@customer_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != session['customer_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('customer.orders'))
    if order.status not in ('pending', 'preparing'):
        flash('This order can no longer be cancelled.', 'error')
        return redirect(url_for('customer.orders'))
    order.status = 'cancelled'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Order cancelled successfully.', 'success')
    return redirect(url_for('customer.orders'))


@customer_bp.route('/customer/orders/<int:order_id>/rate', methods=['POST'])
@customer_required
def rate_rider(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != session['customer_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    if order.status != 'delivered' or not order.rider_id:
        return jsonify({'error': 'Cannot rate this order'}), 400
    if RiderRating.query.filter_by(order_id=order_id, customer_id=session['customer_id']).first():
        return jsonify({'error': 'Already rated'}), 400
    rating_val = int(request.form.get('rating', 0))
    if rating_val < 1 or rating_val > 5:
        flash('Invalid rating value.', 'error')
        return redirect(url_for('customer.order_detail', order_id=order_id))
    comment = request.form.get('comment', '').strip()
    new_rating = RiderRating(
        rider_id=order.rider_id, order_id=order_id,
        customer_id=session['customer_id'], rating=rating_val, comment=comment or None)
    db.session.add(new_rating)
    # Update rider avg_rating
    rider = order.rider
    all_rider_ratings = RiderRating.query.filter_by(rider_id=rider.id).all()
    count = len(all_rider_ratings) + 1
    total = sum(r.rating for r in all_rider_ratings) + rating_val
    rider.avg_rating = round(total / count, 2)
    rider.total_ratings = count
    db.session.commit()
    flash('Thank you for your rating.', 'success')
    return redirect(url_for('customer.order_detail', order_id=order_id))


@customer_bp.route('/customer/chat/<int:order_id>/messages')
@customer_required
def customer_chat_messages(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != session['customer_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    msgs = ChatMessage.query.filter_by(order_id=order_id).order_by(ChatMessage.sent_at).all()
    for m in msgs:
        if m.sender_type == 'rider' and not m.is_read:
            m.is_read = True
    db.session.commit()
    return jsonify([{
        'id': m.id, 'sender': m.sender_type,
        'message': m.message,
        'time': m.sent_at.strftime('%H:%M')
    } for m in msgs])


@customer_bp.route('/customer/chat/<int:order_id>/send', methods=['POST'])
@customer_required
def customer_send_chat(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != session['customer_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json(silent=True) or {}
    msg_text = (data.get('message') or '').strip()
    if not msg_text:
        return jsonify({'error': 'Empty message'}), 400
    msg = ChatMessage(order_id=order_id, sender_type='customer',
                      sender_id=session['customer_id'], message=msg_text)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'ok': True})


# ── VOUCHER VALIDATION (AJAX) ─────────────────────────────────────────────────

@customer_bp.route('/customer/validate-voucher', methods=['POST'])
@customer_required
def validate_voucher():
    customer = Customer.query.get(session['customer_id'])
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    subtotal = float(data.get('subtotal', 0))

    voucher = Voucher.query.filter_by(code=code, is_active=True).first()
    if not voucher:
        return jsonify({'valid': False, 'message': 'Invalid or inactive voucher.'})

    now = datetime.utcnow()
    if voucher.expiration_date and voucher.expiration_date < now:
        return jsonify({'valid': False, 'message': 'Voucher has expired.'})

    if voucher.global_usage_limit is not None:
        used = VoucherUsage.query.filter_by(voucher_id=voucher.id).count()
        if used >= voucher.global_usage_limit:
            return jsonify({'valid': False, 'message': 'Voucher usage limit reached.'})

    user_usage = VoucherUsage.query.filter_by(
        voucher_id=voucher.id, customer_id=customer.id).count()
    if user_usage >= (voucher.per_user_limit or 1):
        return jsonify({'valid': False, 'message': 'You have already used this voucher.'})

    if voucher.discount_type == 'percentage':
        discount = subtotal * (voucher.discount_value / 100)
        if voucher.max_discount:
            discount = min(discount, voucher.max_discount)
    else:
        discount = min(voucher.discount_value, subtotal)

    return jsonify({
        'valid': True,
        'discount': round(discount, 2),
        'message': f'Voucher applied! You save ₱{discount:.2f}',
    })


# ── PASSWORD RESET ────────────────────────────────────────────────────────────

@customer_bp.route('/customer/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        customer = Customer.query.filter_by(email=email).first()
        if customer:
            existing = PasswordResetRequest.query.filter_by(
                user_type='customer', user_id=customer.id, status='pending').first()
            if not existing:
                reset_req = PasswordResetRequest(
                    user_type='customer',
                    user_id=customer.id,
                    user_email=customer.email,
                    user_name=customer.name,
                )
                db.session.add(reset_req)
                db.session.commit()
        flash('If an account exists with that email, a reset request has been submitted. '
              'Please wait for admin to process it.', 'success')
        return redirect(url_for('customer.login'))
    return render_template('customer/forgot_password.html')


@customer_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_req = PasswordResetRequest.query.filter_by(token=token, status='approved').first()
    if not reset_req:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('customer.login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('customer.reset_password', token=token))

        # Apply to correct user type
        if reset_req.user_type == 'customer':
            user = Customer.query.get(reset_req.user_id)
        elif reset_req.user_type == 'vendor':
            user = Vendor.query.get(reset_req.user_id)
        elif reset_req.user_type == 'rider':
            user = Rider.query.get(reset_req.user_id)
        else:
            user = None

        if user:
            user.set_password(password)
            reset_req.status = 'completed'
            reset_req.processed_at = datetime.utcnow()
            db.session.commit()
            flash('Password reset successfully! You can now log in.', 'success')
        else:
            flash('User not found.', 'error')
        return redirect(url_for('customer.login'))

    return render_template('customer/reset_password.html', token=token)


# Shared forgot password for rider and vendor
@customer_bp.route('/rider/forgot-password', methods=['GET', 'POST'])
def rider_forgot_password():
    from models import Rider
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        rider = Rider.query.filter_by(email=email).first()
        if rider:
            existing = PasswordResetRequest.query.filter_by(
                user_type='rider', user_id=rider.id, status='pending').first()
            if not existing:
                reset_req = PasswordResetRequest(
                    user_type='rider',
                    user_id=rider.id,
                    user_email=rider.email,
                    user_name=rider.name,
                )
                db.session.add(reset_req)
                db.session.commit()
        flash('Reset request submitted. Please wait for admin to process it.', 'success')
        return redirect(url_for('rider.login'))
    return render_template('customer/forgot_password.html', portal='rider')


@customer_bp.route('/vendor/forgot-password', methods=['GET', 'POST'])
def vendor_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        vendor = Vendor.query.filter_by(email=email).first()
        if vendor:
            existing = PasswordResetRequest.query.filter_by(
                user_type='vendor', user_id=vendor.id, status='pending').first()
            if not existing:
                reset_req = PasswordResetRequest(
                    user_type='vendor',
                    user_id=vendor.id,
                    user_email=vendor.email,
                    user_name=vendor.shop_name,
                )
                db.session.add(reset_req)
                db.session.commit()
        flash('Reset request submitted. Please wait for admin to process it.', 'success')
        return redirect(url_for('vendor.login'))
    return render_template('customer/forgot_password.html', portal='vendor')
