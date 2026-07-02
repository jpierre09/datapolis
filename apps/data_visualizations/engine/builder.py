from .aggregators import apply_aggregation
from .exceptions import VisualizationEngineError
from .readers import read_source_dataset
from .serializers import build_payload

SUPPORTED_VISUALIZATION_TYPES = {
    "bar_chart",
    "line_chart",
    "scatter_plot",
    "pie_chart",
    "data_table",
    "kpi_card",
}
KPI_SUPPORTED_AGGREGATIONS = {"sum", "average", "count", "minimum", "maximum"}


def build_visualization_payload(project_visualization):
    visualization_type = project_visualization.visualization_type

    if visualization_type not in SUPPORTED_VISUALIZATION_TYPES:
        raise VisualizationEngineError(
            "Unsupported visualization_type: "
            f"{visualization_type}. "
            "Supported types: bar_chart, line_chart, scatter_plot, pie_chart, data_table, kpi_card."
        )

    source_dataset = project_visualization.source_dataset
    if source_dataset is None:
        raise VisualizationEngineError("Visualization has no source_dataset configured.")

    if source_dataset.processing_status != "processed":
        raise VisualizationEngineError(
            "Source dataset must be processed before building a visualization payload."
        )

    try:
        dataframe = read_source_dataset(source_dataset)
    except Exception as exc:
        raise VisualizationEngineError(f"Failed to read source dataset: {exc}") from exc

    x_column = project_visualization.x_axis_column
    y_column = project_visualization.y_axis_column
    aggregation_method = project_visualization.aggregation_method

    if not x_column and visualization_type != "kpi_card":
        raise VisualizationEngineError("x_axis_column is required.")

    if x_column and x_column not in dataframe.columns:
        raise VisualizationEngineError(f"x_axis_column '{x_column}' does not exist in source dataset.")

    y_required = _is_y_required(visualization_type, aggregation_method)
    if y_required:
        if not y_column:
            raise VisualizationEngineError("y_axis_column is required for this aggregation method.")
        if y_column not in dataframe.columns:
            raise VisualizationEngineError(
                f"y_axis_column '{y_column}' does not exist in source dataset."
            )
    elif y_column and y_column not in dataframe.columns:
        raise VisualizationEngineError(
            f"y_axis_column '{y_column}' does not exist in source dataset."
        )

    if visualization_type == "kpi_card" and not x_column and aggregation_method not in KPI_SUPPORTED_AGGREGATIONS:
        raise VisualizationEngineError(
            "kpi_card without x_axis_column supports only aggregation methods: "
            "sum, average, count, minimum, maximum."
        )

    try:
        if visualization_type == "kpi_card" and not x_column:
            data = _build_global_kpi_data(dataframe, y_column, aggregation_method)
        else:
            data = apply_aggregation(dataframe, x_column, y_column, aggregation_method)
    except Exception as exc:
        raise VisualizationEngineError(f"Failed to aggregate visualization data: {exc}") from exc

    if data is None:
        data = []
    elif not isinstance(data, list):
        raise VisualizationEngineError("Visualization data contract error: data must be a list.")

    return build_payload(project_visualization, data)


def _is_y_required(visualization_type, aggregation_method):
    if visualization_type == "kpi_card":
        return aggregation_method in {"sum", "average", "minimum", "maximum", "none"}

    return aggregation_method != "count"


def _build_global_kpi_data(dataframe, y_column, aggregation_method):
    if aggregation_method == "count":
        if y_column:
            value = int(dataframe[y_column].count())
        else:
            value = int(len(dataframe))
        return [{"x": "value", "y": value}]

    series = dataframe[y_column]

    if aggregation_method == "sum":
        value = series.sum()
    elif aggregation_method == "average":
        value = series.mean()
    elif aggregation_method == "minimum":
        value = series.min()
    elif aggregation_method == "maximum":
        value = series.max()
    else:
        raise VisualizationEngineError(
            f"Unsupported aggregation_method for global kpi_card: {aggregation_method}"
        )

    if value is None:
        return []

    if hasattr(value, "item"):
        value = value.item()
    if hasattr(value, "isoformat"):
        value = value.isoformat()

    return [{"x": "value", "y": value}]
