from __future__ import annotations

from typing import Any


def build_google_sheets_export_url(url):
    import re
    if not url:
        raise ValueError("URL de Google Sheets no proporcionada.")
    match = re.search(r'(https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9-_]+)', url)
    if not match:
        raise ValueError("URL de Google Sheets inválida.")

    base_url = match.group(1)
    gid_match = re.search(r'[#&]gid=([0-9]+)', url)
    gid_part = f"&gid={gid_match.group(1)}" if gid_match else ""
    return f"{base_url}/export?format=csv{gid_part}"


def extract_metadata(data_source):
    import pandas as pd

    if data_source.source_type == "csv":
        dataframe = pd.read_csv(data_source.file.path)
    elif data_source.source_type == "excel":
        dataframe = pd.read_excel(data_source.file.path, engine="openpyxl")
    elif data_source.source_type == "google_sheets":
        export_url = build_google_sheets_export_url(data_source.source_url)
        dataframe = pd.read_csv(export_url)
    else:
        raise ValueError(f"Unsupported source_type: {data_source.source_type}")

    row_count = int(len(dataframe))
    columns = []

    for column_name in dataframe.columns:
        series = dataframe[column_name]
        non_null = series.dropna()
        null_count = int(series.isna().sum())
        column_type = _infer_semantic_type(non_null)

        item: dict[str, Any] = {
            "name": str(column_name),
            "type": column_type,
            "original_dtype": str(series.dtype),
            "nullable": bool(null_count > 0),
            "null_count": null_count,
        }

        if column_type in {"categorical", "text"}:
            unique_values = non_null.drop_duplicates()
            item["unique_count"] = int(unique_values.shape[0])
            item["sample_values"] = [_to_json_value(value) for value in unique_values.head(5).tolist()]

        if column_type == "numeric":
            numeric_values = pd.to_numeric(series, errors="coerce").dropna()
            if not numeric_values.empty:
                item["min"] = _to_json_value(numeric_values.min())
                item["max"] = _to_json_value(numeric_values.max())

        columns.append(item)

    return {
        "schema_version": 1,
        "row_count": row_count,
        "columns": columns,
    }


def _infer_semantic_type(non_null_series):
    import pandas as pd
    from pandas.api.types import (
        is_bool_dtype,
        is_datetime64_any_dtype,
        is_numeric_dtype,
    )

    if non_null_series.empty:
        return "unknown"

    if is_bool_dtype(non_null_series):
        return "boolean"

    if is_numeric_dtype(non_null_series):
        return "numeric"

    if is_datetime64_any_dtype(non_null_series):
        return "datetime"

    lowered = {str(value).strip().lower() for value in non_null_series.head(100)}
    boolean_tokens = {"true", "false", "1", "0", "yes", "no", "y", "n", "t", "f"}
    if lowered and lowered.issubset(boolean_tokens):
        return "boolean"

    datetime_probe = pd.to_datetime(non_null_series.head(100), errors="coerce")
    if not datetime_probe.empty and datetime_probe.notna().mean() >= 0.8:
        return "datetime"

    non_null_count = int(non_null_series.shape[0])
    unique_count = int(non_null_series.nunique())
    avg_len = float(non_null_series.astype(str).str.len().mean())

    if unique_count <= 50 and (unique_count / non_null_count) <= 0.5 and avg_len <= 80:
        return "categorical"

    return "text"


def _to_json_value(value):
    if hasattr(value, "item"):
        value = value.item()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value
