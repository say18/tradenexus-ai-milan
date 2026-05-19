// ── NAVIGATION ──
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  event.target.classList.add('active');
  if (name === 'dashboard') loadDashboard();
}

function updateFileName(inputId, displayId) {
  const file = document.getElementById(inputId).files[0];
  if (file) document.getElementById(displayId).textContent = '✅ ' + file.name;
}

function showLoading(id, show) {
  document.getElementById(id).classList.toggle('show', show);
}

function showResult(id, html) {
  const el = document.getElementById(id);
  el.innerHTML = html;
  el.classList.add('show');
}

// ── PAGE 1: SUPPLIER RISK ──
async function analyzeSupplier() {
  const name = document.getElementById('s-name').value.trim();
  if (!name) { alert('Please enter a supplier name.'); return; }

  document.getElementById('s-btn').disabled = true;
  showLoading('s-loading', true);
  document.getElementById('s-result').classList.remove('show');

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        supplier_name: name,
        industry: document.getElementById('s-industry').value,
        country: document.getElementById('s-country').value
      })
    });
    const data = await res.json();
    showLoading('s-loading', false);
    document.getElementById('s-btn').disabled = false;

    const c = data.risk_color || 'yellow';
    showResult('s-result', `
      <div class="risk-box ${c}">
        <div class="score-circle ${c}">
          <div class="score-num">${data.risk_score}</div>
          <div class="score-label">/ 100</div>
        </div>
        <div>
          <div class="badge ${c}">${data.risk_level} RISK</div>
          <div style="font-size:18px;font-weight:800;margin-bottom:4px;">${data.supplier}</div>
          <div style="font-size:12px;color:#8fafc7;">${data.risk_summary || ''}</div>
          <div style="font-size:11px;color:#3a5a72;margin-top:4px;">Confidence: ${data.confidence} | Industry: ${data.industry}</div>
        </div>
      </div>
      <div class="two-col">
        <div class="info-card">
          <h4>⚠️ Risk Factors</h4>
          <ul>${(data.risk_factors||[]).map(f=>`<li>${f}</li>`).join('')||'<li>None found</li>'}</ul>
        </div>
        <div class="info-card">
          <h4>✅ Actions</h4>
          <ul>${(data.recommended_actions||[]).map(a=>`<li>${a}</li>`).join('')||'<li>Continue monitoring</li>'}</ul>
        </div>
      </div>
      <div class="text-box"><h4>📡 News Summary</h4><p>${data.news_summary||'N/A'}</p></div>
      <div class="text-box"><h4>📈 Price Trends</h4><p>${data.price_data||'N/A'}</p></div>
    `);
  } catch(e) {
    showLoading('s-loading', false);
    document.getElementById('s-btn').disabled = false;
    showResult('s-result', `<div class="text-box"><h4>❌ Error</h4><p>${e.message}</p></div>`);
  }
}

// ── PAGE 2: DOCUMENT ──
async function analyzeDocument() {
  const file = document.getElementById('d-file').files[0];
  if (!file) { alert('Please select a PDF file.'); return; }

  document.getElementById('d-btn').disabled = true;
  showLoading('d-loading', true);
  document.getElementById('d-result').classList.remove('show');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('supplier_name', document.getElementById('d-name').value || 'Unknown');

  try {
    const res = await fetch('/analyze-document', { method: 'POST', body: formData });
    const data = await res.json();
    showLoading('d-loading', false);
    document.getElementById('d-btn').disabled = false;

    showResult('d-result', `
      <div class="text-box">
        <h4>📄 Document Analysis — ${data.supplier}</h4>
        <p>${data.analysis || 'No analysis available'}</p>
      </div>
    `);
  } catch(e) {
    showLoading('d-loading', false);
    document.getElementById('d-btn').disabled = false;
    showResult('d-result', `<div class="text-box"><h4>❌ Error</h4><p>${e.message}</p></div>`);
  }
}

