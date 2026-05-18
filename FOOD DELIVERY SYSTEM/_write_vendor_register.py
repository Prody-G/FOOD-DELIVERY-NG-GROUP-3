content_register = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Register Shop — Unifood</title>
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
<style>
body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f4c2a 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 1.5rem; }
.reg-card { background: #fff; border-radius: 20px; padding: 2.2rem; max-width: 580px; width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,.3); }
.brand { text-align: center; margin-bottom: 1.75rem; }
.brand-icon { width: 48px; height: 48px; background: linear-gradient(135deg,#22c55e,#16a34a); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.3rem; color: #fff; margin: 0 auto .6rem; }
.brand h1 { font-size: 1.3rem; margin: 0 0 .2rem; color: #111827; }
.brand p { font-size: .82rem; color: #9ca3af; margin: 0; }
.exclusive-note { background: #fefce8; border: 1px solid #fde047; border-radius: 8px; padding: .7rem 1rem; margin-bottom: 1.25rem; font-size: .82rem; color: #713f12; display: flex; gap: .5rem; align-items: flex-start; }
.pw-bar { height: 5px; border-radius: 3px; margin-top: .4rem; transition: all .3s; background: #e5e7eb; }
.pw-feedback { font-size: .75rem; margin-top: .3rem; font-weight: 600; }
.city-select { width: 100%; padding: .65rem .9rem; border: 2px solid #e5e7eb; border-radius: 8px; font-size: .9rem; background: #fff; }
.city-select:focus { outline: none; border-color: #22c55e; }
</style>
</head>
<body>
<div class="reg-card">
  <div class="brand">
    <div class="brand-icon">U</div>
    <h1>Uni<span style="color:#22c55e;">Food</span> — Register Your Shop</h1>
    <p>Join UniFood as a vendor partner</p>
  </div>

  <div class="exclusive-note">
    ⚠️ <span><strong>UniFood is UMak-Exclusive.</strong> We only accept branches located inside <strong>Makati City</strong> or <strong>Taguig City</strong>. Applications from other cities will not be approved.</span>
  </div>

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
    <div class="flash flash-{{ 'success' if cat == 'success' else 'error' }}" style="margin-bottom:1rem;">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  <form method="POST">
    <div class="form-group">
      <label>Shop / Restaurant Name *</label>
      <input type="text" name="shop_name" required placeholder="e.g. Juan's Grill">
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Business Email *</label>
        <input type="email" name="email" required placeholder="shop@email.com">
      </div>
      <div class="form-group">
        <label>Phone Number</label>
        <input type="text" name="phone" placeholder="09XXXXXXXXX">
      </div>
    </div>

    <!-- Business Location -->
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:1rem;margin-bottom:1rem;">
      <div style="font-size:.8rem;font-weight:700;color:#16a34a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.75rem;">📍 Business Location (Makati / Taguig Only)</div>
      <div class="form-group" style="margin-bottom:.75rem;">
        <label>Branch City *</label>
        <select name="business_city" class="city-select" required>
          <option value="">-- Select City --</option>
          <option value="Makati City">Makati City</option>
          <option value="Taguig City">Taguig City</option>
        </select>
      </div>
      <div class="form-group" style="margin-bottom:0;">
        <label>Full Business Address *</label>
        <input type="text" name="business_address" required placeholder="e.g. G/F BGC Central Square, Taguig City">
      </div>
    </div>

    <div class="form-group">
      <label>Personal/Delivery Address</label>
      <input type="text" name="address" placeholder="Owner's address">
    </div>

    <div class="form-group">
      <label>Reason / Proposal *</label>
      <textarea name="proposal" rows="3" required
        placeholder="Tell us about your restaurant, what you serve, and why you want to partner with UniFood..."
        style="width:100%;padding:.65rem .9rem;border:2px solid #e5e7eb;border-radius:8px;font-size:.9rem;resize:vertical;"></textarea>
      <div style="font-size:.74rem;color:#9ca3af;margin-top:.3rem;">Minimum 20 characters. Describe your menu, specialty, and business goals.</div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Password * <span style="font-size:.72rem;color:#9ca3af;">(8–16 characters)</span></label>
        <input type="password" name="password" id="pw" required placeholder="Min 8, max 16 chars"
               oninput="checkPw()">
        <div class="pw-bar" id="pwBar"></div>
        <div class="pw-feedback" id="pwFeedback"></div>
      </div>
      <div class="form-group">
        <label>Confirm Password *</label>
        <input type="password" name="confirm_password" id="pwc" required placeholder="Re-enter password"
               oninput="checkMatch()">
        <div class="pw-feedback" id="pwcFeedback"></div>
      </div>
    </div>

    <button type="submit" class="btn btn-primary btn-full btn-lg">Submit Application</button>
  </form>

  <div class="auth-links">
    Already registered? <a href="{{ url_for('vendor.login') }}">Sign In</a>
    &nbsp;·&nbsp;
    <a href="{{ url_for('vendor.application_status') }}">Check Application Status</a>
  </div>
</div>

<script>
function checkPw() {
  const pw = document.getElementById('pw').value;
  const bar = document.getElementById('pwBar');
  const fb = document.getElementById('pwFeedback');
  const len = pw.length;
  let score = 0;
  if (len >= 8) score++;
  if (len <= 16 && len >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;

  const colors = ['#ef4444','#f97316','#eab308','#22c55e','#16a34a'];
  const labels = ['Too short','Weak','Fair','Strong','Very strong'];
  const pct = (len === 0) ? 0 : Math.min(100, (score/5)*100);
  bar.style.width = pct + '%';
  bar.style.background = len === 0 ? '#e5e7eb' : colors[Math.min(score-1,4)];

  if (len === 0) { fb.textContent = ''; return; }
  if (len < 8) { fb.textContent = 'Too short (min 8 chars)'; fb.style.color = '#ef4444'; return; }
  if (len > 16) { fb.textContent = 'Too long (max 16 chars)'; fb.style.color = '#ef4444'; return; }
  fb.textContent = labels[Math.min(score-1,4)];
  fb.style.color = colors[Math.min(score-1,4)];
  checkMatch();
}
function checkMatch() {
  const pw = document.getElementById('pw').value;
  const pwc = document.getElementById('pwc').value;
  const fb = document.getElementById('pwcFeedback');
  if (!pwc) { fb.textContent = ''; return; }
  if (pw === pwc) { fb.textContent = '✓ Passwords match'; fb.style.color = '#22c55e'; }
  else { fb.textContent = '✗ Passwords do not match'; fb.style.color = '#ef4444'; }
}
</script>
</body>
</html>
"""

with open('c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM/templates/vendor/register.html', 'w', encoding='utf-8') as f:
    f.write(content_register)
print('Register:', len(content_register))
