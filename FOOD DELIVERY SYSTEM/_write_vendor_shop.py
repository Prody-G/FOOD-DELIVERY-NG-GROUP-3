content = r"""{% extends 'vendor/base.html' %}
{% block title %}Shop Settings{% endblock %}
{% block page_title %}Shop Settings{% endblock %}
{% block content %}
<style>
.section-card { background:#fff; border-radius:14px; border:1px solid #e5e7eb; box-shadow:0 1px 4px rgba(0,0,0,.06); padding:1.5rem; margin-bottom:1.25rem; }
.section-title { font-size:.8rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#16a34a; margin-bottom:1rem; display:flex; align-items:center; gap:.4rem; }
.logo-wrap { display:flex; align-items:center; gap:1.25rem; margin-bottom:1rem; }
.logo-circle { width:90px; height:90px; border-radius:50%; border:3px solid #e5e7eb; overflow:hidden; background:#f3f4f6; flex-shrink:0; display:flex; align-items:center; justify-content:center; cursor:pointer; position:relative; }
.logo-circle img { width:100%; height:100%; object-fit:cover; }
.logo-circle-placeholder { font-size:2rem; color:#d1d5db; }
.logo-edit-badge { position:absolute; bottom:4px; right:4px; background:#22c55e; color:#fff; border-radius:50%; width:22px; height:22px; display:flex; align-items:center; justify-content:center; font-size:.65rem; }
.city-select { width:100%; padding:.65rem .9rem; border:2px solid #e5e7eb; border-radius:8px; font-size:.9rem; background:#fff; }
.city-select:focus { outline:none; border-color:#22c55e; }
</style>

<div style="max-width:680px;">

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
    <div class="flash flash-{{ 'success' if cat=='success' else 'error' }}" style="margin-bottom:1rem;">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  <form method="POST" enctype="multipart/form-data">

    <!-- ── SHOP IDENTITY ─────────────────────────────── -->
    <div class="section-card">
      <div class="section-title">🏪 Shop Identity</div>

      <!-- Logo -->
      <div class="logo-wrap">
        <div class="logo-circle" onclick="document.getElementById('logoInput').click()" title="Click to change logo">
          {% if vendor.shop_logo %}
          <img src="{{ url_for('static', filename=vendor.shop_logo) }}" id="logoPreviewImg" alt="Shop Logo">
          {% else %}
          <div class="logo-circle-placeholder" id="logoPlaceholder">🍽️</div>
          <img src="" id="logoPreviewImg" style="display:none;width:100%;height:100%;object-fit:cover;">
          {% endif %}
          <div class="logo-edit-badge">✏️</div>
        </div>
        <div>
          <div style="font-weight:600;font-size:.9rem;color:#111827;">Shop Logo</div>
          <div style="font-size:.78rem;color:#6b7280;margin:.2rem 0 .5rem;">Shown as circular icon beside your shop name.<br>Recommended: 200×200px · JPG, PNG, WebP</div>
          <button type="button" class="btn btn-outline btn-sm" onclick="document.getElementById('logoInput').click()">Choose Logo</button>
          <input type="file" id="logoInput" name="shop_logo" accept="image/*" style="display:none" onchange="previewLogo(this)">
        </div>
      </div>

      <div class="form-group">
        <label>Shop / Restaurant Name *</label>
        <input type="text" name="shop_name" value="{{ vendor.shop_name }}" required>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Phone Number</label>
          <input type="text" name="phone" value="{{ vendor.phone or '' }}" placeholder="09XXXXXXXXX">
        </div>
        <div class="form-group">
          <label>Shop Description</label>
          <input type="text" name="address" value="{{ vendor.address or '' }}" placeholder="Owner / personal address">
        </div>
      </div>

      <div class="form-group" style="margin-bottom:0;">
        <label>About Your Shop</label>
        <textarea name="description" rows="2" placeholder="Tell customers what you serve…">{{ vendor.description or '' }}</textarea>
      </div>
    </div>

    <!-- ── BUSINESS LOCATION ──────────────────────────── -->
    <div class="section-card" style="border-color:#bbf7d0;">
      <div class="section-title">📍 Business Location
        <span style="font-size:.7rem;font-weight:500;color:#9ca3af;text-transform:none;letter-spacing:0;">(UniFood is UMak-Exclusive — Makati &amp; Taguig only)</span>
      </div>

      <div style="background:#fefce8;border:1px solid #fde047;border-radius:8px;padding:.6rem .9rem;margin-bottom:1rem;font-size:.8rem;color:#713f12;">
        ⚠️ Only branches inside <strong>Makati City</strong> or <strong>Taguig City</strong> are accepted on UniFood.
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Branch City *</label>
          <select name="business_city" class="city-select">
            <option value="">-- Keep current --</option>
            <option value="Makati City" {{ 'selected' if vendor.business_city == 'Makati City' }}>Makati City</option>
            <option value="Taguig City" {{ 'selected' if vendor.business_city == 'Taguig City' }}>Taguig City</option>
          </select>
          {% if vendor.business_city %}
          <div style="font-size:.74rem;color:#22c55e;margin-top:.3rem;">Current: {{ vendor.business_city }}</div>
          {% endif %}
        </div>
        <div class="form-group">
          <label>Full Business Address</label>
          <input type="text" name="business_address" value="{{ vendor.business_address or '' }}"
                 placeholder="e.g. G/F BGC Central, Taguig City">
        </div>
      </div>
    </div>

    <!-- ── COVER BANNER ───────────────────────────────── -->
    <div class="section-card">
      <div class="section-title">🖼️ Cover Banner
        <span style="font-size:.7rem;font-weight:500;color:#9ca3af;text-transform:none;letter-spacing:0;">Shown at the top of your shop page — 1200×400px recommended</span>
      </div>

      {% if vendor.cover_banner %}
      <div style="margin-bottom:.85rem;border-radius:10px;overflow:hidden;position:relative;">
        <img src="{{ url_for('static', filename=vendor.cover_banner) }}"
             style="width:100%;height:160px;object-fit:cover;display:block;">
        <div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,.45);color:#fff;font-size:.75rem;padding:.35rem .75rem;">
          Current banner — upload below to replace
        </div>
      </div>
      {% endif %}

      <div class="upload-box" id="bannerBox" data-input="bannerInput">
        <div id="bannerBox_placeholder">
          <div class="upload-box-icon">
            <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </div>
          <div class="upload-box-title">Click to upload cover banner</div>
          <div class="upload-box-sub">Drag & drop or click to browse · JPG, PNG, WebP</div>
        </div>
        <div class="upload-box-preview" id="bannerBox_preview" style="display:none;"></div>
      </div>
      <input type="file" id="bannerInput" name="cover_banner" accept="image/*"
             style="display:none" onchange="handleUpload(this,'bannerBox')">
    </div>

    <button type="submit" class="btn btn-primary btn-lg">Save Changes</button>
  </form>
</div>

<script>
function previewLogo(input) {
  if (!input.files[0]) return;
  const reader = new FileReader();
  reader.onload = e => {
    const img = document.getElementById('logoPreviewImg');
    img.src = e.target.result;
    img.style.display = '';
    const ph = document.getElementById('logoPlaceholder');
    if (ph) ph.style.display = 'none';
  };
  reader.readAsDataURL(input.files[0]);
}

function handleUpload(input, boxId) {
  const box = document.getElementById(boxId);
  const placeholder = document.getElementById(boxId + '_placeholder');
  const preview = document.getElementById(boxId + '_preview');
  const file = input.files[0];
  if (!file) return;
  box.classList.add('has-file');
  if (file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.innerHTML = '<img src="' + e.target.result + '" style="border-radius:8px;width:100%;max-height:200px;object-fit:cover;"><div class="upload-filename" style="margin-top:.5rem;">' + file.name + '</div>';
      preview.style.display = '';
      placeholder.style.display = 'none';
    };
    reader.readAsDataURL(file);
  } else {
    preview.innerHTML = '<div class="upload-filename">' + file.name + '</div>';
    preview.style.display = '';
    placeholder.style.display = 'none';
  }
}

document.querySelectorAll('.upload-box').forEach(box => {
  box.addEventListener('dragover', e => { e.preventDefault(); box.classList.add('dragover'); });
  box.addEventListener('dragleave', () => box.classList.remove('dragover'));
  box.addEventListener('drop', e => {
    e.preventDefault(); box.classList.remove('dragover');
    const input = document.getElementById(box.dataset.input);
    if (!input || !e.dataTransfer.files.length) return;
    const dt = new DataTransfer();
    dt.items.add(e.dataTransfer.files[0]);
    input.files = dt.files;
    handleUpload(input, box.id);
  });
  box.addEventListener('click', () => {
    const input = document.getElementById(box.dataset.input);
    if (input) input.click();
  });
});
</script>
{% endblock %}
"""

with open('c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM/templates/vendor/shop.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Written', len(content), 'chars')
