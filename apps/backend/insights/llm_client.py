from typing import Protocol


class LlmClient(Protocol):
    def generate(self, prompt: str) -> str: ...


class StubLlmClient:
    def generate(self, prompt: str) -> str:
        return _stub_response_json()


def _stub_response_json() -> str:
    return (
        '{\n'
        '  "summary": "This month showed stable HR spend across departments '
        'with payroll as the dominant cost driver. Total organizational spend '
        'was within expected ranges. A few departments showed elevated claims '
        'activity that warrants monitoring in the coming month.",\n'
        '  "recommendations": [\n'
        '    "Review claims activity in the highest-spend departments for '
        'category-level trends.",\n'
        '    "Monitor month-over-month payroll variance to identify seasonal '
        'patterns.",\n'
        '    "Set up automated anomaly alerts for departments exceeding 10% '
        'month-over-month change.",\n'
        '    "Consider a quarterly claims audit to verify compliance with '
        'expense policies.",\n'
        '    "Track claim type distribution to identify categories with '
        'above-average growth."\n'
        '  ],\n'
        '  "key_findings": [\n'
        '    "Payroll remains the largest cost category across all departments.",\n'
        '    "Claim counts are within expected ranges for the current month.",\n'
        '    "Department spend rankings are consistent with prior month '
        'patterns.",\n'
        '    "No departments exceeded the high-severity anomaly threshold.",\n'
        '    "Claim type distribution suggests no unusual spending patterns '
        'this period."\n'
        '  ]\n'
        '}'
    )
