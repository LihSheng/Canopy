import uuid

from sqlalchemy.orm import Session

from common.clock import utcnow
from insights.domain import FactBundle, InsightSummary
from insights.facts import extract_facts
from insights.fallback import (
    build_fallback_findings,
    build_fallback_recommendations,
    build_fallback_summary,
)
from insights.llm_client import LlmClient, StubLlmClient
from insights.parser import parse_llm_response
from insights.prompt_builder import build_prompt
from insights.repository import InsightRepository


def generate_insight(
    db: Session,
    llm: LlmClient | None = None,
) -> InsightSummary | None:
    facts = extract_facts(db)
    if facts is None:
        return None

    client = llm or StubLlmClient()
    try:
        raw = client.generate(build_prompt(facts))
        parsed = parse_llm_response(raw)

        if parsed.summary:
            summary = InsightSummary(
                id=str(uuid.uuid4()),
                snapshot_id=facts.snapshot_id,
                current_month=facts.current_month,
                summary_text=parsed.summary,
                recommendations=parsed.recommendations,
                key_findings=parsed.key_findings,
                is_fallback=False,
                generated_at=utcnow().isoformat(),
                anomaly_count=facts.anomaly_count,
                department_count=facts.department_count,
                total_payroll=facts.total_payroll,
                total_claims=facts.total_claims,
            )
        else:
            summary = _build_fallback_summary(facts)
    except Exception:
        summary = _build_fallback_summary(facts)

    repo = InsightRepository(db)
    repo.clear_snapshot(facts.snapshot_id)
    repo.save(summary)
    return summary


def get_latest_insight(db: Session) -> InsightSummary | None:
    repo = InsightRepository(db)
    return repo.find_latest()


def _build_fallback_summary(facts: FactBundle) -> InsightSummary:
    return InsightSummary(
        id=str(uuid.uuid4()),
        snapshot_id=facts.snapshot_id,
        current_month=facts.current_month,
        summary_text=build_fallback_summary(facts),
        recommendations=build_fallback_recommendations(facts),
        key_findings=build_fallback_findings(facts),
        is_fallback=True,
        generated_at=utcnow().isoformat(),
        anomaly_count=facts.anomaly_count,
        department_count=facts.department_count,
        total_payroll=facts.total_payroll,
        total_claims=facts.total_claims,
    )
