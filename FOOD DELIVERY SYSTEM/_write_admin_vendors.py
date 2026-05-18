content = r"""{% extends 'admin/base.html' %}
{% block title %}Vendor Management{% endblock %}
{% block page_title %}Vendor Management{% endblock %}
{% block content %}
<div class="page-header flex-between">
  <div>
    <h2>Vendor Management</h2>
    <p>Review applications and manage registered vendor shops.</p>
  </div>
  <div style="display:flex;gap:.5rem;">
    <a href="?tab=pending" class="btn btn-sm {{ 'btn-primary' if tab=='pending' else 'btn-outline' }}">Pending Applications</a>
    <a href="?tab=active"  class="btn btn-sm {{ 'btn-primary' if tab=='active' else 'btn-outline' }}">Active Vendors</a>
    <a href="?tab=all"    class="btn btn-sm {{ 'btn-primary' if tab=='all' else 'btn-outline' }}">All</a>
  </div>
</div>

{% if tab == 'pending' or tab == '' %}
<!-- PENDING APPLICATIONS -->
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:1.25rem;">
{% for v in vendors %}
<div style="background:#fff;border-radius:14px;border:1px solid #e5e7eb;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden;">
  <div style="padding:1rem 1.25rem .75rem;border-bottom:1px solid #f3f4f6;display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div style="font-weight:700;font-size:1rem;color:#111827;">{{ v.shop_name }}</div>
      <div style="font-size:.78rem;color:#6b7280;">{{ v.email }} · {{ v.phone or 'No phone' }}</div>
    </div>
    <span class="badge {% if v.status=='active' %}badge-success{% elif v.status=='under_review' %}badge-info{% elif v.status=='rejected' %}badge-danger{% else %}badge-warning{% endif %}">
      {{ v.status.replace('_',' ').title() }}
    </span>
  </div>
  <div style="padding:.85rem 1.25rem;">
    <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;margin-bottom:.3rem;">Business Location</div>
    <div style="font-size:.85rem;color:#374151;margin-bottom:.75rem;">{{ v.business_address or v.address or '—' }}</div>
    {% if v.proposal %}
    <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:#9ca3af;margin-bottom:.3rem;">Proposal / Reason</div>
    <div style="font-size:.82rem;color:#374151;background:#f9fafb;border-radius:6px;padding:.6rem .75rem;line-height:1.5;">{{ v.proposal }}</div>
    {% endif %}
    <div style="font-size:.75rem;color:#9ca3af;margin-top:.6rem;">Applied: {{ v.created_at.strftime('%b %d, %Y %H:%M') }}</div>
  </div>
  <div style="padding:.7rem 1.25rem;background:#f9fafb;border-top:1px solid #f3f4f6;display:flex;gap:.5rem;flex-wrap:wrap;">
    <a href="{{ url_for('admin.vendor_view', vendor_id=v.id) }}" class="btn btn-dark btn-sm">View</a>
    {% if v.status in ('pending','under_review','rejected') %}
    <form method="POST" action="{{ url_for('admin.vendor_approve', vendor_id=v.id) }}">
      <button class="btn btn-success btn-sm">✓ Approve</button>
    </form>
    {% endif %}
    {% if v.status == 'pending' %}
    <form method="POST" action="{{ url_for('admin.vendor_set_review', vendor_id=v.id) }}">
      <button class="btn btn-info btn-sm">Mark Under Review</button>
    </form>
    {% endif %}
    {% if v.status not in ('rejected',) %}
    <form method="POST" action="{{ url_for('admin.vendor_reject', vendor_id=v.id) }}"
          onsubmit="return confirm('Reject this vendor application?')">
      <button class="btn btn-danger btn-sm">✗ Reject</button>
    </form>
    {% endif %}
    {% if v.status == 'active' %}
    <form method="POST" action="{{ url_for('admin.vendor_suspend', vendor_id=v.id) }}">
      <button class="btn btn-warning btn-sm">Suspend</button>
    </form>
    {% endif %}
    <form method="POST" action="{{ url_for('admin.vendor_delete', vendor_id=v.id) }}"
          onsubmit="return confirm('Delete this vendor and all their data?')">
      <button class="btn btn-danger btn-sm">🗑</button>
    </form>
  </div>
</div>
{% else %}
<div class="card" style="padding:2.5rem;text-align:center;color:#9ca3af;">No applications found.</div>
{% endfor %}
</div>

{% else %}
<!-- TABLE VIEW for active/all -->
<div class="card">
  {% if vendors %}
  <div class="table-wrap">
    <table>
      <thead>
        <tr><th>#</th><th>Shop Name</th><th>Email</th><th>Phone</th><th>Business Address</th><th>Status</th><th>Joined</th><th>Actions</th></tr>
      </thead>
      <tbody>
        {% for v in vendors %}
        <tr>
          <td>{{ v.id }}</td>
          <td><strong>{{ v.shop_name }}</strong></td>
          <td>{{ v.email }}</td>
          <td>{{ v.phone or '—' }}</td>
          <td>{{ v.business_address or v.address or '—' }}</td>
          <td><span class="badge {% if v.status=='active' %}badge-success{% elif v.status=='suspended' %}badge-warning{% elif v.status=='pending' %}badge-info{% else %}badge-danger{% endif %}">{{ v.status.replace('_',' ').title() }}</span></td>
          <td>{{ v.created_at.strftime('%b %d, %Y') }}</td>
          <td>
            <div class="actions">
              <a href="{{ url_for('admin.vendor_view', vendor_id=v.id) }}" class="btn btn-dark btn-sm">View</a>
              {% if v.status != 'active' %}
              <form method="POST" action="{{ url_for('admin.vendor_approve', vendor_id=v.id) }}">
                <button class="btn btn-success btn-sm">Approve</button>
              </form>
              {% endif %}
              {% if v.status == 'active' %}
              <form method="POST" action="{{ url_for('admin.vendor_suspend', vendor_id=v.id) }}">
                <button class="btn btn-warning btn-sm">Suspend</button>
              </form>
              <form method="POST" action="{{ url_for('admin.vendor_ban', vendor_id=v.id) }}">
                <button class="btn btn-danger btn-sm">Ban</button>
              </form>
              {% elif v.status in ('suspended','banned') %}
              <form method="POST" action="{{ url_for('admin.vendor_activate', vendor_id=v.id) }}">
                <button class="btn btn-primary btn-sm">Activate</button>
              </form>
              {% endif %}
              <form method="POST" action="{{ url_for('admin.vendor_delete', vendor_id=v.id) }}"
                    onsubmit="return confirm('Delete?')">
                <button class="btn btn-danger btn-sm">🗑</button>
              </form>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <p class="text-center text-gray" style="padding:2rem;">No vendors found.</p>
  {% endif %}
</div>
{% endif %}
{% endblock %}
"""

with open('c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM/templates/admin/vendors.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Written', len(content), 'chars')
