<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MEP Clash Detection & Rerouting System</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #050d1a;
    --bg2: #071224;
    --panel: #0a1c35;
    --panel2: #0d2040;
    --border: #1a3a5c;
    --accent: #00c8ff;
    --accent2: #ff6b35;
    --accent3: #39ff14;
    --text: #d0e8ff;
    --text-dim: #6a8faa;
    --muted: #304a60;
    --pipe: #ff6b35;
    --duct: #00c8ff;
    --cable: #ffd700;
    --elec: #a855f7;
    --glow: 0 0 20px rgba(0,200,255,0.3);
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Exo 2', sans-serif;
    font-weight: 300;
    overflow-x: hidden;
    cursor: default;
  }

  /* ── SCANLINE OVERLAY ── */
  body::before {
    content: '';
    position: fixed; inset: 0; z-index: 999; pointer-events: none;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
  }

  /* ── GRID BACKGROUND ── */
  .grid-bg {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image:
      linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
  }

  /* ── HERO ── */
  .hero {
    position: relative; z-index: 1;
    padding: 70px 40px 50px;
    text-align: center;
    border-bottom: 1px solid var(--border);
    overflow: hidden;
  }
  .hero::after {
    content: '';
    position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
    width: 60%; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
  }
  .hero-badge {
    display: inline-block;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    border: 1px solid rgba(0,200,255,0.3);
    padding: 5px 16px;
    border-radius: 2px;
    margin-bottom: 24px;
    animation: pulse-border 2s infinite;
  }
  @keyframes pulse-border {
    0%, 100% { border-color: rgba(0,200,255,0.3); box-shadow: none; }
    50% { border-color: rgba(0,200,255,0.7); box-shadow: 0 0 12px rgba(0,200,255,0.2); }
  }
  .hero h1 {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700;
    font-size: clamp(28px, 5vw, 56px);
    line-height: 1.1;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }
  .hero h1 span.hi { color: var(--accent); }
  .hero h1 span.lo { color: var(--accent2); }
  .hero-sub {
    font-size: 14px;
    color: var(--text-dim);
    letter-spacing: 2px;
    font-family: 'Share Tech Mono', monospace;
    margin-bottom: 30px;
  }
  .status-row {
    display: flex; justify-content: center; gap: 24px; flex-wrap: wrap;
    margin-top: 20px;
  }
  .status-chip {
    display: flex; align-items: center; gap: 8px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: var(--text-dim);
  }
  .dot {
    width: 7px; height: 7px; border-radius: 50%;
    animation: blink 1.5s infinite;
  }
  .dot.green { background: var(--accent3); box-shadow: 0 0 6px var(--accent3); }
  .dot.orange { background: var(--accent2); box-shadow: 0 0 6px var(--accent2); animation-delay: 0.5s; }
  .dot.blue { background: var(--accent); box-shadow: 0 0 6px var(--accent); animation-delay: 1s; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

  /* ── LAYOUT ── */
  .container {
    position: relative; z-index: 1;
    max-width: 1100px; margin: 0 auto;
    padding: 40px 24px 80px;
  }

  /* ── SECTION HEADER ── */
  .section-header {
    display: flex; align-items: center; gap: 14px;
    margin-bottom: 24px; margin-top: 48px;
  }
  .section-icon {
    width: 36px; height: 36px;
    border: 1px solid var(--accent);
    border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    box-shadow: var(--glow);
    flex-shrink: 0;
  }
  .section-header h2 {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    font-size: 20px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
  }
  .section-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
  }

  /* ── PROBLEM + OVERVIEW ── */
  .info-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  }
  @media(max-width:650px){ .info-grid { grid-template-columns: 1fr; } }
  .info-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 22px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, transform 0.2s;
  }
  .info-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
  }
  .info-card:hover { border-color: var(--accent); transform: translateY(-2px); }
  .info-card h3 {
    font-family: 'Rajdhani', sans-serif;
    font-size: 15px; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--accent2);
    margin-bottom: 12px;
  }
  .info-card p { font-size: 13.5px; color: var(--text-dim); line-height: 1.7; }

  /* ── CLASH TYPES INTERACTIVE ── */
  .clash-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px;
  }
  .clash-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 18px 16px;
    cursor: pointer;
    transition: all 0.25s;
    position: relative; overflow: hidden;
  }
  .clash-card::after {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(circle at 50% 0%, rgba(0,200,255,0.08), transparent 60%);
    opacity: 0; transition: opacity 0.3s;
  }
  .clash-card:hover::after, .clash-card.active::after { opacity: 1; }
  .clash-card:hover, .clash-card.active {
    border-color: var(--accent);
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,200,255,0.12);
  }
  .clash-card .icon { font-size: 24px; margin-bottom: 10px; }
  .clash-card .label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 14px; font-weight: 600; letter-spacing: 1px;
    color: var(--text); margin-bottom: 6px;
  }
  .clash-card .desc { font-size: 12px; color: var(--text-dim); line-height: 1.5; }
  .clash-card .tag {
    display: inline-block; margin-top: 10px;
    font-family: 'Share Tech Mono', monospace; font-size: 10px;
    padding: 2px 8px; border-radius: 2px;
    background: rgba(0,200,255,0.1); color: var(--accent);
    border: 1px solid rgba(0,200,255,0.2);
  }

  /* ── WORKFLOW DIAGRAM ── */
  .workflow {
    display: flex; flex-direction: column; align-items: center; gap: 0;
    padding: 10px 0;
  }
  .wf-step {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 28px;
    width: min(420px, 100%);
    display: flex; align-items: center; gap: 14px;
    position: relative;
    transition: all 0.3s;
    cursor: default;
  }
  .wf-step:hover {
    border-color: var(--accent);
    box-shadow: var(--glow);
    transform: scale(1.02);
  }
  .wf-num {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px; color: var(--accent);
    width: 24px; text-align: center; flex-shrink: 0;
  }
  .wf-text {
    font-family: 'Rajdhani', sans-serif;
    font-size: 15px; font-weight: 600; letter-spacing: 1px;
  }
  .wf-icon { margin-left: auto; font-size: 18px; }
  .wf-arrow {
    width: 1px; height: 28px;
    background: linear-gradient(180deg, var(--accent), rgba(0,200,255,0.2));
    position: relative;
  }
  .wf-arrow::after {
    content: '▼';
    position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
    font-size: 8px; color: var(--accent);
  }

  /* ── STAGES ── */
  .stages-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  }
  @media(max-width:650px){ .stages-grid { grid-template-columns: 1fr; } }
  .stage-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 24px 20px;
    position: relative; overflow: hidden;
    transition: all 0.3s;
  }
  .stage-card:hover { border-color: var(--accent2); box-shadow: 0 0 20px rgba(255,107,53,0.15); }
  .stage-card::before {
    content: '';
    position: absolute; top: 0; left: 0; bottom: 0; width: 3px;
    background: var(--accent2);
  }
  .stage-num {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px; letter-spacing: 2px; color: var(--accent2);
    margin-bottom: 8px;
  }
  .stage-card h3 {
    font-family: 'Rajdhani', sans-serif;
    font-size: 17px; font-weight: 700; letter-spacing: 1px;
    color: var(--text); margin-bottom: 14px;
  }
  .stage-list { list-style: none; }
  .stage-list li {
    font-size: 13px; color: var(--text-dim);
    padding: 5px 0; display: flex; align-items: flex-start; gap: 8px;
    line-height: 1.5;
  }
  .stage-list li::before { content: '→'; color: var(--accent2); flex-shrink: 0; }

  /* ── CHALLENGES ── */
  .challenge-list {
    display: flex; flex-direction: column; gap: 12px;
  }
  .challenge-item {
    background: var(--panel);
    border: 1px solid var(--border);
    border-left: 3px solid rgba(255,107,53,0.6);
    border-radius: 0 6px 6px 0;
    padding: 14px 18px;
    display: flex; gap: 14px; align-items: flex-start;
    transition: border-color 0.3s;
  }
  .challenge-item:hover { border-left-color: var(--accent2); }
  .challenge-item .ch-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }
  .challenge-item h4 {
    font-family: 'Rajdhani', sans-serif;
    font-size: 14px; font-weight: 600; letter-spacing: 1px;
    color: var(--text); margin-bottom: 4px;
  }
  .challenge-item p { font-size: 12.5px; color: var(--text-dim); line-height: 1.6; }

  /* ── FUTURE ── */
  .future-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px;
  }
  .future-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px 16px;
    text-align: center;
    transition: all 0.3s;
    position: relative; overflow: hidden;
  }
  .future-card::before {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent3), transparent);
    opacity: 0; transition: opacity 0.3s;
  }
  .future-card:hover::before { opacity: 1; }
  .future-card:hover { border-color: var(--accent3); box-shadow: 0 0 16px rgba(57,255,20,0.1); }
  .future-card .f-icon { font-size: 28px; margin-bottom: 12px; }
  .future-card h4 {
    font-family: 'Rajdhani', sans-serif;
    font-size: 14px; font-weight: 600; letter-spacing: 1px;
    color: var(--accent3); margin-bottom: 8px;
  }
  .future-card p { font-size: 12px; color: var(--text-dim); line-height: 1.5; }

  /* ── TEAM ── */
  .team-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;
  }
  .team-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 24px 16px;
    text-align: center;
    transition: all 0.3s;
    position: relative;
  }
  .team-card:hover {
    border-color: var(--accent);
    box-shadow: var(--glow);
    transform: translateY(-4px);
  }
  .avatar {
    width: 56px; height: 56px; border-radius: 50%;
    background: linear-gradient(135deg, var(--panel2), var(--border));
    border: 2px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Rajdhani', sans-serif; font-size: 20px; font-weight: 700;
    color: var(--accent);
    margin: 0 auto 14px;
    transition: border-color 0.3s;
  }
  .team-card:hover .avatar { border-color: var(--accent); box-shadow: var(--glow); }
  .team-card h4 {
    font-family: 'Rajdhani', sans-serif;
    font-size: 15px; font-weight: 600; letter-spacing: 1px;
    color: var(--text); margin-bottom: 4px;
  }
  .team-card p {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px; color: var(--text-dim); letter-spacing: 1px;
  }

  /* ── I/O TABLE ── */
  .io-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media(max-width:600px){ .io-grid { grid-template-columns: 1fr; } }
  .io-box {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px; padding: 20px;
  }
  .io-box h4 {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
    color: var(--accent); margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px;
  }
  .io-box h4::before {
    content: ''; display: block;
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 6px var(--accent);
  }
  .io-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 10px; margin-bottom: 6px;
    background: rgba(0,200,255,0.04);
    border: 1px solid rgba(0,200,255,0.1);
    border-radius: 4px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px; color: var(--text-dim);
    transition: all 0.2s;
  }
  .io-item:hover { background: rgba(0,200,255,0.08); color: var(--text); }

  /* ── FOOTER ── */
  footer {
    position: relative; z-index: 1;
    border-top: 1px solid var(--border);
    padding: 24px 40px;
    text-align: center;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px; color: var(--muted);
    letter-spacing: 2px;
  }
  footer span { color: var(--accent); }

  /* ── TOOLTIP ── */
  [data-tip] { position: relative; }
  [data-tip]:hover::after {
    content: attr(data-tip);
    position: absolute; bottom: 110%; left: 50%; transform: translateX(-50%);
    background: var(--panel2); border: 1px solid var(--border);
    color: var(--text); font-size: 11px; padding: 6px 10px;
    border-radius: 4px; white-space: nowrap; z-index: 100;
    font-family: 'Share Tech Mono', monospace;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  }

  /* ── LIVE COUNTER ANIMATION ── */
  @keyframes countUp {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .counter { animation: countUp 0.6s ease both; }

  /* ── REVEAL ON SCROLL ── */
  .reveal { opacity: 0; transform: translateY(20px); transition: opacity 0.5s, transform 0.5s; }
  .reveal.visible { opacity: 1; transform: translateY(0); }
</style>
</head>
<body>

<div class="grid-bg"></div>

<!-- ── HERO ── -->
<div class="hero">
  <div class="hero-badge">🏗️ BIM Coordination Platform · v2.0</div>
  <h1>
    <span class="hi">MEP</span> Clash Detection<br>
    &amp; <span class="lo">Rerouting</span> System
  </h1>
  <p class="hero-sub">AI-ASSISTED · CONSTRAINT-AWARE · AUTOMATED REPORTING</p>
  <div class="status-row">
    <div class="status-chip"><span class="dot green"></span> Clash Engine: Active</div>
    <div class="status-chip"><span class="dot orange"></span> Rerouting: Stage 1</div>
    <div class="status-chip"><span class="dot blue"></span> AI Assistant: Planned</div>
  </div>
</div>

<div class="container">

  <!-- ── OVERVIEW & PROBLEM ── -->
  <div class="section-header reveal">
    <div class="section-icon">📡</div>
    <h2>Overview & Problem</h2>
    <div class="section-line"></div>
  </div>
  <div class="info-grid reveal">
    <div class="info-card">
      <h3>🚀 What It Is</h3>
      <p>An AI-assisted BIM coordination platform that detects and resolves clashes in MEP systems. Leverages industry workflows enhanced with intelligent rerouting and automation for real-world construction coordination.</p>
    </div>
    <div class="info-card">
      <h3>⚠️ The Problem</h3>
      <p>In real-world construction, MEP systems frequently overlap due to lack of coordination. Manual clash detection is slow, costly, and error-prone — this system automates detection, provides smart rerouting, and improves design efficiency.</p>
    </div>
  </div>

  <!-- ── CLASH TYPES ── -->
  <div class="section-header reveal">
    <div class="section-icon">🔍</div>
    <h2>Clash Detection Types</h2>
    <div class="section-line"></div>
  </div>
  <div class="clash-grid reveal">
    <div class="clash-card" onclick="this.classList.toggle('active')" data-tip="Hard clash: physical overlap">
      <div class="icon">🔴</div>
      <div class="label">Pipe — Pipe</div>
      <div class="desc">Detects physical intersections between plumbing pipe segments within the model.</div>
      <span class="tag">HARD CLASH</span>
    </div>
    <div class="clash-card" onclick="this.classList.toggle('active')" data-tip="Hard clash: duct collision">
      <div class="icon">🟦</div>
      <div class="label">Duct — Duct</div>
      <div class="desc">Identifies overlapping HVAC ductwork sections causing spatial conflicts.</div>
      <span class="tag">HARD CLASH</span>
    </div>
    <div class="clash-card" onclick="this.classList.toggle('active')" data-tip="Inter-system clash">
      <div class="icon">🟠</div>
      <div class="label">Pipe — Duct</div>
      <div class="desc">Cross-system clash between plumbing and mechanical HVAC elements.</div>
      <span class="tag">INTER-SYSTEM</span>
    </div>
    <div class="clash-card" onclick="this.classList.toggle('active')" data-tip="Electrical clearance clash">
      <div class="icon">🟡</div>
      <div class="label">Cable Tray</div>
      <div class="desc">Detects conflicts between electrical cable trays and other MEP elements.</div>
      <span class="tag">SOFT CLASH</span>
    </div>
    <div class="clash-card" onclick="this.classList.toggle('active')" data-tip="Multi-system conflict">
      <div class="icon">🟣</div>
      <div class="label">Inter-System</div>
      <div class="desc">Complex multi-discipline conflicts across all MEP categories simultaneously.</div>
      <span class="tag">COMPLEX</span>
    </div>
  </div>

  <!-- ── WORKFLOW ── -->
  <div class="section-header reveal">
    <div class="section-icon">⚙️</div>
    <h2>System Workflow</h2>
    <div class="section-line"></div>
  </div>
  <div style="display:flex; justify-content:center;">
    <div class="workflow reveal">
      <div class="wf-step" data-tip="Accepts .rvt Revit models">
        <span class="wf-num">01</span>
        <span class="wf-text">Input — .rvt BIM File</span>
        <span class="wf-icon">📂</span>
      </div>
      <div class="wf-arrow"></div>
      <div class="wf-step" data-tip="Spatial intersection algorithms">
        <span class="wf-num">02</span>
        <span class="wf-text">Clash Detection Engine</span>
        <span class="wf-icon">🔍</span>
      </div>
      <div class="wf-arrow"></div>
      <div class="wf-step" data-tip="Type, location, components">
        <span class="wf-num">03</span>
        <span class="wf-text">Clash Data Extraction</span>
        <span class="wf-icon">📊</span>
      </div>
      <div class="wf-arrow"></div>
      <div class="wf-step" data-tip="Stage 1 & Stage 2 rerouting">
        <span class="wf-num">04</span>
        <span class="wf-text">Rerouting Engine</span>
        <span class="wf-icon">🔁</span>
      </div>
      <div class="wf-arrow"></div>
      <div class="wf-step" data-tip="Dashboard + automated reports">
        <span class="wf-num">05</span>
        <span class="wf-text">Visualization &amp; Reports</span>
        <span class="wf-icon">📄</span>
      </div>
    </div>
  </div>

  <!-- ── INPUT / OUTPUT ── -->
  <div class="section-header reveal">
    <div class="section-icon">📂</div>
    <h2>Input &amp; Output</h2>
    <div class="section-line"></div>
  </div>
  <div class="io-grid reveal">
    <div class="io-box">
      <h4>Input</h4>
      <div class="io-item">📐 .rvt — Autodesk Revit BIM Models</div>
      <div class="io-item">🏗️ Full MEP discipline models</div>
      <div class="io-item">📡 Coordinate system metadata</div>
    </div>
    <div class="io-box">
      <h4>Output</h4>
      <div class="io-item">⚠️ Clash type, location &amp; coordinates</div>
      <div class="io-item">🔁 Suggested rerouting paths</div>
      <div class="io-item">📄 Automated structured reports</div>
      <div class="io-item">🧠 AI priority assignments</div>
    </div>
  </div>

  <!-- ── STAGES ── -->
  <div class="section-header reveal">
    <div class="section-icon">🧪</div>
    <h2>Implementation Stages</h2>
    <div class="section-line"></div>
  </div>
  <div class="stages-grid reveal">
    <div class="stage-card">
      <div class="stage-num">// STAGE 01</div>
      <h3>Basic Detection &amp; Rerouting</h3>
      <ul class="stage-list">
        <li>Detect clashes in provided sample model</li>
        <li>Display clash information &amp; details</li>
        <li>Apply basic offset/shift rerouting</li>
        <li>Handle small and simple clash scenarios</li>
      </ul>
    </div>
    <div class="stage-card">
      <div class="stage-num">// STAGE 02</div>
      <h3>Advanced Full BIM Processing</h3>
      <ul class="stage-list">
        <li>Process complete full-scale BIM models</li>
        <li>Constraint-aware intelligent rerouting</li>
        <li>Minimize disruption to existing design</li>
        <li>Intelligent multi-clash optimization</li>
      </ul>
    </div>
  </div>

  <!-- ── CHALLENGES ── -->
  <div class="section-header reveal">
    <div class="section-icon">⚠️</div>
    <h2>Challenges</h2>
    <div class="section-line"></div>
  </div>
  <div class="challenge-list reveal">
    <div class="challenge-item">
      <span class="ch-icon">🗜️</span>
      <div>
        <h4>BIM Data Complexity</h4>
        <p>Revit models contain deeply nested parametric relationships and family hierarchies. Parsing and processing this data efficiently requires robust extraction pipelines and handling edge cases across model variants.</p>
      </div>
    </div>
    <div class="challenge-item">
      <span class="ch-icon">🛤️</span>
      <div>
        <h4>Realistic Rerouting Logic</h4>
        <p>Suggested rerouting must comply with building codes, structural constraints, and MEP design standards — not just spatial clearance. Paths must remain buildable and cost-effective.</p>
      </div>
    </div>
    <div class="challenge-item">
      <span class="ch-icon">📦</span>
      <div>
        <h4>Large-Scale Model Management</h4>
        <p>Real-world BIM models can contain hundreds of thousands of elements. Processing performance, memory management, and detection accuracy at scale present significant engineering challenges.</p>
      </div>
    </div>
  </div>

  <!-- ── FUTURE ── -->
  <div class="section-header reveal">
    <div class="section-icon">🏆</div>
    <h2>Future Enhancements</h2>
    <div class="section-line"></div>
  </div>
  <div class="future-grid reveal">
    <div class="future-card">
      <div class="f-icon">⚡</div>
      <h4>Real-Time Detection</h4>
      <p>Live clash detection as elements are placed, with instant feedback in the design environment.</p>
    </div>
    <div class="future-card">
      <div class="f-icon">🤖</div>
      <h4>Full Auto-Rerouting</h4>
      <p>Fully automated rerouting with zero-touch resolution for common clash patterns.</p>
    </div>
    <div class="future-card">
      <div class="f-icon">🧠</div>
      <h4>AI Design Copilot</h4>
      <p>Prompt-based assistant for generating MEP solutions from natural language descriptions.</p>
    </div>
    <div class="future-card">
      <div class="f-icon">📊</div>
      <h4>Smart Prioritization</h4>
      <p>AI-driven clash priority scoring based on severity, cost impact, and schedule risk.</p>
    </div>
  </div>

  <!-- ── TEAM ── -->
  <div class="section-header reveal">
    <div class="section-icon">👥</div>
    <h2>Team Visionaries</h2>
    <div class="section-line"></div>
  </div>
  <div class="team-grid reveal">
    <div class="team-card">
      <div class="avatar">KM</div>
      <h4>Karan Mishra</h4>
      <p>// CORE DEVELOPER</p>
    </div>
    <div class="team-card">
      <div class="avatar">AM</div>
      <h4>Anup Mehta</h4>
      <p>// SYSTEMS ARCHITECT</p>
    </div>
    <div class="team-card">
      <div class="avatar">AK</div>
      <h4>Aakash Kavediya</h4>
      <p>// BIM SPECIALIST</p>
    </div>
    <div class="team-card">
      <div class="avatar">SK</div>
      <h4>Shlok Khade</h4>
      <p>// AI INTEGRATION</p>
    </div>
  </div>

</div><!-- /container -->

<footer>
  Designed for real-world BIM coordination workflows &nbsp;·&nbsp;
  <span>MEP CLASH DETECTION & REROUTING SYSTEM</span> &nbsp;·&nbsp;
  Practical · Scalable · Intelligent
</footer>

<script>
  // Scroll reveal
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((e, i) => {
      if (e.isIntersecting) {
        setTimeout(() => e.target.classList.add('visible'), i * 60);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  // Clash card click feedback
  document.querySelectorAll('.clash-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.clash-card').forEach(c => {
        if (c !== card) c.classList.remove('active');
      });
    });
  });
</script>
</body>
</html>
