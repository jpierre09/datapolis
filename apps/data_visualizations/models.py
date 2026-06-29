from django.db import models

from apps.data_sources.models import DataSource
from apps.portfolio_projects.models import PortfolioProject


class ProjectVisualization(models.Model):
	class VisualizationType(models.TextChoices):
		BAR_CHART = "bar_chart", "Bar chart"
		LINE_CHART = "line_chart", "Line chart"
		SCATTER_PLOT = "scatter_plot", "Scatter plot"
		PIE_CHART = "pie_chart", "Pie chart"
		DATA_TABLE = "data_table", "Data table"
		KPI_CARD = "kpi_card", "KPI card"

	class AggregationMethod(models.TextChoices):
		NONE = "none", "None"
		SUM = "sum", "Sum"
		AVERAGE = "average", "Average"
		COUNT = "count", "Count"
		MINIMUM = "minimum", "Minimum"
		MAXIMUM = "maximum", "Maximum"

	portfolio_project = models.ForeignKey(
		PortfolioProject,
		on_delete=models.CASCADE,
		related_name="project_visualizations",
	)
	source_dataset = models.ForeignKey(
		DataSource,
		on_delete=models.CASCADE,
		related_name="project_visualizations",
	)
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	visualization_type = models.CharField(
		max_length=30,
		choices=VisualizationType.choices,
	)
	x_axis_column = models.CharField(max_length=120, blank=True)
	y_axis_column = models.CharField(max_length=120, blank=True)
	aggregation_method = models.CharField(
		max_length=20,
		choices=AggregationMethod.choices,
		default=AggregationMethod.NONE,
	)
	visualization_config = models.JSONField(default=dict, blank=True)
	display_order = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["portfolio_project", "display_order", "id"]

	def __str__(self):
		return self.title
