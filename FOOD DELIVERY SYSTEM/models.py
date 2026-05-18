from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import math

# ── LOCATION DATA ─────────────────────────────────────────────────────────────
# Approximate lat/lng center of each Makati City and Taguig City barangay.
# Used for distance-based shipping fee calculation.
BARANGAY_COORDS = {
    # Makati City
    'Bangkal':               (14.5342, 121.0062),
    'Bel-Air':               (14.5660, 121.0130),
    'Carmona':               (14.5608, 121.0040),
    'Cembo':                 (14.5471, 121.0582),
    'Comembo':               (14.5420, 121.0572),
    'Dasmarias':             (14.5750, 121.0170),
    'East Rembo':            (14.5432, 121.0578),
    'Forbes Park':           (14.5600, 121.0120),
    'Guadalupe Nuevo':       (14.5621, 121.0392),
    'Guadalupe Viejo':       (14.5640, 121.0361),
    'Kasilawan':             (14.5430, 121.0570),
    'La Paz':                (14.5540, 121.0012),
    'Magallanes':            (14.5351, 121.0022),
    'Olympia':               (14.5770, 121.0090),
    'Palanan':               (14.5440, 121.0011),
    'Pembo':                 (14.5451, 121.0591),
    'Pinagkaisahan':         (14.5411, 121.0562),
    'Pio Del Pilar':         (14.5491, 121.0072),
    'Pitogo':                (14.5431, 121.0591),
    'Poblacion':             (14.5651, 121.0321),
    'Post Proper Northside': (14.5431, 121.0622),
    'Post Proper Southside': (14.5391, 121.0622),
    'Rizal':                 (14.5452, 121.0601),
    'San Antonio':           (14.5701, 121.0091),
    'San Isidro':            (14.5341, 121.0112),
    'San Lorenzo':           (14.5621, 121.0201),
    'Santa Cruz':            (14.5331, 121.0121),
    'Singkamas':             (14.5601, 121.0011),
    'South Cembo':           (14.5451, 121.0571),
    'Tejeros':               (14.5401, 121.0551),
    'Urdaneta':              (14.5621, 121.0222),
    'Valenzuela':            (14.5401, 121.0581),
    'West Rembo':            (14.5451, 121.0561),
    # UMak Campus (special)
    'UMak Campus':           (14.5547, 121.0244),
    # Taguig City
    'Fort Bonifacio':        (14.5444, 121.0531),
    'Western Bicutan':       (14.5121, 121.0531),
    'Eastern Bicutan':       (14.5091, 121.0781),
    'Central Bicutan':       (14.5101, 121.0641),
    'Ususan':                (14.4821, 121.0851),
    'Tuktukan':              (14.5241, 121.0621),
    'Sta. Ana':              (14.5061, 121.0761),
    'Calzada':               (14.5111, 121.0711),
    'Hagonoy':               (14.5071, 121.0631),
    'Ibayo-Tipas':           (14.5271, 121.0701),
    'Ligid-Tipas':           (14.5221, 121.0731),
    'Lower Bicutan':         (14.5061, 121.0711),
    'New Lower Bicutan':     (14.5071, 121.0721),
    'North Daang Hari':      (14.4901, 121.0661),
    'North Signal Village':  (14.5011, 121.0611),
    'Palingon':              (14.5301, 121.0521),
    'Pinagsama':             (14.5211, 121.0641),
    'South Daang Hari':      (14.4821, 121.0641),
    'South Signal Village':  (14.5001, 121.0611),
    'Tanyag':                (14.4811, 121.0811),
    'Upper Bicutan':         (14.5111, 121.0731),
    'Wawa':                  (14.5221, 121.0761),
    'Central Signal Village':(14.5011, 121.0621),
    # Taguig City (extended barangays)
    'Maharlika Village':     (14.4921, 121.0781),
    'Bagong Tanyag':         (14.4811, 121.0801),
    'Bagumbayan':            (14.5181, 121.0721),
    'Katuparan':             (14.4961, 121.0741),
    'Bambang':               (14.5151, 121.0671),
    'San Miguel':            (14.5101, 121.0601),
    'Napindan':              (14.5271, 121.0821),
    # Mandaluyong border (zone routing only — not in customer checkout)
    'Barangka Ilaya':        (14.5771, 121.0421),
    'Barangka Itaas':        (14.5791, 121.0451),
    'Barangka Drive':        (14.5741, 121.0401),
    'Malamig':               (14.5811, 121.0431),
    'Plainview':             (14.5801, 121.0461),
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Return great-circle distance in km between two lat/lng points."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 2)


def calculate_shipping_fee(distance_km, item_count=1):
    """Distance-based shipping fee + per-item surcharge.
    Base ₱30 covers the first 1 km; +₱12 per additional km; cap ₱150.
    Then ₱5 per item quantity on top (min 1 item).
    """
    base = 30.0
    per_km = 12.0
    if distance_km <= 1.0:
        fee = base
    else:
        fee = base + (distance_km - 1.0) * per_km
    item_surcharge = max(0, int(item_count) - 1) * 5.0
    return round(min(max(fee + item_surcharge, 30.0), 150.0), 2)


def get_shipping_fee(vendor_barangay, customer_barangay, item_count=1):
    """Look up both barangay coordinates and return (distance_km, shipping_fee).
    Falls back to minimum fee if either barangay is not found.
    """
    v_coords = BARANGAY_COORDS.get(vendor_barangay)
    c_coords = BARANGAY_COORDS.get(customer_barangay)
    if not v_coords or not c_coords:
        return 0.0, calculate_shipping_fee(0, item_count)
    dist = haversine_km(v_coords[0], v_coords[1], c_coords[0], c_coords[1])
    return dist, calculate_shipping_fee(dist, item_count)

db = SQLAlchemy()


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    province = db.Column(db.String(100))
    region = db.Column(db.String(100))
    city = db.Column(db.String(100))
    barangay = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, suspended, banned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='customer', lazy=True)
    voucher_usages = db.relationship('VoucherUsage', backref='customer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Rider(db.Model):
    __tablename__ = 'riders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    vehicle_type = db.Column(db.String(50))
    license_number = db.Column(db.String(50))
    id_number = db.Column(db.String(50))
    profile_picture = db.Column(db.String(255))  # uploaded profile photo
    # Walker document uploads
    cor_document = db.Column(db.String(255))
    school_id_document = db.Column(db.String(255))
    psa_document = db.Column(db.String(255))
    # Motorcycle document uploads
    unit_photo = db.Column(db.String(255))
    plate_photo = db.Column(db.String(255))
    valid_license = db.Column(db.String(255))
    drivers_license = db.Column(db.String(255))
    # pending, approved, rejected, suspended
    status = db.Column(db.String(20), default='pending')
    rejection_reason = db.Column(db.Text)
    is_online = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(255))
    avg_rating = db.Column(db.Float, default=5.0)
    total_ratings = db.Column(db.Integer, default=0)
    total_accepted = db.Column(db.Integer, default=0)
    total_offered = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='rider', lazy=True)

    @property
    def batch_level(self):
        if self.avg_rating >= 4.8:
            return 'Gold'
        elif self.avg_rating >= 4.5:
            return 'Silver'
        elif self.avg_rating >= 4.0:
            return 'Bronze'
        return 'Standard'

    @property
    def acceptance_rate(self):
        if not self.total_offered:
            return 100.0
        return round(self.total_accepted / self.total_offered * 100, 1)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    cover_banner = db.Column(db.String(255))
    shop_logo = db.Column(db.String(255))
    shop_type = db.Column(db.String(50), default='restaurant')  # restaurant, cafe, bakery, etc.
    address = db.Column(db.String(255))
    business_address = db.Column(db.String(255))
    business_city = db.Column(db.String(100))
    vendor_barangay = db.Column(db.String(100))  # used for shipping distance calc
    description = db.Column(db.Text)
    proposal = db.Column(db.Text)
    # pending, under_review, active, suspended, banned, rejected
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    categories = db.relationship('Category', backref='vendor', lazy=True,
                                 cascade='all, delete-orphan')
    menu_items = db.relationship('MenuItem', backref='vendor', lazy=True,
                                 cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='vendor', lazy=True,
                              foreign_keys='Order.vendor_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    items = db.relationship('MenuItem', backref='category', lazy=True)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)


class Voucher(db.Model):
    __tablename__ = 'vouchers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_value = db.Column(db.Float, nullable=False)
    max_discount = db.Column(db.Float)
    # percentage, fixed
    discount_type = db.Column(db.String(20), default='percentage')
    expiration_date = db.Column(db.DateTime)
    global_usage_limit = db.Column(db.Integer)
    per_user_limit = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    usages = db.relationship('VoucherUsage', backref='voucher', lazy=True)


class VoucherUsage(db.Model):
    __tablename__ = 'voucher_usages'
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id'), nullable=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'), nullable=True)
    # pending, confirmed, preparing, ready_for_pickup, out_for_delivery, delivered, cancelled
    status = db.Column(db.String(30), default='pending')
    # cod, gcash
    payment_method = db.Column(db.String(20))
    payment_status = db.Column(db.String(20), default='pending')
    subtotal = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    delivery_address = db.Column(db.String(255))
    province = db.Column(db.String(100))
    region = db.Column(db.String(100))
    city = db.Column(db.String(100))
    barangay = db.Column(db.String(100))
    gcash_reference = db.Column(db.String(50))
    notes = db.Column(db.Text)
    proof_of_delivery = db.Column(db.String(255))
    # going_to_vendor → going_to_customer (set when rider marks picked up)
    delivery_phase = db.Column(db.String(30), default='going_to_vendor')
    shipping_fee = db.Column(db.Float, default=0.0)   # rider\'s delivery earnings
    distance_km = db.Column(db.Float, nullable=True)  # calculated vendor→customer distance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True,
                            cascade='all, delete-orphan')
    voucher = db.relationship('Voucher', backref='orders', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    selected_addons = db.relationship('OrderItemAddon', backref='order_item',
                                      lazy=True, cascade='all, delete-orphan')


# ── ADD-ONS ───────────────────────────────────────────────────────────────────

class ItemAddonGroup(db.Model):
    """A group of add-on choices for a menu item (e.g. 'Size', 'Extras')."""
    __tablename__ = 'item_addon_groups'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)       # e.g. "Size", "Extras"
    required = db.Column(db.Boolean, default=False)        # must pick one
    max_selections = db.Column(db.Integer, default=1)      # 1=single, >1=multi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('MenuItem', backref='addon_groups')
    options = db.relationship('ItemAddon', backref='group', lazy=True,
                              cascade='all, delete-orphan')


