from .aggregators import apply_aggregation
from .exceptions import VisualizationEngineError
from .readers import read_source_dataset
from .serializers import build_payload

SUPPORTED_VISUALIZATION_TYPES = {"bar_chart", "line_chart", "scatter_plot"}


def build_visualization_payload(project_visualization):
    if project_visualization.visualization_type not in SUPPORTED_VISUALIZATION_TYPES:
        raise VisualizationEngineError(
            "Unsupported visualization_type: "
            f"{project_visualization.visualization_type}. "
            "Supported types: bar_chart, line_chart, scatter_plot."
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

    if not x_column:
        raise VisualizationEngineError("x_axis_column is required.")

    if x_column not in dataframe.columns:
        raise VisualizationEngineError(f"x_axis_column '{x_column}' does not exist in source dataset.")

    y_required = aggregation_method != "count"
    if y_required:
        if not y_column:
            raise VisualizationEngineError("y_axis_column is required for this aggregation method.")
        if y_column not in dataframe.columns:
            raise VisualizationEngineError(
                f"y_axis_column '{y_column}' does not exist in source dataset."
            )

    try:
        data = apply_aggregation(dataframe, x_column, y_column, aggregation_method)
    except Exception as exc:
        raise VisualizationEngineError(f"Failed to aggregate visualization data: {exc}") from exc

    if data is None:
        data = []
    elif not isinstance(data, list):
        raise VisualizationEngineError("Visualization data contract error: data must be a list.")

    return build_payload(project_visualization, data)
