def build_payload(project_visualization, data):
    normalized_data = data if isinstance(data, list) else []

    return {
        "schema_version": 1,
        "visualization": {
            "id": project_visualization.id,
            "title": project_visualization.title,
            "description": project_visualization.description,
            "type": project_visualization.visualization_type,
            "display_order": project_visualization.display_order,
            "is_active": project_visualization.is_active,
        },
        "source": {
            "id": project_visualization.source_dataset.id,
            "name": project_visualization.source_dataset.name,
            "source_type": project_visualization.source_dataset.source_type,
        },
        "encoding": {
            "x": project_visualization.x_axis_column,
            "y": project_visualization.y_axis_column,
            "aggregation": project_visualization.aggregation_method,
        },
        "data": normalized_data,
    }
