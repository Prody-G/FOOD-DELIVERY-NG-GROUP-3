content_status = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Application Status — Unifood</title>
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
<style>
body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f4c2a 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 1.5rem; }
.status-card { background: #fff; border-radius: 20px; padding: 2.5rem; max-width: 520px; width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,.3); }
.brand { text-align: center; margin-bottom: 2rem; }
.brand-icon { width: 54px; height: 54px; background: linear-gradient(135deg,#22c55e,#16a34a); border-radius: 14px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.5rem; color: #fff; margin: 0 auto .75rem; }
.brand h1 { font-size: 1.4rem; color: #111827; margin: 0 0 .25rem; }
.brand p { font-size: .85rem; color: #9ca3af; margin: 0; }
.tracker { margin: 2rem 0; }
.t-step { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1.5rem; position: relative; }
.t-step:not(:last-child)::after { content: ''; position: absolute; left: 19px; top: 40px; width: 2px; height: calc(100% - 8px); background: #e5e7eb; z-index: 0; }
.t-step.done:not(:last-child)::after { background: #22c55e; }
.t-dot { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #e5e7eb; background: #fff; display: flex; align-items: center; justify-content: center; font-size: .9rem; font-weight: 700; flex-shrink: 0; z-index: 1; position: relative; }
.t-step.done .t-dot { background: #22c55e; border-color: #22c55e; color: #fff; }
.t-step.active .t-dot { border-color: #22c55e; color: #22c55e; background: #f0fdf4; }
.t-step.pending .t-dot { color: #9ca3af; }
.t-info h3 { margin: 0 0 .2rem; font-size: .95rem; color: #111827; }
.t-info h3.active-label { color: #16a34a; }
.t-info p { margin: 0; font-size: .8rem; color: #6b7280; line-height: 1.4; }
.vendor-info { background: #f9fafb; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1.5rem; }
.vendor-info p { margin: 0; font-size: .85rem; color: #374151; }
.vendor-info strong { color: #111827; }
.flash { padding: .7rem 1rem; border-radius: 8px; font-size: .85rem; margin-bottom: 1rem; }
.flash-success { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.flash-error { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
</style>
</head>
<body>
<div class="status-card">
  <div class="brand">
    <div class="brand-icon">U</div>
    <h1>Uni<span style="color:#22c55e;">Food</span> — Application Status</h1>
    <p>UniFood is UMak-Exclusive. We serve Makati & Taguig City only.</p>
  </div>

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
    <div class="flash flash-{{ cat }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  {% if vendor %}
  <div class="vendor-info">
    <p><strong>{{ vendor.shop_name }}</strong></p>
    <p>{{ vendor.email }}</p>
  </div>

  {% set s = vendor.status %}
  <div class="tracker">
    <!-- Step 1: Submitted -->
    <div class="t-step {{ 'done' if s in ('under_review','active') else 'active' if s == 'pending' else '' }}">
      <div class="t-dot">{{ '✓' if s in ('under_review','active') else '1' }}</div>
      <div class="t-info">
        <h3 class="{{ 'active-label' if s == 'pending' else '' }}">Application Submitted</h3>
        <p>Your shop application has been received. We will begin reviewing it shortly.</p>
      </div>
    </div>
    <!-- Step 2: Under Review -->
    <div class="t-step {{ 'done' if s == 'active' else 'active' if s == 'under_review' else 'pending' }}">
      <div class="t-dot">{{ '✓' if s == 'active' else '2' }}</div>
      <div class="t-info">
        <h3 class="{{ 'active-label' if s == 'under_review' else '' }}">Under Review</h3>
        <p>Our team is reviewing your proposal and business details. This usually takes 1–2 business days.</p>
      </div>
    </div>
    <!-- Step 3: Approved -->
    <div class="t-step {{ 'done' if s == 'active' else 'pending' }}">
      <div class="t-dot">{{ '✓' if s == 'active' else '3' }}</div>
      <div class="t-info">
        <h3 class="{{ 'active-label' if s == 'active' else '' }}">Approved</h3>
        <p>{% if s == 'active' %}Congratulations! Your shop is now live on UniFood.{% else %}Once approved, you can log in and start managing your shop.{% endif %}</p>
      </div>
    </div>
  </div>

  {% if s == 'rejected' %}
  <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:1rem 1.25rem;margin-bottom:1.5rem;">
    <p style="margin:0;font-size:.85rem;color:#b91c1c;"><strong>Application Not Approved</strong><br>Your application did not meet our current requirements. Please contact support for more information.</p>
  </div>
  {% endif %}

  {% if s == 'active' %}
  <a href="{{ url_for('vendor.login') }}" class="btn btn-primary btn-full">Go to Vendor Login →</a>
  {% else %}
  <a href="{{ url_for('vendor.login') }}" class="btn btn-outline btn-full" style="margin-top:.5rem;">Back to Login</a>
  {% endif %}

  {% else %}
  <!-- Email lookup form -->
  <p style="font-size:.9rem;color:#6b7280;margin-bottom:1.5rem;text-align:center;">Enter your registered email to check your application status.</p>
  <form method="GET" action="{{ url_for('vendor.application_status') }}">
    <div style="display:flex;gap:.5rem;">
      <input type="email" name="email" value="{{ email or '' }}" required placeholder="shop@email.com"
             style="flex:1;padding:.7rem 1rem;border:2px solid #e5e7eb;border-radius:8px;font-size:.9rem;">
      <button type="submit" class="btn btn-primary">Check</button>
    </div>
  </form>
  {% if email %}
  <p style="color:#b91c1c;font-size:.85rem;margin-top:.8rem;">No application found for <strong>{{ email }}</strong>.</p>
  {% endif %}
  <div style="text-align:center;margin-top:1.5rem;">
    <a href="{{ url_for('vendor.register') }}" style="color:#22c55e;font-size:.85rem;font-weight:600;">Apply Now →</a>
    &nbsp;&bull;&nbsp;
    <a href="{{ url_for('vendor.login') }}" style="color:#6b7280;font-size:.85rem;">Sign In</a>
  </div>
  {% endif %}
</div>
</body>
</html>
"""

with open('c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM/templates/vendor/application_status.html', 'w', encoding='utf-8') as f:
    f.write(content_status)
print('Status:', len(content_status))
