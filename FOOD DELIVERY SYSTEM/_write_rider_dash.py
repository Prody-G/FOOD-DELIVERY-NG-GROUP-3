content = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Rider Dashboard - Unifood</title>
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
<style>
body { background:#f1f5f9; margin:0; }
.r-header {
  background:linear-gradient(135deg,#111827,#1e293b);
  color:#fff; padding:0 2rem; height:60px;
  display:flex; align-items:center; justify-content:space-between;
  position:sticky; top:0; z-index:100;
  box-shadow:0 2px 12px rgba(0,0,0,.18);
}
.r-brand { font-size:1.1rem; font-weight:800; letter-spacing:-.01em; }
.r-brand span { color:#4ade80; }
.r-wrap { max-width:960px; margin:0 auto; padding:1.75rem 1.25rem; }

/* Step tracker */
.order-steps { display:flex; align-items:center; gap:0; margin:1rem 0 1.25rem; }
.step { display:flex; flex-direction:column; align-items:center; flex:1; position:relative; }
.step:not(:last-child)::after {
  content:''; position:absolute; top:13px; left:50%; width:100%;
  height:2px; background:#e5e7eb; z-index:0;
}
.step.done:not(:last-child)::after { background:#22c55e; }
.step-dot {
  width:28px; height:28px; border-radius:50%; border:2px solid #e5e7eb;
  background:#fff; display:flex; align-items:center; justify-content:center;
  font-size:.7rem; font-weight:700; z-index:1; position:relative;
}
.step.done .step-dot { background:#22c55e; border-color:#22c55e; color:#fff; }
.step.active .step-dot { border-color:#22c55e; color:#22c55e; font-weight:800; }
.step-label { font-size:.65rem; text-align:center; margin-top:.35rem; color:#6b7280; line-height:1.3; }
.step.done .step-label { color:#16a34a; }
.step.active .step-label { color:#111827; font-weight:600; }

/* Delivery card */
.delivery-card {
  background:#fff; border-radius:14px;
  box-shadow:0 1px 6px rgba(0,0,0,.08);
  border:1px solid #e5e7eb; margin-bottom:1rem;
  overflow:hidden;
}
.dc-head {
  padding:1rem 1.25rem .8rem;
  display:flex; justify-content:space-between; align-items:flex-start;
  border-bottom:1px solid #f3f4f6;
}
.dc-order-id { font-size:.75rem; color:#6b7280; margin-bottom:.2rem; }
.dc-name { font-size:1rem; font-weight:700; color:#111827; }
.dc-sub { font-size:.8rem; color:#6b7280; margin-top:.15rem; }
.dc-amount { font-size:1.1rem; font-weight:800; color:#22c55e; }
.dc-payment { font-size:.72rem; color:#6b7280; text-align:right; }
.dc-body { padding:.9rem 1.25rem; }
.dc-items { font-size:.82rem; color:#4b5563; margin-bottom:.75rem; line-height:1.6; }
.dc-address { font-size:.82rem; color:#6b7280; display:flex; gap:.4rem; align-items:flex-start; margin-bottom:.75rem; }
.dc-foot { padding:.8rem 1.25rem 1rem; background:#f9fafb; display:flex; gap:.6rem; flex-wrap:wrap; align-items:center; }

/* Available order card */
.avail-card {
  background:#fff; border-radius:14px;
  box-shadow:0 1px 6px rgba(0,0,0,.08);
  border:1px solid #e5e7eb; margin-bottom:.85rem;
  overflow:hidden;
}
.avail-head {
  padding:.85rem 1.2rem .7rem;
  border-bottom:1px solid #f3f4f6;
  display:flex; justify-content:space-between; align-items:flex-start;
}
.avail-shop { font-size:.95rem; font-weight:700; color:#111827; }
.avail-meta { font-size:.78rem; color:#6b7280; margin-top:.15rem; }
.avail-body { padding:.8rem 1.2rem; font-size:.82rem; color:#4b5563; }
.avail-foot { padding:.7rem 1.2rem .9rem; display:flex; justify-content:flex-end; }

/* Proof upload box */
.proof-wrap {
  border:2px dashed #d1d5db; border-radius:10px;
  padding:1rem; text-align:center; cursor:pointer;
  transition:.18s; background:#fafafa; margin:.6rem 0;
}
.proof-wrap:hover { border-color:#22c55e; background:#f0fdf4; }
.proof-wrap.has-file { border-color:#22c55e; border-style:solid; }

/* Section header */
.section-hd {
  display:flex; align-items:center; gap:.6rem;
  margin-bottom:1rem; margin-top:1.5rem;
}
.section-hd h3 { font-size:1rem; font-weight:700; color:#111827; margin:0; }
.section-hd .badge-count {
  background:#22c55e; color:#fff; font-size:.72rem; font-weight:700;
  border-radius:999px; padding:.15rem .55rem;
}

/* Stats */
.r-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:.85rem; margin-bottom:1.5rem; }
.r-stat { background:#fff; border-radius:12px; padding:1rem 1.25rem;
  box-shadow:0 1px 4px rgba(0,0,0,.07); border-top:3px solid #e5e7eb; }
.r-stat.green { border-top-color:#22c55e; }
.r-stat.amber { border-top-color:#f59e0b; }
.r-stat-val { font-size:1.8rem; font-weight:800; color:#111827; }
.r-stat-label { font-size:.75rem; color:#6b7280; margin-top:.15rem; }
</style>
</head>
<body>

<header class="r-header">
  <div class="r-brand">Uni<span>Food</span> <span style="font-weight:400;opacity:.6;font-size:.85rem;">Rider</span></div>
  <div style="display:flex;align-items:center;gap:.75rem;">
    <span style="font-size:.85rem;opacity:.7;">{{ rider.name }}</span>
    <a href="{{ url_for('rider.logout') }}" class="btn btn-danger btn-sm">Logout</a>
  </div>
</header>

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
  <div style="max-width:960px;margin:1rem auto 0;padding:0 1.25rem;">
    {% for cat, msg in messages %}
    <div class="flash flash-{{ 'success' if cat == 'success' else 'error' }}">{{ msg }}</div>
    {% endfor %}
  </div>
  <script>setTimeout(()=>document.querySelectorAll('.flash').forEach(f=>f.remove()),4000)</script>
  {% endif %}
{% endwith %}

<div class="r-wrap">

  <!-- Stats -->
  <div class="r-stats">
    <div class="r-stat amber">
      <div class="r-stat-val">{{ available_orders|length }}</div>
      <div class="r-stat-label">Available Deliveries</div>
    </div>
    <div class="r-stat green">
      <div class="r-stat-val">{{ active_orders|length }}</div>
      <div class="r-stat-label">My Active Orders</div>
    </div>
    <div class="r-stat">
      <div class="r-stat-val">{{ completed_orders|length }}</div>
      <div class="r-stat-label">Completed</div>
    </div>
  </div>

  <!-- Active Deliveries -->
  {% if active_orders %}
  <div class="section-hd">
    <h3>My Active Deliveries</h3>
    <span class="badge-count">{{ active_orders|length }}</span>
  </div>
  {% for order in active_orders %}
  <div class="delivery-card">
    <!-- 5-step progress -->
    <div style="padding:.85rem 1.25rem .5rem;">
      <div class="order-steps">
        {% set steps = [('Order Placed','pending'),('Restaurant Accepted','confirmed'),('Seeking Rider','ready_for_pickup'),('On the Way','out_for_delivery'),('Delivered','delivered')] %}
        {% set status_order = ['pending','confirmed','ready_for_pickup','out_for_delivery','delivered'] %}
        {% set current_idx = status_order.index(order.status) if order.status in status_order else 0 %}
        {% for label, st in steps %}
          {% set idx = loop.index0 %}
          <div class="step {{ 'done' if idx < current_idx else ('active' if idx == current_idx else '') }}">
            <div class="step-dot">{{ '✓' if idx < current_idx else (idx+1) }}</div>
            <div class="step-label">{{ label }}</div>
          </div>
        {% endfor %}
      </div>
    </div>
    <div class="dc-head">
      <div>
        <div class="dc-order-id">Order #{{ order.id }} &middot; {{ order.created_at.strftime('%b %d, %H:%M') }}</div>
        <div class="dc-name">{{ order.customer.name }}</div>
        <div class="dc-sub">{{ order.customer.phone or '' }}</div>
      </div>
      <div style="text-align:right;">
        <div class="dc-amount">&#8369;{{ '%.2f'|format(order.total) }}</div>
        <div class="dc-payment">{{ order.payment_method|upper }}</div>
      </div>
    </div>
    <div class="dc-body">
      <div style="font-size:.78rem;font-weight:600;color:#6b7280;margin-bottom:.3rem;">PICK UP AT</div>
      <div style="font-size:.88rem;font-weight:600;color:#111827;margin-bottom:.6rem;">{{ order.vendor.shop_name }}</div>
      <div class="dc-items">
        {% for item in order.items %}{{ item.quantity }}&times; {{ item.name }}{% if not loop.last %},  {% endif %}{% endfor %}
      </div>
      <div class="dc-address">
        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="flex-shrink:0;margin-top:2px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        {{ order.delivery_address }}, Brgy. {{ order.barangay }}, {{ order.city }}, {{ order.province }}
      </div>
      {% if order.notes %}
      <div style="font-size:.8rem;color:#6b7280;background:#f9fafb;padding:.5rem .75rem;border-radius:6px;">Note: {{ order.notes }}</div>
      {% endif %}
    </div>
    <div class="dc-foot">
      <!-- Proof of delivery upload form -->
      <form method="POST" enctype="multipart/form-data"
            action="{{ url_for('rider.mark_delivered', order_id=order.id) }}"
            style="flex:1;">
        <div class="proof-wrap" id="proofBox{{ order.id }}" onclick="document.getElementById('proofInput{{ order.id }}').click()">
          <div id="proofBox{{ order.id }}_placeholder">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color:#9ca3af;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            <div style="font-size:.8rem;color:#9ca3af;margin-top:.3rem;">Tap to upload proof of delivery photo</div>
          </div>
          <div id="proofBox{{ order.id }}_preview" style="display:none;"></div>
        </div>
        <input type="file" id="proofInput{{ order.id }}" name="proof_photo" accept="image/*" style="display:none"
               onchange="handleProof(this,'proofBox{{ order.id }}')">
        <button type="submit" class="btn btn-primary btn-full" style="margin-top:.5rem;">
          Confirm Delivery
        </button>
      </form>
    </div>
  </div>
  {% endfor %}
  {% endif %}

  <!-- Available Orders -->
  {% if available_orders %}
  <div class="section-hd">
    <h3>Available Deliveries</h3>
    <span class="badge-count" style="background:#f59e0b;">{{ available_orders|length }}</span>
  </div>
  {% for order in available_orders %}
  <div class="avail-card">
    <div class="avail-head">
      <div>
        <div class="avail-shop">{{ order.vendor.shop_name }}</div>
        <div class="avail-meta">Order #{{ order.id }} &middot; {{ order.created_at.strftime('%b %d, %H:%M') }}</div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:1rem;font-weight:800;color:#22c55e;">&#8369;{{ '%.2f'|format(order.total) }}</div>
        <div style="font-size:.72rem;color:#6b7280;">{{ order.payment_method|upper }}</div>
      </div>
    </div>
    <div class="avail-body">
      <div style="margin-bottom:.4rem;">
        <span style="font-size:.74rem;font-weight:600;color:#6b7280;">DELIVER TO</span><br>
        <strong>{{ order.customer.name }}</strong> &mdash;
        {{ order.delivery_address }}, Brgy. {{ order.barangay }}, {{ order.city }}
      </div>
      <div style="color:#6b7280;">
        {% for item in order.items %}{{ item.quantity }}&times; {{ item.name }}{% if not loop.last %}, {% endif %}{% endfor %}
      </div>
    </div>
    <div class="avail-foot">
      <form method="POST" action="{{ url_for('rider.accept_order', order_id=order.id) }}">
        <button class="btn btn-primary">Accept Delivery</button>
      </form>
    </div>
  </div>
  {% endfor %}
  {% else %}
  {% if not active_orders %}
  <div style="text-align:center;padding:3rem 1rem;color:#9ca3af;">
    <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="margin:0 auto 1rem;display:block;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
    <p style="font-size:.95rem;">No deliveries available right now.<br>Check back soon!</p>
  </div>
  {% endif %}
  {% endif %}

  <!-- Delivery History -->
  {% if completed_orders %}
  <div class="section-hd" style="margin-top:2rem;">
    <h3>Recent Deliveries</h3>
  </div>
  <div class="card" style="overflow:hidden;">
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>#</th><th>Customer</th><th>Vendor</th><th>Address</th><th>Total</th><th>Payment</th><th>Proof</th><th>Date</th></tr>
        </thead>
        <tbody>
          {% for order in completed_orders %}
          <tr>
            <td>#{{ order.id }}</td>
            <td>{{ order.customer.name }}</td>
            <td>{{ order.vendor.shop_name }}</td>
            <td style="font-size:.8rem;">{{ order.city }}, {{ order.barangay }}</td>
            <td>&#8369;{{ '%.2f'|format(order.total) }}</td>
            <td>{{ order.payment_method|upper }}</td>
            <td>
              {% if order.proof_of_delivery %}
              <a href="{{ url_for('static', filename=order.proof_of_delivery) }}" target="_blank"
                 style="color:#22c55e;font-size:.8rem;">View</a>
              {% else %}—{% endif %}
            </td>
            <td style="font-size:.8rem;">{{ order.updated_at.strftime('%b %d') if order.updated_at else '—' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
  {% endif %}

</div>

<script>
function handleProof(input, boxId) {
  const box = document.getElementById(boxId);
  const placeholder = document.getElementById(boxId + '_placeholder');
  const preview = document.getElementById(boxId + '_preview');
  const file = input.files[0];
  if (!file) return;
  box.classList.add('has-file');
  const reader = new FileReader();
  reader.onload = e => {
    preview.innerHTML = '<img src="' + e.target.result + '" style="max-height:120px;border-radius:8px;margin:0 auto;display:block;"><div style="font-size:.75rem;color:#22c55e;margin-top:.3rem;">' + file.name + '</div>';
    preview.style.display = ''; placeholder.style.display = 'none';
  };
  reader.readAsDataURL(file);
}
</script>
</body>
</html>"""

with open('c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM/templates/rider/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Written', len(content), 'chars')
