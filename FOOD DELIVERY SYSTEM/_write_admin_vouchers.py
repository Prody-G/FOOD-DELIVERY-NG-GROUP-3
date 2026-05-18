content = r"""{% extends 'admin/base.html' %}
{% block title %}Voucher Management{% endblock %}
{% block page_title %}Voucher Management{% endblock %}
{% block content %}
<style>
.modal-overlay {
  display:none; position:fixed; inset:0; background:rgba(0,0,0,.45);
  z-index:500; align-items:center; justify-content:center; padding:1rem;
}
.modal-overlay.open { display:flex; }
.modal-box {
  background:#fff; border-radius:16px; width:100%; max-width:480px;
  max-height:90vh; overflow-y:auto;
  box-shadow:0 20px 60px rgba(0,0,0,.22);
}
.modal-head {
  padding:1.1rem 1.5rem .9rem; display:flex; align-items:center;
  justify-content:space-between; border-bottom:1px solid #f3f4f6; position:sticky; top:0; background:#fff;
}
.modal-head h3 { margin:0; font-size:1rem; font-weight:700; }
.modal-body { padding:1.25rem 1.5rem; }
.modal-foot { padding:.75rem 1.5rem 1.25rem; display:flex; gap:.6rem; justify-content:flex-end; border-top:1px solid #f3f4f6; }
.modal-close { background:none; border:none; font-size:1.4rem; cursor:pointer; color:#9ca3af; line-height:1; }
.modal-close:hover { color:#111827; }
</style>

<div class="page-header flex-between">
  <div>
    <h2>Voucher Management</h2>
    <p>Create and manage discount vouchers.</p>
  </div>
  <button class="btn btn-primary" onclick="openVoucherModal()">+ New Voucher</button>
</div>

<div class="card">
  {% if vouchers %}
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Code</th><th>Type</th><th>Discount</th><th>Max Discount</th>
          <th>Expiry</th><th>Limit</th><th>Per User</th><th>Used</th><th>Status</th><th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for v in vouchers %}
        {% set is_expired = v.expiration_date and v.expiration_date < now %}
        <tr>
          <td><strong>{{ v.code }}</strong></td>
          <td><span class="badge badge-info">{{ 'Percentage' if v.discount_type == 'percentage' else 'Fixed' }}</span></td>
          <td>{% if v.discount_type == 'percentage' %}{{ v.discount_value }}%{% else %}&#8369;{{ '%.2f'|format(v.discount_value) }}{% endif %}</td>
          <td>{{ '&#8369;%.2f'|format(v.max_discount) if v.max_discount else '&mdash;' }}</td>
          <td>
            {% if v.expiration_date %}
            <span class="{{ 'text-danger' if is_expired else '' }}">
              {{ v.expiration_date.strftime('%b %d, %Y') }}{% if is_expired %} (Expired){% endif %}
            </span>
            {% else %}&mdash;{% endif %}
          </td>
          <td>{{ v.global_usage_limit or '&infin;' }}</td>
          <td>{{ v.per_user_limit or 1 }}</td>
          <td>{{ v.usages|length }}</td>
          <td>
            <span class="badge {% if v.is_active and not is_expired %}badge-success{% else %}badge-danger{% endif %}">
              {% if is_expired %}Expired{% elif v.is_active %}Active{% else %}Disabled{% endif %}
            </span>
          </td>
          <td>
            <div class="actions">
              <button class="btn btn-info btn-sm"
                onclick="openEditModal(
                  {{ v.id }},
                  '{{ v.code }}',
                  '{{ v.discount_type }}',
                  {{ v.discount_value }},
                  {{ v.max_discount or 'null' }},
                  '{{ v.expiration_date.strftime("%Y-%m-%d") if v.expiration_date else "" }}',
                  {{ v.global_usage_limit or 'null' }},
                  {{ v.per_user_limit or 1 }}
                )">Edit</button>
              <form method="POST" action="{{ url_for('admin.voucher_disable', voucher_id=v.id) }}">
                <button class="btn btn-warning btn-sm">{{ 'Disable' if v.is_active else 'Enable' }}</button>
              </form>
              <form method="POST" action="{{ url_for('admin.voucher_delete', voucher_id=v.id) }}"
                    onsubmit="return confirm('Delete this voucher?')">
                <button class="btn btn-danger btn-sm">Delete</button>
              </form>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <p class="text-center text-gray" style="padding:2.5rem;">No vouchers yet. Create your first one!</p>
  {% endif %}
</div>

<!-- Add / Edit Voucher Modal -->
<div class="modal-overlay" id="voucherModal">
  <div class="modal-box">
    <div class="modal-head">
      <h3 id="voucherModalTitle">New Voucher</h3>
      <button class="modal-close" onclick="closeVoucherModal()">&times;</button>
    </div>
    <form id="voucherForm" method="POST" action="{{ url_for('admin.voucher_add') }}">
      <div class="modal-body">
        <div class="form-group">
          <label>Voucher Code *</label>
          <input type="text" name="code" id="vCode" required placeholder="e.g. SAVE20"
                 style="text-transform:uppercase;">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Discount Type *</label>
            <select name="discount_type" id="vType" onchange="toggleMax()">
              <option value="percentage">Percentage (%)</option>
              <option value="fixed">Fixed Amount (&#8369;)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Discount Value *</label>
            <input type="number" name="discount_value" id="vValue" step="0.01" min="0" required placeholder="0">
          </div>
        </div>
        <div class="form-group" id="maxDiscountRow">
          <label>Max Discount (&#8369;) <small style="color:#9ca3af;">optional cap for % discounts</small></label>
          <input type="number" name="max_discount" id="vMax" step="0.01" min="0" placeholder="Leave blank for no cap">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Expiration Date <small style="color:#9ca3af;">optional</small></label>
            <input type="date" name="expiration_date" id="vExpiry">
          </div>
          <div class="form-group">
            <label>Global Usage Limit <small style="color:#9ca3af;">optional</small></label>
            <input type="number" name="global_usage_limit" id="vGlobal" min="1" placeholder="Unlimited">
          </div>
        </div>
        <div class="form-group">
          <label>Per User Limit</label>
          <input type="number" name="per_user_limit" id="vPerUser" min="1" value="1">
        </div>
      </div>
      <div class="modal-foot">
        <button type="button" class="btn btn-sm" onclick="closeVoucherModal()"
                style="background:#f3f4f6;color:#374151;">Cancel</button>
        <button type="submit" class="btn btn-primary" id="vSubmitBtn">Create Voucher</button>
      </div>
    </form>
  </div>
</div>

<script>
function openVoucherModal() {
  document.getElementById('voucherModalTitle').textContent = 'New Voucher';
  document.getElementById('vSubmitBtn').textContent = 'Create Voucher';
  document.getElementById('voucherForm').action = '{{ url_for("admin.voucher_add") }}';
  ['vCode','vValue','vMax','vExpiry','vGlobal'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('vType').value = 'percentage';
  document.getElementById('vPerUser').value = '1';
  toggleMax();
  document.getElementById('voucherModal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function openEditModal(id, code, dtype, val, maxD, expiry, glimit, perUser) {
  document.getElementById('voucherModalTitle').textContent = 'Edit Voucher';
  document.getElementById('vSubmitBtn').textContent = 'Save Changes';
  document.getElementById('voucherForm').action = '/admin/vouchers/' + id + '/edit';
  document.getElementById('vCode').value = code;
  document.getElementById('vType').value = dtype;
  document.getElementById('vValue').value = val;
  document.getElementById('vMax').value = maxD !== null ? maxD : '';
  document.getElementById('vExpiry').value = expiry || '';
  document.getElementById('vGlobal').value = glimit !== null ? glimit : '';
  document.getElementById('vPerUser').value = perUser;
  toggleMax();
  document.getElementById('voucherModal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeVoucherModal() {
  document.getElementById('voucherModal').classList.remove('open');
  document.body.style.overflow = '';
}

function toggleMax() {
  document.getElementById('maxDiscountRow').style.display =
    document.getElementById('vType').value === 'percentage' ? '' : 'none';
}

document.getElementById('voucherModal').addEventListener('click', function(e) {
  if (e.target === this) closeVoucherModal();
});

document.getElementById('vCode').addEventListener('input', function() {
  this.value = this.value.toUpperCase();
});
</script>
{% endblock %}
"""

with open('c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM/templates/admin/vouchers.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Written', len(content), 'chars')