// ── PAGE 3: VISUAL ──
async function analyzeVisual() {
  const file = document.getElementById('v-file').files[0];
  if (!file) { alert('Please select an image file.'); return; }

  document.getElementById('v-btn').disabled = true;
  showLoading('v-loading', true);
  document.getElementById('v-result').classList.remove('show');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('supplier_name', document.getElementById('v-name').value || 'Unknown');

  try {
    const res = await fetch('/analyze-image', { method: 'POST', body: formData });
    const data = await res.json();
    showLoading('v-loading', false);
    document.getElementById('v-btn').disabled = false;

    const p = data.parsed || {};
    showResult('v-result', `
      <div class="text-box">
        <h4>📸 Visual Analysis — ${data.supplier}</h4>
        <p>${data.raw_analysis || 'No analysis'}</p>
      </div>
    `);
  } catch(e) {
    showLoading('v-loading', false);
    document.getElementById('v-btn').disabled = false;
    showResult('v-result', `<div class="text-box"><h4>❌ Error</h4><p>${e.message}</p></div>`);
  }
}

// ── PAGE 4: DEALFLOW ──
async function scoutBuyers() {
  const product = document.getElementById('sc-product').value.trim();
  const industry = document.getElementById('sc-industry').value.trim();
  if (!product || !industry) { alert('Please enter Product and Industry.'); return; }

  document.getElementById('sc-btn').disabled = true;
  showLoading('sc-loading', true);
  document.getElementById('sc-result').classList.remove('show');

  try {
    const res = await fetch('/scout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product,
        industry,
        target_region: document.getElementById('sc-region').value,
        seller_company: document.getElementById('sc-company').value || 'Our Company'
      })
    });
    const data = await res.json();
    showLoading('sc-loading', false);
    document.getElementById('sc-btn').disabled = false;

    const buyersHtml = (data.buyers || []).map((b, i) => `
      <div class="buyer-card">
        <div class="buyer-header">
          <div class="buyer-name">${b.company || 'Unknown'}</div>
          <span class="badge blue">${b.type || 'buyer'}</span>
        </div>
        <div class="buyer-meta">📍 ${b.country || 'N/A'} &nbsp;|&nbsp; Size: ${b.size || 'N/A'} &nbsp;|&nbsp; 📧 ${b.contact || 'N/A'}</div>
        <div class="buyer-fit">💡 ${b.fit_reason || ''}</div>
        <button class="btn btn-secondary btn-sm" onclick="generateEmail('${b.company}','${b.country}','${b.type}')">
          ✉️ Generate Email
        </button>
        <div id="email-${i}" class="email-box" style="display:none;margin-top:10px;">
          <div style="font-size:11px;color:#5a7a99;margin-bottom:8px;">Loading...</div>
        </div>
      </div>
    `).join('');

    window._scoutData = { product, industry, company: document.getElementById('sc-company').value };
    window._buyerCards = data.buyers || [];

    showResult('sc-result', `
      <div class="card" style="margin-bottom:0;">
        <h2>✅ ${data.buyers?.length || 0} Buyers Found</h2>
        <div class="text-box" style="margin-bottom:14px;"><h4>Market Insight</h4><p>${data.raw_response?.split('MARKET INSIGHT:')[1]?.split('BEST')[0]?.trim() || 'N/A'}</p></div>
        ${buyersHtml}
      </div>
    `);
  } catch(e) {
    showLoading('sc-loading', false);
    document.getElementById('sc-btn').disabled = false;
    showResult('sc-result', `<div class="text-box"><h4>❌ Error</h4><p>${e.message}</p></div>`);
  }
}

async function generateEmail(company, country, type) {
  const sd = window._scoutData || {};
  const idx = (window._buyerCards || []).findIndex(b => b.company === company);
  const emailDiv = document.getElementById('email-' + idx);
  if (!emailDiv) return;

  emailDiv.style.display = 'block';
  emailDiv.innerHTML = '<div style="font-size:11px;color:#5a7a99;">✉️ Generating email...</div>';

  try {
    const res = await fetch('/generate-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        buyer_company: company,
        buyer_country: country,
        buyer_type: type,
        seller_company: sd.company || 'Our Company',
        product: sd.product || '',
        industry: sd.industry || ''
      })
    });
    const data = await res.json();
    emailDiv.innerHTML = `
      <div class="email-subject">📧 Subject: ${data.subject}</div>
      <div class="email-body">${data.email_body}</div>
      ${data.follow_up ? `<div style="font-size:11px;color:#5a7a99;margin-top:10px;">📅 Follow-up: ${data.follow_up}</div>` : ''}
    `;
  } catch(e) {
    emailDiv.innerHTML = `<div style="color:#ff6b35;font-size:12px;">Error: ${e.message}</div>`;
  }
}

