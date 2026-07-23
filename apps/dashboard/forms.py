import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from apps.data_sources.models import DataSource
from apps.dashboard.dataset_columns import analyze_data_source_columns, build_recommended_column_choices
from apps.dashboard.models import PublicProfile
from apps.portfolio_projects.models import PortfolioProject
from apps.data_visualizations.models import ProjectVisualization


PROFILE_EXTERNAL_LINK_SLOTS = 4


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = PortfolioProject
        fields = ["title", "question", "description", "cover_image", "project_type", "category", "findings", "conclusion"]
        labels = {
            "title": "Da un nombre a tu proyecto",
            "question": "Pregunta de análisis",
            "description": "Pequeña descripción",
            "cover_image": "Imagen de referencia",
            "project_type": "Tipo de proyecto",
            "category": "Categoría",
            "findings": "Hallazgos iniciales",
            "conclusion": "Conclusión inicial",
        }
        help_texts = {
            "cover_image": "Opcional. Se muestra debajo de la pregunta de análisis en la vista pública del proyecto.",
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
            "cover_image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "project_type": forms.Select(),
            "category": forms.Select(),
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
        fields = ["name", "source_type", "source_url", "file"]
        labels = {
            "name": "Nombre del dataset",
            "source_type": "Origen de datos",
            "source_url": "URL de Google Sheets",
            "file": "Archivo",
        }
        help_texts = {
            "name": "Usa un nombre claro para identificar el dataset dentro del proyecto.",
            "source_type": "Elige CSV, Excel o Google Sheets.",
            "source_url": "URL pública del documento de Google Sheets (Requiere origen 'Google Sheets').",
            "file": "Sube un archivo .csv, .xlsx o .xls. (No requerido para Google Sheets).",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Ventas regionales 2026"}),
            "source_type": forms.Select(),
            "source_url": forms.URLInput(attrs={"placeholder": "https://docs.google.com/spreadsheets/d/..."}),
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

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get("source_type")
        source_url = cleaned_data.get("source_url")
        file = cleaned_data.get("file")

        form_errors = False
        if source_type == DataSource.SourceType.GOOGLE_SHEETS:
            if not source_url:
                self.add_error("source_url", "Debes ingresar una URL de Google Sheets.")
                form_errors = True
        else:
            if not file and not self.instance.file:
                self.add_error("file", "Debes subir un archivo para este tipo de fuente.")
                form_errors = True

        if form_errors:
            # Let Django's add_error handle it, no need to clear fields unless we want to
            pass

        return cleaned_data


class DataSourceEditForm(forms.ModelForm):
    file = forms.FileField(
        label="Reemplazar archivo",
        required=False,
        help_text="Opcional. Sube un nuevo archivo .csv, .xlsx o .xls. (No requerido para Google Sheets o si mantienes el archivo actual).",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx,.xls"}),
    )

    class Meta:
        model = DataSource
        fields = ["name", "source_type", "is_active", "source_url", "file"]
        labels = {
            "name": "Nombre del dataset",
            "source_type": "Origen de datos",
            "is_active": "Dataset Activo",
            "source_url": "URL de Google Sheets",
        }
        help_texts = {
            "name": "Usa un nombre claro para identificar el dataset dentro del proyecto.",
            "source_type": "Elige CSV, Excel o Google Sheets.",
            "is_active": "Las fuentes de datos inactivas están ocultas y no disponibles para nuevas visualizaciones.",
            "source_url": "Actualiza la URL pública si vas a cambiar el origen a otra hoja de Google Sheets.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Ventas regionales 2026"}),
            "source_type": forms.Select(),
            "source_url": forms.URLInput(attrs={"placeholder": "https://docs.google.com/spreadsheets/d/..."}),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            widget_class = "dashboard-input"
            if isinstance(field.widget, forms.Select):
                widget_class = "dashboard-input dashboard-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                widget_class = ""

            existing_classes = field.widget.attrs.get("class", "")
            if widget_class:
                field.widget.attrs["class"] = f"{existing_classes} {widget_class}".strip()

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get("source_type")
        source_url = cleaned_data.get("source_url")
        file = cleaned_data.get("file")

        if source_type == DataSource.SourceType.GOOGLE_SHEETS:
            if not source_url:
                self.add_error("source_url", "Debes ingresar una URL de Google Sheets.")
        else:
            if not file and not getattr(self.instance, "file", None):
                self.add_error("file", "Debes subir un archivo para este tipo de fuente.")

        return cleaned_data


class PublicProfileForm(forms.ModelForm):
    skills_text = forms.CharField(
        label="Habilidades",
        required=False,
        help_text="Escribe tus habilidades separadas por coma. Ejemplo: Python, SQL, Data Visualization.",
        widget=forms.TextInput(attrs={"placeholder": "Python, SQL, Data Visualization"}),
    )

    class Meta:
        model = PublicProfile
        fields = ["display_name", "headline", "bio", "location"]
        labels = {
            "display_name": "Nombre para mostrar",
            "headline": "Titular",
            "bio": "Biografía",
            "location": "Ubicación",
        }
        help_texts = {
            "display_name": "Nombre que verán en el portafolio público.",
            "headline": "Una línea breve que resuma tu perfil.",
            "bio": "Un texto corto y profesional sobre tu trabajo o experiencia.",
            "location": "Ciudad, país o referencia geográfica opcional.",
        }
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "Ej. Laura Pérez"}),
            "headline": forms.TextInput(attrs={"placeholder": "Ej. Analista de datos y storytelling visual"}),
            "bio": forms.Textarea(attrs={"rows": 5, "placeholder": "Resume tu experiencia, enfoque y especialidad."}),
            "location": forms.TextInput(attrs={"placeholder": "Ej. Bogotá, Colombia"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        skills = []
        if self.instance and self.instance.pk:
            skills = [str(skill).strip() for skill in (self.instance.skills or []) if str(skill).strip()]
            external_links = self.instance.external_links if isinstance(self.instance.external_links, dict) else {}
            for slot in range(1, PROFILE_EXTERNAL_LINK_SLOTS + 1):
                label_key = f"external_link_{slot}_label"
                url_key = f"external_link_{slot}_url"
                link_label = ""
                link_url = ""
                if slot <= len(external_links):
                    try:
                        label, url = list(external_links.items())[slot - 1]
                    except (ValueError, IndexError):
                        label, url = "", ""
                    link_label = str(label).strip()
                    link_url = str(url).strip()
                self.fields[label_key].initial = link_label
                self.fields[url_key].initial = link_url

        self.fields["skills_text"].initial = ", ".join(skills)

        for field_name, field in self.fields.items():
            widget_class = "dashboard-input"
            if isinstance(field.widget, forms.Textarea):
                widget_class = "dashboard-input dashboard-textarea"
            elif isinstance(field.widget, forms.ClearableFileInput):
                widget_class = "dashboard-input"

            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} {widget_class}".strip()

    def _clean_skills(self):
        skills_text = self.cleaned_data.get("skills_text", "")
        return [skill.strip() for skill in skills_text.split(",") if skill.strip()]

    def _clean_external_links(self):
        external_links = {}
        for slot in range(1, PROFILE_EXTERNAL_LINK_SLOTS + 1):
            label = self.cleaned_data.get(f"external_link_{slot}_label", "").strip()
            url = self.cleaned_data.get(f"external_link_{slot}_url", "").strip()
            if label and url:
                external_links[label] = url
        return external_links

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.skills = self._clean_skills()
        instance.external_links = self._clean_external_links()
        if commit:
            instance.save()
        return instance


# for slot in range(1, PROFILE_EXTERNAL_LINK_SLOTS + 1):
#     PublicProfileForm.base_fields[f"external_link_{slot}_label"] = forms.CharField(
#         label=f"Enlace {slot} - texto",
#         required=False,
#         help_text="Ej. Sitio web, GitHub o LinkedIn.",
#         widget=forms.TextInput(attrs={"placeholder": "GitHub"}),
#     )
#     PublicProfileForm.base_fields[f"external_link_{slot}_url"] = forms.URLField(
#         label=f"Enlace {slot} - URL",
#         required=False,
#         help_text="Pega la URL completa del enlace.",
#         widget=forms.URLInput(attrs={"placeholder": "https://github.com/usuario"}),
#     )

# Definimos las listas de sugerencias en orden (slot 1, slot 2, etc.)
PLACEHOLDER_LABELS = ["Sitio web", "LinkedIn", "YouTube", "GitHub"]
PLACEHOLDER_URLS = [
    "https://tuweb.com",
    "https://linkedin.com",
    "https://youtube.com",
    "https://github.com/usuario"
]

for slot in range(1, PROFILE_EXTERNAL_LINK_SLOTS + 1):
    # Conseguimos el índice correspondiente (0 para el slot 1, 1 para el slot 2, etc.)
    # Si hay más slots que elementos en la lista, usamos "Sitio web" por defecto
    idx = slot - 1
    label_placeholder = PLACEHOLDER_LABELS[idx] if idx < len(PLACEHOLDER_LABELS) else "Sitio web"
    url_placeholder = PLACEHOLDER_URLS[idx] if idx < len(PLACEHOLDER_URLS) else "https://enlace.com"

    PublicProfileForm.base_fields[f"external_link_{slot}_label"] = forms.CharField(
        label=f"Enlace {slot} - texto",
        required=False,
        help_text="Ej. Sitio web, GitHub o LinkedIn.",
        widget=forms.TextInput(attrs={"placeholder": label_placeholder}),
    )
    PublicProfileForm.base_fields[f"external_link_{slot}_url"] = forms.URLField(
        label=f"Enlace {slot} - URL",
        required=False,
        help_text="Pega la URL completa del enlace.",
        widget=forms.URLInput(attrs={"placeholder": url_placeholder}),
    )


class VisualizationCreateForm(forms.ModelForm):
    VISUALIZATION_TYPE_CHOICES = [
        (ProjectVisualization.VisualizationType.BAR_CHART, "Barras"),
        (ProjectVisualization.VisualizationType.LINE_CHART, "Línea"),
        (ProjectVisualization.VisualizationType.SCATTER_PLOT, "Dispersión"),
        (ProjectVisualization.VisualizationType.PIE_CHART, "Torta"),
        (ProjectVisualization.VisualizationType.DATA_TABLE, "Tabla"),
        (ProjectVisualization.VisualizationType.KPI_CARD, "KPI"),
        (ProjectVisualization.VisualizationType.EXTERNAL_EMBED, "Embed externo (Tableau / Power BI / Looker Studio)"),
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
    embed_url = forms.CharField(
        label="URL del Dashboard Externo",
        required=False,
        help_text="Pega la URL para compartir de tu dashboard de Tableau Public, Power BI o Looker Studio.",
        widget=forms.URLInput(attrs={"placeholder": "https://public.tableau.com/views/..."}),
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
            "embed_url",
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
            "embed_url": "URL del Dashboard Externo",
            "display_order": "Orden",
            "is_active": "Activa",
        }
        help_texts = {
            "title": "Usa un título claro para identificar la visualización.",
            "visualization_type": "Elige el tipo visual que mejor represente el dato.",
            "x_axis_column": "Solo se muestran columnas recomendadas para el eje X.",
            "y_axis_column": "Solo se muestran columnas numéricas recomendadas para el eje Y.",
            "aggregation_method": "Selecciona cómo agrupar o resumir los datos.",
            "embed_url": "Pega la URL para compartir de tu dashboard de Tableau Public, Power BI o Looker Studio.",
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

    def clean_embed_url(self):
        value = (self.cleaned_data.get("embed_url") or "").strip()
        if not value:
            return value

        iframe_src_match = re.search(r'<iframe[^>]*\ssrc=["\']([^"\']+)["\']', value, re.IGNORECASE)
        if iframe_src_match:
            value = iframe_src_match.group(1).strip()

        value = value.replace("&amp;", "&")

        if "public.tableau.com/app/profile/" in value:
            path = value.split("?")[0].rstrip("/")
            path_parts = path.split("/")
            workbook_name, sheet_name = path_parts[-2], path_parts[-1]
            value = f"https://public.tableau.com/views/{workbook_name}/{sheet_name}"

        if "public.tableau.com" in value:
            base_url, _, query = value.partition("?")
            required_flags = {":showvizhome=no": ":showVizHome=no", ":embed=true": ":embed=true"}
            existing_flags = {flag.lower() for flag in query.split("&") if flag}
            missing_flags = [
                flag for key, flag in required_flags.items() if key not in existing_flags
            ]
            value = base_url + "?" + "&".join(filter(None, [query] + missing_flags)) if (query or missing_flags) else base_url

        validator = URLValidator()
        try:
            validator(value)
        except ValidationError:
            raise ValidationError("Ingresa una URL válida para el dashboard externo.")

        return value

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("visualization_type") == ProjectVisualization.VisualizationType.EXTERNAL_EMBED:
            if not cleaned_data.get("embed_url"):
                self.add_error("embed_url", "La URL del dashboard externo es obligatoria.")

        return cleaned_data
