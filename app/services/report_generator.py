from datetime import datetime, timezone

from jinja2 import Environment, DictLoader

from app.schemas.insights import (
    GapsResponse,
    Insight,
    MethodTrend,
    PortfolioSummary,
    ROIResult,
)
from app.schemas.metrics import PaymentMethodMetrics

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FinoMart Payment Health Report</title>
<style>
  body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; color: #222; }
  h1 { color: #1a237e; }
  h2 { color: #283593; border-bottom: 2px solid #3949ab; padding-bottom: 4px; }
  table { border-collapse: collapse; width: 100%; margin-bottom: 24px; background: #fff; }
  th { background: #3949ab; color: #fff; padding: 8px 10px; text-align: left; }
  td { padding: 6px 10px; border-bottom: 1px solid #ddd; }
  tr:hover { background: #e8eaf6; }
  .badge { padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
  .badge-keep { background: #c8e6c9; color: #2e7d32; }
  .badge-negotiate { background: #fff9c4; color: #f57f17; }
  .badge-remove { background: #ffcdd2; color: #c62828; }
  .badge-active { background: #c8e6c9; color: #2e7d32; }
  .badge-declining { background: #fff9c4; color: #f57f17; }
  .badge-dormant { background: #ffcdd2; color: #c62828; }
  .insight-zombie { background: #ffcdd2; }
  .insight-cost_trap { background: #ffcdd2; }
  .insight-performance_alert { background: #fff9c4; }
  .insight-hidden_gem { background: #c8e6c9; }
  .summary-cards { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
  .card { background: #fff; padding: 16px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,.1); min-width: 140px; }
  .card-value { font-size: 1.8em; font-weight: bold; color: #3949ab; }
  .card-label { font-size: 0.85em; color: #666; }
  .flag-declining { color: #c62828; font-weight: bold; }
  .flag-growing { color: #2e7d32; font-weight: bold; }
  .flag-chargeback { color: #e65100; font-weight: bold; }
  .generated { color: #888; font-size: 0.8em; margin-top: 32px; }
</style>
</head>
<body>
<h1>FinoMart Payment Method Health Report</h1>
<p class="generated">Generated: {{ generated_at }}</p>

<h2>Portfolio Overview</h2>
<div class="summary-cards">
  <div class="card"><div class="card-value">{{ summary.total_methods }}</div><div class="card-label">Total Methods</div></div>
  <div class="card"><div class="card-value">{{ summary.active_count }}</div><div class="card-label">Active</div></div>
  <div class="card"><div class="card-value">{{ summary.declining_count }}</div><div class="card-label">Declining</div></div>
  <div class="card"><div class="card-value">{{ summary.dormant_count }}</div><div class="card-label">Dormant</div></div>
  <div class="card"><div class="card-value">${{ "%.0f"|format(summary.total_net_revenue_usd) }}</div><div class="card-label">Net Revenue (USD)</div></div>
  <div class="card"><div class="card-value">{{ "%.1f"|format(summary.avg_approval_rate * 100) }}%</div><div class="card-label">Avg Approval Rate</div></div>
  <div class="card"><div class="card-value">{{ "%.0f"|format(summary.total_roi_pct) }}%</div><div class="card-label">Portfolio ROI</div></div>
</div>
<div class="summary-cards">
  <div class="card"><div class="card-value" style="color:#c62828">{{ summary.zombie_count }}</div><div class="card-label">Zombies</div></div>
  <div class="card"><div class="card-value" style="color:#2e7d32">{{ summary.hidden_gem_count }}</div><div class="card-label">Hidden Gems</div></div>
  <div class="card"><div class="card-value" style="color:#c62828">{{ summary.cost_trap_count }}</div><div class="card-label">Cost Traps</div></div>
  <div class="card"><div class="card-value" style="color:#f57f17">{{ summary.performance_alert_count }}</div><div class="card-label">Performance Alerts</div></div>
</div>

<h2>Top Performers</h2>
<table>
<tr><th>Method</th><th>Country</th><th>Transactions</th><th>Net Revenue (USD)</th><th>Approval Rate</th><th>Status</th></tr>
{% for m in top_performers %}
<tr>
  <td>{{ m.name }}</td>
  <td>{{ m.country }}</td>
  <td>{{ m.total_transactions }}</td>
  <td>${{ "%.2f"|format(m.net_revenue_usd) }}</td>
  <td>{{ "%.1f"|format(m.approval_rate * 100) }}%</td>
  <td><span class="badge badge-{{ m.activity_status }}">{{ m.activity_status.upper() }}</span></td>
</tr>
{% endfor %}
</table>

<h2>Flagged Insights</h2>
<table>
<tr><th>Method</th><th>Country</th><th>Type</th><th>Metric</th><th>Value</th><th>Action</th></tr>
{% for ins in insights %}
<tr class="insight-{{ ins.insight_type }}">
  <td>{{ ins.payment_method_name }}</td>
  <td>{{ ins.country }}</td>
  <td>{{ ins.insight_type.replace("_", " ").title() }}</td>
  <td>{{ ins.metric }}</td>
  <td>{{ "%.2f"|format(ins.value) }}</td>
  <td>{{ ins.recommended_action }}</td>
</tr>
{% endfor %}
</table>

<h2>ROI Analysis</h2>
<table>
<tr><th>Method</th><th>Country</th><th>Net Revenue (USD)</th><th>Total Cost (USD)</th><th>ROI %</th><th>Recommendation</th><th>Breakeven Tx</th></tr>
{% for r in roi_results %}
<tr>
  <td>{{ r.name }}</td>
  <td>{{ r.country }}</td>
  <td>${{ "%.2f"|format(r.net_revenue_usd) }}</td>
  <td>${{ "%.2f"|format(r.total_cost_usd) }}</td>
  <td>{{ "%.1f"|format(r.roi_pct) }}%</td>
  <td><span class="badge badge-{{ r.recommendation.lower() }}">{{ r.recommendation }}</span></td>
  <td>{{ r.breakeven_tx_count }}</td>
</tr>
{% endfor %}
</table>

<h2>Trend Summary</h2>
<table>
<tr><th>Method</th><th>Country</th><th>Flags</th><th>Latest Week Tx</th><th>Latest Week Revenue</th><th>Latest Approval Rate</th></tr>
{% for t in trend_methods %}
<tr>
  <td>{{ t.name }}</td>
  <td>{{ t.country }}</td>
  <td>
    {% for flag in t.flags %}
      {% if flag == "DECLINING" %}<span class="flag-declining">DECLINING</span>{% endif %}
      {% if flag == "GROWING" %}<span class="flag-growing">GROWING</span>{% endif %}
      {% if flag == "CHARGEBACK_SPIKE" %}<span class="flag-chargeback">CHARGEBACK SPIKE</span>{% endif %}
    {% endfor %}
  </td>
  {% if t.weekly_trend %}
  <td>{{ t.weekly_trend[-1].tx_count }}</td>
  <td>${{ "%.2f"|format(t.weekly_trend[-1].net_revenue_usd) }}</td>
  <td>{{ "%.1f"|format(t.weekly_trend[-1].approval_rate * 100) }}%</td>
  {% else %}
  <td>—</td><td>—</td><td>—</td>
  {% endif %}
</tr>
{% endfor %}
</table>

<h2>Market Gaps</h2>
<table>
<tr><th>Country</th><th>Missing Method</th><th>Type</th><th>Popularity Score</th><th>Est. Revenue Uplift (USD/mo)</th></tr>
{% for g in gaps %}
<tr>
  <td>{{ g.country }}</td>
  <td>{{ g.method_name }}</td>
  <td>{{ g.method_type }}</td>
  <td>{{ g.popularity_score }}/10</td>
  <td>${{ "%.0f"|format(g.estimated_revenue_uplift_usd) }}</td>
</tr>
{% endfor %}
</table>

</body>
</html>
"""

_env = Environment(loader=DictLoader({"report.html": HTML_TEMPLATE}), autoescape=True)


def generate_html_report(
    metrics: list[PaymentMethodMetrics],
    insights: list[Insight],
    roi_results: list[ROIResult],
    trends: list[MethodTrend],
    gaps: GapsResponse,
    summary: PortfolioSummary,
) -> str:
    top_performers = sorted(metrics, key=lambda m: m.net_revenue_usd, reverse=True)[:10]
    template = _env.get_template("report.html")
    return template.render(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        summary=summary,
        top_performers=top_performers,
        insights=insights,
        roi_results=sorted(roi_results, key=lambda r: r.roi_pct),
        trend_methods=trends,
        gaps=gaps.gaps,
    )


def build_portfolio_summary(
    metrics: list[PaymentMethodMetrics],
    insights: list[Insight],
    roi_results: list[ROIResult],
) -> PortfolioSummary:
    active = sum(1 for m in metrics if m.activity_status == "active")
    declining = sum(1 for m in metrics if m.activity_status == "declining")
    dormant = sum(1 for m in metrics if m.activity_status == "dormant")
    total_rev = sum(m.net_revenue_usd for m in metrics)
    total_cost = sum(m.total_cost_usd for m in metrics)
    total_roi = (total_rev - total_cost) / total_cost * 100 if total_cost > 0 else 0.0
    approval_rates = [m.approval_rate for m in metrics if m.total_transactions > 0]
    avg_approval = sum(approval_rates) / len(approval_rates) if approval_rates else 0.0

    return PortfolioSummary(
        total_methods=len(metrics),
        active_count=active,
        declining_count=declining,
        dormant_count=dormant,
        total_net_revenue_usd=round(total_rev, 2),
        total_cost_usd=round(total_cost, 2),
        total_roi_pct=round(total_roi, 2),
        avg_approval_rate=round(avg_approval, 4),
        zombie_count=sum(1 for i in insights if i.insight_type == "zombie"),
        hidden_gem_count=sum(1 for i in insights if i.insight_type == "hidden_gem"),
        cost_trap_count=sum(1 for i in insights if i.insight_type == "cost_trap"),
        performance_alert_count=sum(1 for i in insights if i.insight_type == "performance_alert"),
    )