// ── PAGE 5: DASHBOARD ──
async function loadDashboard() {
  showLoading('db-loading', true);
  document.getElementById('db-result').classList.remove('show');

  try {
    const res = await fetch('/dashboard');
    const data = await res.json();
    showLoading('db-loading', false);

    const stats = data.stats || {};
    const suppliers = data.suppliers || [];

    const supplierRows = suppliers.map(s => {
      const c = s.score > 75 ? 'red' : s.score > 50 ? 'orange' : s.score > 25 ? 'yellow' : 'green';
      return `<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e2d42;">
        <span style="font-size:13px;">${s.name}</span>
        <span class="badge ${c}">${s.score}/100 ${s.level}</span>
      </div>`;
    }).join('') || '<p style="color:#5a7a99;font-size:13px;">No suppliers analyzed yet</p>';

    showResult('db-result', `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-num">${stats.total_suppliers || 0}</div>
          <div class="stat-label">Suppliers Tracked</div>
        </div>
        <div class="stat-card">
          <div class="stat-num" style="color:#ff6b35;">${stats.high_risk || 0}</div>
          <div class="stat-label">High Risk</div>
        </div>
        <div class="stat-card">
          <div class="stat-num" style="color:#0077ff;">${stats.total_leads || 0}</div>
          <div class="stat-label">Leads Found</div>
        </div>
      </div>

      <div class="card">
        <h2>⚡ Supplier Risk Overview</h2>
        ${supplierRows}
      </div>

      <div class="card">
        <h2>🧠 AI Daily Briefing</h2>
        <div class="briefing-box">
          <h4>Today's Intelligence Report</h4>
          <p>${data.briefing || 'Analyze some suppliers and find leads first to generate briefing.'}</p>
        </div>
      </div>
    `);
  } catch(e) {
    showLoading('db-loading', false);
    showResult('db-result', `<div class="text-box"><h4>❌ Error</h4><p>${e.message}</p></div>`);
  }
}

