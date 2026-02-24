"""
meshpi.dashboard
================
Serves a real-time HTML dashboard from the host server.
Mounted at /dashboard on the FastAPI app.
No external dependencies — pure HTML + JS + CSS (inline).
"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MeshPi Dashboard</title>
<style>
  :root {
    --bg: #0f1117; --surface: #1a1d27; --surface2: #22263a;
    --cyan: #00d4ff; --green: #00e676; --red: #ff5252;
    --yellow: #ffd740; --text: #e2e8f0; --muted: #64748b;
    --border: #2d3148; --radius: 8px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'SF Mono', 'Fira Code', monospace; font-size: 13px; }
  header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 12px 24px; display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 16px; color: var(--cyan); letter-spacing: 2px; text-transform: uppercase; }
  #status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); animation: pulse 2s infinite; }
  #status-dot.connected { background: var(--green); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .badge-online { background: #00e67622; color: var(--green); border: 1px solid #00e67644; }
  .badge-offline { background: #ff525222; color: var(--red); border: 1px solid #ff525244; }
  main { display: grid; grid-template-columns: 280px 1fr; gap: 0; height: calc(100vh - 49px); }
  aside { background: var(--surface); border-right: 1px solid var(--border); overflow-y: auto; }
  aside h2 { padding: 14px 16px; font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; border-bottom: 1px solid var(--border); }
  .device-item { padding: 12px 16px; border-bottom: 1px solid var(--border); cursor: pointer; transition: background .15s; display: flex; align-items: center; gap: 10px; }
  .device-item:hover, .device-item.active { background: var(--surface2); }
  .device-item.active { border-left: 3px solid var(--cyan); }
  .device-name { font-weight: 600; font-size: 13px; }
  .device-ip { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
  .dot-on { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot-off { background: var(--muted); }
  .content { overflow-y: auto; padding: 20px; }
  .no-select { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--muted); font-size: 15px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin-bottom: 16px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; }
  .card-label { font-size: 10px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; margin-bottom: 6px; }
  .card-value { font-size: 22px; font-weight: 700; color: var(--cyan); }
  .card-sub { font-size: 11px; color: var(--muted); margin-top: 3px; }
  .card-value.warn { color: var(--yellow); }
  .card-value.danger { color: var(--red); }
  h3 { font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; margin: 16px 0 8px; }
  .table { width: 100%; border-collapse: collapse; }
  .table th { text-align: left; padding: 6px 8px; font-size: 10px; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--border); }
  .table td { padding: 7px 8px; border-bottom: 1px solid var(--border); font-size: 12px; }
  .table tr:hover td { background: var(--surface2); }
  .log-box { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px 12px; max-height: 180px; overflow-y: auto; font-size: 11px; }
  .log-line { color: var(--muted); padding: 1px 0; }
  .log-line.err { color: var(--red); }
  .pill { display: inline-block; padding: 1px 7px; border-radius: 12px; font-size: 10px; margin: 1px; background: var(--surface2); border: 1px solid var(--border); color: var(--text); }
  .actions { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
  button { background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 6px 14px; border-radius: var(--radius); cursor: pointer; font-size: 12px; font-family: inherit; transition: all .15s; }
  button:hover { background: var(--surface); border-color: var(--cyan); color: var(--cyan); }
  button.danger:hover { border-color: var(--red); color: var(--red); }
  .cmd-bar { display: flex; gap: 8px; margin-bottom: 16px; }
  .cmd-input { flex: 1; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 7px 12px; border-radius: var(--radius); font-size: 12px; font-family: inherit; outline: none; }
  .cmd-input:focus { border-color: var(--cyan); }
  .cmd-output { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px 12px; max-height: 200px; overflow-y: auto; font-size: 11px; color: var(--green); white-space: pre-wrap; word-break: break-all; }
  .progress-bar { height: 4px; background: var(--surface2); border-radius: 2px; overflow: hidden; margin-top: 6px; }
  .progress-fill { height: 100%; border-radius: 2px; transition: width .5s; }
  #toast { position: fixed; bottom: 20px; right: 20px; background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 10px 18px; border-radius: var(--radius); font-size: 12px; opacity: 0; transition: opacity .3s; pointer-events: none; }
  #toast.show { opacity: 1; }
</style>
</head>
<body>

<header>
  <div id="status-dot"></div>
  <h1>⬡ MeshPi</h1>
  <span id="header-info" style="color:var(--muted);font-size:11px;margin-left:auto">Connecting…</span>
</header>

<main>
  <aside>
    <h2>Devices <span id="device-count" style="float:right"></span></h2>
    <div id="device-list"></div>
  </aside>

  <div class="content" id="content">
    <div class="no-select">Select a device →</div>
  </div>
</main>

<div id="toast"></div>

<script>
const API = window.location.origin;
let devices = {};
let selected = null;
let pollTimer = null;

// ── Polling ────────────────────────────────────────────────────────────────
async function fetchDevices() {
  try {
    const r = await fetch(`${API}/devices`);
    const list = await r.json();
    list.forEach(d => { devices[d.device_id] = d; });
    renderSidebar();
    document.getElementById('status-dot').className = 'connected';
    document.getElementById('header-info').textContent =
      `${list.length} devices — ${list.filter(d=>d.online).length} online`;
    document.getElementById('device-count').textContent = list.length;
    if (selected && devices[selected]) renderDetail(selected);
  } catch(e) {
    document.getElementById('status-dot').className = '';
    document.getElementById('header-info').textContent = 'Connection lost';
  }
}

async function fetchDiag(deviceId) {
  const r = await fetch(`${API}/devices/${deviceId}/diagnostics`);
  if (!r.ok) return null;
  return r.json();
}

// ── Sidebar ────────────────────────────────────────────────────────────────
function renderSidebar() {
  const el = document.getElementById('device-list');
  const sorted = Object.values(devices).sort((a,b) => b.online - a.online || a.device_id.localeCompare(b.device_id));
  el.innerHTML = sorted.map(d => `
    <div class="device-item ${selected===d.device_id?'active':''}" onclick="selectDevice('${d.device_id}')">
      <div class="dot ${d.online?'dot-on':'dot-off'}"></div>
      <div>
        <div class="device-name">${d.device_id}</div>
        <div class="device-ip">${d.address} ${d.notes ? '· '+d.notes : ''}</div>
      </div>
    </div>
  `).join('');
}

// ── Select device ──────────────────────────────────────────────────────────
async function selectDevice(id) {
  selected = id;
  renderSidebar();
  renderDetail(id);
}

async function renderDetail(id) {
  const dev = devices[id];
  if (!dev) return;

  const diag = dev.online ? await fetchDiag(id) : dev.last_diagnostics || {};
  const sys  = diag.system   || {};
  const cpu  = diag.cpu      || {};
  const mem  = diag.memory   || {};
  const temp = diag.temperature || {};
  const pwr  = diag.power    || {};
  const wifi = diag.wifi     || {};
  const net  = diag.network  || {};
  const svc  = diag.services || {};
  const i2c  = diag.i2c      || {};
  const logs = diag.logs     || [];
  const procs = diag.processes || [];

  const tempVal = temp.cpu_gpu ?? temp.zone_0 ?? null;
  const tempClass = tempVal > 80 ? 'danger' : tempVal > 70 ? 'warn' : '';
  const memPct = mem.used_percent || 0;
  const memClass = memPct > 90 ? 'danger' : memPct > 75 ? 'warn' : '';
  const loadVal = cpu.load_1m || 0;
  const loadClass = loadVal > 3 ? 'danger' : loadVal > 1.5 ? 'warn' : '';

  const profilePills = (dev.applied_profiles || []).map(p => `<span class="pill">${p}</span>`).join('') || '<span style="color:var(--muted)">none</span>';

  document.getElementById('content').innerHTML = `
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <span class="dot ${dev.online?'dot-on':'dot-off'}" style="width:10px;height:10px"></span>
      <h2 style="font-size:18px;color:var(--cyan)">${id}</h2>
      <span class="badge ${dev.online?'badge-online':'badge-offline'}">${dev.online?'ONLINE':'OFFLINE'}</span>
      <span style="margin-left:auto;color:var(--muted);font-size:11px">${sys.rpi_model||''}</span>
    </div>

    <div class="actions">
      <button onclick="sendCmd('${id}','reboot')">⟳ Reboot</button>
      <button onclick="runDiag('${id}')">↻ Refresh diag</button>
      <button onclick="showNote('${id}')">✎ Note</button>
      <button onclick="showHwModal('${id}')">⊞ Apply profile</button>
      <button class="danger" onclick="confirmRemove('${id}')">✕ Remove</button>
    </div>

    <div class="grid">
      <div class="card">
        <div class="card-label">CPU Load (1m)</div>
        <div class="card-value ${loadClass}">${loadVal}</div>
        <div class="card-sub">${cpu.load_5m} / ${cpu.load_15m} (5m/15m)</div>
      </div>
      <div class="card">
        <div class="card-label">Memory</div>
        <div class="card-value ${memClass}">${memPct}%</div>
        <div class="card-sub">${Math.round((mem.used_kb||0)/1024)} MB / ${Math.round((mem.total_kb||0)/1024)} MB</div>
        <div class="progress-bar"><div class="progress-fill" style="width:${memPct}%;background:${memClass==='danger'?'var(--red)':memClass==='warn'?'var(--yellow)':'var(--cyan)'}"></div></div>
      </div>
      <div class="card">
        <div class="card-label">Temperature</div>
        <div class="card-value ${tempClass}">${tempVal!==null?tempVal+'°C':'—'}</div>
        <div class="card-sub">Under-V: ${pwr.under_voltage?'⚠ YES':'OK'} | Throttled: ${pwr.currently_throttled?'⚠ YES':'NO'}</div>
      </div>
      <div class="card">
        <div class="card-label">WiFi</div>
        <div class="card-value" style="font-size:14px">${wifi.ssid||'—'}</div>
        <div class="card-sub">Internet: ${net.ping_ok?'✓ OK':'✗ FAIL'} | ${wifi.signal||''}</div>
      </div>
      <div class="card">
        <div class="card-label">Uptime</div>
        <div class="card-value" style="font-size:16px">${formatUptime(sys.uptime_secs)}</div>
        <div class="card-sub">${sys.os_release||''}</div>
      </div>
      <div class="card">
        <div class="card-label">Kernel</div>
        <div class="card-value" style="font-size:13px">${sys.kernel||'—'}</div>
        <div class="card-sub">${sys.hostname||''}</div>
      </div>
    </div>

    <h3>Hardware Profiles</h3>
    <div style="margin-bottom:16px">${profilePills}</div>

    <h3>I2C Devices</h3>
    <div style="margin-bottom:16px">${renderI2C(i2c)}</div>

    <h3>Services</h3>
    <table class="table" style="margin-bottom:16px">
      <tr><th>Service</th><th>Status</th></tr>
      ${Object.entries(svc.statuses||{}).map(([k,v])=>`
        <tr><td>${k}</td><td style="color:${v==='active'?'var(--green)':'var(--muted)'}">${v}</td></tr>
      `).join('')}
      ${(svc.failed_units||[]).map(u=>`<tr><td>${u}</td><td style="color:var(--red)">failed</td></tr>`).join('')}
    </table>

    <h3>Top Processes</h3>
    <table class="table" style="margin-bottom:16px">
      <tr><th>PID</th><th>User</th><th>CPU%</th><th>MEM%</th><th>Command</th></tr>
      ${procs.map(p=>`<tr><td>${p.pid}</td><td>${p.user}</td><td>${p.cpu}</td><td>${p.mem}</td><td style="color:var(--muted)">${p.command}</td></tr>`).join('')}
    </table>

    <h3>Run Command</h3>
    <div class="cmd-bar">
      <input class="cmd-input" id="cmd-input-${id}" placeholder="e.g. df -h | grep mmcblk" onkeydown="if(event.key==='Enter')runCmd('${id}')">
      <button onclick="runCmd('${id}')">▶ Run</button>
    </div>
    <div class="cmd-output" id="cmd-output-${id}" style="display:none"></div>

    <h3>Recent System Errors</h3>
    <div class="log-box">
      ${logs.length ? logs.map(l=>`<div class="log-line ${l.toLowerCase().includes('error')||l.toLowerCase().includes('fail')?'err':''}">${escHtml(l)}</div>`).join('') : '<span style="color:var(--muted)">No recent errors</span>'}
    </div>
  `;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function formatUptime(secs) {
  if (!secs) return '—';
  const h = Math.floor(secs/3600), m = Math.floor((secs%3600)/60);
  return h > 24 ? `${Math.floor(h/24)}d ${h%24}h` : `${h}h ${m}m`;
}

function renderI2C(i2c) {
  const devices = i2c.devices || {};
  const entries = Object.entries(devices);
  if (!entries.length) return '<span style="color:var(--muted)">No I2C devices detected</span>';
  return entries.map(([bus, addrs]) =>
    `<span style="color:var(--muted)">${bus}:</span> ${addrs.map(a=>`<span class="pill">0x${a}</span>`).join('')}`
  ).join('<br>');
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function toast(msg, ms=2500) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'show';
  setTimeout(()=>el.className='', ms);
}

// ── Actions ────────────────────────────────────────────────────────────────
async function sendCmd(id, action, extra={}) {
  const body = {action, ...extra};
  if (action === 'reboot' && !confirm(`Reboot ${id}?`)) return;
  const r = await fetch(`${API}/devices/${id}/command`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body),
  });
  if (r.ok) toast(`✓ ${action} sent to ${id}`);
  else toast(`✗ Failed: ${(await r.json()).detail}`);
}

async function runCmd(id) {
  const input = document.getElementById(`cmd-input-${id}`);
  const output = document.getElementById(`cmd-output-${id}`);
  const cmd = input.value.trim();
  if (!cmd) return;
  output.style.display = 'block';
  output.textContent = '⏳ Running…';
  await sendCmd(id, 'run_command', {command: cmd, timeout: 30});
  output.textContent = '⏳ Command sent. Result will appear in next diagnostics push.\n(Use journalctl -fu meshpi-daemon on client for immediate output)';
}

async function runDiag(id) {
  await sendCmd(id, 'run_command', {command: 'true'});
  await fetchDevices();
  toast('Diagnostics refreshed');
}

async function showNote(id) {
  const note = prompt(`Note for ${id}:`, devices[id]?.notes || '');
  if (note === null) return;
  await fetch(`${API}/devices/${id}/note`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({note}),
  });
  await fetchDevices();
}

async function showHwModal(id) {
  const pid = prompt('Hardware profile ID (e.g. oled_ssd1306_i2c):\nRun: meshpi hw list  for full list');
  if (!pid) return;
  await sendCmd(id, 'apply_profile', {profile_id: pid});
}

async function confirmRemove(id) {
  if (!confirm(`Remove ${id} from registry?`)) return;
  await fetch(`${API}/devices/${id}`, {method:'DELETE'});
  selected = null;
  document.getElementById('content').innerHTML = '<div class="no-select">Select a device →</div>';
  await fetchDevices();
}

// ── Boot ───────────────────────────────────────────────────────────────────
fetchDevices();
setInterval(fetchDevices, 5000);
</script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    return DASHBOARD_HTML
