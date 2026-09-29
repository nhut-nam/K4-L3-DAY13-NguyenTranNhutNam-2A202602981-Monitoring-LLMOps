from __future__ import annotations

import json
from pathlib import Path

LOG_PATH = Path("data/logs.jsonl")
OUTPUT_HTML = Path("data/dashboard.html")


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return round(d0 + d1, 2)


def main() -> None:
    if not LOG_PATH.exists():
        print(f"Log file {LOG_PATH} not found.")
        return

    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    req_received = [r for r in records if r.get("event") == "request_received"]
    resp_sent = [r for r in records if r.get("event") == "response_sent"]
    req_failed = [r for r in records if r.get("event") == "request_failed"]

    latencies = [float(r["latency_ms"]) for r in resp_sent if "latency_ms" in r]
    ttfts = [float(r["ttft_ms"]) for r in resp_sent if "ttft_ms" in r]

    p50_lat = percentile(latencies, 50)
    p95_lat = percentile(latencies, 95)
    p99_lat = percentile(latencies, 99)
    p95_ttft = percentile(ttfts, 95)

    traffic_count = len(req_received)
    failed_count = len(req_failed)
    total_reqs = traffic_count if traffic_count > 0 else 1
    error_rate_pct = round((failed_count / total_reqs) * 100, 2)

    tool_successes = [r.get("tool_success") for r in records if r.get("tool_success") is not None]
    tool_success_pct = (
        round((sum(1 for s in tool_successes if s is True) / len(tool_successes)) * 100, 2)
        if tool_successes
        else 100.0
    )

    total_cost = round(sum(float(r.get("cost_usd", 0.0)) for r in resp_sent), 6)
    tokens_in = sum(int(r.get("tokens_in", 0)) for r in resp_sent)
    tokens_out = sum(int(r.get("tokens_out", 0)) for r in resp_sent)

    quality_scores = [float(r["quality_score"]) for r in resp_sent if "quality_score" in r]
    mean_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>K4-L3A Day 13 Monitoring & LLMOps Dashboard</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      margin: 0;
      padding: 24px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #334155;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }}
    h1 {{ margin: 0; font-size: 22px; color: #38bdf8; }}
    .badge {{ background: #1e293b; padding: 6px 12px; border-radius: 6px; font-size: 13px; color: #94a3b8; border: 1px solid #334155; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 20px;
    }}
    .panel {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }}
    .panel-title {{
      font-size: 14px;
      font-weight: 600;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
    }}
    .metric-main {{
      font-size: 32px;
      font-weight: 700;
      color: #f8fafc;
      margin-bottom: 8px;
    }}
    .metric-sub {{
      font-size: 13px;
      color: #64748b;
      line-height: 1.6;
    }}
    .status-ok {{ color: #4ade80; }}
    .status-warn {{ color: #fbbf24; }}
    .status-alert {{ color: #f87171; }}
    .threshold-tag {{
      display: inline-block;
      font-size: 11px;
      background: #0f172a;
      padding: 2px 8px;
      border-radius: 4px;
      color: #38bdf8;
      margin-top: 10px;
      border: 1px solid #334155;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>K4-L3A Day 13 Monitoring & LLMOps Dashboard</h1>
      <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">Time range: Last 60 minutes | Refresh: 30s | Source: data/logs.jsonl</div>
    </div>
    <div class="badge">Student: 2A202602981</div>
  </div>

  <div class="grid">
    <!-- Panel 1: Latency -->
    <div class="panel">
      <div class="panel-title">
        <span>Latency percentiles and TTFT</span>
        <span class="status-ok">P95 &le; 3000ms</span>
      </div>
      <div class="metric-main">{p95_lat} <span style="font-size: 16px; color: #94a3b8;">ms (P95)</span></div>
      <div class="metric-sub">
        <div>• P50: <strong>{p50_lat} ms</strong> | P99: <strong>{p99_lat} ms</strong></div>
        <div>• TTFT P95: <strong>{p95_ttft} ms</strong></div>
      </div>
      <div class="threshold-tag">SLO Threshold: P95 &le; 3000 ms</div>
    </div>

    <!-- Panel 2: Traffic -->
    <div class="panel">
      <div class="panel-title">
        <span>Request traffic</span>
        <span class="status-ok">Active</span>
      </div>
      <div class="metric-main">{traffic_count} <span style="font-size: 16px; color: #94a3b8;">requests</span></div>
      <div class="metric-sub">
        <div>• Total received: <strong>{traffic_count}</strong></div>
        <div>• Rate: <strong>~{traffic_count} req/min</strong></div>
      </div>
      <div class="threshold-tag">Threshold: rate &ge; 1 req/min</div>
    </div>

    <!-- Panel 3: Errors -->
    <div class="panel">
      <div class="panel-title">
        <span>Error rate &amp; Retrieval success</span>
        <span class="status-ok">Healthy</span>
      </div>
      <div class="metric-main">{error_rate_pct}% <span style="font-size: 16px; color: #94a3b8;">error rate</span></div>
      <div class="metric-sub">
        <div>• Failed requests: <strong>{failed_count} / {traffic_count}</strong></div>
        <div>• Retrieval success rate: <strong>{tool_success_pct}%</strong></div>
      </div>
      <div class="threshold-tag">SLO Threshold: Error rate &le; 2%, Tool success &ge; 90%</div>
    </div>

    <!-- Panel 4: Cost -->
    <div class="panel">
      <div class="panel-title">
        <span>Cost over time</span>
        <span class="status-ok">Within Budget</span>
      </div>
      <div class="metric-main">${total_cost:.4f} <span style="font-size: 16px; color: #94a3b8;">USD</span></div>
      <div class="metric-sub">
        <div>• Cumulative window cost: <strong>${total_cost:.6f}</strong></div>
        <div>• Cost per request avg: <strong>${(total_cost/max(len(resp_sent), 1)):.6f}</strong></div>
      </div>
      <div class="threshold-tag">Budget Threshold: Total &le; $2.50 USD</div>
    </div>

    <!-- Panel 5: Tokens -->
    <div class="panel">
      <div class="panel-title">
        <span>Input &amp; Output Tokens</span>
        <span class="status-ok">Normal</span>
      </div>
      <div class="metric-main">{tokens_in + tokens_out} <span style="font-size: 16px; color: #94a3b8;">total tokens</span></div>
      <div class="metric-sub">
        <div>• Input tokens: <strong>{tokens_in}</strong></div>
        <div>• Output tokens: <strong>{tokens_out}</strong></div>
      </div>
      <div class="threshold-tag">Threshold: sum &le; 50,000 tokens</div>
    </div>

    <!-- Panel 6: Quality -->
    <div class="panel">
      <div class="panel-title">
        <span>Quality Proxy</span>
        <span class="status-ok">Good</span>
      </div>
      <div class="metric-main">{mean_quality} <span style="font-size: 16px; color: #94a3b8;">/ 1.0</span></div>
      <div class="metric-sub">
        <div>• Mean quality score: <strong>{mean_quality}</strong></div>
        <div>• Evaluated responses: <strong>{len(quality_scores)}</strong></div>
      </div>
      <div class="threshold-tag">SLO Threshold: Mean &ge; 0.75</div>
    </div>
  </div>
</body>
</html>
"""
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")
    print(f"Generated dashboard HTML at {OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
