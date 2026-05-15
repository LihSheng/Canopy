from insights.domain import FactBundle


def build_prompt(facts: FactBundle) -> str:
    top_deps_str = "\n".join(
        f"  - {d.name}: MYR {d.total_spend:,.2f} total "
        f"(payroll: MYR {d.payroll_spend:,.2f}, claims: MYR {d.claims_spend:,.2f}) "
        f"[{d.change_pct:+.1f}% MoM]"
        for d in facts.top_departments
    ) or "  None"

    anomalies_str = "\n".join(
        f"  - [{a.severity.upper()}] {a.department_name}: {a.description}"
        for a in facts.anomalies
    ) or "  None"

    claim_types_str = "\n".join(
        f"  - {c.type}: MYR {c.amount:,.2f} ({c.count} claims)"
        for c in facts.claim_type_breakdown
    ) or "  None"

    rankings_str = "\n".join(
        f"  {i+1}. {r.name}: MYR {r.total_spend:,.2f}"
        for i, r in enumerate(facts.department_rankings)
    ) or "  None"

    previous_str = facts.previous_month if facts.previous_month else "N/A"

    return f"""You are an executive HR spend analyst. Based on the structured facts below, produce:
1. An executive summary (2-3 paragraphs) of the current month's HR spend situation.
2. A list of 3-5 actionable, read-only recommendations for cost optimization.
   Do not suggest any write-back, approval, or operational actions —
   only analysis and monitoring suggestions.
3. A list of 3-5 key findings that highlight the most important signals in the data.

Current month: {facts.current_month}
Previous month: {previous_str}

Dashboard summary:
- Total payroll: MYR {facts.total_payroll:,.2f}
- Total claims: MYR {facts.total_claims:,.2f}
- Departments reporting: {facts.department_count}
- Anomalies detected: {facts.anomaly_count}

Top departments by spend:
{top_deps_str}

Anomalies:
{anomalies_str}

Claim type breakdown:
{claim_types_str}

Full department rankings:
{rankings_str}

Return your response in JSON format with exactly these keys:
  "summary": "<executive summary text>",
  "recommendations": ["<recommendation 1>", "<recommendation 2>", ...],
  "key_findings": ["<finding 1>", "<finding 2>", ...]"""
