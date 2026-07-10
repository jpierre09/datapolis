from django import forms

from apps.data_sources.models import DataSource
from apps.dashboard.dataset_columns import analyze_data_source_columns, build_recommended_column_choices
from apps.portfolio_projects.models import PortfolioProject
from apps.data_visualizations.models import ProjectVisualization


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = PortfolioProject
        fields = ["title", "question", "description", "project_type", "category", "status", "findings", "conclusion"]
        labels = {
            "title": "Da un nombre a tu proyecto",
            "question": "Pregunta de análisis",
            "description": "Pequeña descripción",
            "project_type": "Tipo de proyecto",
            "category": "Categoría",
            "status": "Estado del proyecto",
            "findings": "Hallazgos iniciales",
            "conclusion": "Conclusión inicial",
        }

        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ej. Evolución de ingresos por región"}),
            "question": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Ejemplo: ¿Cómo evolucionaron los ingresos por región durante 2026?",
                }
            ),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Resume el contexto del análisis en pocas líneas."}),
            "project_type": forms.Select(),
            "category": forms.Select(),
            "status": forms.Select(),
            "findings": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Anota patrones, cambios o puntos relevantes que ya identificaste.",
                }
            ),
            "conclusion": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Resume la idea principal que quieres comunicar con este proyecto.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["status"].initial = PortfolioProject.Status.DRAFT

        for field_name, field in self.fields.items():
            widget_class = "dashboard-input"
            if isinstance(field.widget, forms.Select):
                widget_class = "dashboard-input dashboard-select"
            elif isinstance(field.widget, forms.Textarea):
                widget_class = "dashboard-input dashboard-textarea"

            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} {widget_class}".strip()


class DataSourceUploadForm(forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ["name", "source_type", "file"]
        labels = {
            "name": "Nombre del dataset",
            "source_type": "Tipo de archivo",
            "file": "Archivo",
        }
        help_texts = {
            "name": "Usa un nombre claro para identificar el dataset dentro del proyecto.",
            "source_type": "Elige CSV o Excel según el archivo que vas a subir.",
            "file": "Sube un archivo .csv, .xlsx o .xls.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Ventas regionales 2026"}),
            "source_type": forms.Select(),
            "file": forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx,.xls"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            widget_class = "dashboard-input"
            if isinstance(field.widget, forms.Select):
                widget_class = "dashboard-input dashboard-select"

            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} {widget_class}".strip()


class DataSourceEditForm(forms.ModelForm):
    file = forms.FileField(
        label="Reemplazar archivo",
        required=False,
        help_text="Opcional. Sube un nuevo archivo .csv, .xlsx o .xls para reemplazar la fuente de datos actual. Al hacerlo, se actualizará automáticamente la metadata.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx,.xls"}),
    )

    class Meta:
        model = DataSource
        fields = ["name", "source_type", "is_active", "file"]
        labels = {
            "name": "Nombre del dataset",
            "source_type": "Tipo de archivo",
            "is_active": "Dataset Activo",
        }
        help_texts = {
            "name": "Usa un nombre claro para identificar el dataset dentro del proyecto.",
            "source_type": "Elige CSV o Excel según el tipo de archivo que vas a subir si vas a reemplazarlo.",
            "is_active": "Las fuentes de datos inactivas están ocultas y no disponibles para nuevas visualizaciones.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Ventas regionales 2026"}),
            "source_type": forms.Select(),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            widget_class = "dashboard-input"
            if isinstance(field.widget, forms.Select):
                widget_class = "dashboard-input dashboard-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                widget_class = ""  # Keep browser/dashboard default styles for checkbox

            existing_classes = field.widget.attrs.get("class", "")
            if widget_class:
                field.widget.attrs["class"] = f"{existing_classes} {widget_class}".strip()


