COLUMN_TYPE_LABELS = {
    "numeric": "numérica",
    "categorical": "categórica",
    "datetime": "fecha",
    "text": "texto",
}


def is_recommendable_column(column, row_count):
    column_name = str(column.get("name", "")).strip()
    if not column_name:
        return False

    if column_name.startswith("Unnamed"):
        return False

    if column_name in {"Delete", "ID2"}:
        return False

    null_count = column.get("null_count")
    if row_count is not None and null_count is not None and null_count == row_count:
        return False

    column_type = str(column.get("type", "unknown")).strip().lower()
    sample_values = column.get("sample_values") if isinstance(column.get("sample_values"), list) else []
    unique_count = column.get("unique_count")
    has_useful_values = bool(sample_values) or unique_count not in (None, 0)

    if column_type == "unknown" and not has_useful_values:
        return False

    return True


def analyze_data_source_columns(data_source):
    columns_schema = data_source.columns_schema if isinstance(data_source.columns_schema, dict) else {}
    raw_columns = columns_schema.get("columns") if isinstance(columns_schema.get("columns"), list) else []
    row_count = data_source.row_count if isinstance(data_source.row_count, int) else None

    columns = []
    summary = {
        "total_columns": 0,
        "numeric_columns": 0,
        "categorical_columns": 0,
        "datetime_columns": 0,
        "nullable_columns": 0,
    }
    x_axis_columns = []
    y_axis_columns = []

    for raw_column in raw_columns:
        if not isinstance(raw_column, dict):
            continue

        column_type = str(raw_column.get("type", "unknown")).strip().lower()
        column_name = raw_column.get("name") or "Sin nombre"
        nullable = bool(raw_column.get("nullable"))
        null_count = raw_column.get("null_count")

        column = {
            "name": column_name,
            "type": column_type,
            "original_dtype": raw_column.get("original_dtype", "Desconocido"),
            "nullable": nullable,
            "null_count": null_count if null_count is not None else 0,
            "unique_count": raw_column.get("unique_count"),
            "min": raw_column.get("min"),
            "max": raw_column.get("max"),
            "sample_values": raw_column.get("sample_values") if isinstance(raw_column.get("sample_values"), list) else [],
        }
        columns.append(column)

        summary["total_columns"] += 1
        if column["type"] == "numeric":
            summary["numeric_columns"] += 1
        if column["type"] == "categorical":
            summary["categorical_columns"] += 1
        if column["type"] == "datetime":
            summary["datetime_columns"] += 1
        if nullable or (isinstance(null_count, int) and null_count > 0):
            summary["nullable_columns"] += 1

        if not is_recommendable_column(column, row_count):
            continue

        if column["type"] == "numeric":
            y_axis_columns.append(column)
        if column["type"] in {"categorical", "datetime", "text"}:
            x_axis_columns.append(column)

    return {
        "columns_schema": columns_schema,
        "columns": columns,
        "summary": summary,
        "x_axis_columns": x_axis_columns,
        "y_axis_columns": y_axis_columns,
    }


def build_recommended_column_choices(columns):
    return [
        (column["name"], f'{column["name"]} ({COLUMN_TYPE_LABELS.get(column["type"], column["type"])})')
        for column in columns
    ]
