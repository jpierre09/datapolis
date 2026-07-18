from django.conf import settings
from django.db import models


class ProjectCategory(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name"]
		verbose_name_plural = "Project categories"

	def __str__(self):
		return self.name


class ProjectType(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class PortfolioProject(models.Model):
	class Status(models.TextChoices):
		DRAFT = "draft", "Draft"
		PUBLISHED = "published", "Published"
		ARCHIVED = "archived", "Archived"

	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="portfolio_projects",
	)
	category = models.ForeignKey(
		ProjectCategory,
		on_delete=models.PROTECT,
		related_name="projects",
	)
	project_type = models.ForeignKey(
		ProjectType,
		on_delete=models.PROTECT,
		related_name="projects",
	)
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=220, unique=True)
	question = models.TextField()
	description = models.TextField()
	cover_image = models.ImageField(upload_to="project_covers/", blank=True, null=True)
	findings = models.TextField(blank=True)
	conclusion = models.TextField(blank=True)
	status = models.CharField(
		max_length=20,
		choices=Status.choices,
		default=Status.DRAFT,
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at", "title"]

	def __str__(self):
		return self.title
