from django.contrib import admin

from .models import DataSource
from .services import extract_metadata


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
	list_display = ("name", "project", "source_type", "row_count", "is_active", "uploaded_at")
	search_fields = ("name", "original_filename", "project__title")
	list_filter = ("source_type", "is_active", "uploaded_at")
	readonly_fields = ("uploaded_at", "updated_at")

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		if obj.file and not obj.original_filename:
			obj.original_filename = obj.file.name.split("/")[-1]

		try:
			columns_schema = extract_metadata(obj)
			obj.columns_schema = columns_schema
			obj.row_count = columns_schema.get("row_count")
			obj.processing_status = DataSource.ProcessingStatus.PROCESSED
			obj.processing_error = ""
		except Exception as exc:
			obj.columns_schema = {}
			obj.row_count = None
			obj.processing_status = DataSource.ProcessingStatus.FAILED
			obj.processing_error = f"Metadata extraction failed: {exc}"

		obj.save(
			update_fields=[
				"original_filename",
				"columns_schema",
				"row_count",
				"processing_status",
				"processing_error",
				"updated_at",
			]
		)
