"""
Call Analytics Dashboard — A lightweight HTTP server that displays
call outcome statistics (Total / Successful / Failed) from the SQLite database.

Run:  python src/call_analytics_dashboard.py
Open: http://localhost:5051

Privacy: No transcripts, passwords, OTPs, PINs, account numbers, or
medical details are stored or displayed.
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

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
<title>Call Analytics — Learning & Literacy</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

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
    background: linear-gradient(90deg, #38bdf8, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .header .refresh-info {
    font-size: 0.8rem;
    color: #64748b;
  }

  .container { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }

  /* ── Stat Cards ── */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 36px;
  }

  .stat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  }

  .stat-card.total {
    border-color: rgba(56,189,248,0.2);
  }
  .stat-card.total:hover {
    border-color: rgba(56,189,248,0.4);
    box-shadow: 0 8px 32px rgba(56,189,248,0.1);
  }

  .stat-card.success {
    border-color: rgba(34,197,94,0.2);
  }
  .stat-card.success:hover {
    border-color: rgba(34,197,94,0.4);
    box-shadow: 0 8px 32px rgba(34,197,94,0.1);
  }

  .stat-card.failed {
    border-color: rgba(239,68,68,0.2);
  }
  .stat-card.failed:hover {
    border-color: rgba(239,68,68,0.4);
    box-shadow: 0 8px 32px rgba(239,68,68,0.1);
  }

  .stat-card.rate {
    border-color: rgba(167,139,250,0.2);
  }
  .stat-card.rate:hover {
    border-color: rgba(167,139,250,0.4);
    box-shadow: 0 8px 32px rgba(167,139,250,0.1);
  }

  .stat-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
    font-size: 1.5rem;
  }

  .stat-card.total .stat-icon {
    background: rgba(56,189,248,0.12);
    border: 1px solid rgba(56,189,248,0.25);
  }

  .stat-card.success .stat-icon {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.25);
  }

  .stat-card.failed .stat-icon {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.25);
  }

  .stat-card.rate .stat-icon {
    background: rgba(167,139,250,0.12);
    border: 1px solid rgba(167,139,250,0.25);
  }

  .stat-number {
    font-size: 2.8rem;
    font-weight: 800;
    margin-bottom: 6px;
    line-height: 1;
  }

  .stat-card.total .stat-number { color: #38bdf8; }
  .stat-card.success .stat-number { color: #4ade80; }
  .stat-card.failed .stat-number { color: #f87171; }
  .stat-card.rate .stat-number { color: #a78bfa; }

  .stat-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* ── Recent Calls Table ── */
  .section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 16px;
  }

  .table-wrap {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    overflow: hidden;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th {
    text-align: left;
    padding: 14px 18px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    background: rgba(0,0,0,0.25);
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }

  td {
    padding: 14px 18px;
    font-size: 0.88rem;
    color: #cbd5e1;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }

  tr:hover td {
    background: rgba(255,255,255,0.02);
  }

  .badge {
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: inline-block;
  }

  .badge.successful {
    background: rgba(34,197,94,0.15);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.3);
  }

  .badge.failed {
    background: rgba(239,68,68,0.15);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.3);
  }

  .badge.in_progress {
    background: rgba(251,191,36,0.15);
    color: #fbbf24;
    border: 1px solid rgba(251,191,36,0.3);
  }

  .badge.web {
    background: rgba(56,189,248,0.12);
    color: #38bdf8;
    border: 1px solid rgba(56,189,248,0.25);
  }

  .badge.sip {
    background: rgba(167,139,250,0.12);
    color: #a78bfa;
    border: 1px solid rgba(167,139,250,0.25);
  }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #64748b;
  }

  .empty-state .icon { font-size: 2.5rem; margin-bottom: 12px; }
  .empty-state h2 { font-size: 1.2rem; color: #94a3b8; margin-bottom: 6px; }
  .empty-state p { font-size: 0.9rem; }

  @media (max-width: 640px) {
    .stats-grid { grid-template-columns: 1fr; }
    .header { padding: 20px; flex-direction: column; gap: 12px; }
    th, td { padding: 10px 12px; font-size: 0.78rem; }
  }
</style>
</head>
<body>

<div class="header">
  <h1>📊 Call Analytics Dashboard</h1>
  <span class="refresh-info">Auto-refreshes every 5s</span>
</div>

<div class="container">
  <!-- Stat Cards -->
  <div class="stats-grid">
    <div class="stat-card total">
      <div class="stat-icon">📞</div>
      <div class="stat-number">{{total}}</div>
      <div class="stat-label">Total Calls</div>
    </div>
    <div class="stat-card success">
      <div class="stat-icon">✅</div>
      <div class="stat-number">{{successful}}</div>
      <div class="stat-label">Successful Calls</div>
    </div>
    <div class="stat-card failed">
      <div class="stat-icon">❌</div>
      <div class="stat-number">{{failed}}</div>
      <div class="stat-label">Failed Calls</div>
    </div>
    <div class="stat-card rate">
      <div class="stat-icon">📈</div>
      <div class="stat-number">{{success_rate}}%</div>
      <div class="stat-label">Success Rate</div>
    </div>
  </div>

  <!-- Recent Calls -->
  <h2 class="section-title">Recent Calls</h2>
  {{recent_calls_content}}
</div>

<script>
  // Auto-refresh every 5 seconds
  setTimeout(() => location.reload(), 5000);
</script>
</body>
</html>"""


