# UniFood Delivery System: Technical Overview

## 1. System Architecture
The UniFood Delivery System is a multi-tenant platform built using a **Monolithic Model-View-Controller (MVC)** architecture. It utilizes a centralized database to coordinate activities between four distinct user roles: Customers, Vendors, Riders, and Administrators.

### **Technical Stack**
- **Backend:** Python / Flask
- **Database:** SQLite with SQLAlchemy ORM
- **Frontend:** HTML5, Vanilla CSS (Custom UI), JavaScript (ES6+)
- **Authentication:** Session-based with Werkzeug password hashing

---

## 2. Core Components & Logic

### **A. Location & Zone Engine (`models.py`)**
The system uses a custom **Location Intelligence** module based on the **Haversine Formula**.
- **Barangay Mapping:** Stores exact coordinates for Makati and Taguig barangays.
- **Dynamic Shipping:** Fees are calculated based on the great-circle distance between Vendor and Customer.
    - *Base Fee:* ₱30 for the first 1km.
    - *Distance Surcharge:* ₱12/km.
    - *Quantity Surcharge:* ₱5 per additional item.
- **Zone Enforcement:** Riders book shifts in specific "Zones" (e.g., Makati CBD). The system filters available orders so riders only see deliveries within their active shift's city.

### **B. Financial Logic**
- **Rider Earnings:** Riders earn 100% of the calculated shipping fee.
- **Platform Fees:** The system is designed to handle a 20% platform fee on food totals (configurable in `models.py`).
- **Cashout System:** Riders accumulate "Pending" earnings which must be approved by an Admin for payout.

---

## 3. User Portals (Layouts & Features)

### **1. Customer Portal**
- **Discovery:** Searchable landing page for active restaurants.
- **Checkout:** AJAX-powered cart with real-time shipping fee estimation and voucher validation.
- **Order Tracking:** A multi-step status timeline (`Pending` -> `Delivered`).
- **Interaction:** Live chat with the assigned rider once the order is picked up.

### **2. Vendor Portal**
- **Menu Management:** Complete control over categories, items, and item availability.
- **Order Flow:** Vendors must manually "Confirm" and mark orders as "Ready for Pickup" before they appear to riders.
- **Analytics:** Basic dashboard showing shop performance and order history.

### **3. Rider Portal**
- **Shift Management:** A 14-day advance booking system for specific zones.
- **Execution:** Mobile-optimized dashboard to Accept, Pick Up, and Deliver orders.
- **Proof of Delivery:** Mandatory photo upload to complete a delivery.
- **Performance:** Tracks Acceptance Rate and Average Rating.

### **4. Admin Dashboard**
- **Oversight:** Approve/Reject new Rider and Vendor applications.
- **Voucher Engine:** Create global or user-specific discounts with usage limits and expiry dates.
- **Safety:** Ability to suspend or ban users and manage password reset requests.

---

## 4. System Flow (Order Lifecycle)

1.  **Placement:** Customer selects items -> System calculates distance/fee -> Order created (`pending`).
2.  **Confirmation:** Vendor accepts order (`confirmed`) -> Starts cooking (`preparing`).
3.  **Handoff:** Vendor marks `ready_for_pickup`.
4.  **Assignment:** Online Rider with a matching shift accepts the order -> Status becomes `out_for_delivery`.
5.  **Transit:** Rider picks up order -> Chat opens -> Rider navigates to Customer.
6.  **Completion:** Rider uploads photo and marks `delivered` -> Earnings credited to Rider -> Customer rates the experience.

---

## 5. Code Structure Overview

- `app.py`: The entry point. Initializes the Flask app, registers Blueprints, and seeds the default Admin.
- `models.py`: The heart of the system. Contains the database schema and business logic for distance/fees.
- `routes/`: Modularized logic for each portal:
    - `admin.py`: Management and approval logic.
    - `customer.py`: Shopping and checkout flow.
    - `rider.py`: Shift booking and delivery execution.
    - `vendor.py`: Menu and shop management.
- `static/`: Contains `main.css` (the custom design system) and `uploads/` for images (banners, logos, delivery proofs).
- `templates/`: Structured by role (`/admin`, `/customer`, etc.) for clean separation of concerns.
