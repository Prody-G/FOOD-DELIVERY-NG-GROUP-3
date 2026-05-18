content = r"""{% extends 'rider/base.html' %}
{% block title %}Rider Dashboard{% endblock %}
{% block content %}
<style>
/* Online/offline toggle */
.online-toggle { display:flex; align-items:center; gap:.75rem; background:#fff; border-radius:12px; padding:.75rem 1.25rem; margin-bottom:1.5rem; box-shadow:0 1px 4px rgba(0,0,0,.06); border:1px solid #e5e7eb; }
.status-dot { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
.status-dot.online { background:#22c55e; box-shadow:0 0 0 3px rgba(34,197,94,.2); }
.status-dot.offline { background:#9ca3af; }
.order-card { background:#fff; border-radius:14px; border:1px solid #e5e7eb; margin-bottom:1rem; box-shadow:0 1px 4px rgba(0,0,0,.06); overflow:hidden; }
.steps-row { display:flex; align-items:center; padding:.85rem 1.25rem .25rem; }
.ostep { display:flex; flex-direction:column; align-items:center; flex:1; position:relative; }
.ostep:not(:last-child)::after { content:''; position:absolute; top:11px; left:50%; width:100%; height:2px; background:#e5e7eb; z-index:0; }
.ostep.done:not(:last-child)::after { background:#22c55e; }
.ostep-dot { width:24px; height:24px; border-radius:50%; border:2px solid #e5e7eb; background:#fff; display:flex; align-items:center; justify-content:center; font-size:.6rem; font-weight:700; z-index:1; position:relative; }
.ostep.done .ostep-dot { background:#22c55e; border-color:#22c55e; color:#fff; }
.ostep.active .ostep-dot { border-color:#22c55e; color:#22c55e; }
.ostep-label { font-size:.58rem; text-align:center; margin-top:.3rem; color:#9ca3af; line-height:1.2; }
.ostep.done .ostep-label { color:#16a34a; }
.ostep.active .ostep-label { color:#111827; font-weight:600; }
.proof-box { border:2px dashed #e5e7eb; border-radius:10px; padding:1rem; text-align:center; cursor:pointer; margin-bottom:.75rem; }
.proof-box:hover { border-color:#22c55e; background:#f0fdf4; }
</style>

<!-- Online / Offline toggle -->
<div class="online-toggle">
  <div class="status-dot {{ 'online' if rider.is_online else 'offline' }}"></div>
  <div style="flex:1;">
    <div style="font-weight:700;font-size:.9rem;color:#111827;">{{ 'Online — You can receive orders' if rider.is_online else 'Offline — You will not receive orders' }}</div>
    <div style="font-size:.75rem;color:#6b7280;">Toggle your status to start or stop receiving delivery requests.</div>
  </div>
  <form method="POST" action="{{ url_for('rider.toggle_online') }}">
    <button type="submit" class="btn btn-sm {{ 'btn-danger' if rider.is_online else 'btn-success' }}">
      {{ 'Go Offline' if rider.is_online else 'Go Online' }}
    </button>
  </form>
</div>

<!-- Stats -->
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:1.5rem;">
  <div style="background:#fff;border-radius:12px;padding:1rem;text-align:center;border:1px solid #e5e7eb;box-shadow:0 1px 4px rgba(0,0,0,.05);">
    <div style="font-size:1.6rem;font-weight:800;color:#f59e0b;">{{ available_orders|length }}</div>
    <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;margin-top:.2rem;">Available</div>
  </div>
  <div style="background:#fff;border-radius:12px;padding:1rem;text-align:center;border:1px solid #e5e7eb;box-shadow:0 1px 4px rgba(0,0,0,.05);">
    <div style="font-size:1.6rem;font-weight:800;color:#22c55e;">{{ active_orders|length }}</div>
    <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;margin-top:.2rem;">Active</div>
  </div>
  <div style="background:#fff;border-radius:12px;padding:1rem;text-align:center;border:1px solid #e5e7eb;box-shadow:0 1px 4px rgba(0,0,0,.05);">
    <div style="font-size:1.6rem;font-weight:800;color:#6b7280;">{{ completed_orders|length }}</div>
    <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;margin-top:.2rem;">Completed</div>
  </div>
</div>

<!-- Active Deliveries -->
{% if active_orders %}
<h3 style="font-size:.9rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#374151;margin-bottom:.75rem;">🚴 Active Deliveries</h3>
{% for order in active_orders %}
<div class="order-card">
  <div class="steps-row">
    {% set steps = ['Order Placed','Restaurant Accepted','Seeking Rider','On the Way','Delivered'] %}
    {% for lbl in steps %}
      {% set idx = loop.index0 %}
      <div class="ostep {{ 'done' if idx < 3 else ('active' if idx == 3 else '') }}">
        <div class="ostep-dot">{{ '✓' if idx < 3 else '' }}</div>
        <div class="ostep-label">{{ lbl }}</div>
      </div>
    {% endfor %}
  </div>
  <div style="padding:.75rem 1.25rem;border-top:1px solid #f3f4f6;border-bottom:1px solid #f3f4f6;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;">
      <div>
        <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;color:#9ca3af;margin-bottom:.2rem;">Pickup</div>
        <div style="font-size:.85rem;font-weight:600;color:#111827;">{{ order.vendor.shop_name }}</div>
        <div style="font-size:.78rem;color:#6b7280;">{{ order.vendor.address or 'Address on file' }}</div>
      </div>
      <div>
        <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;color:#9ca3af;margin-bottom:.2rem;">Deliver To</div>
        <div style="font-size:.85rem;font-weight:600;color:#111827;">{{ order.customer.name }}</div>
        <div style="font-size:.78rem;color:#6b7280;">{{ order.delivery_address }}, {{ order.city }}</div>
      </div>
    </div>
    <div style="margin-top:.6rem;display:flex;justify-content:space-between;align-items:center;">
      <div style="font-size:.78rem;color:#6b7280;">Order #{{ order.id }} · {{ order.payment_method|upper }} · <strong style="color:{{ '#22c55e' if order.payment_status=='paid' else '#f59e0b' }}">{{ order.payment_status|upper }}</strong></div>
      <div style="font-size:1rem;font-weight:800;color:#22c55e;">&#8369;{{ '%.2f'|format(order.total) }}</div>
    </div>
  </div>
  <div style="padding:.85rem 1.25rem;">
    <form method="POST" action="{{ url_for('rider.mark_delivered', order_id=order.id) }}" enctype="multipart/form-data">
      <div class="proof-box" id="proofBox{{ order.id }}" onclick="document.getElementById('proofInput{{ order.id }}').click()">
        <div id="proofPreview{{ order.id }}" style="display:none;"><img id="proofImg{{ order.id }}" style="max-height:120px;margin:0 auto;border-radius:6px;"></div>
        <div id="proofPlaceholder{{ order.id }}">
          <div style="font-size:1.5rem;margin-bottom:.3rem;">📷</div>
          <div style="font-size:.8rem;color:#6b7280;font-weight:600;">Upload Proof of Delivery</div>
          <div style="font-size:.72rem;color:#9ca3af;">Click to select a photo</div>
        </div>
      </div>
      <input type="file" name="proof_photo" id="proofInput{{ order.id }}" accept="image/*" hidden
             onchange="previewProof('{{ order.id }}', this)">
      <button type="submit" class="btn btn-success btn-full">Confirm Delivery</button>
    </form>
  </div>
</div>
{% endfor %}
{% endif %}

<!-- Available Orders -->
{% if rider.is_online %}
<h3 style="font-size:.9rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#374151;margin:.5rem 0 .75rem;">📦 Available Deliveries</h3>
{% if available_orders %}
{% for order in available_orders %}
<div class="order-card">
  <div style="padding:.85rem 1.25rem .75rem;display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #f3f4f6;flex-wrap:wrap;gap:.5rem;">
    <div>
      <div style="font-size:.75rem;color:#9ca3af;margin-bottom:.15rem;">Order #{{ order.id }} · {{ order.created_at.strftime('%H:%M') }}</div>
      <div style="font-weight:700;font-size:.95rem;color:#111827;">{{ order.vendor.shop_name }}</div>
      <div style="font-size:.78rem;color:#6b7280;">📍 {{ order.delivery_address }}, {{ order.city }}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:1.05rem;font-weight:800;color:#22c55e;">&#8369;{{ '%.2f'|format(order.total) }}</div>
      <div style="font-size:.72rem;color:#6b7280;">{{ order.payment_method|upper }}</div>
    </div>
  </div>
  <div style="padding:.7rem 1.25rem;display:flex;justify-content:flex-end;">
    <form method="POST" action="{{ url_for('rider.accept_order', order_id=order.id) }}">
      <button class="btn btn-primary btn-sm">Accept Delivery</button>
    </form>
  </div>
</div>
{% endfor %}
{% else %}
<div style="background:#fff;border-radius:12px;padding:2rem;text-align:center;color:#9ca3af;border:1px solid #e5e7eb;">No available deliveries right now.</div>
{% endif %}
{% else %}
<div style="background:#fff;border-radius:12px;padding:2rem;text-align:center;border:1px solid #e5e7eb;">
  <div style="font-size:2rem;margin-bottom:.5rem;">📴</div>
  <p style="color:#6b7280;font-size:.9rem;">You are offline. Go online to receive delivery requests.</p>
</div>
{% endif %}

<!-- Delivery History -->
{% if completed_orders %}
<h3 style="font-size:.9rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#374151;margin:1.25rem 0 .75rem;">📋 Delivery History</h3>
<div style="background:#fff;border-radius:14px;border:1px solid #e5e7eb;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06);">
  <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#f9fafb;">
          <th style="padding:.6rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;text-align:left;">#</th>
          <th style="padding:.6rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;text-align:left;">Customer</th>
          <th style="padding:.6rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;text-align:left;">Vendor</th>
          <th style="padding:.6rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;text-align:left;">Total</th>
          <th style="padding:.6rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;text-align:left;">Proof</th>
          <th style="padding:.6rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;text-align:left;">Date</th>
        </tr>
      </thead>
      <tbody>
        {% for order in completed_orders %}
        <tr style="border-top:1px solid #f3f4f6;">
          <td style="padding:.65rem 1rem;font-size:.82rem;">#{{ order.id }}</td>
          <td style="padding:.65rem 1rem;font-size:.82rem;">{{ order.customer.name }}</td>
          <td style="padding:.65rem 1rem;font-size:.82rem;">{{ order.vendor.shop_name }}</td>
          <td style="padding:.65rem 1rem;font-size:.82rem;font-weight:700;color:#22c55e;">&#8369;{{ '%.2f'|format(order.total) }}</td>
          <td style="padding:.65rem 1rem;font-size:.82rem;">{% if order.proof_of_delivery %}<a href="{{ url_for('static', filename=order.proof_of_delivery) }}" target="_blank" style="color:#22c55e;font-weight:600;">View</a>{% else %}—{% endif %}</td>
          <td style="padding:.65rem 1rem;font-size:.82rem;color:#9ca3af;">{{ order.created_at.strftime('%b %d') }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endif %}

<script>
function previewProof(orderId, input) {
  if (!input.files[0]) return;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById('proofImg' + orderId).src = e.target.result;
    document.getElementById('proofPreview' + orderId).style.display = '';
    document.getElementById('proofPlaceholder' + orderId).style.display = 'none';
  };
  reader.readAsDataURL(input.files[0]);
}
</script>
{% endblock %}
"""

BASE = 'c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM'

# Check if rider/base.html exists; if not use standalone header
import os
if not os.path.exists(f'{BASE}/templates/rider/base.html'):
    # Wrap with standalone header
    content_full = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Rider Dashboard — Unifood</title>
<link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
""" + content.replace('{% extends \'rider/base.html\' %}', '').replace('{% block title %}Rider Dashboard{% endblock %}', '').replace('{% block content %}', '').replace('{% endblock %}', '') + """
</body>
</html>"""
    print("No base.html — writing standalone")
    with open(f'{BASE}/templates/rider/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content_full)
else:
    with open(f'{BASE}/templates/rider/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('rider/dashboard.html:', len(content))
