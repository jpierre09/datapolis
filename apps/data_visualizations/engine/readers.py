import pandas as pd

from apps.data_sources.services import build_google_sheets_export_url
from .exceptions import VisualizationEngineError


def read_source_dataset(source_dataset):
    try:
        if source_dataset.source_type == "csv":
            return pd.read_csv(source_dataset.file.path)

        if source_dataset.source_type == "excel":
            return pd.read_excel(source_dataset.file.path, engine="openpyxl")

        if source_dataset.source_type == "google_sheets":
            export_url = build_google_sheets_export_url(source_dataset.source_url)
            return pd.read_csv(export_url)

        raise ValueError(f"Unsupported source_type: {source_dataset.source_type}")
    except Exception as exc:
        raise VisualizationEngineError(f"No se pudo leer la fuente de datos: {exc}")