// ── MARKETPULSE ──
async function runMarketPulse() {
  const commodity = document.getElementById('mp-commodity').value.trim();
  const industry  = document.getElementById('mp-industry').value.trim();
  const region    = document.getElementById('mp-region').value;
  const country   = document.getElementById('mp-country').value.trim();
  if (!commodity || !industry) { alert('Please enter Commodity and Industry.'); return; }

  document.getElementById('mp-loading').style.display = 'flex';
  document.getElementById('mp-results').style.display = 'none';

  try {
    const res = await fetch('/api/market-pulse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ commodity, industry, region, country }),
    });
    const data = await res.json();
    if (data.status !== 'success') { alert('Error: ' + (data.message || 'Unknown')); return; }

    // Layer 1: Tomorrow
    const t = data.tomorrow;
    const dirEl = document.getElementById('mp-direction');
    const emoji = t.direction === 'UP' ? '📈 UP' : t.direction === 'DOWN' ? '📉 DOWN' : '➡️ STABLE';
    dirEl.textContent = emoji; dirEl.className = 'mp-direction ' + t.direction;
    document.getElementById('mp-prob').textContent   = t.probability ?? '—';
    document.getElementById('mp-change').textContent = (t.price_change_pct > 0 ? '+' : '') + (t.price_change_pct ?? '—');
    document.getElementById('mp-conf').textContent   = t.confidence ?? '—';
    document.getElementById('mp-recommendation').textContent = t.recommendation ?? '—';
    document.getElementById('mp-risk').textContent   = t.risk_warning ?? '—';
    const drvUl = document.getElementById('mp-drivers'); drvUl.innerHTML = '';
    (t.key_drivers || []).forEach(d => { const li = document.createElement('li'); li.textContent = d; drvUl.appendChild(li); });

    // Layer 2: Trend
    const tr = data.trend;
    document.getElementById('tr-outlook').textContent = (tr.growth_outlook || '—').replace(/_/g,' ');
    document.getElementById('tr-cagr').textContent    = tr.cagr_estimate ?? '—';
    document.getElementById('tr-conf').textContent    = tr.confidence ?? '—';
    ['tr-opportunities','tr-threats','tr-actions'].forEach((id, i) => {
      const arr = [tr.top_opportunities, tr.top_threats, tr.sme_action_items][i] || [];
      const ul = document.getElementById(id); ul.innerHTML = '';
      arr.forEach(item => { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
    });
    const tgrid = document.getElementById('tr-trends-grid'); tgrid.innerHTML = '';
    (tr.key_trends || []).forEach(k => {
      tgrid.innerHTML += `<div class="mp-trend-item"><div class="mt-name">${k.trend}</div><div class="mt-impact ${k.impact}">Impact: ${k.impact}</div><div class="mt-desc">${k.description}</div></div>`;
    });

    // Layer 3: Mega
    const mg = data.mega_trend;
    const vEl = document.getElementById('mega-verdict');
    vEl.textContent = (mg.overall_verdict || '—').replace(/_/g,' ');
    vEl.className   = mg.overall_verdict || '';
    document.getElementById('mega-opportunity').textContent = mg.biggest_opportunity ?? '—';
    document.getElementById('mega-risk').textContent        = mg.biggest_risk ?? '—';
    const mgList = document.getElementById('mega-trends-list'); mgList.innerHTML = '';
    (mg.mega_trends || []).forEach(m => {
      mgList.innerHTML += `<div class="mega-item"><div class="mg-name">${m.name}</div><div class="mg-prob">Probability: ${m.probability}% | Impact: ${m.impact}</div><div class="mg-desc">${m.description}</div><div class="mg-action">➡️ ${m.sme_implication}</div></div>`;
    });
    const stUl = document.getElementById('mega-strategies'); stUl.innerHTML = '';
    (mg.survival_strategies || []).forEach(s => { const li = document.createElement('li'); li.textContent = s; stUl.appendChild(li); });

    document.getElementById('mp-results').style.display = 'block';
  } catch(e) {
    alert('Request failed: ' + e.message);
  } finally {
    document.getElementById('mp-loading').style.display = 'none';
  }
}

// ── CYBER RISK ──
async function runCyberRisk() {
  const company = document.getElementById('cr-company').value.trim();
  const domain  = document.getElementById('cr-domain').value.trim();
  if (!company) { alert('Please enter a company name.'); return; }

  document.getElementById('cr-loading').style.display = 'flex';
  document.getElementById('cr-results').style.display = 'none';

  try {
    const res = await fetch('/api/cyber-risk', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({company_name: company, domain: domain})
    });
    const data = await res.json();
    if (data.status === 'error') { alert('Error: ' + data.message); return; }

    const ai = data.ai_analysis || {};
    const score = data.cyber_risk_score || 0;
    const level = data.risk_level || '—';

    // Score bar
    const bar = document.getElementById('cr-score-bar');
    const scoreEl = document.getElementById('cr-score-num');
    scoreEl.textContent = score;
    bar.style.width = score + '%';
    bar.style.background = score > 75 ? '#ef4444' : score > 50 ? '#f59e0b' : score > 25 ? '#3b82f6' : '#22c55e';

    document.getElementById('cr-level').textContent = level;
    document.getElementById('cr-level').className = 'cr-badge cr-' + level.toLowerCase();
    document.getElementById('cr-domain-display').textContent = data.domain || '—';
    document.getElementById('cr-recommendation').textContent = ai.recommendation || '—';
    document.getElementById('cr-summary').textContent = ai.summary || '—';

    const renderList = (id, arr) => {
      const ul = document.getElementById(id); ul.innerHTML = '';
      (arr || ['None detected']).forEach(item => { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
    };
    renderList('cr-vulns', ai.key_vulnerabilities);
    renderList('cr-redflags', ai.red_flags);
    renderList('cr-positive', ai.positive_signals);
    renderList('cr-vectors', ai.attack_vectors);

    // OSINT details
    const osint = data.osint || {};
    const ssl = osint.ssl_certificate || {};
    const ports = osint.port_scan || {};
    const breach = osint.data_breach || {};
    const malware = osint.malware_scan || {};

    document.getElementById('cr-ssl').textContent = ssl.valid ? `✅ Valid (${ssl.days_left || '?'} days left)` : `❌ ${ssl.error || 'Invalid'}`;
    document.getElementById('cr-ports').textContent = ports.risky_count > 0 ? `⚠️ ${ports.risky_count} risky ports open` : ports.scanned ? '✅ No risky ports' : '— Not scanned';
    document.getElementById('cr-breach').textContent = breach.breached === true ? `🚨 ${breach.breach_count} breach(es) found` : breach.breached === false ? '✅ No breaches found' : '— Unavailable';
    document.getElementById('cr-malware').textContent = malware.flagged ? `🚨 ${malware.malicious_flags} malicious flag(s)` : '✅ Clean';

    document.getElementById('cr-results').style.display = 'block';
  } catch(e) {
    alert('Request failed: ' + e.message);
  } finally {
    document.getElementById('cr-loading').style.display = 'none';
  }
}

// ── MICRO-ECON ──
let meSuppliers = [];

function addMeSupplier() {
  const name  = document.getElementById('me-sup-name').value.trim();
  const share = parseFloat(document.getElementById('me-sup-share').value) || 20;
  const price = parseFloat(document.getElementById('me-sup-price').value) || 10;
  const qual  = parseFloat(document.getElementById('me-sup-quality').value) || 7;
  const units = parseFloat(document.getElementById('me-sup-units').value) || 100;
  if (!name) { alert('Please enter a supplier name.'); return; }

  meSuppliers.push({name, market_share_pct: share, price_per_unit: price, quality_score: qual, units_needed: units, lead_time_days: 30, risk_score: 50});
  renderMeSupplierList();
  document.getElementById('me-sup-name').value = '';
}

function removeMeSupplier(i) {
  meSuppliers.splice(i, 1);
  renderMeSupplierList();
}

function renderMeSupplierList() {
  const div = document.getElementById('me-supplier-list');
  div.innerHTML = '';
  meSuppliers.forEach((s, i) => {
    div.innerHTML += `<div class="me-supplier-item">
      <span><strong>${s.name}</strong> — Share: ${s.market_share_pct}% | Price: $${s.price_per_unit} | Quality: ${s.quality_score}/10 | Units: ${s.units_needed}</span>
      <button onclick="removeMeSupplier(${i})" style="background:#ef4444;border:none;color:white;padding:4px 10px;border-radius:6px;cursor:pointer;">✕</button>
    </div>`;
  });
}

async function runMicroEcon() {
  const commodity = document.getElementById('me-commodity').value.trim();
  const industry  = document.getElementById('me-industry').value.trim();
  const budget    = parseFloat(document.getElementById('me-budget').value) || 0;
  const country   = document.getElementById('me-country').value.trim() || 'Bangladesh';

  if (!commodity || !industry) { alert('Please enter Commodity and Industry.'); return; }
  if (meSuppliers.length < 2) { alert('Please add at least 2 suppliers.'); return; }
  if (budget <= 0) { alert('Please enter a budget amount.'); return; }

  document.getElementById('me-loading').style.display = 'flex';
  document.getElementById('me-results').style.display = 'none';

  try {
    const res = await fetch('/api/micro-econ', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({commodity, industry, budget, suppliers: meSuppliers, country})
    });
    const data = await res.json();
    if (data.status === 'error') { alert('Error: ' + data.message); return; }

    const ai = data.ai_analysis || {};
    const mp = ai.market_power_assessment || {};
    const os = ai.optimal_strategy || {};
    const uv = ai.utility_verdict || {};
    const um = data.utility_maximization || {};

    document.getElementById('me-hhi').textContent = data.hhi || '—';
    document.getElementById('me-market-structure').textContent = (mp.market_structure || '—').replace(/_/g,' ');
    document.getElementById('me-monopoly-risk').textContent = mp.monopoly_risk || '—';
    document.getElementById('me-bargaining').textContent = mp.buyer_bargaining_power || '—';
    document.getElementById('me-interpretation').textContent = mp.interpretation || '—';

    document.getElementById('me-action').textContent = os.recommended_action || '—';
    document.getElementById('me-lockin').textContent = (os.lock_in_percentage || 0) + '%';
    document.getElementById('me-reasoning').textContent = os.reasoning || '—';
    document.getElementById('me-leverage').textContent = os.negotiation_leverage || '—';

    document.getElementById('me-best-supplier').textContent = uv.best_supplier || '—';
    document.getElementById('me-utility-score').textContent = uv.utility_score || '—';
    document.getElementById('me-savings').textContent = '$' + (uv.total_savings_vs_worst || 0);
    document.getElementById('me-verdict').textContent = uv.recommendation || '—';
    document.getElementById('me-summary').textContent = ai.summary || '—';

    // Ranked table
    const tbody = document.getElementById('me-ranked-tbody');
    tbody.innerHTML = '';
    (um.ranked_options || []).forEach((opt, i) => {
      tbody.innerHTML += `<tr>
        <td>${i+1}. ${opt.name}</td>
        <td>$${opt.price_per_unit}</td>
        <td>${opt.quality_score}/10</td>
        <td>${opt.utility_per_dollar}</td>
        <td>$${opt.total_cost}</td>
        <td>${opt.affordable ? '✅' : '❌'}</td>
      </tr>`;
    });

    document.getElementById('me-results').style.display = 'block';
  } catch(e) {
    alert('Request failed: ' + e.message);
  } finally {
    document.getElementById('me-loading').style.display = 'none';
  }
}

// ── AUDIT TRAIL ──
async function loadLastAudit() {
  document.getElementById('at-loading').style.display = 'flex';
  document.getElementById('at-results').style.display = 'none';
  try {
    const res = await fetch('/api/audit/last');
    const data = await res.json();
    renderAuditResult(data);
  } catch(e) {
    alert('Error: ' + e.message);
  } finally {
    document.getElementById('at-loading').style.display = 'none';
  }
}

async function runAuditNow() {
  if (!confirm('Start manual audit? This will take ~60 seconds.')) return;
  document.getElementById('at-run-btn').textContent = '⏳ Running...';
  document.getElementById('at-run-btn').disabled = true;
  try {
    await fetch('/api/audit/run-now', {method:'POST'});
    setTimeout(async () => {
      await loadLastAudit();
      document.getElementById('at-run-btn').textContent = '▶️ Run Audit Now';
      document.getElementById('at-run-btn').disabled = false;
    }, 65000);
    alert('Audit started! Results will load automatically in 65 seconds.');
  } catch(e) {
    alert('Error: ' + e.message);
    document.getElementById('at-run-btn').textContent = '▶️ Run Audit Now';
    document.getElementById('at-run-btn').disabled = false;
  }
}

function renderAuditResult(data) {
  if (data.status === 'no_audit') {
    const atRes = document.getElementById('at-results');
    if(atRes) { atRes.innerHTML = '<div class="card"><p style="opacity:0.6;">No audit run yet. Click "Run Audit Now" to start.</p></div>'; atRes.style.display = 'block'; }
    return;
  }

  const ts = data.run_timestamp ? new Date(data.run_timestamp).toLocaleString() : '—';
  const tsEl = document.getElementById('at-timestamp'); if(tsEl) tsEl.textContent = ts;
  const durEl = document.getElementById('at-duration'); if(durEl) durEl.textContent = (data.duration_seconds || 0) + 's';
  const chkEl = document.getElementById('at-checked'); if(chkEl) chkEl.textContent = data.total_suppliers_checked || 0;
  const critEl = document.getElementById('at-critical'); if(critEl) critEl.textContent = data.critical_count || 0;
  const hrEl = document.getElementById('at-highrisk'); if(hrEl) hrEl.textContent = data.high_risk_count || 0;

  const alertDiv = document.getElementById('at-alerts');
  alertDiv.innerHTML = '';
  const alerts = data.alerts || [];
  if (alerts.length === 0) {
    alertDiv.innerHTML = '<p style="color:#22c55e;">✅ No alerts — all suppliers within normal range.</p>';
  } else {
    alerts.forEach(a => {
      const p = document.createElement('p');
      p.textContent = a;
      p.style.color = a.includes('CRITICAL') ? '#ef4444' : '#f59e0b';
      p.style.margin = '6px 0';
      alertDiv.appendChild(p);
    });
  }

  const resultsDiv = document.getElementById('at-supplier-results');
  resultsDiv.innerHTML = '';
  (data.results || []).forEach(r => {
    const risk = r.risk_check || {};
    const cyber = r.cyber_check || {};
    resultsDiv.innerHTML += `
      <div class="at-supplier-row">
        <div class="at-sup-name">${r.supplier}</div>
        <div class="at-sup-badges">
          <span class="at-badge" style="background:${risk.score>75?'#ef4444':risk.score>50?'#f59e0b':'#22c55e'}">
            Risk: ${risk.score||'?'}/100
          </span>
          <span class="at-badge" style="background:${cyber.score>70?'#ef4444':cyber.score>40?'#f59e0b':'#22c55e'}">
            Cyber: ${cyber.score||'?'}/100
          </span>
        </div>
        ${r.alerts.length > 0 ? `<div style="color:#f59e0b;font-size:12px;margin-top:4px;">${r.alerts[0]}</div>` : ''}
      </div>`;
  });

  document.getElementById('at-results').style.display = 'block';
}