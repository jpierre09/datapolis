from django.contrib import admin

from .models import PortfolioProject, ProjectCategory, ProjectType


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "is_active", "updated_at")
	search_fields = ("name", "slug", "description")
	list_filter = ("is_active",)
	prepopulated_fields = {"slug": ("name",)}


@admin.register(ProjectType)
class ProjectTypeAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "is_active", "updated_at")
	search_fields = ("name", "slug", "description")
	list_filter = ("is_active",)
	prepopulated_fields = {"slug": ("name",)}


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
	list_display = (
		"title",
		"owner",
		"category",
		"project_type",
		"status",
		"updated_at",
	)
	search_fields = (
		"title",
		"slug",
		"question",
		"description",
		"findings",
		"conclusion",
		"owner__username",
		"owner__email",
	)
	list_filter = ("status", "category", "project_type", "created_at", "updated_at")
	prepopulated_fields = {"slug": ("title",)}
