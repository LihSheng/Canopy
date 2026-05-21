import pytest

pytestmark = pytest.mark.business_rule

from anomalies.severity import ANOMALY_THRESHOLDS, classify_severity


class TestClassifySeverity:
    def test_high_above_threshold(self):
        assert classify_severity(20.0) == "high"
        assert classify_severity(15.0) == "high"
        assert classify_severity(-20.0) == "high"
        assert classify_severity(-15.0) == "high"

    def test_medium_between_thresholds(self):
        assert classify_severity(10.0) == "medium"
        assert classify_severity(7.5) == "medium"
        assert classify_severity(-10.0) == "medium"
        assert classify_severity(-7.5) == "medium"

    def test_low_below_threshold(self):
        assert classify_severity(5.0) == "low"
        assert classify_severity(0.0) == "low"
        assert classify_severity(-5.0) == "low"

    def test_custom_thresholds(self):
        custom = {"high_threshold_pct": 30.0, "medium_threshold_pct": 15.0}
        assert classify_severity(25.0, custom) == "medium"
        assert classify_severity(35.0, custom) == "high"
        assert classify_severity(10.0, custom) == "low"

    def test_default_thresholds(self):
        assert ANOMALY_THRESHOLDS["high_threshold_pct"] == 15.0
        assert ANOMALY_THRESHOLDS["medium_threshold_pct"] == 7.5


class TestDetectedAnomalyModel:
    """Cover unpack_drivers exception handling (lines 60-61)."""

    def test_pack_unpack_drivers_roundtrip(self):
        from anomalies.schema import DetectedAnomalyModel

        drivers = ["High claims dept-1 (+150%)", "3 claims in current month"]
        packed = DetectedAnomalyModel.pack_drivers(drivers)
        unpacked = DetectedAnomalyModel.unpack_drivers(packed)
        assert unpacked == drivers

    def test_unpack_drivers_invalid_json(self):
        """line 60: JSONDecodeError returns empty list."""
        from anomalies.schema import DetectedAnomalyModel

        result = DetectedAnomalyModel.unpack_drivers("not-json")
        assert result == []

    def test_unpack_drivers_type_error(self):
        """line 60-61: TypeError returns empty list."""
        from anomalies.schema import DetectedAnomalyModel

        result = DetectedAnomalyModel.unpack_drivers(None)
        assert result == []

    def test_unpack_drivers_empty_default(self):
        from anomalies.schema import DetectedAnomalyModel

        result = DetectedAnomalyModel.unpack_drivers("[]")
        assert result == []
