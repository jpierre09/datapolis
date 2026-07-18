from django.http import HttpResponse
from django.shortcuts import render

from apps.data_visualizations.models import ProjectVisualization
from apps.portfolio_projects.models import PortfolioProject


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

	current_filter = request.GET.get("tipo", "todos")
	if current_filter == "embed":
		projects = projects.filter(
			project_visualizations__is_active=True,
			project_visualizations__visualization_type=ProjectVisualization.VisualizationType.EXTERNAL_EMBED,
		).distinct()
	elif current_filter == "dataset":
		projects = projects.filter(data_sources__is_active=True).exclude(data_sources__file="").distinct()
	else:
		current_filter = "todos"

	return render(
		request,
		"platform/explore.html",
		{
			"featured_project": featured_project,
			"projects": projects,
			"current_filter": current_filter,
		},
	)


def healthcheck(request):
	return HttpResponse("ok", content_type="text/plain")
