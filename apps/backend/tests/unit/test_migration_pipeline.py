import pytest

from tenant_data.migration_pipeline import (
    MigrationPipeline,
    is_rollback_supported,
    is_upgrade_supported,
)


class TestMigrationPipelineCompatibility:
    def test_same_version_is_compatible(self):
        pipeline = MigrationPipeline()
        assert pipeline.check_compatibility(1, 1) is True
        assert pipeline.check_compatibility(5, 5) is True

    def test_newer_version_is_compatible(self):
        pipeline = MigrationPipeline()
        assert pipeline.check_compatibility(1, 2) is True
        assert pipeline.check_compatibility(1, 10) is True

    def test_older_version_is_not_compatible(self):
        pipeline = MigrationPipeline()
        assert pipeline.check_compatibility(2, 1) is False
        assert pipeline.check_compatibility(10, 1) is False

    def test_version_zero_to_current_is_compatible(self):
        pipeline = MigrationPipeline()
        assert pipeline.check_compatibility(0, 1) is True


class TestMigrationPipelineVersionTracking:
    def test_get_current_schema_version(self):
        pipeline = MigrationPipeline()
        assert pipeline.get_current_schema_version() == 1

    def test_verify_rollout_no_engines_returns_true(self):
        pipeline = MigrationPipeline()
        assert pipeline.verify_rollout() is True

    def test_verify_rollout_with_engine_getter(self):
        pipeline = MigrationPipeline(
            tenant_engine_getter=lambda: []
        )
        assert pipeline.verify_rollout() is True


class TestMigrationPipelineRun:
    def test_run_migration_without_alembic_is_noop(self):
        pipeline = MigrationPipeline()
        pipeline.run_migration()

    def test_run_migration_calls_alembic(self):
        calls = []
        def fake_upgrade(target):
            calls.append(target)

        pipeline = MigrationPipeline(alembic_upgrade=fake_upgrade)
        pipeline.run_migration("head")
        assert calls == ["head"]

    def test_run_migration_with_none_target(self):
        calls = []
        def fake_upgrade(target):
            calls.append(target)

        pipeline = MigrationPipeline(alembic_upgrade=fake_upgrade)
        pipeline.run_migration(None)
        assert calls == [None]


class TestMigrationUtilityFunctions:
    def test_is_upgrade_supported(self):
        assert is_upgrade_supported(1, 1) is True
        assert is_upgrade_supported(1, 2) is True
        assert is_upgrade_supported(2, 1) is False

    def test_is_rollback_supported(self):
        assert is_rollback_supported(2, 2) is True
        assert is_rollback_supported(2, 1) is True
        assert is_rollback_supported(1, 2) is False


class TestMigrationPipelineExpandContract:
    def test_expand_phase_is_noop(self):
        pipeline = MigrationPipeline()
        pipeline.expand_phase()

    def test_contract_phase_is_noop(self):
        pipeline = MigrationPipeline()
        pipeline.contract_phase()

