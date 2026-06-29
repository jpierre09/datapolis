from django.shortcuts import get_object_or_404, render

from .models import PortfolioProject


def project_list(request):
	projects = (
		PortfolioProject.objects.filter(status=PortfolioProject.Status.PUBLISHED)
		.select_related("category", "project_type", "owner")
		.order_by("-created_at")
	)
	return render(request, "portfolio_projects/project_list.html", {"projects": projects})


def project_detail(request, slug):
	project = get_object_or_404(
		PortfolioProject.objects.select_related("category", "project_type", "owner"),
		slug=slug,
		status=PortfolioProject.Status.PUBLISHED,
	)
	return render(request, "portfolio_projects/project_detail.html", {"project": project})