class VisualizationCreateForm(forms.ModelForm):
    VISUALIZATION_TYPE_CHOICES = [
        (ProjectVisualization.VisualizationType.BAR_CHART, "Barras"),
        (ProjectVisualization.VisualizationType.LINE_CHART, "Línea"),
        (ProjectVisualization.VisualizationType.SCATTER_PLOT, "Dispersión"),
        (ProjectVisualization.VisualizationType.PIE_CHART, "Torta"),
        (ProjectVisualization.VisualizationType.DATA_TABLE, "Tabla"),
        (ProjectVisualization.VisualizationType.KPI_CARD, "KPI"),
    ]

    AGGREGATION_METHOD_CHOICES = [
        (ProjectVisualization.AggregationMethod.NONE, "Sin agregación"),
        (ProjectVisualization.AggregationMethod.SUM, "Suma"),
        (ProjectVisualization.AggregationMethod.AVERAGE, "Promedio"),
        (ProjectVisualization.AggregationMethod.COUNT, "Conteo"),
        (ProjectVisualization.AggregationMethod.MINIMUM, "Mínimo"),
        (ProjectVisualization.AggregationMethod.MAXIMUM, "Máximo"),
    ]

    visualization_type = forms.ChoiceField(
        label="Tipo de visualización",
        choices=VISUALIZATION_TYPE_CHOICES,
        help_text="Elige el tipo visual que mejor represente el dato.",
    )
    aggregation_method = forms.ChoiceField(
        label="Método de agregación",
        choices=AGGREGATION_METHOD_CHOICES,
        help_text="Selecciona cómo agrupar o resumir los datos.",
    )
    x_axis_column = forms.ChoiceField(
        label="Columna X",
        required=False,
        help_text="Solo se muestran columnas recomendadas para el eje X.",
    )
    y_axis_column = forms.ChoiceField(
        label="Columna Y",
        required=False,
        help_text="Solo se muestran columnas numéricas recomendadas para el eje Y.",
    )
    display_order = forms.IntegerField(
        label="Orden",
        min_value=0,
        help_text="Un número menor aparece antes en el proyecto público.",
        widget=forms.NumberInput(attrs={"min": 0}),
    )
    is_active = forms.BooleanField(
        label="Activa",
        required=False,
        help_text="Las visualizaciones activas aparecen en el portal público.",
    )

    class Meta:
        model = ProjectVisualization
        fields = [
            "title",
            "description",
            "visualization_type",
            "x_axis_column",
            "y_axis_column",
            "aggregation_method",
            "display_order",
            "is_active",
        ]
        labels = {
            "title": "Título",
            "description": "Descripción",
            "visualization_type": "Tipo de visualización",
            "x_axis_column": "Columna X",
            "y_axis_column": "Columna Y",
            "aggregation_method": "Método de agregación",
            "display_order": "Orden",
            "is_active": "Activa",
        }
        help_texts = {
            "title": "Usa un título claro para identificar la visualización.",
            "description": "Resume qué responde la visualización o qué muestra.",
            "visualization_type": "Elige el tipo visual que mejor represente el dato.",
            "x_axis_column": "Solo se muestran columnas recomendadas para el eje X.",
            "y_axis_column": "Solo se muestran columnas numéricas recomendadas para el eje Y.",
            "aggregation_method": "Selecciona cómo agrupar o resumir los datos.",
            "display_order": "Un número menor aparece antes en el proyecto público.",
            "is_active": "Las visualizaciones activas aparecen en el portal público.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ej. Ventas por región"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe la intención de esta visualización."}),
            "display_order": forms.NumberInput(attrs={"min": 0}),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        self.data_source = kwargs.pop("data_source", None)
        super().__init__(*args, **kwargs)

        if self.data_source is not None:
            column_analysis = analyze_data_source_columns(self.data_source)
            x_choices = build_recommended_column_choices(column_analysis["x_axis_columns"])
            y_choices = build_recommended_column_choices(column_analysis["y_axis_columns"])
        else:
            x_choices = []
            y_choices = []

        self.fields["x_axis_column"].choices = [("", "Selecciona una columna")] + x_choices
        self.fields["y_axis_column"].choices = [("", "Selecciona una columna")] + y_choices

        if not self.is_bound:
            self.fields["visualization_type"].initial = ProjectVisualization.VisualizationType.BAR_CHART
            self.fields["x_axis_column"].initial = x_choices[0][0] if x_choices else ""
            self.fields["y_axis_column"].initial = y_choices[0][0] if y_choices else ""
            self.fields["aggregation_method"].initial = (
                ProjectVisualization.AggregationMethod.SUM if y_choices else ProjectVisualization.AggregationMethod.COUNT
            )
            self.fields["is_active"].initial = True

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue

            widget_class = "dashboard-input"
            if isinstance(field.widget, forms.Select):
                widget_class = "dashboard-input dashboard-select"
            elif isinstance(field.widget, forms.Textarea):
                widget_class = "dashboard-input dashboard-textarea"

            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} {widget_class}".strip()
