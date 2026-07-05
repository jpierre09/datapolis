from django import forms

from apps.data_sources.models import DataSource
from apps.portfolio_projects.models import PortfolioProject


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = PortfolioProject
        fields = ["title", "question", "description", "project_type", "category", "status", "findings", "conclusion"]
        labels = {
            "title": "Título del proyecto",
            "question": "Pregunta de análisis",
            "description": "Descripción corta",
            "project_type": "Tipo de proyecto",
            "category": "Categoría",
            "status": "Estado del proyecto",
            "findings": "Hallazgos iniciales",
            "conclusion": "Conclusión inicial",
        }
        help_texts = {
            "title": "Usa un nombre claro y fácil de reconocer.",
            "question": "Ejemplo: ¿Cómo evolucionaron los ingresos por región durante 2026?",
            "description": "Resume el contexto del análisis en pocas líneas.",
            "findings": "Anota patrones, cambios o puntos relevantes que ya identificaste.",
            "conclusion": "Resume la idea principal que quieres comunicar con este proyecto.",
            "status": "Puedes cambiarlo cuando el proyecto avance.",
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
