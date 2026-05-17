import json
from pathlib import Path


def read_dataset_preview(
    storage_path: str,
    page: int = 1,
    page_size: int = 100,
    search: str | None = None,
) -> dict:
    path = Path(storage_path)
    if not path.exists():
        return {
            "columns": [],
            "rows": [],
            "total_row_count": 0,
            "filtered_row_count": 0,
            "page": page,
            "page_size": page_size,
        }

    columns: list[str] = []
    rows: list[list] = []
    total_row_count = 0
    filtered_row_count = 0
    lower_search = search.lower().strip() if search else ""

    skip = (page - 1) * page_size

    with open(str(path), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue

            if not columns:
                columns = list(row.keys())

            total_row_count += 1

            if lower_search:
                row_values = [str(r).lower() if r is not None else "" for r in row.values()]
                if not any(lower_search in v for v in row_values):
                    continue

            filtered_row_count += 1

            if filtered_row_count <= skip:
                continue

            if len(rows) < page_size:
                rows.append([row.get(c) for c in columns])

    return {
        "columns": columns,
        "rows": rows,
        "total_row_count": total_row_count,
        "filtered_row_count": filtered_row_count if lower_search else total_row_count,
        "page": page,
        "page_size": page_size,
    }
