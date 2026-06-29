import pandas as pd


def apply_aggregation(df, x_column, y_column, aggregation_method):
    if aggregation_method == "none":
        rows = df[[x_column, y_column]].dropna(subset=[x_column])
        return [{"x": _to_native(x), "y": _to_native(y)} for x, y in rows.itertuples(index=False, name=None)]

    if aggregation_method == "count":
        grouped = df.groupby(x_column, dropna=False).size().reset_index(name="y")
        return [{"x": _to_native(x), "y": int(y)} for x, y in grouped.itertuples(index=False, name=None)]

    aggregation_map = {
        "sum": "sum",
        "average": "mean",
        "minimum": "min",
        "maximum": "max",
    }

    if aggregation_method not in aggregation_map:
        raise ValueError(f"Unsupported aggregation_method: {aggregation_method}")

    grouped = (
        df.groupby(x_column, dropna=False)[y_column]
        .agg(aggregation_map[aggregation_method])
        .reset_index(name="y")
    )
    return [{"x": _to_native(x), "y": _to_native(y)} for x, y in grouped.itertuples(index=False, name=None)]


def _to_native(value):
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value
