"""
Escalation Dashboard — A lightweight HTTP server that displays open
escalation requests from the local SQLite database.

Run:  python src/escalation_dashboard.py
Open: http://localhost:5050
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Allow imports from src/ directory
sys.path.insert(0, os.path.dirname(__file__))

import database  # noqa: E402

# Ensure DB tables exist
database.initialize_db()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Escalation Dashboard — Learning &amp; Literacy</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', sans-serif;
    background: #0f0f1a;
    color: #e0e0e8;
    min-height: 100vh;
  }

  .header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 28px 40px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .header .badge {
    background: rgba(239,68,68,0.15);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.3);
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .header .badge.empty {
    background: rgba(34,197,94,0.15);
    color: #4ade80;
    border-color: rgba(34,197,94,0.3);
  }

  .container { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }

  .tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
  }

  .tab {
    padding: 8px 20px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    color: #94a3b8;
    transition: all 0.2s;
  }

  .tab.active {
    background: rgba(167,139,250,0.15);
    color: #a78bfa;
    border-color: rgba(167,139,250,0.3);
  }

  .tab:hover { background: rgba(255,255,255,0.06); }

  .empty-state {
    text-align: center;
    padding: 80px 20px;
    color: #64748b;
  }

  .empty-state .icon { font-size: 3rem; margin-bottom: 16px; }
  .empty-state h2 { font-size: 1.3rem; color: #94a3b8; margin-bottom: 8px; }
  .empty-state p { font-size: 0.95rem; }

  .card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .card:hover {
    border-color: rgba(167,139,250,0.25);
    box-shadow: 0 4px 24px rgba(167,139,250,0.06);
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .card-header .ref {
    font-size: 0.8rem;
    font-weight: 600;
    color: #a78bfa;
    background: rgba(167,139,250,0.1);
    padding: 4px 12px;
    border-radius: 6px;
  }

  .urgency {
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .urgency.high {
    background: rgba(239,68,68,0.15);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.3);
  }

  .urgency.medium {
    background: rgba(251,191,36,0.15);
    color: #fbbf24;
    border: 1px solid rgba(251,191,36,0.3);
  }

  .card-body h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 12px;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
  }

  .detail {
    background: rgba(0,0,0,0.2);
    padding: 12px 16px;
    border-radius: 8px;
  }

  .detail-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    margin-bottom: 4px;
  }

  .detail-value {
    font-size: 0.9rem;
    color: #cbd5e1;
    line-height: 1.4;
  }

  .detail.full { grid-column: 1 / -1; }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,0.05);
  }

  .card-footer .time {
    font-size: 0.8rem;
    color: #64748b;
  }

  .btn-resolve {
    padding: 8px 20px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    background: rgba(34,197,94,0.15);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.3);
  }

  .btn-resolve:hover {
    background: rgba(34,197,94,0.25);
    box-shadow: 0 2px 12px rgba(34,197,94,0.15);
  }

  .status-resolved {
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(34,197,94,0.1);
    color: #4ade80;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  @media (max-width: 640px) {
    .detail-grid { grid-template-columns: 1fr; }
    .header { padding: 20px; flex-direction: column; gap: 12px; }
  }
</style>
</head>
<body>

<div class="header">
  <h1>Escalation Dashboard</h1>
  <div class="badge {{badge_class}}">{{badge_text}}</div>
</div>

<div class="container">
  <div class="tabs">
    <div class="tab {{tab_open_class}}" onclick="location.href='/'">Open Requests</div>
    <div class="tab {{tab_all_class}}" onclick="location.href='/?view=all'">All Requests</div>
  </div>

  {{content}}
</div>

<script>
async function resolveEscalation(refId) {
  if (!confirm('Mark escalation ' + refId + ' as resolved?')) return;
  const resp = await fetch('/resolve/' + refId, { method: 'POST' });
  if (resp.ok) location.reload();
  else alert('Failed to resolve escalation.');
}
</script>
</body>
</html>"""


def _render_card(esc: dict) -> str:
    urgency_cls = "high" if esc["urgency"] == "high" else "medium"
    is_resolved = esc["status"] == "resolved"

    try:
        dt = datetime.fromisoformat(esc["created_at"])
        time_str = dt.strftime("%b %d, %Y at %I:%M %p")
    except Exception:
        time_str = esc["created_at"]

    footer_action = (
        f'<span class="status-resolved">Resolved</span>'
        if is_resolved
        else f'<button class="btn-resolve" onclick="resolveEscalation(\'{esc["reference_id"]}\')">Mark Resolved</button>'
    )

    return f"""
    <div class="card">
      <div class="card-header">
        <span class="ref">{esc["reference_id"]}</span>
        <span class="urgency {urgency_cls}">{esc["urgency"]} urgency</span>
      </div>
      <div class="card-body">
        <h3>{esc["who_needs_help"]}</h3>
        <div class="detail-grid">
          <div class="detail full">
            <div class="detail-label">What Happened</div>
            <div class="detail-value">{esc["what_happened"]}</div>
          </div>
          <div class="detail full">
            <div class="detail-label">What the Agent Already Checked</div>
            <div class="detail-value">{esc["agent_checks"]}</div>
          </div>
          <div class="detail">
            <div class="detail-label">Language</div>
            <div class="detail-value">{esc["language_preference"]}</div>
          </div>
          <div class="detail">
            <div class="detail-label">Preferred Follow-Up</div>
            <div class="detail-value">{esc["preferred_followup"]}</div>
          </div>
        </div>
      </div>
      <div class="card-footer">
        <span class="time">{time_str}</span>
        {footer_action}
      </div>
    </div>"""


def _build_page(view: str = "open") -> str:
    if view == "all":
        escalations = database.get_all_escalations()
        tab_open_class = ""
        tab_all_class = "active"
    else:
        escalations = database.get_open_escalations()
        tab_open_class = "active"
        tab_all_class = ""

    open_count = len(database.get_open_escalations())
    badge_text = f"{open_count} Open Request{'s' if open_count != 1 else ''}" if open_count > 0 else "No Open Requests"
    badge_class = "" if open_count > 0 else "empty"

    if not escalations:
        content = """
        <div class="empty-state">
          <div class="icon">&#10003;</div>
          <h2>All Clear!</h2>
          <p>No open escalation requests at the moment.</p>
        </div>"""
    else:
        content = "\n".join(_render_card(e) for e in escalations)

    html = DASHBOARD_HTML
    html = html.replace("{{badge_text}}", badge_text)
    html = html.replace("{{badge_class}}", badge_class)
    html = html.replace("{{tab_open_class}}", tab_open_class)
    html = html.replace("{{tab_all_class}}", tab_all_class)
    html = html.replace("{{content}}", content)
    return html


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "":
            params = dict(p.split("=") for p in parsed.query.split("&") if "=" in p)
            view = params.get("view", "open")
            html = _build_page(view)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        elif parsed.path == "/api/escalations":
            escalations = database.get_all_escalations()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(escalations, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith("/resolve/"):
            ref_id = self.path.split("/resolve/")[1]
            success = database.resolve_escalation(ref_id)
            self.send_response(200 if success else 404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            result = {"resolved": success, "reference_id": ref_id}
            self.wfile.write(json.dumps(result).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[Dashboard] {args[0]}")


def main():
    port = int(os.environ.get("DASHBOARD_PORT", "5050"))
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"[Escalation Dashboard] Running at http://localhost:{port}")
    print("  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Dashboard] Stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
