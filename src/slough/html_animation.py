import json
from typing import Any

from slough.models import TraceResult

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Slough Dry-Run Animation</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Consolas', 'Courier New', monospace;
    background: #ffffff; color: #000000;
    display: flex; flex-direction: column; align-items: center;
    min-height: 100vh; padding: 16px;
  }
  .container {
    max-width: 1400px; width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  }
  .panel {
    height: 500px; overflow-y: auto; padding: 12px;
    font-size: 13px; line-height: 1.5;
    position: relative;
  }
  .code-panel {
    background: #f5f5f5; border-right: 1px solid #ddd;
    font-family: 'Consolas', 'Courier New', monospace;
  }
  .vars-panel {
    background: #fafafa;
    font-family: 'Consolas', 'Courier New', monospace;
  }
  .panel-header {
    font-size: 11px; font-weight: bold; text-transform: uppercase;
    letter-spacing: 0.5px; color: #888;
    padding-bottom: 8px; margin-bottom: 8px;
    border-bottom: 1px solid #ddd;
    position: sticky; top: 0; z-index: 2;
  }
  .code-panel .panel-header { background: #f5f5f5; }
  .vars-panel .panel-header { background: #fafafa; }
  .code-line {
    display: flex; align-items: center; gap: 8px;
    padding: 1px 4px; border-radius: 2px;
    transition: background 0.15s;
    min-height: 20px;
  }
  .code-line.highlight {
    background: #e8f0fe; font-weight: bold;
    outline: 2px solid #1a56db; outline-offset: -2px;
  }
  .line-num {
    color: #888; text-align: right; user-select: none;
    min-width: 32px; font-size: 11px;
    flex-shrink: 0;
  }
  .line-text { white-space: pre-wrap; word-break: break-all; }
  .var-entry {
    display: flex; gap: 8px; padding: 1px 4px;
    font-size: 12px; align-items: baseline;
  }
  .var-key { color: #1a56db; font-weight: bold; }
  .var-val { color: #16a34a; word-break: break-all; }
  .var-sep { color: #888; }
  .controls {
    grid-column: 1 / -1;
    display: flex; align-items: center; gap: 8px;
    padding: 10px 16px;
    background: #fff; border-top: 1px solid #ddd;
    flex-wrap: wrap;
  }
  .controls button {
    background: #f0f0f0; border: 1px solid #ccc;
    border-radius: 4px; padding: 6px 14px;
    font-family: 'Consolas', monospace; font-size: 13px;
    cursor: pointer; transition: background 0.15s;
  }
  .controls button:hover { background: #e0e0e0; }
  .controls button:active { background: #d0d0d0; }
  .controls button:disabled { opacity: 0.4; cursor: default; }
  .controls .btn-primary {
    background: #1a56db; color: #fff; border-color: #1a56db;
  }
  .controls .btn-primary:hover { background: #1648c0; }
  .controls .tc-label { font-size: 12px; color: #888; margin-left: auto; }
  .controls .speed-label { font-size: 12px; color: #888; }
  .controls input[type="range"] { width: 80px; }
  .status-bar {
    grid-column: 1 / -1;
    padding: 6px 16px; font-size: 12px;
    background: #fff; border-top: 1px solid #ddd;
    color: #555; min-height: 28px;
  }
  .summary-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000; visibility: hidden; opacity: 0;
    transition: opacity 0.3s;
  }
  .summary-overlay.active { visibility: visible; opacity: 1; }
  .summary-box {
    background: #fff; border-radius: 12px;
    padding: 32px 40px; max-width: 600px; width: 90%;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    text-align: center;
  }
  .summary-box h2 { margin-bottom: 20px; font-size: 20px; }
  .summary-row {
    display: flex; justify-content: space-between;
    padding: 8px 0; border-bottom: 1px solid #eee;
    font-size: 14px;
  }
  .summary-row .pass { color: #16a34a; font-weight: bold; }
  .summary-row .fail { color: #dc2626; font-weight: bold; }
  .summary-close {
    margin-top: 20px; padding: 8px 24px;
    background: #1a56db; color: #fff; border: none;
    border-radius: 6px; font-size: 14px; cursor: pointer;
  }
  .summary-close:hover { background: #1648c0; }
  .status-pass { color: #16a34a; font-weight: bold; }
  .status-fail { color: #dc2626; font-weight: bold; }
  .data-structure {
    margin: 4px 0; padding: 4px 8px;
    background: #f0f0f0; border-radius: 4px;
    font-size: 12px;
    display: inline-flex; flex-wrap: wrap; gap: 2px;
  }
  .ds-box {
    display: inline-flex; flex-direction: column; align-items: center;
    border: 1px solid #ccc; border-radius: 3px;
    padding: 2px 6px; background: #fff;
    font-size: 11px; min-width: 32px;
  }
  .ds-index { font-size: 9px; color: #888; }
  .return-line { margin-top: 4px; padding-top: 4px; border-top: 1px dashed #ddd; }
  @media (max-width: 768px) {
    .container { grid-template-columns: 1fr; }
    .code-panel { border-right: none; border-bottom: 1px solid #ddd; }
    .panel { height: 350px; }
  }
</style>
</head>
<body>
<div class="container" id="app">
  <div class="panel code-panel" id="codePanel">
    <div class="panel-header">&#x25A0; Source</div>
    <div id="codeLines"></div>
  </div>
  <div class="panel vars-panel" id="varsPanel">
    <div class="panel-header">&#x25A0; Variables</div>
    <div id="varContent"></div>
  </div>
  <div class="controls">
    <button id="btnPrev" title="Previous step">&#x25C0;</button>
    <button id="btnStep" class="btn-primary" title="Auto-play">&#x25B6; Play</button>
    <button id="btnNext" title="Next step">&#x25B6;</button>
    <button id="btnRestart" title="Restart">&#x21BA;</button>
    <span class="speed-label">Speed</span>
    <input type="range" id="speedRange" min="1" max="10" value="5">
    <span class="tc-label" id="tcLabel"></span>
  </div>
  <div class="status-bar" id="statusBar">Ready</div>
</div>

<div class="summary-overlay" id="summaryOverlay">
  <div class="summary-box">
    <h2>Results Summary</h2>
    <div id="summaryRows"></div>
    <button class="summary-close" onclick="closeSummary()">Close</button>
  </div>
</div>

<script>
// ===== DATA =====
const SOURCE_LINES = %SOURCE_LINES%;
const STEPS = %STEPS%;

// ===== STATE =====
let currentFrame = 0;
let totalFrames = 0;
let frames = [];
let isPlaying = false;
let playTimer = null;
let speedMs = 800;

function buildFrames() {
  frames = [];
  for (let tcIdx = 0; tcIdx < STEPS.length; tcIdx++) {
    const tc = STEPS[tcIdx];
    for (let sIdx = 0; sIdx < tc.steps.length; sIdx++) {
      frames.push({ tcIdx: tcIdx, stepIdx: sIdx, data: tc.steps[sIdx] });
    }
    frames.push({
      tcIdx: tcIdx,
      stepIdx: -1,
      data: { event: 'test_complete', lineno: null, vars: {}, func_name: '', return_value: tc.return_value, expected: tc.expected }
    });
  }
  totalFrames = frames.length;
}

function renderCode(highlightLineno) {
  const el = document.getElementById('codeLines');
  let html = '';
  for (let i = 0; i < SOURCE_LINES.length; i++) {
    const lineNum = i + 1;
    const isHighlight = lineNum === highlightLineno;
    html += '<div class="code-line' + (isHighlight ? ' highlight' : '') + '">';
    html += '<span class="line-num">' + lineNum + '</span>';
    html += '<span class="line-text">' + escapeHtml(SOURCE_LINES[i]) + '</span>';
    html += '</div>';
  }
  el.innerHTML = html;
  if (highlightLineno) {
    const highlighted = el.querySelector('.highlight');
    if (highlighted) highlighted.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
}

function renderVars(varsData, frameNum, total, eventType, funcName, returnValue) {
  const el = document.getElementById('varContent');
  let html = '';
  html += '<div style="margin-bottom:6px;color:#888;font-size:11px;">';
  html += 'Step ' + frameNum + ' of ' + total;
  if (funcName) html += ' &middot; ' + funcName;
  if (eventType && eventType !== 'line') html += ' &middot; <strong>' + eventType + '</strong>';
  html += '</div>';

  const keys = Object.keys(varsData);
  if (keys.length === 0) {
    html += '<div style="color:#aaa;font-style:italic;">No variables</div>';
  } else {
    for (const k of keys) {
      const v = varsData[k];
      html += '<div class="var-entry">';
      html += '<span class="var-key">' + escapeHtml(k) + '</span>';
      html += '<span class="var-sep">=</span>';
      html += '<span class="var-val">' + formatValue(v) + '</span>';
      html += '</div>';
    }
  }

  if (returnValue !== undefined && returnValue !== null) {
    html += '<div class="return-line var-entry">';
    html += '<span class="var-key" style="color:#7c3aed;">return</span>';
    html += '<span class="var-sep">=</span>';
    html += '<span class="var-val">' + formatValue(returnValue) + '</span>';
    html += '</div>';
  }

  el.innerHTML = html;
}

function formatValue(val) {
  if (val === null) return '<span style="color:#888;">null</span>';
  if (val === undefined) return '<span style="color:#888;">undefined</span>';
  if (typeof val === 'boolean') return '<span style="color:#7c3aed;">' + val + '</span>';
  if (typeof val === 'number') return '<span style="color:#7c3aed;">' + val + '</span>';
  if (typeof val === 'string') return '<span style="color:#c41a16;">"' + escapeHtml(val) + '"</span>';
  if (Array.isArray(val)) return formatList(val);
  if (typeof val === 'object') return formatDict(val);
  return escapeHtml(String(val));
}

function formatList(arr) {
  if (arr.length <= 20 && arr.every(v => typeof v !== 'object' || v === null)) {
    let html = '<span class="data-structure">';
    for (let i = 0; i < arr.length; i++) {
      html += '<span class="ds-box"><span class="ds-index">' + i + '</span><span>' + formatScalar(arr[i]) + '</span></span>';
    }
    html += '</span>';
    return html;
  }
  return '<span style="color:#888;">[' + arr.map(v => formatValue(v)).join(', ') + ']</span>';
}

function formatScalar(val) {
  if (val === null) return 'null';
  if (typeof val === 'string') return escapeHtml(val);
  return String(val);
}

function formatDict(obj) {
  const items = [];
  for (const k of Object.keys(obj)) {
    items.push(escapeHtml(k) + ': ' + formatValue(obj[k]));
  }
  return '<span style="color:#888;">{</span>' + items.join('<span style="color:#888;">, </span>') + '<span style="color:#888;">}</span>';
}

function escapeHtml(s) {
  if (typeof s !== 'string') return String(s);
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function goToFrame(idx) {
  if (idx < 0 || idx >= totalFrames) return;
  currentFrame = idx;
  const frame = frames[idx];
  const data = frame.data;

  if (data.event === 'test_complete') {
    renderCode(null);
    const tc = STEPS[frame.tcIdx];
    const rv = data.return_value;
    const expected = data.expected;
    let statusHtml = 'Test case ' + (frame.tcIdx + 1) + ' complete &middot; ';
    statusHtml += 'Return: ' + formatValue(rv);
    if (expected !== undefined && expected !== null) {
      const pass = JSON.stringify(rv) === JSON.stringify(expected);
      statusHtml += ' &middot; ';
      statusHtml += pass
        ? '<span class="status-pass">&#x2713; PASS</span>'
        : '<span class="status-fail">&#x2717; FAIL (expected: ' + formatValue(expected) + ')</span>';
    }
    document.getElementById('statusBar').innerHTML = statusHtml;
    renderVars({}, idx + 1, totalFrames, 'complete', '', rv);
  } else {
    renderCode(data.lineno);
    const filteredVars = {};
    for (const k of Object.keys(data.vars || {})) {
      if (k !== 'self') filteredVars[k] = data.vars[k];
    }
    renderVars(filteredVars, idx + 1, totalFrames, data.event, data.func_name, data.return_value);
    document.getElementById('statusBar').innerHTML = 'Line ' + (data.lineno || '?') + ' &middot; ' + (data.event || '');
  }

  document.getElementById('tcLabel').textContent = 'Test case ' + (frame.tcIdx + 1) + ' of ' + STEPS.length;
  updateButtons();
}

function updateButtons() {
  document.getElementById('btnPrev').disabled = currentFrame <= 0;
  document.getElementById('btnNext').disabled = currentFrame >= totalFrames - 1;
}

function nextStep() {
  if (currentFrame < totalFrames - 1) goToFrame(currentFrame + 1);
  else stopPlay();
}

function prevStep() {
  if (currentFrame > 0) goToFrame(currentFrame - 1);
}

function togglePlay() {
  const btn = document.getElementById('btnStep');
  if (isPlaying) {
    stopPlay();
  } else {
    if (currentFrame >= totalFrames - 1) goToFrame(0);
    isPlaying = true;
    btn.textContent = '\u23F8 Pause';
    tick();
  }
}

function stopPlay() {
  isPlaying = false;
  document.getElementById('btnStep').textContent = '\u25B6 Play';
  if (playTimer) { clearTimeout(playTimer); playTimer = null; }
}

function tick() {
  if (!isPlaying) return;
  goToFrame(currentFrame);
  if (currentFrame >= totalFrames - 1) {
    stopPlay();
    showSummary();
    return;
  }
  currentFrame++;
  playTimer = setTimeout(tick, speedMs);
}

function restart() {
  stopPlay();
  goToFrame(0);
}

function showSummary() {
  const el = document.getElementById('summaryRows');
  let html = '';
  let passed = 0, failed = 0;
  for (let i = 0; i < STEPS.length; i++) {
    const tc = STEPS[i];
    const rv = tc.return_value;
    const expected = tc.expected;
    const pass = JSON.stringify(rv) === JSON.stringify(expected);
    if (pass) passed++; else failed++;
    html += '<div class="summary-row">';
    html += '<span>Test case ' + (i + 1) + '</span>';
    html += '<span>Return: ' + formatValue(rv) + '</span>';
    if (expected !== undefined && expected !== null) {
      html += '<span>Expected: ' + formatValue(expected) + '</span>';
    }
    html += '<span class="' + (pass ? 'pass' : 'fail') + '">' + (pass ? '\u2713 PASS' : '\u2717 FAIL') + '</span>';
    html += '</div>';
  }
  html += '<div class="summary-row" style="font-weight:bold;border-top:2px solid #333;margin-top:8px;">';
  html += '<span>Total: ' + STEPS.length + '</span>';
  html += '<span class="pass">Passed: ' + passed + '</span>';
  if (failed > 0) html += '<span class="fail">Failed: ' + failed + '</span>';
  html += '</div>';
  el.innerHTML = html;
  document.getElementById('summaryOverlay').classList.add('active');
}

function closeSummary() {
  document.getElementById('summaryOverlay').classList.remove('active');
}

// Speed control
document.getElementById('speedRange').addEventListener('input', function() {
  const val = parseInt(this.value);
  speedMs = 1200 - (val - 1) * 110;
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === ' ' || e.key === 'Space') { e.preventDefault(); togglePlay(); }
  if (e.key === 'ArrowRight') { e.preventDefault(); nextStep(); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); prevStep(); }
  if (e.key === 'r') { restart(); }
});

// Init
document.getElementById('btnPrev').addEventListener('click', prevStep);
document.getElementById('btnNext').addEventListener('click', nextStep);
document.getElementById('btnStep').addEventListener('click', togglePlay);
document.getElementById('btnRestart').addEventListener('click', restart);

buildFrames();
goToFrame(0);
</script>
</body>
</html>"""


def _serialize_value(val: Any) -> str:
    """Serialize a value to a JSON-compatible string, handling custom objects."""
    if hasattr(val, "__dict__"):
        return json.dumps(val.__dict__, default=str)
    return json.dumps(val, default=str)


def _serialize_steps(results: list[TraceResult]) -> str:
    """Serialize trace results to a JSON string for embedding in HTML."""
    data = []
    for result in results:
        tc = result.test_case
        steps_data = []
        for step in result.steps:
            filtered_vars = {k: v for k, v in step.vars.items() if k != "self"}
            step_dict = {
                "lineno": step.lineno,
                "event": step.event,
                "func_name": step.func_name,
                "vars": filtered_vars,
                "return_value": step.return_value,
            }
            steps_data.append(step_dict)
        tc_dict = {
            "inputs": tc.inputs,
            "expected": tc.expected,
            "return_value": result.return_value,
            "steps": steps_data,
        }
        data.append(tc_dict)
    return json.dumps(data, default=str)


class HTMLAnimationGenerator:
    def __init__(self, source_lines: list[str], results: list[TraceResult], output_path: str):
        self._source_lines = source_lines
        self._results = results
        self._output_path = output_path

    def _build_html(self) -> str:
        steps_json = _serialize_steps(self._results)
        source_json = json.dumps(self._source_lines)
        html = _HTML_TEMPLATE.replace("%SOURCE_LINES%", source_json)
        html = html.replace("%STEPS%", steps_json)
        return html

    def generate(self) -> str:
        html = self._build_html()
        with open(self._output_path, "w") as f:
            f.write(html)
        return html


def generate_html_animation(results: list[TraceResult], source_lines: list[str], output_path: str) -> str:
    return HTMLAnimationGenerator(source_lines, results, output_path).generate()
