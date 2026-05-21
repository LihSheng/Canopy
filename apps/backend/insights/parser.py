import json


class ParsedInsight:
    def __init__(
        self,
        summary: str = "",
        recommendations: list[str] | None = None,
        key_findings: list[str] | None = None,
    ):
        self.summary = summary
        self.recommendations = recommendations or []
        self.key_findings = key_findings or []


def parse_llm_response(raw: str) -> ParsedInsight:
    try:
        data = _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        return ParsedInsight()

    return ParsedInsight(
        summary=_clean_text(data.get("summary", "")),
        recommendations=_clean_list(data.get("recommendations", [])),
        key_findings=_clean_list(data.get("key_findings", [])),
    )


def _extract_json(raw: str) -> dict:
    raw = raw.strip()

    if raw.startswith("```"):
        lines = raw.splitlines()
        content_lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        raw = "\n".join(content_lines)

    return json.loads(raw)  # type: ignore[no-any-return]


def _clean_text(text: str) -> str:
    return text.strip()


def _clean_list(items: list) -> list[str]:
    return [str(item).strip() for item in items if str(item).strip()]
