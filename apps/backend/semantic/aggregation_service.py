import logging

from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.errors import NotFoundError, ValidationError
from connection.database_adapter import get_adapter
from connection.repository import ConnectionRepository
from connection.secret_store import AesGcmSecretStore, decrypt_secret_value
from dataset.repository import DatasetRepository
from semantic.domain import SemanticMapping

logger = logging.getLogger(__name__)

ALLOWED_AGGREGATIONS = {"count", "sum", "avg", "min", "max", "count_distinct"}


class MetricSpec(BaseModel):
    property: str
    type: str


class AggregationRequest(BaseModel):
    object_type_id: str
    dimension: str
    metric: MetricSpec
    filter_expression: dict | None = None


class AggregationBucket(BaseModel):
    dimension_value: str
    metric_value: float


class AggregationResponse(BaseModel):
    object_type: str
    results: list[AggregationBucket]
    truncated: bool


class AggregationService:
    def __init__(self, db: Session):
        self._db = db
        self._dataset_repo = DatasetRepository(db)
        self._connection_repo = ConnectionRepository(db)

    async def aggregate(self, req: AggregationRequest, mapping: SemanticMapping) -> AggregationResponse:
        # Validate dimension property
        dimension_pm = next((p for p in mapping.properties if p.property_name == req.dimension), None)
        if not dimension_pm:
            raise ValidationError(f"Dimension property '{req.dimension}' not found in mapping.")
        if not dimension_pm.included:
            raise ValidationError(f"Dimension property '{req.dimension}' is not included in mapping.")

        # Validate metric property
        metric_pm = next((p for p in mapping.properties if p.property_name == req.metric.property), None)
        if not metric_pm:
            raise ValidationError(f"Metric property '{req.metric.property}' not found in mapping.")
        if not metric_pm.included:
            raise ValidationError(f"Metric property '{req.metric.property}' is not included in mapping.")

        # Validate aggregation type
        if req.metric.type not in ALLOWED_AGGREGATIONS:
            raise ValidationError(f"Unsupported aggregation type '{req.metric.type}'.")

        # Rejects non-numeric properties for sum/avg/min/max
        if req.metric.type in ("sum", "avg", "min", "max"):
            if metric_pm.semantic_type not in ("integer", "number"):
                raise ValidationError(
                    f"Numeric aggregation '{req.metric.type}' requires numeric metric "
                    f"property, but got '{metric_pm.semantic_type}'."
                )

        # Retrieve dataset and connection
        dataset = self._dataset_repo.get(mapping.dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset '{mapping.dataset_id}' not found.")

        if not dataset.connection_id:
            raise ValidationError("Dataset must be DB-backed for aggregation.")

        connection = self._connection_repo.get(dataset.connection_id)
        if not connection:
            raise NotFoundError(f"Connection '{dataset.connection_id}' not found.")

        if connection.source_type not in ("postgresql", "mysql"):
            raise ValidationError(f"Aggregation is not supported for source type '{connection.source_type}'.")

        # Get database config and decrypt password
        config = dict(connection.config_json or {})
        password = config.get("password")
        if password and isinstance(password, str):
            config["password"] = decrypt_secret_value(
                password,
                AesGcmSecretStore(),
                allow_legacy_plaintext=True,
            )

        adapter = get_adapter(connection.source_type)

        # Helper to quote identifiers based on source type
        def q(ident: str) -> str:
            if connection.source_type == "mysql":
                return f"`{ident}`"
            return f'"{ident}"'

        table_quoted = q(dataset.source_object_name)
        dim_col = q(dimension_pm.source_column)
        metric_col = q(metric_pm.source_column)

        if req.metric.type == "count":
            agg_fn = f"COUNT({metric_col})"
        elif req.metric.type == "count_distinct":
            agg_fn = f"COUNT(DISTINCT {metric_col})"
        elif req.metric.type == "sum":
            agg_fn = f"SUM({metric_col})"
        elif req.metric.type == "avg":
            agg_fn = f"AVG({metric_col})"
        elif req.metric.type == "min":
            agg_fn = f"MIN({metric_col})"
        elif req.metric.type == "max":
            agg_fn = f"MAX({metric_col})"

        query = f"""
            SELECT {dim_col} AS dimension_value,
                   {agg_fn} AS metric_value
            FROM {table_quoted}
            GROUP BY {dim_col}
            ORDER BY metric_value DESC
            LIMIT 51
        """

        rows = await adapter.execute_query(config, query)

        results = []
        for row in rows:
            dim_val = row.get("dimension_value")
            dimension_value = str(dim_val) if dim_val is not None else ""
            metric_value = float(row.get("metric_value") or 0.0)
            results.append(AggregationBucket(dimension_value=dimension_value, metric_value=metric_value))

        if len(results) > 50:
            top_50_dims = [b.dimension_value for b in results[:50]]
            placeholders = ", ".join(["%s"] * len(top_50_dims))
            other_query = f"""
                SELECT {agg_fn} AS metric_value
                FROM {table_quoted}
                WHERE {dim_col} NOT IN ({placeholders})
            """
            other_rows = await adapter.execute_query(config, other_query, tuple(top_50_dims))
            other_val = 0.0
            if other_rows and other_rows[0].get("metric_value") is not None:
                other_val = float(other_rows[0].get("metric_value"))

            final_results = results[:50]
            final_results.append(AggregationBucket(dimension_value="Other", metric_value=other_val))
            return AggregationResponse(
                object_type=mapping.object_type_key,
                results=final_results,
                truncated=True,
            )

        return AggregationResponse(
            object_type=mapping.object_type_key,
            results=results,
            truncated=False,
        )
