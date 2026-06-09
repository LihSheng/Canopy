from unittest.mock import AsyncMock, MagicMock

import pytest

from common.errors import ValidationError
from connection.domain import Connection
from dataset.domain import Dataset
from semantic.aggregation_service import (
    AggregationBucket,
    AggregationRequest,
    AggregationService,
    MetricSpec,
)
from semantic.domain import PropertyMapping, SemanticMapping


class StubRepo:
    def __init__(self, obj):
        self._obj = obj

    def get(self, _id):
        return self._obj


@pytest.fixture
def mock_dataset():
    return Dataset(
        id="ds-1",
        connection_id="conn-1",
        name="Employees",
        source_object_name="employees_table",
    )


@pytest.fixture
def mock_connection():
    return Connection(
        id="conn-1",
        source_type="postgresql",
        name="Postgres DB",
        config_json={"host": "localhost", "database": "test_db"},
    )


@pytest.fixture
def mock_mapping():
    return SemanticMapping(
        id="map-1",
        tenant_id="tenant-1",
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        version_number=1,
        object_type_id="obj-1",
        object_type_key="employee",
        properties=[
            PropertyMapping(
                source_column="id",
                property_name="ID",
                semantic_type="integer",
                included=True,
                is_primary_key=True,
            ),
            PropertyMapping(
                source_column="dept_name",
                property_name="Department",
                semantic_type="string",
                included=True,
            ),
            PropertyMapping(
                source_column="salary",
                property_name="Salary",
                semantic_type="number",
                included=True,
            ),
            PropertyMapping(
                source_column="age",
                property_name="Age",
                semantic_type="integer",
                included=True,
            ),
            PropertyMapping(
                source_column="hidden_col",
                property_name="Hidden",
                semantic_type="string",
                included=False,
            ),
        ],
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validation_invalid_dimension(mock_dataset, mock_connection, mock_mapping):
    service = AggregationService(db=None)
    service._dataset_repo = StubRepo(mock_dataset)
    service._connection_repo = StubRepo(mock_connection)

    req = AggregationRequest(
        object_type_id="obj-1", dimension="NonExistent", metric=MetricSpec(property="ID", type="count")
    )

    with pytest.raises(ValidationError) as excinfo:
        await service.aggregate(req, mock_mapping)
    assert "Dimension property 'NonExistent' not found" in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validation_excluded_dimension(mock_dataset, mock_connection, mock_mapping):
    service = AggregationService(db=None)
    service._dataset_repo = StubRepo(mock_dataset)
    service._connection_repo = StubRepo(mock_connection)

    req = AggregationRequest(object_type_id="obj-1", dimension="Hidden", metric=MetricSpec(property="ID", type="count"))

    with pytest.raises(ValidationError) as excinfo:
        await service.aggregate(req, mock_mapping)
    assert "Dimension property 'Hidden' is not included" in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validation_invalid_metric_property(mock_dataset, mock_connection, mock_mapping):
    service = AggregationService(db=None)
    service._dataset_repo = StubRepo(mock_dataset)
    service._connection_repo = StubRepo(mock_connection)

    req = AggregationRequest(
        object_type_id="obj-1", dimension="Department", metric=MetricSpec(property="NonExistent", type="count")
    )

    with pytest.raises(ValidationError) as excinfo:
        await service.aggregate(req, mock_mapping)
    assert "Metric property 'NonExistent' not found" in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validation_invalid_aggregation_type(mock_dataset, mock_connection, mock_mapping):
    service = AggregationService(db=None)
    service._dataset_repo = StubRepo(mock_dataset)
    service._connection_repo = StubRepo(mock_connection)

    req = AggregationRequest(
        object_type_id="obj-1", dimension="Department", metric=MetricSpec(property="Salary", type="invalid_type")
    )

    with pytest.raises(ValidationError) as excinfo:
        await service.aggregate(req, mock_mapping)
    assert "Unsupported aggregation type" in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validation_non_numeric_for_numeric_agg(mock_dataset, mock_connection, mock_mapping):
    service = AggregationService(db=None)
    service._dataset_repo = StubRepo(mock_dataset)
    service._connection_repo = StubRepo(mock_connection)

    req = AggregationRequest(
        object_type_id="obj-1", dimension="Department", metric=MetricSpec(property="Department", type="sum")
    )

    with pytest.raises(ValidationError) as excinfo:
        await service.aggregate(req, mock_mapping)
    assert "Numeric aggregation 'sum' requires numeric metric property" in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aggregation_happy_path(mock_dataset, mock_connection, mock_mapping, monkeypatch):
    service = AggregationService(db=None)
    service._dataset_repo = StubRepo(mock_dataset)
    service._connection_repo = StubRepo(mock_connection)

    mock_adapter = MagicMock()
    mock_adapter.execute_query = AsyncMock(
        return_value=[
            {"dimension_value": "Engineering", "metric_value": 150000.0},
            {"dimension_value": "Sales", "metric_value": 120000.0},
        ]
    )
    monkeypatch.setattr("semantic.aggregation_service.get_adapter", lambda source_type: mock_adapter)

    req = AggregationRequest(
        object_type_id="obj-1", dimension="Department", metric=MetricSpec(property="Salary", type="sum")
    )

    res = await service.aggregate(req, mock_mapping)

    assert res.object_type == "employee"
    assert len(res.results) == 2
    assert res.results[0] == AggregationBucket(dimension_value="Engineering", metric_value=150000.0)
    assert res.results[1] == AggregationBucket(dimension_value="Sales", metric_value=120000.0)
    assert not res.truncated

    # Verify SQL generation
    called_sql = mock_adapter.execute_query.call_args[0][1]
    assert 'GROUP BY "dept_name"' in called_sql
    assert 'SUM("salary")' in called_sql
    assert 'FROM "employees_table"' in called_sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aggregation_capping_and_other(mock_dataset, mock_connection, mock_mapping, monkeypatch):
    service = AggregationService(db=None)
    service._dataset_repo = StubRepo(mock_dataset)
    service._connection_repo = StubRepo(mock_connection)

    # Simulate returning 51 rows from the database
    db_rows = [{"dimension_value": f"Dept {i}", "metric_value": 10.0} for i in range(51)]

    mock_adapter = MagicMock()

    # First query returns the 51 rows. Second query returns the aggregate of remaining.
    mock_adapter.execute_query = AsyncMock()
    mock_adapter.execute_query.side_effect = [db_rows, [{"metric_value": 100.0}]]
    monkeypatch.setattr("semantic.aggregation_service.get_adapter", lambda source_type: mock_adapter)

    req = AggregationRequest(
        object_type_id="obj-1", dimension="Department", metric=MetricSpec(property="Salary", type="sum")
    )

    res = await service.aggregate(req, mock_mapping)

    assert res.object_type == "employee"
    assert len(res.results) == 51  # 50 top buckets + 1 "Other" bucket
    assert res.results[-1] == AggregationBucket(dimension_value="Other", metric_value=100.0)
    assert res.truncated

    assert mock_adapter.execute_query.call_count == 2

    # Verify second query exclusion params
    second_call_args = mock_adapter.execute_query.call_args_list[1][0]
    second_sql = second_call_args[1]
    params = second_call_args[2]
    assert "NOT IN" in second_sql
    assert len(params) == 50
