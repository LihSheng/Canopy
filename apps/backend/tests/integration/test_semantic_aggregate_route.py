from unittest.mock import AsyncMock, MagicMock

import pytest

from common.errors import ValidationError
from semantic.aggregation_service import AggregationBucket, AggregationResponse

# Import fixtures from test_semantic_api

pytestmark = pytest.mark.api_schema


@pytest.fixture
def mock_aggregation_service(monkeypatch):
    mock_service = MagicMock()
    mock_service.aggregate = AsyncMock()
    monkeypatch.setattr("api.routes.semantic.AggregationService", lambda db: mock_service)
    return mock_service


class TestSemanticAggregateRoute:
    def test_aggregate_route_not_found(self, client, auth_headers):
        """Should return 404 if the object type does not exist."""
        response = client.post(
            "/api/semantic/object-types/nonexistent-id/aggregate",
            json={
                "object_type_id": "nonexistent-id",
                "dimension": "dept",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_aggregate_route_tenant_isolation(self, client, auth_headers_tenant2, seed_object_type):
        """Tenant 2 should not be able to aggregate Tenant 1's object type (should return 404)."""
        response = client.post(
            f"/api/semantic/object-types/{seed_object_type.id}/aggregate",
            json={
                "object_type_id": seed_object_type.id,
                "dimension": "dept",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers_tenant2,
        )
        assert response.status_code == 404

    def test_aggregate_route_happy_path(
        self, client, auth_headers, seed_object_type, db_session, mock_aggregation_service
    ):
        """Should successfully return aggregation results."""
        # Setup a dummy semantic mapping in the DB so it is found
        import uuid

        from semantic.domain import PropertyMapping, SemanticMapping
        from semantic.repository import SemanticMappingRepository

        mapping = SemanticMapping(
            id=str(uuid.uuid4()),
            tenant_id="test-tenant-1",
            dataset_id="test-ds",
            dataset_version_id="test-version",
            version_number=1,
            object_type_id=seed_object_type.id,
            object_type_key=seed_object_type.object_type_key,
            properties=[
                PropertyMapping(source_column="dept", property_name="dept", included=True),
                PropertyMapping(source_column="salary", property_name="salary", semantic_type="number", included=True),
            ],
        )
        repo = SemanticMappingRepository(db_session)
        repo.save(mapping)

        # Configure mock response
        mock_response = AggregationResponse(
            object_type=seed_object_type.object_type_key,
            results=[
                AggregationBucket(dimension_value="HR", metric_value=50000.0),
                AggregationBucket(dimension_value="IT", metric_value=120000.0),
            ],
            truncated=False,
        )
        mock_aggregation_service.aggregate.return_value = mock_response

        response = client.post(
            f"/api/semantic/object-types/{seed_object_type.id}/aggregate",
            json={
                "object_type_id": seed_object_type.id,
                "dimension": "dept",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object_type"] == seed_object_type.object_type_key
        assert len(data["results"]) == 2
        assert data["results"][0]["dimension_value"] == "HR"
        assert data["results"][0]["metric_value"] == 50000.0
        assert data["truncated"] is False

    def test_aggregate_route_validation_error(
        self, client, auth_headers, seed_object_type, db_session, mock_aggregation_service
    ):
        """Should forward service ValidationErrors as 400 Bad Request."""
        import uuid

        from semantic.domain import PropertyMapping, SemanticMapping
        from semantic.repository import SemanticMappingRepository

        mapping = SemanticMapping(
            id=str(uuid.uuid4()),
            tenant_id="test-tenant-1",
            dataset_id="test-ds",
            dataset_version_id="test-version",
            version_number=1,
            object_type_id=seed_object_type.id,
            object_type_key=seed_object_type.object_type_key,
            properties=[
                PropertyMapping(source_column="dept", property_name="dept", included=True),
            ],
        )
        repo = SemanticMappingRepository(db_session)
        repo.save(mapping)

        mock_aggregation_service.aggregate.side_effect = ValidationError("Invalid property selected")

        response = client.post(
            f"/api/semantic/object-types/{seed_object_type.id}/aggregate",
            json={
                "object_type_id": seed_object_type.id,
                "dimension": "invalid_property",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid property selected" in response.json()["detail"]
