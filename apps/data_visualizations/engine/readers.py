import pandas as pd


def read_source_dataset(source_dataset):
    if source_dataset.source_type == "csv":
        return pd.read_csv(source_dataset.file.path)

    if source_dataset.source_type == "excel":
        return pd.read_excel(source_dataset.file.path, engine="openpyxl")

    raise ValueError(f"Unsupported source_type: {source_dataset.source_type}")
