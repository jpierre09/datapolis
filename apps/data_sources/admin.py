from django.contrib import admin

from .models import DataSource


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
	list_display = ("name", "project", "source_type", "row_count", "is_active", "uploaded_at")
	search_fields = ("name", "original_filename", "project__title")
	list_filter = ("source_type", "is_active", "uploaded_at")
	readonly_fields = ("uploaded_at", "updated_at")
