from django import forms

from apps.portfolio_projects.models import PortfolioProject


class ProjectCreateForm(forms.ModelForm):
    analysis_question = forms.CharField(label="Pregunta de análisis", widget=forms.Textarea(attrs={"rows": 4}))

    class Meta:
        model = PortfolioProject
        fields = ["title", "analysis_question", "project_type", "category"]
        labels = {
            "title": "Título",
            "project_type": "Tipo de proyecto",
            "category": "Categoría",
        }
