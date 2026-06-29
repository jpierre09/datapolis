from django.contrib import admin

from .models import ProjectVisualization


@admin.register(ProjectVisualization)
class ProjectVisualizationAdmin(admin.ModelAdmin):
	list_display = (
		"title",
		"portfolio_project",
		"source_dataset",
		"visualization_type",
		"x_axis_column",
		"y_axis_column",
		"aggregation_method",
		"is_active",
		"display_order",
	)
	search_fields = (
		"title",
		"description",
		"portfolio_project__title",
		"source_dataset__name",
	)
	list_filter = ("visualization_type", "aggregation_method", "is_active")
