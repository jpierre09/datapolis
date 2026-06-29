from django.db import models

from apps.portfolio_projects.models import PortfolioProject


class DataSource(models.Model):
	class SourceType(models.TextChoices):
		CSV = "csv", "CSV"
		EXCEL = "excel", "Excel"

	project = models.ForeignKey(
		PortfolioProject,
		on_delete=models.CASCADE,
		related_name="data_sources",
	)
	name = models.CharField(max_length=200)
	source_type = models.CharField(
		max_length=20,
		choices=SourceType.choices,
	)
	file = models.FileField(upload_to="data_sources/")
	original_filename = models.CharField(max_length=255, blank=True)
	columns_schema = models.JSONField(default=dict, blank=True)
	row_count = models.PositiveIntegerField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-uploaded_at"]

	def __str__(self):
		return self.name
