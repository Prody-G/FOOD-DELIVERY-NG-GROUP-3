content = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Rider Application — Unifood</title>
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
</head>
<body>
<div class="auth-wrap" style="align-items:flex-start;padding-top:2rem;padding-bottom:2rem;">
  <div class="auth-card" style="max-width:580px;">
    <div class="auth-logo">
      <h1>Become a Rider</h1>
      <p>Apply to deliver with Unifood</p>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for cat, msg in messages %}
        <div class="flash flash-{{ 'success' if cat == 'success' else 'error' }}" style="margin-bottom:1rem;">{{ msg }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST" enctype="multipart/form-data">

      <!-- Basic info -->
      <div class="form-row">
        <div class="form-group">
          <label>Full Name *</label>
          <input type="text" name="name" required placeholder="Juan Dela Cruz">
        </div>
        <div class="form-group">
          <label>Email Address *</label>
          <input type="email" name="email" required placeholder="rider@email.com">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Phone Number *</label>
          <input type="text" name="phone" required placeholder="09XXXXXXXXX">
        </div>
        <div class="form-group">
          <label>Vehicle Type *</label>
          <select name="vehicle_type" id="vehicleTypeSelect" required onchange="onVehicleChange()">
            <option value="">-- Select --</option>
            <option value="Walker">Walker (On Foot)</option>
            <option value="Motorcycle">Motorcycle</option>
            <option value="Bicycle">Bicycle / E-Bike</option>
          </select>
        </div>
      </div>

      <!-- WALKER SECTION -->
      <div id="walkerSection" style="display:none;">
        <div style="background:#f0fdf4;border-left:3px solid #22c55e;padding:.85rem 1rem;border-radius:8px;margin-bottom:1.25rem;">
          <strong style="color:#166534;">Walker Requirements</strong>
          <p style="font-size:.82rem;color:#166534;margin:.25rem 0 0;">Upload the following documents to complete your application.</p>
        </div>
        <div class="form-group">
          <label>Certificate of Registration (COR) *</label>
          <div class="upload-box" id="walkerCorBox" data-input="walkerCorInput">
            <div id="walkerCorBox_placeholder">
              <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div>
              <div class="upload-box-title">Upload COR Document</div>
              <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
            </div>
            <div class="upload-box-preview" id="walkerCorBox_preview" style="display:none;"></div>
          </div>
          <input type="file" id="walkerCorInput" name="cor_document" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'walkerCorBox')">
        </div>
        <div class="form-group">
          <label>Valid School ID *</label>
          <div class="upload-box" id="walkerSidBox" data-input="walkerSidInput">
            <div id="walkerSidBox_placeholder">
              <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2"/></svg></div>
              <div class="upload-box-title">Upload Valid School ID</div>
              <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
            </div>
            <div class="upload-box-preview" id="walkerSidBox_preview" style="display:none;"></div>
          </div>
          <input type="file" id="walkerSidInput" name="school_id_document" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'walkerSidBox')">
        </div>
        <div class="form-group">
          <label>PSA Birth Certificate *</label>
          <div class="upload-box" id="walkerPsaBox" data-input="walkerPsaInput">
            <div id="walkerPsaBox_placeholder">
              <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div>
              <div class="upload-box-title">Upload PSA Birth Certificate</div>
              <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
            </div>
            <div class="upload-box-preview" id="walkerPsaBox_preview" style="display:none;"></div>
          </div>
          <input type="file" id="walkerPsaInput" name="psa_document" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'walkerPsaBox')">
        </div>
      </div>

      <!-- MOTORCYCLE SECTION -->
      <div id="motoSection" style="display:none;">
        <div style="background:#fff7ed;border-left:3px solid #f97316;padding:.85rem 1rem;border-radius:8px;margin-bottom:1.25rem;">
          <strong style="color:#9a3412;">Motorcycle Requirements</strong>
          <p style="font-size:.82rem;color:#9a3412;margin:.25rem 0 0;">Upload the following documents and photos for your motorcycle.</p>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Photo of Unit *</label>
            <div class="upload-box" id="motoUnitBox" data-input="motoUnitInput">
              <div id="motoUnitBox_placeholder">
                <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg></div>
                <div class="upload-box-title">Photo of Motorcycle</div>
                <div class="upload-box-sub">JPG or PNG — max 16MB</div>
              </div>
              <div class="upload-box-preview" id="motoUnitBox_preview" style="display:none;"></div>
            </div>
            <input type="file" id="motoUnitInput" name="moto_unit_photo" accept="image/*" style="display:none" onchange="handleUpload(this,'motoUnitBox')">
          </div>
          <div class="form-group">
            <label>Photo of Actual Plate *</label>
            <div class="upload-box" id="motoPlateBox" data-input="motoPlateInput">
              <div id="motoPlateBox_placeholder">
                <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg></div>
                <div class="upload-box-title">Photo of License Plate</div>
                <div class="upload-box-sub">JPG or PNG — max 16MB</div>
              </div>
              <div class="upload-box-preview" id="motoPlateBox_preview" style="display:none;"></div>
            </div>
            <input type="file" id="motoPlateInput" name="moto_plate_photo" accept="image/*" style="display:none" onchange="handleUpload(this,'motoPlateBox')">
          </div>
        </div>
        <div class="form-group">
          <label>Certificate of Registration (COR) *</label>
          <div class="upload-box" id="motoCorBox" data-input="motoCorInput">
            <div id="motoCorBox_placeholder">
              <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div>
              <div class="upload-box-title">Certificate of Registration</div>
              <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
            </div>
            <div class="upload-box-preview" id="motoCorBox_preview" style="display:none;"></div>
          </div>
          <input type="file" id="motoCorInput" name="moto_cor_document" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'motoCorBox')">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Valid License *</label>
            <div class="upload-box" id="motoLicBox" data-input="motoLicInput">
              <div id="motoLicBox_placeholder">
                <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0"/></svg></div>
                <div class="upload-box-title">Valid License</div>
                <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
              </div>
              <div class="upload-box-preview" id="motoLicBox_preview" style="display:none;"></div>
            </div>
            <input type="file" id="motoLicInput" name="moto_valid_license" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'motoLicBox')">
          </div>
          <div class="form-group">
            <label>Driver's License *</label>
            <div class="upload-box" id="motoDlicBox" data-input="motoDlicInput">
              <div id="motoDlicBox_placeholder">
                <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2"/></svg></div>
                <div class="upload-box-title">Driver's License</div>
                <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
              </div>
              <div class="upload-box-preview" id="motoDlicBox_preview" style="display:none;"></div>
            </div>
            <input type="file" id="motoDlicInput" name="moto_drivers_license" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'motoDlicBox')">
          </div>
        </div>
      </div>

      <!-- BICYCLE / E-BIKE SECTION -->
      <div id="bikeSection" style="display:none;">
        <div style="background:#eff6ff;border-left:3px solid #3b82f6;padding:.85rem 1rem;border-radius:8px;margin-bottom:1.25rem;">
          <strong style="color:#1e40af;">Bicycle / E-Bike Requirements</strong>
          <p style="font-size:.82rem;color:#1e40af;margin:.25rem 0 0;">Upload the following documents and photos for your bicycle.</p>
        </div>
        <div class="form-group">
          <label>Photo of Unit *</label>
          <div class="upload-box" id="bikeUnitBox" data-input="bikeUnitInput">
            <div id="bikeUnitBox_placeholder">
              <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg></div>
              <div class="upload-box-title">Photo of Bicycle / E-Bike</div>
              <div class="upload-box-sub">JPG or PNG — max 16MB</div>
            </div>
            <div class="upload-box-preview" id="bikeUnitBox_preview" style="display:none;"></div>
          </div>
          <input type="file" id="bikeUnitInput" name="bike_unit_photo" accept="image/*" style="display:none" onchange="handleUpload(this,'bikeUnitBox')">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Valid School ID *</label>
            <div class="upload-box" id="bikeSidBox" data-input="bikeSidInput">
              <div id="bikeSidBox_placeholder">
                <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2"/></svg></div>
                <div class="upload-box-title">Valid School ID</div>
                <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
              </div>
              <div class="upload-box-preview" id="bikeSidBox_preview" style="display:none;"></div>
            </div>
            <input type="file" id="bikeSidInput" name="bike_school_id_document" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'bikeSidBox')">
          </div>
          <div class="form-group">
            <label>Certificate of Registration (COR) *</label>
            <div class="upload-box" id="bikeCorBox" data-input="bikeCorInput">
              <div id="bikeCorBox_placeholder">
                <div class="upload-box-icon"><svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div>
                <div class="upload-box-title">Certificate of Registration</div>
                <div class="upload-box-sub">JPG, PNG or PDF — max 16MB</div>
              </div>
              <div class="upload-box-preview" id="bikeCorBox_preview" style="display:none;"></div>
            </div>
            <input type="file" id="bikeCorInput" name="bike_cor_document" accept="image/*,application/pdf" style="display:none" onchange="handleUpload(this,'bikeCorBox')">
          </div>
        </div>
      </div>

      <!-- Password -->
      <div class="form-row">
        <div class="form-group">
          <label>Password *</label>
          <input type="password" name="password" required placeholder="Min 8 characters">
        </div>
        <div class="form-group">
          <label>Confirm Password *</label>
          <input type="password" name="confirm_password" required>
        </div>
      </div>

      <div style="background:#f0fdf4;border-left:3px solid #22c55e;padding:.75rem 1rem;border-radius:8px;margin-bottom:1.1rem;font-size:.82rem;color:#166534;">
        Your application will be reviewed by our admin team within 1-3 business days.
      </div>

      <button type="submit" class="btn btn-primary btn-full btn-lg">Submit Application</button>
    </form>

    <div class="auth-links">
      Already have an account? <a href="{{ url_for('rider.login') }}">Sign In</a>
    </div>
  </div>
