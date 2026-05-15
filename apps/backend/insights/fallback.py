from insights.domain import FactBundle


def build_fallback_summary(facts: FactBundle) -> str:
    lines: list[str] = []
    lines.append(
        f"HR Spend Executive Summary for {facts.current_month}\n"
    )

    lines.append("Overview")
    lines.append("--------")
    lines.append(
        f"Total organizational spend this month was MYR "
        f"{facts.total_payroll + facts.total_claims:,.2f}, comprising "
        f"MYR {facts.total_payroll:,.2f} in payroll and "
        f"MYR {facts.total_claims:,.2f} in claims across "
        f"{facts.department_count} departments."
    )

    if facts.anomaly_count > 0:
        lines.append(
            f"\n{facts.anomaly_count} spending anomaly(s) were detected "
            f"this period, requiring management attention."
        )
    else:
        lines.append(
            "\nNo spending anomalies were detected this period."
        )

    if facts.top_departments:
        lines.append("\nTop Departments by Spend")
        lines.append("------------------------")
        for d in facts.top_departments[:3]:
            lines.append(
                f"  - {d.name}: MYR {d.total_spend:,.2f} "
                f"({d.change_pct:+.1f}% vs previous month)"
            )

    if facts.claim_type_breakdown:
        lines.append("\nClaim Type Distribution")
        lines.append("----------------------")
        for c in facts.claim_type_breakdown[:5]:
            lines.append(f"  - {c.type}: MYR {c.amount:,.2f} ({c.count} claims)")

    return "\n".join(lines)


def build_fallback_recommendations(facts: FactBundle) -> list[str]:
    recs: list[str] = []

    if facts.anomaly_count > 0:
        recs.append(
            "Review departments with detected anomalies for root cause analysis."
        )

    high_change = [
        d for d in facts.top_departments if abs(d.change_pct) >= 10.0
    ]
    if high_change:
        names = ", ".join(d.name for d in high_change[:3])
        recs.append(
            f"Monitor month-over-month spend trends in departments with "
            f"significant variance: {names}."
        )

    recs.append(
        "Consider a quarterly spend review to identify cost optimisation "
        "opportunities."
    )

    if facts.top_departments:
        top = facts.top_departments[0]
        recs.append(
            f"Investigate claims composition in {top.name}, the highest-spend "
            f"department this period."
        )

    recs.append(
        "Set up automated anomaly thresholds to receive early warning "
        "for unusual spend patterns."
    )

    return recs[:5]


def build_fallback_findings(facts: FactBundle) -> list[str]:
    findings: list[str] = []

    total = facts.total_payroll + facts.total_claims
    findings.append(
        f"Payroll represents {_pct(facts.total_payroll, total)}% "
        f"of total organisational spend (MYR {facts.total_payroll:,.2f})."
    )

    findings.append(
        f"Claims represent {_pct(facts.total_claims, facts.total_payroll + facts.total_claims)}% "
        f"of total organisational spend (MYR {facts.total_claims:,.2f})."
    )

    if facts.anomaly_count > 0:
        high_count = sum(1 for a in facts.anomalies if a.severity == "high")
        medium_count = sum(1 for a in facts.anomalies if a.severity == "medium")
        parts: list[str] = []
        if high_count:
            parts.append(f"{high_count} high-severity")
        if medium_count:
            parts.append(f"{medium_count} medium-severity")
        parts.append(f"of {facts.anomaly_count} total anomalies")
        findings.append(f"Spending anomalies detected: {', '.join(parts)}.")
    else:
        findings.append("No spending anomalies were detected this period.")

    if len(facts.department_rankings) >= 3:
        top3 = facts.department_rankings[:3]
        findings.append(
            "Top 3 departments by spend: "
            + ", ".join(f"{r.name} (MYR {r.total_spend:,.0f})" for r in top3)
            + "."
        )

    if facts.claim_type_breakdown:
        top_type = facts.claim_type_breakdown[0]
        findings.append(
            f"The largest claim category is '{top_type.type}' at MYR "
            f"{top_type.amount:,.2f} ({top_type.count} claims)."
        )

    return findings[:5]


def _pct(part: float, total: float) -> str:
    if total == 0:
        return "0"
    return f"{round((part / total) * 100, 1):.1f}"
