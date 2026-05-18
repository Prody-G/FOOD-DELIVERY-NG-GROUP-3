import os

# ── 1. Vendor orders (accept = auto seek rider) ───────────────────────────
vendor_orders = r"""{% extends 'vendor/base.html' %}
{% block title %}Orders{% endblock %}
{% block page_title %}Orders{% endblock %}
{% block content %}
<style>
.steps-row { display:flex; align-items:center; gap:0; margin:.6rem 0 1rem; }
.ostep { display:flex; flex-direction:column; align-items:center; flex:1; position:relative; }
.ostep:not(:last-child)::after { content:''; position:absolute; top:11px; left:50%; width:100%; height:2px; background:#e5e7eb; z-index:0; }
.ostep.done:not(:last-child)::after { background:#22c55e; }
.ostep-dot { width:24px; height:24px; border-radius:50%; border:2px solid #e5e7eb; background:#fff; display:flex; align-items:center; justify-content:center; font-size:.6rem; font-weight:700; z-index:1; position:relative; }
.ostep.done .ostep-dot { background:#22c55e; border-color:#22c55e; color:#fff; }
.ostep.active .ostep-dot { border-color:#22c55e; color:#22c55e; }
.ostep-label { font-size:.6rem; text-align:center; margin-top:.3rem; color:#9ca3af; line-height:1.2; }
.ostep.done .ostep-label { color:#16a34a; }
.ostep.active .ostep-label { color:#111827; font-weight:600; }
.order-card { background:#fff; border-radius:14px; border:1px solid #e5e7eb; margin-bottom:1rem; box-shadow:0 1px 4px rgba(0,0,0,.06); overflow:hidden; }
.oc-head { padding:.9rem 1.25rem .75rem; display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid #f3f4f6; flex-wrap:wrap; gap:.5rem; }
.oc-body { padding:.85rem 1.25rem; display:grid; grid-template-columns:1fr 1fr; gap:.75rem; }
.oc-label { font-size:.7rem; font-weight:600; text-transform:uppercase; color:#9ca3af; margin-bottom:.2rem; }
.oc-val { font-size:.82rem; color:#374151; }
.oc-foot { padding:.7rem 1.25rem .9rem; background:#f9fafb; display:flex; gap:.5rem; align-items:center; justify-content:flex-end; }
</style>

<div style="margin-bottom:1.25rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem;">
  <div>
    <h2 style="margin:0;font-size:1.15rem;">Incoming Orders</h2>
    <p style="margin:.2rem 0 0;font-size:.82rem;color:#6b7280;">Accept orders to immediately start seeking a rider.</p>
  </div>
  <div style="display:flex;gap:.5rem;">
    <span class="badge badge-info">{{ orders|selectattr('status','eq','pending')|list|length }} Pending</span>
    <span class="badge badge-success">{{ orders|selectattr('status','in',['ready_for_pickup','out_for_delivery'])|list|length }} Active</span>
  </div>
</div>

{% if orders %}
{% set status_order = ['pending','ready_for_pickup','out_for_delivery','delivered'] %}
{% set step_labels  = ['Order Placed','Accepted & Seeking Rider','Rider On the Way','Delivered'] %}

{% for order in orders %}
{% if order.status != 'cancelled' %}
<div class="order-card">
  <div style="padding:.85rem 1.25rem .25rem;">
    <div class="steps-row">
      {% set cur = status_order.index(order.status) if order.status in status_order else 0 %}
      {% for lbl in step_labels %}
        {% set idx = loop.index0 %}
        <div class="ostep {{ 'done' if idx < cur else ('active' if idx == cur else '') }}">
          <div class="ostep-dot">{{ '✓' if idx < cur else '' }}</div>
          <div class="ostep-label">{{ lbl }}</div>
        </div>
      {% endfor %}
    </div>
  </div>

  <div class="oc-head">
    <div>
      <div style="font-size:.75rem;color:#9ca3af;margin-bottom:.15rem;">Order #{{ order.id }} · {{ order.created_at.strftime('%b %d, %H:%M') }}</div>
      <div style="font-size:.95rem;font-weight:700;color:#111827;">{{ order.customer.name }}</div>
      <div style="font-size:.78rem;color:#6b7280;">{{ order.customer.phone or '' }}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:1.1rem;font-weight:800;color:#22c55e;">&#8369;{{ '%.2f'|format(order.total) }}</div>
      <div style="font-size:.72rem;color:#6b7280;">{{ order.payment_method|upper }}{% if order.gcash_reference %} · Ref: {{ order.gcash_reference }}{% endif %} · <span style="color:{{ '#22c55e' if order.payment_status=='paid' else '#f59e0b' }}">{{ order.payment_status|upper }}</span></div>
    </div>
  </div>

  <div class="oc-body">
    <div>
      <div class="oc-label">Items</div>
      <div style="font-size:.82rem;color:#374151;line-height:1.6;">
        {% for item in order.items %}{{ item.quantity }}× {{ item.name }} — &#8369;{{ '%.2f'|format(item.price * item.quantity) }}<br>{% endfor %}
      </div>
    </div>
    <div>
      <div class="oc-label">Delivery Address</div>
      <div class="oc-val">{{ order.delivery_address }}, Brgy. {{ order.barangay }}, {{ order.city }}, {{ order.province }}</div>
      {% if order.notes %}<div style="margin-top:.5rem;"><div class="oc-label">Note</div><div class="oc-val" style="color:#6b7280;">{{ order.notes }}</div></div>{% endif %}
      {% if order.rider %}<div style="margin-top:.5rem;"><div class="oc-label">Rider</div><div class="oc-val">{{ order.rider.name }}</div></div>{% endif %}
      {% if order.proof_of_delivery %}<div style="margin-top:.5rem;"><div class="oc-label">Proof of Delivery</div><a href="{{ url_for('static', filename=order.proof_of_delivery) }}" target="_blank" style="font-size:.8rem;color:#22c55e;">View Photo</a></div>{% endif %}
    </div>
  </div>

  <div class="oc-foot">
    {% if order.status == 'pending' %}
    <span style="font-size:.78rem;color:#6b7280;">Accepting will automatically seek a rider.</span>
    <form method="POST" action="{{ url_for('vendor.order_confirm', order_id=order.id) }}">
      <button class="btn btn-primary btn-sm">✓ Accept & Seek Rider</button>
    </form>
    {% elif order.status == 'ready_for_pickup' %}
    <span style="font-size:.8rem;color:#f59e0b;font-weight:600;">&#9679; Seeking a rider…</span>
    {% elif order.status == 'out_for_delivery' %}
    <span style="font-size:.8rem;color:#3b82f6;font-weight:600;">&#9679; Rider on the way</span>
    {% elif order.status == 'delivered' %}
    <span style="font-size:.8rem;color:#22c55e;font-weight:600;">&#10003; Delivered</span>
    {% endif %}
  </div>
</div>
{% endif %}
{% endfor %}

{% else %}
<div style="text-align:center;padding:4rem 1rem;color:#9ca3af;">
  <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="margin:0 auto 1rem;display:block;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
  <p>No orders received yet.</p>
</div>
{% endif %}
{% endblock %}
"""

BASE = 'c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM'
with open(f'{BASE}/templates/vendor/orders.html', 'w', encoding='utf-8') as f:
    f.write(vendor_orders)
print('vendor/orders.html:', len(vendor_orders))

os.system(f'python {BASE}/_write_admin_vendors.py')
