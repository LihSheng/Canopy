"""Unit tests for the formula engine (Step 1)."""

import pytest

from common.errors import ValidationError
from entity_formula_engine.engine import FormulaEngine

pytestmark = pytest.mark.unit


class TestFormulaEngine:
    """TDD: RED tests for formula engine."""

    def test_direct_field_access(self):
        """Bare property key returns the row value."""
        engine = FormulaEngine()
        result = engine.evaluate(
            formula="employee_name",
            row_data={"employee_name": "Alice"},
        )
        assert result == "Alice"

    def test_upper_transform(self):
        """upper() returns uppercase string."""
        engine = FormulaEngine()
        result = engine.evaluate(
            formula="upper(employee_name)",
            row_data={"employee_name": "Alice"},
        )
        assert result == "ALICE"

    def test_coalesce(self):
        """coalesce returns first non-null value."""
        engine = FormulaEngine()
        result = engine.evaluate(
            formula="coalesce(null, backup_value)",
            row_data={"backup_value": "fallback"},
        )
        assert result == "fallback"

    def test_if_condition(self):
        """if evaluates condition and picks branch."""
        engine = FormulaEngine()
        result = engine.evaluate(
            formula="if(greater_than(salary, 50000), 'high', 'low')",
            row_data={"salary": 60000},
        )
        assert result == "high"

    def test_add(self):
        """add returns numeric sum."""
        engine = FormulaEngine()
        result = engine.evaluate(
            formula="add(base_salary, bonus)",
            row_data={"base_salary": 5000, "bonus": 500},
        )
        assert result == 5500

    def test_concat(self):
        """concat joins strings."""
        engine = FormulaEngine()
        result = engine.evaluate(
            formula="concat(first_name, ' ', last_name)",
            row_data={"first_name": "Alice", "last_name": "Smith"},
        )
        assert result == "Alice Smith"

    def test_is_null(self):
        """is_null returns True for null."""
        engine = FormulaEngine()
        result = engine.evaluate(
            formula="is_null(null)",
            row_data={},
        )
        assert result is True

    def test_invalid_formula_raises(self):
        """Malformed formula raises ValidationError."""
        engine = FormulaEngine()
        with pytest.raises(ValidationError):
            engine.evaluate(
                formula="upper(employee_name",
                row_data={"employee_name": "Alice"},
            )

    def test_unsupported_function_raises(self):
        """Unknown function raises ValidationError."""
        engine = FormulaEngine()
        with pytest.raises(ValidationError):
            engine.evaluate(
                formula="foobar(employee_name)",
                row_data={"employee_name": "Alice"},
            )
