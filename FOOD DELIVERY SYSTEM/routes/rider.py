from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from functools import wraps
from models import db, Rider, Order, RiderEarning, RiderCashout, PLATFORM_FEE_RATE, RiderRating, ChatMessage, RiderShift, SHIFT_ZONES, _ZONE_NAME_TO_KEY, get_shipping_fee
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import os
import uuid

rider_bp = Blueprint('rider', __name__)

ALLOWED_DOC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

def save_rider_doc(file, folder):
    if not file or not file.filename:
        return None
    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    if ext.lstrip('.') not in ALLOWED_DOC_EXTENSIONS:
        return None
    filename = str(uuid.uuid4()) + ext
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return 'uploads/rider_docs/' + filename


def rider_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'rider_id' not in session:
            flash('Please log in as a rider.', 'error')
            return redirect(url_for('rider.login'))
        rider = Rider.query.get(session['rider_id'])
        if not rider or rider.status != 'approved':
            session.pop('rider_id', None)
            flash('Your account is not approved or has been suspended.', 'error')
            return redirect(url_for('rider.login'))
        return f(*args, **kwargs)
    return decorated


@rider_bp.route('/apply', methods=['GET', 'POST'])
def apply():
    ACCEPTED_CITIES = {'makati', 'taguig', 'makati city', 'taguig city'}
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        vehicle_type = request.form.get('vehicle_type', '')
        license_number = request.form.get('license_number', '').strip()
        id_number = request.form.get('id_number', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        rider_city = request.form.get('rider_city', '').strip()
        location = request.form.get('location', '').strip()

        if len(password) < 8 or len(password) > 16:
            flash('Password must be 8–16 characters.', 'error')
            return redirect(url_for('rider.apply'))
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('rider.apply'))
        if rider_city.lower() not in ACCEPTED_CITIES:
            flash('Sorry, we only accept riders based in Makati City or Taguig City.', 'error')
            return redirect(url_for('rider.apply'))
        if Rider.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('rider.apply'))

        full_location = f'{location}, {rider_city}' if location else rider_city

        doc_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'rider_docs')
        cor_doc = school_id_doc = psa_doc = None
        unit_photo = plate_photo = valid_license = drivers_license = None

        if vehicle_type == 'Walker':
            cor_doc       = save_rider_doc(request.files.get('cor_document'), doc_folder)
            school_id_doc = save_rider_doc(request.files.get('school_id_document'), doc_folder)
            psa_doc       = save_rider_doc(request.files.get('psa_document'), doc_folder)
        elif vehicle_type == 'Motorcycle':
            unit_photo      = save_rider_doc(request.files.get('moto_unit_photo'), doc_folder)
            plate_photo     = save_rider_doc(request.files.get('moto_plate_photo'), doc_folder)
            cor_doc         = save_rider_doc(request.files.get('moto_cor_document'), doc_folder)
            valid_license   = save_rider_doc(request.files.get('moto_valid_license'), doc_folder)
            drivers_license = save_rider_doc(request.files.get('moto_drivers_license'), doc_folder)
        elif vehicle_type == 'Bicycle':
            unit_photo    = save_rider_doc(request.files.get('bike_unit_photo'), doc_folder)
            school_id_doc = save_rider_doc(request.files.get('bike_school_id_document'), doc_folder)
            cor_doc       = save_rider_doc(request.files.get('bike_cor_document'), doc_folder)

        rider = Rider(name=name, email=email, phone=phone,
                      vehicle_type=vehicle_type, status='pending',
                      location=full_location,
                      cor_document=cor_doc,
                      school_id_document=school_id_doc,
                      psa_document=psa_doc,
                      unit_photo=unit_photo,
                      plate_photo=plate_photo,
                      valid_license=valid_license,
                      drivers_license=drivers_license)
        rider.set_password(password)
        db.session.add(rider)
        db.session.commit()
        flash('Application submitted! Please wait for admin approval.', 'success')
        return redirect(url_for('rider.login'))
    return render_template('rider/apply.html')