def _format_time(iso_str: str | None) -> str:
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return iso_str


def _build_recent_calls_table(calls: list[dict]) -> str:
    if not calls:
        return """
        <div class="empty-state">
          <div class="icon">📭</div>
          <h2>No Calls Yet</h2>
          <p>Make a call through the voice agent to see data here.</p>
        </div>"""

    rows = ""
    for c in calls:
        outcome_badge = f'<span class="badge {c["outcome"]}">{c["outcome"].replace("_", " ")}</span>'
        type_badge = f'<span class="badge {c["call_type"]}">{c["call_type"].upper()}</span>'
        rows += f"""
        <tr>
          <td>{c["call_id"]}</td>
          <td>{c["caller_name"] or "Unknown"}</td>
          <td>{type_badge}</td>
          <td>{outcome_badge}</td>
          <td>{c["exercises_attempted"]}</td>
          <td>{c["exercises_passed"]}</td>
          <td>{_format_time(c["started_at"])}</td>
        </tr>"""

    return f"""
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Call ID</th>
            <th>Caller</th>
            <th>Type</th>
            <th>Outcome</th>
            <th>Exercises Attempted</th>
            <th>Exercises Passed</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def _build_page() -> str:
    stats = database.get_call_stats()
    recent = database.get_recent_calls(limit=20)

    html = DASHBOARD_HTML
    html = html.replace("{{total}}", str(stats["total"]))
    html = html.replace("{{successful}}", str(stats["successful"]))
    html = html.replace("{{failed}}", str(stats["failed"]))
    rate = round((stats["successful"] / stats["total"]) * 100) if stats["total"] > 0 else 0
    html = html.replace("{{success_rate}}", str(rate))
    html = html.replace("{{recent_calls_content}}", _build_recent_calls_table(recent))
    return html


class AnalyticsDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "":
            html = _build_page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        elif self.path == "/api/stats":
            stats = database.get_call_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats, indent=2).encode("utf-8"))
        elif self.path == "/api/calls":
            calls = database.get_recent_calls()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(calls, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[CallAnalytics] {args[0]}")


def main():
    port = int(os.environ.get("ANALYTICS_PORT", "5051"))
    server = HTTPServer(("0.0.0.0", port), AnalyticsDashboardHandler)
    print(f"[Call Analytics Dashboard] Running at http://localhost:{port}")
    print("  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CallAnalytics] Stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
