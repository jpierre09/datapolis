from django.db import models

from apps.portfolio_projects.models import PortfolioProject


class DataSource(models.Model):
	class SourceType(models.TextChoices):
		CSV = "csv", "CSV"
		EXCEL = "excel", "Excel"
		GOOGLE_SHEETS = "google_sheets", "Google Sheets"

	class ProcessingStatus(models.TextChoices):
		PENDING = "pending", "Pending"
		PROCESSED = "processed", "Processed"
		FAILED = "failed", "Failed"

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
	source_url = models.URLField(max_length=500, blank=True)
	file = models.FileField(upload_to="data_sources/", blank=True)
	original_filename = models.CharField(max_length=255, blank=True)
	columns_schema = models.JSONField(default=dict, blank=True)
	row_count = models.PositiveIntegerField(null=True, blank=True)
	processing_status = models.CharField(
		max_length=20,
		choices=ProcessingStatus.choices,
		default=ProcessingStatus.PENDING,
	)
	processing_error = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-uploaded_at"]

	def __str__(self):
		return self.name