class ItemAddon(db.Model):
    """A single add-on option within a group (e.g. 'Large +₱20')."""
    __tablename__ = 'item_addons'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('item_addon_groups.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)       # e.g. "Large", "Extra Cheese"
    price = db.Column(db.Float, default=0.0)               # extra charge (0 = free)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OrderItemAddon(db.Model):
    """Records which add-on options were chosen for an order item."""
    __tablename__ = 'order_item_addons'
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False)
    addon_id = db.Column(db.Integer, db.ForeignKey('item_addons.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)       # snapshot at order time
    price = db.Column(db.Float, default=0.0)


class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), nullable=False)  # customer, vendor, rider
    user_id = db.Column(db.Integer, nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    user_name = db.Column(db.String(100))
    token = db.Column(db.String(100), unique=True)
    # pending, approved, denied, completed
    status = db.Column(db.String(20), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    def generate_token(self):
        self.token = secrets.token_urlsafe(32)


# ── RIDER EARNINGS ────────────────────────────────────────────────────────────
PLATFORM_FEE_RATE = 0.20  # 20% platform fee (like Foodpanda)

class RiderEarning(db.Model):
    __tablename__ = 'rider_earnings'
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    order_total = db.Column(db.Float, default=0)       # full order amount
    platform_fee = db.Column(db.Float, default=0)      # 20% deducted
    rider_earnings = db.Column(db.Float, default=0)    # 80% kept by rider
    payment_method = db.Column(db.String(20))          # cod or gcash
    # pending = not yet cashed out; cashed_out = included in a cashout
    status = db.Column(db.String(20), default='pending')
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    rider = db.relationship('Rider', backref='earnings')
    order = db.relationship('Order', backref='earning')


class RiderCashout(db.Model):
    __tablename__ = 'rider_cashouts'
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id'), nullable=False)
    amount = db.Column(db.Float, default=0)
    # pending = requested; completed = paid out; rejected = denied
    status = db.Column(db.String(20), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    rider = db.relationship('Rider', backref='cashouts')


SHIFT_ZONES = {
    'makati_cbd': {
        'name': 'Makati CBD',
        'barangays': ['Bel-Air', 'San Lorenzo', 'Pio Del Pilar', 'San Antonio', 'Urdaneta',
                      'Palanan', 'San Isidro', 'Bangkal', 'Magallanes', 'Forbes Park', 'Dasmarias'],
    },
    'poblacion': {
        'name': 'Poblacion Area',
        'barangays': ['Poblacion', 'Valenzuela', 'Olympia', 'Tejeros', 'Santa Cruz',
                      'Kasilawan', 'Carmona', 'La Paz', 'Singkamas'],
    },
    'bgc_taguig': {
        'name': 'BGC / Taguig',
        'barangays': ['Fort Bonifacio', 'Pinagsama', 'Western Bicutan', 'Upper Bicutan',
                      'Central Bicutan', 'Lower Bicutan', 'New Lower Bicutan', 'Maharlika Village',
                      'Bagong Tanyag', 'Tanyag', 'Bagumbayan', 'North Daang Hari', 'South Daang Hari',
                      'Central Signal Village', 'North Signal Village', 'South Signal Village',
                      'Katuparan', 'Ususan', 'Tuktukan', 'Bambang', 'San Miguel', 'Hagonoy',
                      'Wawa', 'Sta. Ana', 'Calzada', 'Ibayo-Tipas', 'Ligid-Tipas', 'Palingon',
                      'Napindan', 'Eastern Bicutan'],
    },
    'rockwell_guadalupe': {
        'name': 'Rockwell / Guadalupe',
        'barangays': ['Guadalupe Viejo', 'Guadalupe Nuevo', 'Pinagkaisahan', 'Pitogo'],
    },
    'umak_campus': {
        'name': 'UMak Campus Area',
        'barangays': ['West Rembo', 'Pembo', 'East Rembo', 'Cembo', 'South Cembo',
                      'Comembo', 'Rizal', 'Post Proper Northside', 'Post Proper Southside',
                      'UMak Campus'],
    },
    'mandaluyong_border': {
        'name': 'Mandaluyong Border',
        'barangays': ['Guadalupe Viejo', 'Guadalupe Nuevo', 'Barangka Ilaya', 'Barangka Itaas',
                      'Barangka Drive', 'Malamig', 'Plainview'],
    },
}
# Backward-compat: old display-name zone strings map to new keys
_ZONE_NAME_TO_KEY = {v['name']: k for k, v in SHIFT_ZONES.items()}


class RiderShift(db.Model):
    __tablename__ = 'rider_shifts'
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id'), nullable=False)
    zone = db.Column(db.String(100))          # zone key, e.g. 'makati_cbd'
    shift_date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50))      # human-readable, e.g. '08:00 - 16:00' or 'Open Shift'
    start_time = db.Column(db.String(5))      # HH:MM  (None for open shifts)
    end_time = db.Column(db.String(5))        # HH:MM  (None for open shifts)
    is_open_shift = db.Column(db.Boolean, default=False)
    # booked, completed, cancelled
    status = db.Column(db.String(20), default='booked')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rider = db.relationship('Rider', backref='shifts')


class RiderRating(db.Model):
    __tablename__ = 'rider_ratings'
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rider = db.relationship('Rider', backref='ratings')
    order = db.relationship('Order', backref='rider_rating', uselist=False)


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    sender_type = db.Column(db.String(10))  # 'rider' or 'customer'
    sender_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    order = db.relationship('Order', backref='chat_messages')