</div>

<script>
const WALKER_INPUTS = ['walkerCorInput','walkerSidInput','walkerPsaInput'];
const MOTO_INPUTS   = ['motoUnitInput','motoPlateInput','motoCorInput','motoLicInput','motoDlicInput'];
const BIKE_INPUTS   = ['bikeUnitInput','bikeSidInput','bikeCorInput'];

function onVehicleChange() {
  const val = document.getElementById('vehicleTypeSelect').value;
  document.getElementById('walkerSection').style.display = val === 'Walker'     ? '' : 'none';
  document.getElementById('motoSection').style.display   = val === 'Motorcycle' ? '' : 'none';
  document.getElementById('bikeSection').style.display   = val === 'Bicycle'    ? '' : 'none';
  [...WALKER_INPUTS, ...MOTO_INPUTS, ...BIKE_INPUTS].forEach(id => {
    const el = document.getElementById(id); if (el) el.required = false;
  });
  const map = { Walker: WALKER_INPUTS, Motorcycle: MOTO_INPUTS, Bicycle: BIKE_INPUTS };
  (map[val] || []).forEach(id => { const el = document.getElementById(id); if (el) el.required = true; });
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
      preview.innerHTML = '<img src="' + e.target.result + '" style="max-height:130px;border-radius:8px;margin:0 auto;display:block;"><div class="upload-filename" style="margin-top:.4rem;">' + file.name + '</div>';
      preview.style.display = ''; placeholder.style.display = 'none';
    };
    reader.readAsDataURL(file);
  } else {
    preview.innerHTML = '<div class="upload-filename">' + file.name + '</div>';
    preview.style.display = ''; placeholder.style.display = 'none';
  }
}

document.querySelectorAll('.upload-box').forEach(box => {
  box.addEventListener('dragover', e => { e.preventDefault(); box.classList.add('dragover'); });
  box.addEventListener('dragleave', () => box.classList.remove('dragover'));
  box.addEventListener('drop', e => {
    e.preventDefault(); box.classList.remove('dragover');
    const input = document.getElementById(box.dataset.input);
    if (!input || !e.dataTransfer.files.length) return;
    const dt = new DataTransfer(); dt.items.add(e.dataTransfer.files[0]);
    input.files = dt.files; handleUpload(input, box.id);
  });
  box.addEventListener('click', () => { const input = document.getElementById(box.dataset.input); if (input) input.click(); });
});
</script>
</body>
</html>"""

with open('c:/Users/MSI/Desktop/FOOD DELIVERY SYSTEM/templates/rider/apply.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Written', len(content), 'chars')
