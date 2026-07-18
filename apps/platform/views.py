from django.http import HttpResponse
from django.shortcuts import render

from apps.portfolio_projects.models import PortfolioProject, ProjectCategory


def home(request):
	return render(request, "public_pages/home.html")


def project_explore(request):
	published = (
		PortfolioProject.objects.filter(status=PortfolioProject.Status.PUBLISHED)
		.select_related("category", "project_type", "owner", "owner__public_profile")
		.order_by("-created_at")
	)

	featured_project = (
		published.exclude(cover_image__isnull=True).exclude(cover_image="").first()
	)

	projects = published
	if featured_project:
		projects = projects.exclude(pk=featured_project.pk)

	categories = (
		ProjectCategory.objects.filter(
			is_active=True,
			projects__status=PortfolioProject.Status.PUBLISHED,
		)
		.distinct()
		.order_by("name")
	)

	current_category_slug = request.GET.get("categoria", "todos")
	if current_category_slug != "todos":
		if categories.filter(slug=current_category_slug).exists():
			projects = projects.filter(category__slug=current_category_slug)
		else:
			current_category_slug = "todos"

	return render(
		request,
		"platform/explore.html",
		{
			"featured_project": featured_project,
			"projects": projects,
			"categories": categories,
			"current_category_slug": current_category_slug,
		},
	)


def healthcheck(request):
	return HttpResponse("ok", content_type="text/plain")