@rider_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'rider_id' in session:
        return redirect(url_for('rider.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        rider = Rider.query.filter_by(email=email).first()
        if rider and rider.check_password(password):
            if rider.status == 'pending':
                flash('Your application is still under review.', 'error')
            elif rider.status == 'rejected':
                flash('Your application was rejected. Reason: ' + (rider.rejection_reason or 'N/A'), 'error')
            elif rider.status == 'suspended':
                flash('Your account has been suspended.', 'error')
            else:
                session['rider_id'] = rider.id
                session['rider_name'] = rider.name
                return redirect(url_for('rider.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('rider/login.html')


@rider_bp.route('/logout')
def logout():
    session.pop('rider_id', None)
    session.pop('rider_name', None)
    return redirect(url_for('rider.login'))


@rider_bp.route('/dashboard')
@rider_required
def dashboard():
    rider = Rider.query.get(session['rider_id'])
    active_orders = Order.query.filter_by(
        rider_id=rider.id, status='out_for_delivery').order_by(Order.created_at.desc()).all()

    # Zone → city mapping (only Makati City and Taguig City served)
    ZONE_CITY_MAP = {
        'makati_cbd':          'Makati City',
        'poblacion':           'Makati City',
        'rockwell_guadalupe':  'Makati City',
        'umak_campus':         'Makati City',
        'mandaluyong_border':  'Makati City',
        'bgc_taguig':          'Taguig City',
    }

    available_orders = []
    if rider.is_online:
        today_shifts = RiderShift.query.filter_by(
            rider_id=rider.id, status='booked', shift_date=date.today()).all()
        q = Order.query.filter_by(status='ready_for_pickup', rider_id=None)
        if today_shifts:
            # Collect cities covered by today's shifts
            zone_cities = set()
            for s in today_shifts:
                key = s.zone if s.zone in SHIFT_ZONES else _ZONE_NAME_TO_KEY.get(s.zone, '')
                city = ZONE_CITY_MAP.get(key)
                if city:
                    zone_cities.add(city)
            if zone_cities:
                # Filter orders by customer drop-off city (order.city), not restaurant city
                q = q.filter(Order.city.in_(list(zone_cities)))
        available_orders = q.order_by(Order.created_at.desc()).all()
    completed_orders = Order.query.filter_by(
        rider_id=rider.id, status='delivered').order_by(Order.created_at.desc()).limit(20).all()
    # Wallet
    pending_earnings = RiderEarning.query.filter_by(rider_id=rider.id, status='pending').all()
    total_pending = round(sum(e.rider_earnings for e in pending_earnings), 2)
    all_earnings = RiderEarning.query.filter_by(rider_id=rider.id).all()
    total_earned = round(sum(e.rider_earnings for e in all_earnings), 2)
    recent_cashouts = RiderCashout.query.filter_by(rider_id=rider.id).order_by(
        RiderCashout.requested_at.desc()).limit(5).all()
    # Earnings breakdown
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = today_start - timedelta(days=today_start.weekday())
    today_earnings = round(sum(
        e.rider_earnings for e in all_earnings
        if e.earned_at and e.earned_at >= today_start), 2)
    week_earnings = round(sum(
        e.rider_earnings for e in all_earnings
        if e.earned_at and e.earned_at >= week_start), 2)
    today_deliveries = sum(1 for e in all_earnings if e.earned_at and e.earned_at >= today_start)
    week_deliveries  = sum(1 for e in all_earnings if e.earned_at and e.earned_at >= week_start)
    # Performance metrics
    total_delivered = Order.query.filter_by(rider_id=rider.id, status='delivered').count()
    total_accepted_orders = Order.query.filter_by(rider_id=rider.id).filter(
        Order.status.in_(['out_for_delivery', 'delivered'])).count()
    completion_rate = round(total_delivered / total_accepted_orders * 100, 1) \
        if total_accepted_orders else 100.0
    # Upcoming shifts
    upcoming_shifts = RiderShift.query.filter_by(rider_id=rider.id, status='booked').filter(
        RiderShift.shift_date >= date.today()).order_by(RiderShift.shift_date).limit(3).all()
    return render_template('rider/dashboard.html', rider=rider,
                           active_orders=active_orders,
                           available_orders=available_orders,
                           completed_orders=completed_orders,
                           total_pending=total_pending,
                           total_earned=total_earned,
                           recent_cashouts=recent_cashouts,
                           today_earnings=today_earnings,
                           week_earnings=week_earnings,
                           today_deliveries=today_deliveries,
                           week_deliveries=week_deliveries,
                           completion_rate=completion_rate,
                           total_delivered=total_delivered,
                           upcoming_shifts=upcoming_shifts)


@rider_bp.route('/toggle-online', methods=['POST'])
@rider_required
def toggle_online():
    rider = Rider.query.get(session['rider_id'])
    rider.is_online = not rider.is_online
    db.session.commit()
    return redirect(url_for('rider.dashboard'))


@rider_bp.route('/orders/<int:order_id>/accept', methods=['POST'])
@rider_required
def accept_order(order_id):
    order = Order.query.get_or_404(order_id)
    rider = Rider.query.get(session['rider_id'])
    if order.status != 'ready_for_pickup' or order.rider_id:
        flash('Order is no longer available.', 'error')
        return redirect(url_for('rider.dashboard'))
    order.rider_id = rider.id
    order.status = 'out_for_delivery'
    order.delivery_phase = 'going_to_vendor'
    order.updated_at = datetime.utcnow()
    rider.total_offered = (rider.total_offered or 0) + 1
    rider.total_accepted = (rider.total_accepted or 0) + 1
    db.session.commit()
    flash('Delivery accepted. Head to the restaurant to pick up the order.', 'success')
    return redirect(url_for('rider.dashboard'))


@rider_bp.route('/orders/<int:order_id>/picked-up', methods=['POST'])
@rider_required
def mark_picked_up(order_id):
    order = Order.query.get_or_404(order_id)
    if order.rider_id != session['rider_id'] or order.status != 'out_for_delivery':
        flash('Unauthorized.', 'error')
        return redirect(url_for('rider.dashboard'))
    order.delivery_phase = 'going_to_customer'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Order picked up. Deliver to the customer now.', 'success')
    return redirect(url_for('rider.dashboard'))


@rider_bp.route('/orders/<int:order_id>/cancel-delivery', methods=['POST'])
@rider_required
def cancel_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    if order.rider_id != session['rider_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('rider.dashboard'))
    if order.delivery_phase != 'going_to_vendor':
        flash('You cannot cancel after picking up the order.', 'error')
        return redirect(url_for('rider.dashboard'))
    order.status = 'ready_for_pickup'
    order.rider_id = None
    order.delivery_phase = None
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Delivery cancelled. The order is available for another rider.', 'success')
    return redirect(url_for('rider.dashboard'))


@rider_bp.route('/orders/<int:order_id>/delivered', methods=['POST'])
@rider_required
def mark_delivered(order_id):
    order = Order.query.get_or_404(order_id)
    if order.rider_id != session['rider_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('rider.dashboard'))
    proof_file = request.files.get('proof_photo')
    if proof_file and proof_file.filename:
        proof_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'delivery_proofs')
        proof_path = save_rider_doc(proof_file, proof_folder)
        if proof_path:
            order.proof_of_delivery = proof_path
    order.status = 'delivered'
    order.updated_at = datetime.utcnow()
    order.payment_status = 'paid'  # mark paid for both COD (collected) and GCash (online)
    # Rider earns 100% of the shipping fee (food order commission stays with restaurant)
    shipping = round(float(order.shipping_fee or 0), 2)
    earning = RiderEarning(
        rider_id=order.rider_id,
        order_id=order.id,
        order_total=shipping,
        platform_fee=0.0,
        rider_earnings=shipping,
        payment_method=order.payment_method,
        status='pending'
    )
    db.session.add(earning)
    db.session.commit()
    flash('Order marked as delivered.', 'success')
    return redirect(url_for('rider.dashboard'))


@rider_bp.route('/cashout', methods=['POST'])
@rider_required
def cashout():
    rider = Rider.query.get(session['rider_id'])
    pending = RiderEarning.query.filter_by(rider_id=rider.id, status='pending').all()
    total = round(sum(e.rider_earnings for e in pending), 2)
    if total <= 0:
        flash('No pending earnings to cash out.', 'error')
        return redirect(url_for('rider.dashboard'))
    new_cashout = RiderCashout(rider_id=rider.id, amount=total, status='pending')
    db.session.add(new_cashout)
    for e in pending:
        e.status = 'cashed_out'
    db.session.commit()
    flash(f'Cash out request of ₱{total:.2f} submitted.', 'success')
    return redirect(url_for('rider.dashboard'))


@rider_bp.route('/profile')
@rider_required
def profile():
    rider = Rider.query.get(session['rider_id'])
    total_delivered = Order.query.filter_by(rider_id=rider.id, status='delivered').count()
    total_accepted_orders = Order.query.filter_by(rider_id=rider.id).filter(
        Order.status.in_(['out_for_delivery', 'delivered'])).count()
    completion_rate = round(total_delivered / total_accepted_orders * 100, 1) \
        if total_accepted_orders else 100.0
    recent_ratings = RiderRating.query.filter_by(rider_id=rider.id).order_by(
        RiderRating.created_at.desc()).limit(10).all()
    all_earnings = RiderEarning.query.filter_by(rider_id=rider.id).all()
    total_earned = round(sum(e.rider_earnings for e in all_earnings), 2)
    return render_template('rider/profile.html', rider=rider,
                           total_delivered=total_delivered,
                           completion_rate=completion_rate,
                           recent_ratings=recent_ratings,
                           total_earned=total_earned)


@rider_bp.route('/profile/upload-photo', methods=['POST'])
@rider_required
def upload_profile_photo():
    rider = Rider.query.get(session['rider_id'])
    photo = request.files.get('profile_picture')
    if not photo or not photo.filename:
        flash('No file selected.', 'error')
        return redirect(url_for('rider.profile'))
    ext = os.path.splitext(secure_filename(photo.filename))[1].lower()
    if ext.lstrip('.') not in {'png', 'jpg', 'jpeg', 'webp', 'gif'}:
        flash('Invalid file type. Use JPG, PNG, or WebP.', 'error')
        return redirect(url_for('rider.profile'))
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'riders')
    os.makedirs(folder, exist_ok=True)
    filename = str(uuid.uuid4()) + ext
    photo.save(os.path.join(folder, filename))
    rider.profile_picture = f'uploads/riders/{filename}'
    db.session.commit()
    flash('Profile photo updated.', 'success')
    return redirect(url_for('rider.profile'))


@rider_bp.route('/shifts', methods=['GET', 'POST'])
@rider_required
def shifts():
    rider = Rider.query.get(session['rider_id'])
    if request.method == 'POST':
        zone_key   = request.form.get('zone', '').strip()
        start_now  = request.form.get('start_now') == '1'

        # ── Zone validation ───────────────────────────────────────────────────
        if zone_key not in SHIFT_ZONES:
            flash('Invalid zone selected.', 'error')
            return redirect(url_for('rider.shifts'))

        today = date.today()

        if start_now:
            # ── Start Now: today's date, current time as start ────────────────
            shift_date = today
            now = datetime.now()
            # Round start to nearest 5 minutes
            start_min_total = now.hour * 60 + now.minute
            start_min_total = (start_min_total // 5) * 5
            sh = start_min_total // 60
            sm = start_min_total % 60
            start_time = f"{sh:02d}:{sm:02d}"

            end_time = request.form.get('end_time', '').strip()
            if not end_time:
                flash('Please select an end time.', 'error')
                return redirect(url_for('rider.shifts'))
            try:
                eh, em = map(int, end_time.split(':'))
            except (ValueError, TypeError):
                flash('Invalid end time.', 'error')
                return redirect(url_for('rider.shifts'))

            duration_minutes = (eh * 60 + em) - start_min_total
            if duration_minutes < 120:
                flash('Shift must be at least 2 hours.', 'error')
                return redirect(url_for('rider.shifts'))
            if duration_minutes > 480:
                flash('Shift cannot exceed 8 hours.', 'error')
                return redirect(url_for('rider.shifts'))
        else:
            # ── Scheduled booking ─────────────────────────────────────────────
            shift_date_str = request.form.get('shift_date', '').strip()
            start_time     = request.form.get('start_time', '').strip()
            end_time       = request.form.get('end_time', '').strip()

            try:
                shift_date = date.fromisoformat(shift_date_str)
            except (ValueError, TypeError):
                flash('Invalid date.', 'error')
                return redirect(url_for('rider.shifts'))

            if shift_date < today:
                flash('Cannot book a shift in the past.', 'error')
                return redirect(url_for('rider.shifts'))
            if shift_date > today + timedelta(days=14):
                flash('Shifts can only be booked up to 14 days in advance.', 'error')
                return redirect(url_for('rider.shifts'))

            if not start_time or not end_time:
                flash('Please set start and end time for your shift.', 'error')
                return redirect(url_for('rider.shifts'))
            try:
                sh, sm = map(int, start_time.split(':'))
                eh, em = map(int, end_time.split(':'))
                if not (0 <= sh <= 23 and 0 <= sm <= 59 and 0 <= eh <= 23 and 0 <= em <= 59):
                    raise ValueError
            except (ValueError, TypeError):
                flash('Invalid time format.', 'error')
                return redirect(url_for('rider.shifts'))

            duration_minutes = (eh * 60 + em) - (sh * 60 + sm)
            if duration_minutes < 120:
                flash('Shift duration must be at least 2 hours.', 'error')
                return redirect(url_for('rider.shifts'))
            if duration_minutes > 480:
                flash('Shift duration cannot exceed 8 hours.', 'error')
                return redirect(url_for('rider.shifts'))

            # 8-hour advance booking (only for today's date)
            if shift_date == today:
                local_now = datetime.now()
                now_min   = local_now.hour * 60 + local_now.minute
                start_min = sh * 60 + sm
                if start_min - now_min < 480:
                    flash('Scheduled shifts must be booked at least 8 hours before the start time. '
                          'Use "Start Shift Now" to begin a shift immediately.', 'error')
                    return redirect(url_for('rider.shifts'))

        # ── Weekly limit (max 10 per week) ────────────────────────────────────
        week_start = shift_date - timedelta(days=shift_date.weekday())
        week_end   = week_start + timedelta(days=6)
        week_count = RiderShift.query.filter_by(rider_id=rider.id, status='booked').filter(
            RiderShift.shift_date >= week_start,
            RiderShift.shift_date <= week_end
        ).count()
        if week_count >= 10:
            flash('Maximum 10 shifts per week reached for that week.', 'error')
            return redirect(url_for('rider.shifts'))

        # ── 4-hour gap check on same date ─────────────────────────────────────
        sh_s = int(start_time[:2]) * 60 + int(start_time[3:])
        eh_e = int(end_time[:2]) * 60 + int(end_time[3:])
        GAP  = 240  # 4 hours in minutes
        existing = RiderShift.query.filter_by(
            rider_id=rider.id, shift_date=shift_date, status='booked').all()
        for ex in existing:
            if ex.start_time and ex.end_time:
                exs = int(ex.start_time[:2]) * 60 + int(ex.start_time[3:])
                exe = int(ex.end_time[:2]) * 60 + int(ex.end_time[3:])
                if not (eh_e <= exs - GAP or sh_s >= exe + GAP):
                    flash('A 4-hour gap is required between shifts on the same day.', 'error')
                    return redirect(url_for('rider.shifts'))

        time_slot = f"{start_time} \u2013 {end_time}"
        new_shift = RiderShift(
            rider_id=rider.id,
            zone=zone_key,
            shift_date=shift_date,
            time_slot=time_slot,
            start_time=start_time,
            end_time=end_time,
            is_open_shift=False,
            status='booked',
        )
        db.session.add(new_shift)
        db.session.commit()
        zone_name = SHIFT_ZONES[zone_key]['name']
        msg = ('Shift started: ' if start_now else 'Shift booked: ')
        flash(f'{msg}{zone_name} \u2014 {time_slot} on {shift_date.strftime("%b %d, %Y")}.', 'success')
        return redirect(url_for('rider.shifts'))

    # ── GET ───────────────────────────────────────────────────────────────────
    today = date.today()
    all_shifts = RiderShift.query.filter_by(rider_id=rider.id).filter(
        RiderShift.shift_date >= today - timedelta(days=3)).order_by(
        RiderShift.shift_date, RiderShift.time_slot).all()

    week_start      = today - timedelta(days=today.weekday())
    week_end        = week_start + timedelta(days=6)
    this_week_count = sum(1 for s in all_shifts
                          if week_start <= s.shift_date <= week_end and s.status == 'booked')
    booked_dates    = [s.shift_date.isoformat() for s in all_shifts if s.status == 'booked']

    return render_template('rider/shifts.html', rider=rider,
                           upcoming_shifts=all_shifts,
                           this_week_count=this_week_count,
                           booked_dates=booked_dates,
                           shift_zones=SHIFT_ZONES,
                           today=today.isoformat(),
                           max_date=(today + timedelta(days=14)).isoformat())


@rider_bp.route('/shifts/<int:shift_id>/cancel', methods=['POST'])
@rider_required
def cancel_shift(shift_id):
    shift = RiderShift.query.get_or_404(shift_id)
    if shift.rider_id != session['rider_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('rider.shifts'))
    shift.status = 'cancelled'
    db.session.commit()
    flash('Shift cancelled.', 'success')
    return redirect(url_for('rider.shifts'))


@rider_bp.route('/chat/<int:order_id>/messages')
@rider_required
def rider_chat_messages(order_id):
    order = Order.query.get_or_404(order_id)
    if order.rider_id != session['rider_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    msgs = ChatMessage.query.filter_by(order_id=order_id).order_by(ChatMessage.sent_at).all()
    # Mark customer messages as read
    for m in msgs:
        if m.sender_type == 'customer' and not m.is_read:
            m.is_read = True
    db.session.commit()
    return jsonify([{
        'id': m.id, 'sender': m.sender_type,
        'message': m.message,
        'time': m.sent_at.strftime('%H:%M')
    } for m in msgs])


@rider_bp.route('/chat/<int:order_id>/send', methods=['POST'])
@rider_required
def rider_send_chat(order_id):
    order = Order.query.get_or_404(order_id)
    if order.rider_id != session['rider_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json(silent=True) or {}
    msg_text = (data.get('message') or '').strip()
    if not msg_text:
        return jsonify({'error': 'Empty message'}), 400
    msg = ChatMessage(order_id=order_id, sender_type='rider',
                      sender_id=session['rider_id'], message=msg_text)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'ok': True})
