"""Unit tests for MonthlyAggregationService — compute method, properties, and convenience wrapper."""

from unittest.mock import MagicMock

import pytest

from analytics.domain import DashboardSummaryCache
from analytics.services.monthly_aggregation_service import (
    AggregationInput,
    AggregationResult,
    MonthlyAggregationService,
)

pytestmark = pytest.mark.unit


class TestMonthlyAggregationService:
    def test_compute_method_wrapper(self):
        """lines 70-78: compute() accepts AggregationInput and returns AggregationResult."""
        mock_db = MagicMock()
        service = MonthlyAggregationService(mock_db)
        service._run_pipeline = MagicMock(
            return_value=DashboardSummaryCache(
                snapshot_id="snap-1",
                year=2026,
                month=5,
                total_payroll=50000.0,
                total_claims=5000.0,
                department_count=3,
                anomaly_count=1,
                created_at="2026-05-15T10:00:00Z",
            )
        )

        input_data = AggregationInput(
            snapshot_id="snap-1",
            current_month="2026-05",
            previous_month="2026-04",
            anomaly_count=1,
        )
        result = service.compute(input_data)

        assert isinstance(result, AggregationResult)
        assert result.summary.snapshot_id == "snap-1"
        assert result.summary.total_payroll == 50000.0

    def test_spend_repo_property(self):
        """line 96-97: spend_repo property returns the repository."""
        mock_db = MagicMock()
        service = MonthlyAggregationService(mock_db)
        repo = service.spend_repo
        assert repo is not None

    def test_cache_repo_property(self):
        """line 100-101: cache_repo property returns the repository."""
        mock_db = MagicMock()
        service = MonthlyAggregationService(mock_db)
        repo = service.cache_repo
        assert repo is not None

    def test_compute_monthly_spends_delegates_to_pipeline(self):
        """lines 54-68: compute_monthly_spends delegates to _run_pipeline."""
        mock_db = MagicMock()
        service = MonthlyAggregationService(mock_db)
        service._run_pipeline = MagicMock(
            return_value=DashboardSummaryCache(
                snapshot_id="snap-1",
                year=2026,
                month=5,
                total_payroll=0.0,
                total_claims=0.0,
                department_count=0,
                anomaly_count=0,
            )
        )

        result = service.compute_monthly_spends(
            snapshot_id="snap-1",
            current_month="2026-05",
            previous_month="2026-04",
        )
        assert result.snapshot_id == "snap-1"
